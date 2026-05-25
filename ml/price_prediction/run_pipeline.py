"""
Main orchestrator for the product price prediction pipeline.
"""

import json
import logging
import sys
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from ml.core.artifacts import (
    ArtifactRun,
    begin_latest_artifact_run,
    discard_staged_artifact,
    publish_latest_artifact,
    validate_artifact_files,
)

from .compare_models import comparison_frame, evaluate_regression, select_best_model
from .config import Config, cfg
from .data_loader import load_product_training_data
from .persistence import register_price_prediction_model
from .plots import (
    plot_actual_vs_predicted,
    plot_feature_correlation,
    plot_model_performance,
    plot_price_distribution,
)
from .preprocessing import (
    PreprocessingProfile,
    build_feature_frame_for_profile,
    build_feature_frame_from_cleaned,
    clean_price_data,
    feature_columns,
)
from .train_baseline import build_baseline_pipeline
from .train_model import build_performant_pipeline


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("price_prediction_pipeline")


def _time_aware_split(
    prepared: pd.DataFrame,
    cleaned: pd.DataFrame,
    config: Config,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    meta = pd.DataFrame(
        {
            "row_index": np.arange(len(prepared)),
            "product_id": cleaned["product_id"].reset_index(drop=True).iloc[: len(prepared)].to_numpy(),
            "created_at": pd.to_datetime(
                cleaned["created_at"].reset_index(drop=True).iloc[: len(prepared)],
                errors="coerce",
            ),
        }
    )
    meta = meta.sort_values(["created_at", "product_id"], na_position="first").reset_index(drop=True)
    split_at = int(len(meta) * (1 - config.model.test_size))
    if split_at <= 0 or split_at >= len(meta):
        raise ValueError("Not enough price rows for time-aware train/test split.")

    train_meta = meta.iloc[:split_at].copy()
    test_meta = meta.iloc[split_at:].copy()
    return (
        train_meta["row_index"].to_numpy(),
        test_meta["row_index"].to_numpy(),
        {
            "type": "time_aware_product_created_at",
            "train_rows": int(len(train_meta)),
            "test_rows": int(len(test_meta)),
            "train_max_created_at": str(train_meta["created_at"].max()),
            "test_min_created_at": str(test_meta["created_at"].min()),
        },
    )


def _train_profile_models(df, profile: PreprocessingProfile, config: Config = cfg) -> tuple[dict[str, dict[str, Any]], Any, dict[str, Any]]:
    cleaned = None
    if profile == "improved":
        cleaned, report = clean_price_data(df, config=config, include_target=True)
        prepared = build_feature_frame_from_cleaned(cleaned, config=config, include_target=True)
    else:
        prepared, report = build_feature_frame_for_profile(
            df,
            config=config,
            profile=profile,
            include_target=True,
            return_report=True,
        )
    if len(prepared) < config.model.min_training_rows:
        raise ValueError(
            f"Need at least {config.model.min_training_rows} product rows to train {profile} price prediction; got {len(prepared)}."
        )

    columns = feature_columns(config, profile)
    X = prepared[columns]
    y = prepared[config.features.target_col].astype(float)
    if cleaned is not None:
        train_idx, test_idx, split_strategy = _time_aware_split(prepared, cleaned, config)
        X_train = X.iloc[train_idx].reset_index(drop=True)
        X_test = X.iloc[test_idx].reset_index(drop=True)
        y_train = y.iloc[train_idx].reset_index(drop=True)
        y_test = y.iloc[test_idx].reset_index(drop=True)
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=config.model.test_size,
            random_state=config.model.random_state,
        )
        split_strategy = {
            "type": "random",
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
        }

    candidates = {
        config.model.baseline_name: build_baseline_pipeline(
            config,
            profile=profile,
            use_log_target=profile == "improved" and config.model.baseline_use_log_target,
        ),
        config.model.performant_name: build_performant_pipeline(
            config,
            profile=profile,
            use_log_target=profile == "improved" and config.model.performant_use_log_target,
        ),
    }

    results: dict[str, dict[str, Any]] = {}
    for name, pipeline in candidates.items():
        logger.info("Training price prediction model: %s (%s preprocessing)", name, profile)
        pipeline.fit(X_train, y_train)
        train_predictions = pipeline.predict(X_train)
        predictions = pipeline.predict(X_test)
        result_key = name if profile == "improved" else f"{profile}__{name}"
        results[result_key] = {
            "pipeline": pipeline,
            "predictions": predictions,
            "train_metrics": evaluate_regression(y_train, train_predictions),
            "metrics": evaluate_regression(y_test, predictions),
            "profile": profile,
            "model_name": name,
            "use_log_target": (
                profile == "improved"
                and (
                    config.model.baseline_use_log_target
                    if name == config.model.baseline_name
                    else config.model.performant_use_log_target
                )
            ),
            "y_test": y_test,
            "split_strategy": split_strategy,
        }
        joblib.dump(pipeline, config.models_dir / f"{profile}_{name}.pkl")

    return results, prepared, report


def _required_price_artifact_files(config: Config) -> list[str]:
    return [
        "model/best_model.pkl",
        f"model/improved_{config.model.baseline_name}.pkl",
        f"model/improved_{config.model.performant_name}.pkl",
        "metadata/metadata.json",
        "reports/model_comparison.csv",
        "reports/preprocessing_report.json",
        "data/raw/products_price_raw.csv",
        "data/processed/products_price_preprocessed.csv",
        "plots/price_distribution.png",
        "plots/feature_correlation.png",
        "plots/actual_vs_predicted_price.png",
        "plots/model_performance_comparison.png",
    ]


def train_price_prediction_models(
    df,
    config: Config = cfg,
    artifact_run: ArtifactRun | None = None,
    local_config: Config | None = None,
) -> dict[str, Any]:
    """Train, evaluate, compare, and persist final baseline/performance models."""
    if artifact_run is None:
        artifact_run, local_config = begin_latest_artifact_run(config)
    run = artifact_run
    lcfg = local_config or config
    try:
        lcfg.raw_data_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(lcfg.raw_data_dir / "products_price_raw.csv", index=False)
        improved_results, improved_prepared, improved_report = _train_profile_models(df, "improved", config=lcfg)
        results = improved_results

        best_name = select_best_model(results)
        best_pipeline = results[best_name]["pipeline"]
        joblib.dump(best_pipeline, lcfg.models_dir / "best_model.pkl")

        metrics_by_model = {name: data["metrics"] for name, data in results.items()}
        comparison = comparison_frame(results, config=lcfg)
        lcfg.processed_data_dir.mkdir(parents=True, exist_ok=True)
        improved_prepared.to_csv(lcfg.processed_data_dir / "products_price_preprocessed.csv", index=False)

        plot_price_distribution(improved_prepared, config=lcfg)
        plot_feature_correlation(improved_prepared, config=lcfg)
        plot_actual_vs_predicted(results[best_name]["y_test"], results[best_name]["predictions"], best_name, config=lcfg)
        plot_model_performance(metrics_by_model, config=lcfg)

        preprocessing_report = {
            "improved": improved_report,
            "leakage_controls": [
                "category_id and subcategory_id are excluded from the improved model features",
                "final_price is excluded because it is computed from price",
                "encoders/scalers are fitted only on the training split inside sklearn pipelines",
                "the improved baseline uses log1p target transformation and inverse predictions with expm1",
                "log target transformation is disabled for RandomForest when it worsens validation RMSE",
            ],
        }
        with open(lcfg.reports_dir / "preprocessing_report.json", "w", encoding="utf-8") as f:
            json.dump(preprocessing_report, f, indent=2)

        metadata = {
            "model_name": lcfg.price_model_name,
            "model_version": lcfg.price_model_version,
            "best_model": results[best_name]["model_name"],
            "best_profile": results[best_name]["profile"],
            "best_result_key": best_name,
            "metrics": metrics_by_model,
            "train_metrics": {name: data["train_metrics"] for name, data in results.items()},
            "split_strategy": results[best_name]["split_strategy"],
            "feature_columns": feature_columns(lcfg, results[best_name]["profile"]),
            "target": lcfg.features.target_col,
            "artifact_policy": "latest_valid_only",
            "pricing_signal_sources": {
                "sales_history": "order_items joined to orders",
                "historical_price_proxy": "order_items.unit_price",
                "stock_movement": "order quantities and current product stock",
                "product_demand": "user_interactions, cart_items, wishlists, reviews",
                "category_price_priors": "train-only target mean encoding inside sklearn pipeline",
            },
            "preprocessing_report": preprocessing_report,
            "comparison": comparison.to_dict(orient="records"),
        }
        lcfg.metadata_dir.mkdir(parents=True, exist_ok=True)
        with open(lcfg.metadata_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        validate_artifact_files(run.staging_root, _required_price_artifact_files(lcfg))
        publish_latest_artifact(config, run)

        return {
            "best_model": best_name,
            "best_profile": results[best_name]["profile"],
            "metrics_by_model": metrics_by_model,
            "comparison": comparison,
            "artifact_path": str(config.models_dir / "best_model.pkl"),
            "artifact_root": str(config.artifacts_dir),
            "metadata": metadata,
        }
    except Exception:
        discard_staged_artifact(config, run)
        raise


def run_price_prediction_pipeline(config: Config = cfg, force_reload: bool = False) -> dict[str, Any]:
    """Run the full DB-backed price prediction training workflow."""
    logger.info("STARTING PRICE PREDICTION PIPELINE")
    artifact_run, local_config = begin_latest_artifact_run(config)
    try:
        df_raw = load_product_training_data(config=local_config, force_reload=True)
        results = train_price_prediction_models(
            df_raw, config=config, artifact_run=artifact_run, local_config=local_config,
        )
    except Exception:
        discard_staged_artifact(config, artifact_run)
        raise

    register_price_prediction_model(
        algorithm=results["metadata"]["best_result_key"],
        metrics=results["metrics_by_model"][results["best_model"]],
        parameters={
            "baseline_model": config.model.baseline_name,
            "performant_model": config.model.performant_name,
            "preprocessing_profile": results["best_profile"],
            "baseline_use_log_target": config.model.baseline_use_log_target,
            "performant_use_log_target": config.model.performant_use_log_target,
            "features": feature_columns(config, results["best_profile"]),
            "target": config.features.target_col,
        },
        artifact_path=results["artifact_path"],
        config=config,
    )

    print("\n" + "=" * 50)
    print("PRICE PREDICTION PIPELINE RESULT")
    print("=" * 50)
    print(f"Best model: {results['best_model']} ({results['best_profile']} preprocessing)")
    for model_name, metrics in results["metrics_by_model"].items():
        print(
            f"- {model_name}: MAE={metrics['mae']:.2f}, MSE={metrics['mse']:.2f}, "
            f"RMSE={metrics['rmse']:.2f}, R2={metrics['r2']:.4f}"
        )
    print("=" * 50 + "\n")

    return results


if __name__ == "__main__":
    run_price_prediction_pipeline()
