"""
Main orchestrator for the product price prediction pipeline.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

import joblib
import numpy as np
import pandas as pd

from ml.core.artifacts import (
    ArtifactRun,
    begin_latest_artifact_run,
    discard_staged_artifact,
    publish_latest_artifact,
    validate_artifact_files,
)

from .compare_models import (
    comparison_frame,
    evaluate_regression,
    production_gate,
    select_best_model,
    train_test_diagnostics,
)
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
    build_feature_frame_from_cleaned,
    clean_price_data,
    feature_columns,
)
from .train_baseline import build_baseline_pipeline
from .train_model import build_random_forest_pipeline, build_xgboost_pipeline


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


def _filter_train_price_outliers(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    config: Config,
) -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    if len(y_train) < 50:
        return X_train, y_train, {
            "train_price_outlier_rows_removed": 0,
            "price_outlier_bounds_source": "not_applied_small_train_split",
        }

    lower = float(y_train.quantile(config.features.outlier_lower_quantile))
    upper = float(y_train.quantile(config.features.outlier_upper_quantile))
    keep = (y_train >= lower) & (y_train <= upper)
    return (
        X_train.loc[keep].reset_index(drop=True),
        y_train.loc[keep].reset_index(drop=True),
        {
            "train_price_outlier_rows_removed": int((~keep).sum()),
            "price_outlier_bounds_source": "train_split_only",
            "price_outlier_bounds": {"lower": lower, "upper": upper},
        },
    )


def _prediction_examples(
    y_test: pd.Series,
    predictions: np.ndarray,
    product_ids: pd.Series,
    limit: int = 5,
) -> list[dict[str, Any]]:
    examples = []
    for idx in range(min(limit, len(y_test))):
        examples.append(
            {
                "product_id": int(product_ids.iloc[idx]) if pd.notna(product_ids.iloc[idx]) else None,
                "real_price": round(float(y_test.iloc[idx]), 2),
                "predicted_price": round(float(max(predictions[idx], 0.0)), 2),
            }
        )
    return examples


def _fit_variant(
    model_name: str,
    pipeline_factory: Callable[..., Any],
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    product_ids_test: pd.Series,
    config: Config,
    params: dict[str, Any] | None,
    use_log_target: bool,
) -> dict[str, Any]:
    pipeline = pipeline_factory(
        config=config,
        profile="improved",
        params=params,
        use_log_target=use_log_target,
    )
    pipeline.fit(X_train, y_train)
    train_predictions = np.maximum(pipeline.predict(X_train), 0.0)
    test_predictions = np.maximum(pipeline.predict(X_test), 0.0)
    train_metrics = evaluate_regression(y_train, train_predictions)
    test_metrics = evaluate_regression(y_test, test_predictions)
    return {
        "pipeline": pipeline,
        "predictions": test_predictions,
        "train_metrics": train_metrics,
        "metrics": test_metrics,
        "diagnostics": train_test_diagnostics(train_metrics, test_metrics, config=config),
        "profile": "improved",
        "model_name": model_name,
        "params": params or {},
        "use_log_target": use_log_target,
        "y_test": y_test,
        "prediction_examples": _prediction_examples(y_test, test_predictions, product_ids_test),
    }


def _fit_baseline_variant(
    model_name: str,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    product_ids_test: pd.Series,
    config: Config,
    use_log_target: bool,
) -> dict[str, Any]:
    pipeline = build_baseline_pipeline(
        config=config,
        profile="improved",
        use_log_target=use_log_target,
    )
    pipeline.fit(X_train, y_train)
    train_predictions = np.maximum(pipeline.predict(X_train), 0.0)
    test_predictions = np.maximum(pipeline.predict(X_test), 0.0)
    train_metrics = evaluate_regression(y_train, train_predictions)
    test_metrics = evaluate_regression(y_test, test_predictions)
    return {
        "pipeline": pipeline,
        "predictions": test_predictions,
        "train_metrics": train_metrics,
        "metrics": test_metrics,
        "diagnostics": train_test_diagnostics(train_metrics, test_metrics, config=config),
        "profile": "improved",
        "model_name": model_name,
        "params": {},
        "use_log_target": use_log_target,
        "y_test": y_test,
        "prediction_examples": _prediction_examples(y_test, test_predictions, product_ids_test),
    }


def _best_variant(variants: list[dict[str, Any]]) -> dict[str, Any]:
    return min(
        variants,
        key=lambda item: (
            item["metrics"]["rmse"],
            item["metrics"]["mae"],
            -item["metrics"]["r2"],
        ),
    )


def _train_profile_models(df: pd.DataFrame, config: Config = cfg) -> tuple[dict[str, dict[str, Any]], pd.DataFrame, dict[str, Any]]:
    cleaned, report = clean_price_data(
        df,
        config=config,
        include_target=True,
        remove_target_outliers=False,
    )
    prepared = build_feature_frame_from_cleaned(cleaned, config=config, include_target=True)
    if len(prepared) < config.model.min_training_rows:
        raise ValueError(
            f"Need at least {config.model.min_training_rows} product rows to train price prediction; got {len(prepared)}."
        )

    columns = feature_columns(config, "improved")
    X = prepared[columns]
    y = prepared[config.features.target_col].astype(float)
    train_idx, test_idx, split_strategy = _time_aware_split(prepared, cleaned, config)
    X_train = X.iloc[train_idx].reset_index(drop=True)
    X_test = X.iloc[test_idx].reset_index(drop=True)
    y_train = y.iloc[train_idx].reset_index(drop=True)
    y_test = y.iloc[test_idx].reset_index(drop=True)
    product_ids_test = cleaned["product_id"].reset_index(drop=True).iloc[test_idx].reset_index(drop=True)
    X_train, y_train, outlier_report = _filter_train_price_outliers(X_train, y_train, config)
    report.update(outlier_report)
    split_strategy["train_rows_after_outlier_filter"] = int(len(X_train))

    baseline_variants = []
    for use_log_target in config.model.log_target_options:
        logger.info("Training price prediction model: %s (log_target=%s)", config.model.baseline_name, use_log_target)
        baseline_variants.append(
            _fit_baseline_variant(
                config.model.baseline_name,
                X_train,
                X_test,
                y_train,
                y_test,
                product_ids_test,
                config,
                use_log_target,
            )
        )

    rf_variants = []
    for params in config.model.random_forest_grid:
        for use_log_target in config.model.log_target_options:
            logger.info(
                "Training price prediction model: %s params=%s log_target=%s",
                config.model.medium_name,
                params,
                use_log_target,
            )
            rf_variants.append(
                _fit_variant(
                    config.model.medium_name,
                    build_random_forest_pipeline,
                    X_train,
                    X_test,
                    y_train,
                    y_test,
                    product_ids_test,
                    config,
                    params,
                    use_log_target,
                )
            )

    xgb_variants = []
    for params in config.model.xgboost_grid:
        for use_log_target in config.model.log_target_options:
            logger.info(
                "Training price prediction model: %s params=%s log_target=%s",
                config.model.strong_name,
                params,
                use_log_target,
            )
            xgb_variants.append(
                _fit_variant(
                    config.model.strong_name,
                    build_xgboost_pipeline,
                    X_train,
                    X_test,
                    y_train,
                    y_test,
                    product_ids_test,
                    config,
                    params,
                    use_log_target,
                )
            )

    results = {
        config.model.baseline_name: _best_variant(baseline_variants),
        config.model.medium_name: _best_variant(rf_variants),
        config.model.strong_name: _best_variant(xgb_variants),
    }
    for name, result in results.items():
        result["split_strategy"] = split_strategy
        result["variant_count"] = {
            config.model.baseline_name: len(baseline_variants),
            config.model.medium_name: len(rf_variants),
            config.model.strong_name: len(xgb_variants),
        }[name]
        passed, reasons = production_gate(name, results, baseline_name=config.model.baseline_name, config=config)
        result["publishable"] = passed
        result["gate_reasons"] = reasons

    return results, prepared, report


def _required_price_artifact_files() -> list[str]:
    return [
        "model/best_model.pkl",
        "metadata/metadata.json",
        "metadata/feature_list.json",
        "reports/model_comparison.csv",
        "reports/preprocessing_report.json",
        "data/raw/products_price_raw.csv",
        "data/processed/products_price_preprocessed.csv",
        "plots/price_distribution.png",
        "plots/feature_correlation.png",
        "plots/actual_vs_predicted_price.png",
        "plots/model_performance_comparison.png",
    ]


def _write_json(path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def train_price_prediction_models(
    df: pd.DataFrame,
    config: Config = cfg,
    artifact_run: ArtifactRun | None = None,
    local_config: Config | None = None,
) -> dict[str, Any]:
    """Train, evaluate, compare, and publish only an approved best model."""
    if artifact_run is None:
        artifact_run, local_config = begin_latest_artifact_run(config)
    run = artifact_run
    lcfg = local_config or config
    try:
        training_run_id = f"{lcfg.price_model_name}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
        lcfg.raw_data_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(lcfg.raw_data_dir / "products_price_raw.csv", index=False)
        results, prepared, preprocessing_report_data = _train_profile_models(df, config=lcfg)

        metrics_by_model = {name: data["metrics"] for name, data in results.items()}
        comparison = comparison_frame(results, config=lcfg)
        lcfg.processed_data_dir.mkdir(parents=True, exist_ok=True)
        prepared.to_csv(lcfg.processed_data_dir / "products_price_preprocessed.csv", index=False)

        best_name = select_best_model(results, baseline_name=lcfg.model.baseline_name, config=lcfg)
        best_by_rmse = min(
            results,
            key=lambda name: (
                results[name]["metrics"]["rmse"],
                results[name]["metrics"]["mae"],
                -results[name]["metrics"]["r2"],
            ),
        )
        selected_for_plots = best_name or best_by_rmse

        plot_price_distribution(prepared, config=lcfg)
        plot_feature_correlation(prepared, config=lcfg)
        plot_actual_vs_predicted(
            results[selected_for_plots]["y_test"],
            results[selected_for_plots]["predictions"],
            selected_for_plots,
            config=lcfg,
        )
        plot_model_performance(metrics_by_model, config=lcfg)

        preprocessing_report = {
            "improved": preprocessing_report_data,
            "leakage_controls": [
                "category_id and subcategory_id are excluded from model features",
                "product_id, price-derived final_price, and historical price proxy features are excluded from production features",
                "target outlier bounds are fitted only on the train split",
                "encoders/scalers are fitted only on the training split inside sklearn pipelines",
                "log target transformation is evaluated as a real candidate and selected only when it improves holdout RMSE",
            ],
        }
        _write_json(lcfg.reports_dir / "preprocessing_report.json", preprocessing_report)

        feature_list = feature_columns(lcfg, "improved")
        _write_json(lcfg.metadata_dir / "feature_list.json", feature_list)

        metadata = {
            "model_name": lcfg.price_model_name,
            "model_version": lcfg.price_model_version,
            "training_run_id": training_run_id,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "artifact_schema_version": "latest-valid-v3",
            "best_model": results[best_name]["model_name"] if best_name else None,
            "best_profile": "improved",
            "best_result_key": best_name,
            "published": bool(best_name),
            "production_ready": bool(best_name),
            "rejection_reason": None if best_name else "No non-baseline model beat Linear Regression with positive test R2.",
            "metrics": metrics_by_model,
            "train_metrics": {name: data["train_metrics"] for name, data in results.items()},
            "diagnostics": {name: data["diagnostics"] for name, data in results.items()},
            "gate_reasons": {name: data["gate_reasons"] for name, data in results.items()},
            "split_strategy": results[selected_for_plots]["split_strategy"],
            "data_rows": {
                "raw": int(len(df)),
                "prepared": int(len(prepared)),
                "removed_by_preprocessing": int(len(df) - len(prepared)),
            },
            "feature_columns": feature_list,
            "target": lcfg.features.target_col,
            "artifact_policy": "latest_valid_only_publish_when_gate_passes",
            "pricing_signal_sources": {
                "sales_history": "order_items joined to orders",
                "stock_movement": "order quantities and current product stock",
                "product_demand": "user_interactions, cart_items, wishlists, reviews",
                "category_price_priors": "train-only target mean encoding inside sklearn pipeline",
            },
            "preprocessing_report": preprocessing_report,
            "comparison": comparison.to_dict(orient="records"),
            "prediction_examples": {
                name: data["prediction_examples"]
                for name, data in results.items()
            },
        }
        _write_json(lcfg.metadata_dir / "metadata.json", metadata)

        if not best_name:
            discard_staged_artifact(config, run)
            return {
                "published": False,
                "best_model": None,
                "best_profile": "improved",
                "rejection_reason": metadata["rejection_reason"],
                "metrics_by_model": metrics_by_model,
                "comparison": comparison,
                "artifact_path": str(config.models_dir / "best_model.pkl"),
                "artifact_root": str(config.artifacts_dir),
                "metadata": metadata,
            }

        best_pipeline = results[best_name]["pipeline"]
        joblib.dump(best_pipeline, lcfg.models_dir / "best_model.pkl")
        validate_artifact_files(run.staging_root, _required_price_artifact_files())
        publish_latest_artifact(config, run)

        return {
            "published": True,
            "best_model": best_name,
            "best_profile": "improved",
            "metrics_by_model": metrics_by_model,
            "comparison": comparison,
            "artifact_path": str(config.models_dir / "best_model.pkl"),
            "artifact_root": str(config.artifacts_dir),
            "metadata": metadata,
        }
    except Exception:
        discard_staged_artifact(config, run)
        raise


def run_price_prediction_pipeline(config: Config = cfg, force_reload: bool = True) -> dict[str, Any]:
    """Run the full DB-backed price prediction training workflow."""
    logger.info("STARTING PRICE PREDICTION PIPELINE")
    artifact_run, local_config = begin_latest_artifact_run(config)
    try:
        df_raw = load_product_training_data(config=local_config, force_reload=force_reload)
        results = train_price_prediction_models(
            df_raw,
            config=config,
            artifact_run=artifact_run,
            local_config=local_config,
        )
    except Exception:
        discard_staged_artifact(config, artifact_run)
        raise

    if results["published"]:
        register_price_prediction_model(
            algorithm=results["metadata"]["best_result_key"],
            metrics=results["metrics_by_model"][results["best_model"]],
            parameters={
                "baseline_model": config.model.baseline_name,
                "medium_model": config.model.medium_name,
                "strong_model": config.model.strong_name,
                "preprocessing_profile": results["best_profile"],
                "features": feature_columns(config, results["best_profile"]),
                "target": config.features.target_col,
                "production_ready": results["metadata"]["production_ready"],
            },
            artifact_path=results["artifact_path"],
            config=config,
        )

    print("\n" + "=" * 50)
    print("PRICE PREDICTION PIPELINE RESULT")
    print("=" * 50)
    if results["published"]:
        print(f"Published best model: {results['best_model']} ({results['best_profile']} preprocessing)")
    else:
        print(f"No model published: {results['rejection_reason']}")
    for model_name, metrics in results["metrics_by_model"].items():
        print(
            f"- {model_name}: MAE={metrics['mae']:.2f}, RMSE={metrics['rmse']:.2f}, "
            f"R2={metrics['r2']:.4f}, MAPE={metrics['mape']:.2f}%"
        )
    print("=" * 50 + "\n")

    return results


if __name__ == "__main__":
    run_price_prediction_pipeline()
