"""
Main orchestrator for the product price prediction pipeline.
"""

import json
import logging
import sys
from typing import Any

import joblib
from sklearn.model_selection import train_test_split

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
from .preprocessing import PreprocessingProfile, build_feature_frame_for_profile, feature_columns
from .train_baseline import build_baseline_pipeline
from .train_model import build_performant_pipeline


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("price_prediction_pipeline")


def _train_profile_models(df, profile: PreprocessingProfile, config: Config = cfg) -> tuple[dict[str, dict[str, Any]], Any, dict[str, Any]]:
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
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.model.test_size,
        random_state=config.model.random_state,
    )

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
        predictions = pipeline.predict(X_test)
        result_key = f"{profile}__{name}"
        results[result_key] = {
            "pipeline": pipeline,
            "predictions": predictions,
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
        }
        joblib.dump(pipeline, config.models_dir / f"{profile}_{name}.pkl")

    return results, prepared, report


def train_price_prediction_models(df, config: Config = cfg) -> dict[str, Any]:
    """Train, evaluate, compare, and persist legacy and improved models."""
    legacy_results, legacy_prepared, legacy_report = _train_profile_models(df, "legacy", config=config)
    improved_results, improved_prepared, improved_report = _train_profile_models(df, "improved", config=config)
    results = {**legacy_results, **improved_results}

    best_name = select_best_model(results)
    best_pipeline = results[best_name]["pipeline"]
    joblib.dump(best_pipeline, config.models_dir / "best_model.pkl")

    metrics_by_model = {name: data["metrics"] for name, data in results.items()}
    comparison = comparison_frame(results, config=config)
    legacy_prepared.to_csv(config.data_dir / "products_price_legacy_preprocessed.csv", index=False)
    improved_prepared.to_csv(config.data_dir / "products_price_preprocessed.csv", index=False)

    plot_price_distribution(improved_prepared, config=config)
    plot_feature_correlation(improved_prepared, config=config)
    plot_actual_vs_predicted(results[best_name]["y_test"], results[best_name]["predictions"], best_name, config=config)
    plot_model_performance(metrics_by_model, config=config)

    preprocessing_report = {
        "legacy": legacy_report,
        "improved": improved_report,
        "leakage_controls": [
            "category_id and subcategory_id are excluded from the improved model features",
            "final_price is excluded because it is computed from price",
            "encoders/scalers are fitted only on the training split inside sklearn pipelines",
            "the improved baseline uses log1p target transformation and inverse predictions with expm1",
            "log target transformation is disabled for RandomForest when it worsens validation RMSE",
        ],
    }
    with open(config.reports_dir / "preprocessing_report.json", "w", encoding="utf-8") as f:
        json.dump(preprocessing_report, f, indent=2)

    metadata = {
        "model_name": config.price_model_name,
        "model_version": config.price_model_version,
        "best_model": results[best_name]["model_name"],
        "best_profile": results[best_name]["profile"],
        "best_result_key": best_name,
        "metrics": metrics_by_model,
        "feature_columns": feature_columns(config, results[best_name]["profile"]),
        "target": config.features.target_col,
        "preprocessing_report": preprocessing_report,
        "comparison": comparison.to_dict(orient="records"),
    }
    with open(config.models_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return {
        "best_model": best_name,
        "best_profile": results[best_name]["profile"],
        "metrics_by_model": metrics_by_model,
        "comparison": comparison,
        "artifact_path": str(config.models_dir / "best_model.pkl"),
        "metadata": metadata,
    }


def run_price_prediction_pipeline(config: Config = cfg, force_reload: bool = False) -> dict[str, Any]:
    """Run the full DB-backed price prediction training workflow."""
    logger.info("STARTING PRICE PREDICTION PIPELINE")
    df_raw = load_product_training_data(config=config, force_reload=force_reload)
    results = train_price_prediction_models(df_raw, config=config)

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
