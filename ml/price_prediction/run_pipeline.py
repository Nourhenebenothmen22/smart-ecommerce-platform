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


def _to_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_builtin(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_builtin(item) for item in value]
    if isinstance(value, tuple):
        return [_to_builtin(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.ndarray, pd.Series)):
        return [_to_builtin(item) for item in value.tolist()]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _fitted_regressor(pipeline: Any) -> Any:
    if hasattr(pipeline, "regressor_"):
        return pipeline.regressor_
    if hasattr(pipeline, "regressor"):
        return pipeline.regressor
    return pipeline


def _fitted_preprocessor(pipeline: Any) -> Any:
    regressor = _fitted_regressor(pipeline)
    preprocessor = getattr(regressor, "named_steps", {}).get("preprocessor")
    if preprocessor is None:
        raise RuntimeError("Trained price prediction pipeline is missing its preprocessing step.")
    return preprocessor


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


def _target_summary(y: pd.Series) -> dict[str, Any]:
    values = pd.to_numeric(y, errors="coerce").dropna()
    if values.empty:
        return {"count": 0}
    return {
        "count": int(len(values)),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "std": float(values.std(ddof=0)),
        "min": float(values.min()),
        "max": float(values.max()),
        "skew": float(values.skew()) if len(values) > 2 else 0.0,
        "quantiles": {
            "p01": float(values.quantile(0.01)),
            "p05": float(values.quantile(0.05)),
            "p25": float(values.quantile(0.25)),
            "p75": float(values.quantile(0.75)),
            "p95": float(values.quantile(0.95)),
            "p99": float(values.quantile(0.99)),
        },
    }


def _categorical_quality(frame: pd.DataFrame, config: Config) -> dict[str, Any]:
    quality: dict[str, Any] = {}
    for column in config.features.categorical_features:
        if column not in frame.columns:
            continue
        series = frame[column].fillna("unknown").astype(str)
        counts = series.value_counts(dropna=False)
        quality[column] = {
            "unique_values": int(series.nunique(dropna=False)),
            "unknown_rate": float(series.str.lower().isin({"", "unknown", "none", "nan"}).mean()),
            "top_value_share": float(counts.iloc[0] / len(series)) if len(series) else 0.0,
        }
    return quality


def _feature_signal_report(prepared: pd.DataFrame, config: Config) -> dict[str, Any]:
    target = config.features.target_col
    numeric_features = [column for column in config.features.numeric_features if column in prepared.columns]
    correlations: dict[str, float] = {}
    for column in numeric_features:
        series = pd.to_numeric(prepared[column], errors="coerce")
        if series.nunique(dropna=True) <= 1:
            continue
        corr = series.corr(prepared[target].astype(float), method="spearman")
        if pd.notna(corr):
            correlations[column] = float(abs(corr))

    ordered = sorted(correlations.items(), key=lambda item: item[1], reverse=True)
    zero_variance = [
        column
        for column in numeric_features
        if pd.to_numeric(prepared[column], errors="coerce").nunique(dropna=True) <= 1
    ]
    return {
        "numeric_feature_count": int(len(numeric_features)),
        "zero_variance_numeric_features": zero_variance,
        "top_abs_spearman_correlations": [
            {"feature": feature, "abs_spearman_corr": value}
            for feature, value in ordered[:10]
        ],
        "max_abs_spearman_corr": float(ordered[0][1]) if ordered else 0.0,
        "features_with_abs_corr_at_least_0_10": int(sum(value >= 0.10 for value in correlations.values())),
    }


def _split_quality_report(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    config: Config,
) -> dict[str, Any]:
    categorical_coverage: dict[str, Any] = {}
    for column in ["brand", "category_name", "subcategory_name", "brand_category", "category_subcategory"]:
        if column not in X_train.columns or column not in X_test.columns:
            continue
        train_values = set(X_train[column].fillna("unknown").astype(str))
        test_values = set(X_test[column].fillna("unknown").astype(str))
        unseen = sorted(test_values - train_values)
        categorical_coverage[column] = {
            "train_unique": int(len(train_values)),
            "test_unique": int(len(test_values)),
            "unseen_test_values": unseen[:20],
            "unseen_test_value_count": int(len(unseen)),
        }

    return {
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "train_target": _target_summary(y_train),
        "test_target": _target_summary(y_test),
        "target_mean_shift_pct": float(
            abs(y_test.mean() - y_train.mean()) / y_train.mean() * 100
        )
        if len(y_train) and y_train.mean() != 0
        else 0.0,
        "categorical_coverage": categorical_coverage,
        "test_size": float(config.model.test_size),
    }


def _price_data_quality_report(
    raw_df: pd.DataFrame,
    cleaned: pd.DataFrame,
    prepared: pd.DataFrame,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    cleaning_report: dict[str, Any],
    split_strategy: dict[str, Any],
    config: Config,
) -> dict[str, Any]:
    target = config.features.target_col
    target_values = pd.to_numeric(prepared[target], errors="coerce").dropna()
    near_zero_threshold = max(1.0, float(target_values.median() * 0.01)) if len(target_values) else 1.0
    missing_rates = raw_df.isna().mean().sort_values(ascending=False)
    categorical_quality = _categorical_quality(prepared, config)
    feature_signal = _feature_signal_report(prepared, config)
    high_unknown = [
        column
        for column, data in categorical_quality.items()
        if data["unknown_rate"] >= 0.25 or data["top_value_share"] >= 0.90
    ]

    report = {
        "dataset_size": {
            "raw_rows": int(len(raw_df)),
            "cleaned_rows": int(len(cleaned)),
            "prepared_rows": int(len(prepared)),
            "min_training_rows": int(config.model.min_training_rows),
        },
        "missing_values": {
            "top_missing_rate_columns": [
                {"column": str(column), "missing_rate": float(rate)}
                for column, rate in missing_rates.head(15).items()
                if rate > 0
            ]
        },
        "price_outliers": {
            "invalid_price_rows_removed": int(cleaning_report.get("invalid_price_rows_removed", 0)),
            "train_price_outlier_rows_removed": int(cleaning_report.get("train_price_outlier_rows_removed", 0)),
            "price_outlier_bounds": cleaning_report.get("price_outlier_bounds"),
        },
        "near_zero_prices": {
            "threshold": near_zero_threshold,
            "count": int((target_values <= near_zero_threshold).sum()),
            "share": float((target_values <= near_zero_threshold).mean()) if len(target_values) else 0.0,
            "mape_warning": bool((target_values <= near_zero_threshold).any()),
        },
        "target_distribution": _target_summary(target_values),
        "categorical_feature_quality": categorical_quality,
        "feature_signal": feature_signal,
        "train_test_split_quality": {
            "strategy": split_strategy,
            **_split_quality_report(X_train, X_test, y_train, y_test, config),
        },
        "preprocessing_weaknesses": {
            "high_unknown_or_dominant_categorical_features": high_unknown,
            "zero_variance_numeric_feature_count": int(len(feature_signal["zero_variance_numeric_features"])),
            "feature_order_source": "feature_columns(config, 'improved') saved in metadata and validated at prediction time",
        },
        "database_signal_assessment": {
            "has_enough_rows_for_stable_regression": bool(len(prepared) >= max(100, config.model.min_training_rows)),
            "has_numeric_features_with_detectable_signal": bool(feature_signal["features_with_abs_corr_at_least_0_10"] > 0),
            "missing_production_grade_price_drivers": [
                "supplier_cost",
                "margin",
                "campaign_or_promotion_history",
                "product_specifications",
                "dedicated_price_history_snapshots",
            ],
        },
    }
    return _to_builtin(report)


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
    preprocessing_strategy: str,
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
        "preprocessing_strategy": preprocessing_strategy,
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
        "preprocessing_strategy": "linear_regression",
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


def _train_profile_models(
    df: pd.DataFrame,
    config: Config = cfg,
) -> tuple[dict[str, dict[str, Any]], pd.DataFrame, dict[str, Any], dict[str, Any]]:
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
    data_quality_report = _price_data_quality_report(
        raw_df=df,
        cleaned=cleaned,
        prepared=prepared,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        cleaning_report=report,
        split_strategy=split_strategy,
        config=config,
    )

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
                    "random_forest",
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
                    "xgboost",
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

    model_has_positive_r2 = any(data["metrics"]["r2"] > 0 for data in results.values())
    data_quality_report["database_signal_assessment"]["any_model_positive_test_r2"] = bool(model_has_positive_r2)
    data_quality_report["database_signal_assessment"]["all_models_negative_test_r2"] = bool(
        all(data["metrics"]["r2"] < 0 for data in results.values())
    )

    return results, prepared, report, data_quality_report


def _required_price_artifact_files() -> list[str]:
    return [
        "model/best_model.pkl",
        "model/preprocessing_pipeline.pkl",
        "metadata/metadata.json",
        "metadata/feature_list.json",
        "reports/model_comparison.csv",
        "reports/metrics_report.json",
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
        json.dump(_to_builtin(payload), f, indent=2)


def _write_rejection_report(config: Config, report: dict[str, Any]) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    _write_json(config.reports_dir / "latest_rejection_report.json", report)
    _write_json(config.reports_dir / f"rejection_report_{timestamp}.json", report)


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
        results, prepared, preprocessing_report_data, data_quality_report = _train_profile_models(df, config=lcfg)

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
                "numeric feature outlier clipping is fitted only on the training split inside each sklearn pipeline",
                "encoders/scalers are fitted only on the training split inside sklearn pipelines",
                "log target transformation is evaluated as a real candidate and selected only when it improves holdout RMSE",
            ],
            "model_preprocessing_strategies": {
                name: data["preprocessing_strategy"]
                for name, data in results.items()
            },
        }
        _write_json(lcfg.reports_dir / "preprocessing_report.json", preprocessing_report)

        feature_list = feature_columns(lcfg, "improved")
        _write_json(lcfg.metadata_dir / "feature_list.json", feature_list)
        metrics_report = {
            "training_run_id": training_run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "baseline_model": lcfg.model.baseline_name,
            "metrics_by_model": metrics_by_model,
            "train_metrics_by_model": {name: data["train_metrics"] for name, data in results.items()},
            "diagnostics_by_model": {name: data["diagnostics"] for name, data in results.items()},
            "gate_reasons_by_model": {name: data["gate_reasons"] for name, data in results.items()},
            "comparison": comparison.to_dict(orient="records"),
            "data_quality": data_quality_report,
        }
        _write_json(lcfg.reports_dir / "metrics_report.json", metrics_report)

        metadata = {
            "model_name": lcfg.price_model_name,
            "model_version": lcfg.price_model_version,
            "training_run_id": training_run_id,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "artifact_schema_version": "latest-valid-v4",
            "best_model": results[best_name]["model_name"] if best_name else None,
            "best_profile": "improved",
            "best_preprocessing_strategy": results[best_name]["preprocessing_strategy"] if best_name else None,
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
            "data_quality_report": data_quality_report,
            "comparison": comparison.to_dict(orient="records"),
            "prediction_examples": {
                name: data["prediction_examples"]
                for name, data in results.items()
            },
        }
        _write_json(lcfg.metadata_dir / "metadata.json", metadata)

        if not best_name:
            rejection_report = {
                "training_run_id": training_run_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "published": False,
                "kept_production_artifact": str(config.models_dir / "best_model.pkl"),
                "rejection_reason": metadata["rejection_reason"],
                "decision_rule": "Publish only a non-baseline model that beats Linear Regression and has positive test R2.",
                "metrics_by_model": metrics_by_model,
                "comparison": comparison.to_dict(orient="records"),
                "gate_reasons_by_model": metadata["gate_reasons"],
                "negative_r2_diagnosis": data_quality_report
                if data_quality_report["database_signal_assessment"]["all_models_negative_test_r2"]
                else None,
                "data_quality_problems": data_quality_report,
            }
            discard_staged_artifact(config, run)
            _write_rejection_report(config, rejection_report)
            return {
                "published": False,
                "best_model": None,
                "best_profile": "improved",
                "best_preprocessing_strategy": None,
                "rejection_reason": metadata["rejection_reason"],
                "metrics_by_model": metrics_by_model,
                "comparison": comparison,
                "rejection_report": rejection_report,
                "artifact_path": str(config.models_dir / "best_model.pkl"),
                "artifact_root": str(config.artifacts_dir),
                "metadata": metadata,
            }

        best_pipeline = results[best_name]["pipeline"]
        joblib.dump(best_pipeline, lcfg.models_dir / "best_model.pkl")
        joblib.dump(_fitted_preprocessor(best_pipeline), lcfg.models_dir / "preprocessing_pipeline.pkl")
        validate_artifact_files(run.staging_root, _required_price_artifact_files())
        publish_latest_artifact(config, run)

        return {
            "published": True,
            "best_model": best_name,
            "best_profile": "improved",
            "best_preprocessing_strategy": results[best_name]["preprocessing_strategy"],
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
                "preprocessing_strategy": results["best_preprocessing_strategy"],
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
