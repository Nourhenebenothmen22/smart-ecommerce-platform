"""
Run production-style ML validation using live PostgreSQL data only.

This workflow trains fresh validation models into a latest-only artifact
folder. It does not use cached CSVs, hardcoded data, or synthetic metrics.
"""

from __future__ import annotations

import json
import logging
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler

from ml.core.config import settings
from ml.core.db import get_db_cursor
from ml.core.artifacts import _remove_tree
from ml.customer_segmentation.config import Config as SegmentationConfig
from ml.customer_segmentation.data_loader import load_and_prepare
from ml.price_prediction.config import Config as PriceConfig
from ml.price_prediction.data_loader import load_product_training_data
from ml.price_prediction.preprocessing import build_feature_frame, clean_price_data, feature_columns
from ml.price_prediction.train_baseline import build_baseline_pipeline
from ml.price_prediction.train_model import build_performant_pipeline

logger = logging.getLogger("real_db_ml_validation")


@dataclass
class ValidationArtifacts:
    run_id: str
    root_dir: Path
    segmentation_dir: Path
    price_dir: Path
    reports_dir: Path
    plots_dir: Path

def create_validation_artifacts() -> ValidationArtifacts:
    run_id = "latest_validation"
    root = Path(__file__).resolve().parents[1] / "artifacts" / "validation"
    if root.exists():
        _remove_tree(root, ignore_errors=True)
    paths = {
        "segmentation": root / "client_segmentation",
        "price": root / "price_prediction",
        "reports": root / "reports",
        "plots": root / "plots",
    }
    for path in [
        root,
        paths["segmentation"] / "model",
        paths["segmentation"] / "data" / "raw",
        paths["segmentation"] / "data" / "processed",
        paths["segmentation"] / "reports",
        paths["segmentation"] / "metadata",
        paths["price"] / "model",
        paths["price"] / "data" / "raw",
        paths["price"] / "data" / "processed",
        paths["price"] / "reports",
        paths["price"] / "metadata",
        paths["reports"],
        paths["plots"],
    ]:
        path.mkdir(parents=True, exist_ok=True)
    return ValidationArtifacts(
        run_id=run_id,
        root_dir=root,
        segmentation_dir=paths["segmentation"],
        price_dir=paths["price"],
        reports_dir=paths["reports"],
        plots_dir=paths["plots"],
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, pd.Series):
        return value.to_dict()
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(data), indent=2), encoding="utf-8")


def _safe_cluster_metrics(X: np.ndarray, labels: np.ndarray) -> dict[str, float | None]:
    unique = np.unique(labels)
    if len(unique) < 2 or len(unique) >= len(labels):
        return {"silhouette_score": None, "davies_bouldin": None, "calinski_harabasz": None}
    return {
        "silhouette_score": float(silhouette_score(X, labels)),
        "davies_bouldin": float(davies_bouldin_score(X, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(X, labels)),
    }


def _regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    mse = float(mean_squared_error(y_true, y_pred))
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(y_true, y_pred)) if len(y_true) > 1 else 0.0,
    }


def _numeric_drift(train: pd.DataFrame, other: pd.DataFrame, columns: list[str]) -> dict[str, dict[str, float]]:
    drift: dict[str, dict[str, float]] = {}
    for col in columns:
        train_col = pd.to_numeric(train[col], errors="coerce").dropna()
        other_col = pd.to_numeric(other[col], errors="coerce").dropna()
        if train_col.empty or other_col.empty:
            continue
        train_std = float(train_col.std(ddof=0)) or 1.0
        drift[col] = {
            "train_mean": float(train_col.mean()),
            "other_mean": float(other_col.mean()),
            "standardized_mean_diff": abs(float(train_col.mean()) - float(other_col.mean())) / train_std,
            "train_missing_rate": float(train[col].isna().mean()),
            "other_missing_rate": float(other[col].isna().mean()),
        }
    return drift


def _outlier_summary(df: pd.DataFrame, columns: list[str]) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for col in columns:
        values = pd.to_numeric(df[col], errors="coerce").dropna()
        if values.empty:
            continue
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 3 * iqr, q3 + 3 * iqr
        summary[col] = {
            "min": float(values.min()),
            "max": float(values.max()),
            "iqr_outlier_count": int(((values < lower) | (values > upper)).sum()),
        }
    return summary


def _db_consistency_check() -> dict[str, Any]:
    checks: dict[str, Any] = {}
    with get_db_cursor() as cur:
        queries = {
            "products_total": "SELECT COUNT(*) FROM products",
            "products_invalid_price": "SELECT COUNT(*) FROM products WHERE price IS NULL OR price <= 0",
            "products_invalid_stock": "SELECT COUNT(*) FROM products WHERE stock < 0",
            "products_invalid_rating": "SELECT COUNT(*) FROM products WHERE rating_avg < 0 OR rating_avg > 5",
            "users_total": "SELECT COUNT(*) FROM users",
            "orders_total": "SELECT COUNT(*) FROM orders",
            "user_features_total": "SELECT COUNT(*) FROM user_features",
            "user_features_orphaned": """
                SELECT COUNT(*)
                FROM user_features uf
                LEFT JOIN users u ON u.id = uf.user_id
                WHERE u.id IS NULL
            """,
        }
        for key, query in queries.items():
            cur.execute(query)
            checks[key] = int(cur.fetchone()[0])
    checks["passed"] = (
        checks["products_total"] > 0
        and checks["users_total"] > 0
        and checks["user_features_total"] > 0
        and checks["products_invalid_price"] == 0
        and checks["user_features_orphaned"] == 0
    )
    return checks


def _plot_price_actual_vs_predicted(path: Path, y_true: pd.Series, predictions: dict[str, np.ndarray]) -> None:
    fig, axes = plt.subplots(1, len(predictions), figsize=(7 * len(predictions), 6))
    if len(predictions) == 1:
        axes = [axes]
    min_value = float(y_true.min())
    max_value = float(y_true.max())
    for ax, (name, y_pred) in zip(axes, predictions.items()):
        ax.scatter(y_true, y_pred, alpha=0.45, s=20)
        ax.plot([min_value, max_value], [min_value, max_value], "--", color="crimson")
        ax.set_title(name)
        ax.set_xlabel("Real DB price")
        ax.set_ylabel("Predicted price")
        ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_metric_bar(path: Path, metrics: dict[str, dict[str, float]], metric_names: list[str]) -> None:
    rows = []
    for model_name, model_metrics in metrics.items():
        for metric_name in metric_names:
            rows.append((model_name, metric_name.upper(), model_metrics[metric_name]))
    df = pd.DataFrame(rows, columns=["model", "metric", "value"])
    fig, ax = plt.subplots(figsize=(12, 7))
    for idx, metric_name in enumerate(metric_names):
        subset = df[df["metric"] == metric_name.upper()]
        ax.bar(
            np.arange(len(subset)) + idx * 0.22,
            subset["value"],
            width=0.22,
            label=metric_name.upper(),
        )
    ax.set_xticks(np.arange(len(metrics)) + 0.22)
    ax.set_xticklabels(list(metrics.keys()), rotation=20, ha="right")
    ax.set_title("Real DB Validation Metrics")
    ax.legend()
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_segmentation_pca(path: Path, X: np.ndarray, labels: np.ndarray) -> None:
    if X.shape[0] < 3:
        return
    coords = PCA(n_components=2, random_state=42).fit_transform(X)
    fig, ax = plt.subplots(figsize=(10, 7))
    scatter = ax.scatter(coords[:, 0], coords[:, 1], c=labels, cmap="tab10", s=24, alpha=0.75)
    ax.set_title("Client Segmentation PCA Projection")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.grid(alpha=0.2)
    fig.colorbar(scatter, ax=ax, label="segment")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def validate_client_segmentation(artifacts: ValidationArtifacts) -> dict[str, Any]:
    config = SegmentationConfig()
    config.data_dir = artifacts.segmentation_dir / "data"
    config.raw_data_dir = config.data_dir / "raw"
    config.processed_data_dir = config.data_dir / "processed"
    config.models_dir = artifacts.segmentation_dir / "model"
    config.reports_dir = artifacts.segmentation_dir / "reports"
    config.plots_dir = artifacts.segmentation_dir / "plots"
    config.metadata_dir = artifacts.segmentation_dir / "metadata"
    for path in [
        config.raw_data_dir,
        config.processed_data_dir,
        config.models_dir,
        config.reports_dir,
        config.plots_dir,
        config.metadata_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)
    df_raw = load_and_prepare(config, force_reload=True)
    before = len(df_raw)
    df_raw = df_raw.drop_duplicates(subset=["user_id"], keep="last").reset_index(drop=True)
    features = config.features.feature_cols

    missing = [col for col in ["user_id", *features] if col not in df_raw.columns]
    if missing:
        raise ValueError(f"user_features is missing required segmentation columns: {missing}")

    feature_frame = df_raw[["user_id", *features]].copy()
    for col in features:
        feature_frame[col] = pd.to_numeric(feature_frame[col], errors="coerce").fillna(0).clip(lower=0)

    train_df, test_df = train_test_split(
        feature_frame,
        test_size=0.2,
        random_state=config.random_state,
        shuffle=True,
    )
    leakage_overlap = sorted(set(train_df["user_id"]).intersection(set(test_df["user_id"])))

    X_train_raw = train_df[features].copy()
    X_test_raw = test_df[features].copy()
    X_current_raw = feature_frame[features].copy()

    for col in config.features.log_transform_cols:
        if col in features:
            X_train_raw[col] = np.log1p(X_train_raw[col])
            X_test_raw[col] = np.log1p(X_test_raw[col])
            X_current_raw[col] = np.log1p(X_current_raw[col])

    bounds: dict[str, dict[str, float]] = {}
    for col in features:
        q1, q3 = X_train_raw[col].quantile(0.25), X_train_raw[col].quantile(0.75)
        iqr = q3 - q1
        lower, upper = float(q1 - 3 * iqr), float(q3 + 3 * iqr)
        bounds[col] = {"lower": lower, "upper": upper}
        X_train_raw[col] = X_train_raw[col].clip(lower=lower, upper=upper)
        X_test_raw[col] = X_test_raw[col].clip(lower=lower, upper=upper)
        X_current_raw[col] = X_current_raw[col].clip(lower=lower, upper=upper)

    scaler = RobustScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_test = scaler.transform(X_test_raw)
    X_current = scaler.transform(X_current_raw)

    valid_k = [k for k in config.kmeans.k_range if 2 <= k < len(X_train)]
    best_k = valid_k[0]
    best_score = -1.0
    for k in valid_k:
        candidate = KMeans(n_clusters=k, n_init=config.kmeans.n_init, random_state=config.random_state)
        labels = candidate.fit_predict(X_train)
        score = float(silhouette_score(X_train, labels)) if len(np.unique(labels)) > 1 else -1.0
        if score > best_score:
            best_k, best_score = k, score

    model = KMeans(n_clusters=best_k, n_init=config.kmeans.n_init, random_state=config.random_state)
    train_labels = model.fit_predict(X_train)
    test_labels = model.predict(X_test)
    current_labels = model.predict(X_current)

    train_metrics = _safe_cluster_metrics(X_train, train_labels)
    test_metrics = _safe_cluster_metrics(X_test, test_labels)
    current_metrics = _safe_cluster_metrics(X_current, current_labels)
    drift_train_test = _numeric_drift(train_df, test_df, features)
    drift_train_current = _numeric_drift(train_df, feature_frame, features)
    outliers = _outlier_summary(feature_frame, features)

    run_suffix = artifacts.run_id
    model_path = config.models_dir / "kmeans_model.pkl"
    preprocessor_path = config.models_dir / "preprocessing.pkl"
    labels_path = config.processed_data_dir / "client_segmentation_assignments.csv"
    metrics_path = config.reports_dir / "client_segmentation_metrics.json"

    joblib.dump(model, model_path)
    joblib.dump({"scaler": scaler, "features": features, "log_transform_cols": config.features.log_transform_cols, "bounds": bounds}, preprocessor_path)
    pd.DataFrame({"user_id": feature_frame["user_id"], "segment_id": current_labels}).to_csv(labels_path, index=False)
    _plot_segmentation_pca(artifacts.plots_dir / f"client_segmentation_pca_{run_suffix}.png", X_current, current_labels)

    result = {
        "data_source": "PostgreSQL user_features generated from real customer/order/product behavior",
        "rows_before_cleaning": before,
        "rows_after_cleaning": int(len(feature_frame)),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "current_rows": int(len(feature_frame)),
        "model": "KMeans",
        "selected_k": int(best_k),
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "current_metrics": current_metrics,
        "overfitting_check": {
            "silhouette_gap": (
                None
                if train_metrics["silhouette_score"] is None or test_metrics["silhouette_score"] is None
                else float(train_metrics["silhouette_score"] - test_metrics["silhouette_score"])
            )
        },
        "leakage_check": {
            "split_key": "user_id",
            "train_test_overlap_count": len(leakage_overlap),
            "forbidden_features_present": [col for col in ["user_id", "email", "password_hash"] if col in features],
            "passed": len(leakage_overlap) == 0,
        },
        "drift_check": {
            "train_vs_test": drift_train_test,
            "train_vs_current": drift_train_current,
        },
        "outlier_check": outliers,
        "artifacts": {
            "model": model_path,
            "preprocessing_pipeline": preprocessor_path,
            "assignments": labels_path,
            "metrics": metrics_path,
        },
    }
    _save_json(metrics_path, result)
    return result


HISTORICAL_PRICE_PROXY_FEATURES = {
    "avg_historical_unit_price",
    "min_historical_unit_price",
    "max_historical_unit_price",
    "historical_unit_price_stddev",
    "historical_price_range",
    "historical_price_std_ratio",
    "historical_discount_gap_pct",
    "total_order_revenue",
    "log_total_order_revenue",
    "revenue_per_buyer",
}


def _time_aware_price_split(cleaned: pd.DataFrame, frame: pd.DataFrame, config: PriceConfig):
    product_ids = cleaned["product_id"].reset_index(drop=True).iloc[: len(frame)]
    created_at = pd.to_datetime(cleaned["created_at"].reset_index(drop=True).iloc[: len(frame)], errors="coerce")
    split_frame = pd.DataFrame({
        "row_index": np.arange(len(frame)),
        "product_id": product_ids.to_numpy(),
        "created_at": created_at,
        "has_sales_history": (cleaned["order_line_count"].reset_index(drop=True).iloc[: len(frame)] > 0).to_numpy(),
    })
    split_frame = split_frame.sort_values(["created_at", "product_id"], na_position="first").reset_index(drop=True)
    split_at = int(len(split_frame) * (1 - config.model.test_size))
    if split_at <= 0 or split_at >= len(split_frame):
        raise ValueError("Not enough price rows for time-aware train/test split.")
    train_meta = split_frame.iloc[:split_at].copy()
    test_meta = split_frame.iloc[split_at:].copy()
    return train_meta, test_meta


def _subset_regression_metrics(y_true: pd.Series, y_pred: np.ndarray, mask: pd.Series) -> dict[str, Any]:
    mask_values = mask.to_numpy(dtype=bool)
    rows = int(mask_values.sum())
    if rows < 2:
        return {"rows": rows, "metrics": None}
    return {
        "rows": rows,
        "metrics": _regression_metrics(y_true[mask_values], y_pred[mask_values]),
    }


def _price_config_without_historical_proxies(config: PriceConfig) -> PriceConfig:
    ablation_config = PriceConfig()
    ablation_config.data_dir = config.data_dir
    ablation_config.raw_data_dir = config.raw_data_dir
    ablation_config.processed_data_dir = config.processed_data_dir
    ablation_config.models_dir = config.models_dir
    ablation_config.reports_dir = config.reports_dir
    ablation_config.plots_dir = config.plots_dir
    ablation_config.metadata_dir = config.metadata_dir
    ablation_config.model = config.model
    ablation_config.n_jobs = config.n_jobs
    ablation_config.features.numeric_features = [
        col for col in config.features.numeric_features
        if col not in HISTORICAL_PRICE_PROXY_FEATURES
    ]
    return ablation_config


def validate_price_prediction(artifacts: ValidationArtifacts) -> dict[str, Any]:
    config = PriceConfig()
    config.data_dir = artifacts.price_dir / "data"
    config.raw_data_dir = config.data_dir / "raw"
    config.processed_data_dir = config.data_dir / "processed"
    config.models_dir = artifacts.price_dir / "model"
    config.reports_dir = artifacts.price_dir / "reports"
    config.plots_dir = artifacts.price_dir / "plots"
    config.metadata_dir = artifacts.price_dir / "metadata"
    for path in [
        config.raw_data_dir,
        config.processed_data_dir,
        config.models_dir,
        config.reports_dir,
        config.plots_dir,
        config.metadata_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)
    df_raw = load_product_training_data(config, force_reload=True)
    cleaned, cleaning_report = clean_price_data(df_raw, config=config, include_target=True)
    frame = build_feature_frame(cleaned, config=config, include_target=True)
    assert isinstance(frame, pd.DataFrame)
    signal_availability = {
        "products_with_sales_history": int((cleaned["order_line_count"] > 0).sum()),
        "sales_history_coverage": float((cleaned["order_line_count"] > 0).mean()) if len(cleaned) else 0.0,
        "products_with_historical_unit_price": int((cleaned["avg_historical_unit_price"] > 0).sum()),
        "products_with_interactions": int((cleaned["interaction_count"] > 0).sum()),
        "interaction_coverage": float((cleaned["interaction_count"] > 0).mean()) if len(cleaned) else 0.0,
        "products_in_current_carts": int((cleaned["current_cart_quantity"] > 0).sum()),
        "products_in_wishlists": int((cleaned["wishlist_count"] > 0).sum()),
        "products_with_reviews": int((cleaned["review_rows_count"] > 0).sum()),
    }

    columns = feature_columns(config, "improved")
    X = frame[columns]
    y = frame[config.features.target_col].astype(float)
    train_meta, test_meta = _time_aware_price_split(cleaned, frame, config)
    X_train = X.iloc[train_meta["row_index"].to_numpy()].reset_index(drop=True)
    X_test = X.iloc[test_meta["row_index"].to_numpy()].reset_index(drop=True)
    y_train = y.iloc[train_meta["row_index"].to_numpy()].reset_index(drop=True)
    y_test = y.iloc[test_meta["row_index"].to_numpy()].reset_index(drop=True)
    id_train = train_meta["product_id"]
    id_test = test_meta["product_id"]
    test_has_sales_history = test_meta["has_sales_history"].reset_index(drop=True)
    leakage_overlap = sorted(set(id_train).intersection(set(id_test)))

    baseline = build_baseline_pipeline(config, profile="improved", use_log_target=config.model.baseline_use_log_target)
    performant = build_performant_pipeline(config, profile="improved", use_log_target=config.model.performant_use_log_target)
    models = {
        "price_prediction_baseline": baseline,
        "price_prediction_performant": performant,
    }

    metrics: dict[str, dict[str, Any]] = {}
    predictions: dict[str, np.ndarray] = {}
    run_suffix = artifacts.run_id
    for name, model in models.items():
        model.fit(X_train, y_train)
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)
        predictions[name] = test_pred
        metrics[name] = {
            "train": _regression_metrics(y_train, train_pred),
            "test": _regression_metrics(y_test, test_pred),
            "test_by_sales_history": {
                "with_sales_history": _subset_regression_metrics(y_test, test_pred, test_has_sales_history),
                "cold_start_no_sales_history": _subset_regression_metrics(y_test, test_pred, ~test_has_sales_history),
            },
            "overfitting_check": {
                "rmse_gap_train_to_test": _regression_metrics(y_test, test_pred)["rmse"] - _regression_metrics(y_train, train_pred)["rmse"],
                "r2_gap_train_to_test": _regression_metrics(y_train, train_pred)["r2"] - _regression_metrics(y_test, test_pred)["r2"],
            },
        }
        joblib.dump(model, config.models_dir / f"{name}.pkl")

    ablation_config = _price_config_without_historical_proxies(config)
    ablation_columns = feature_columns(ablation_config, "improved")
    ablation_model = build_performant_pipeline(
        ablation_config,
        profile="improved",
        use_log_target=ablation_config.model.performant_use_log_target,
    )
    ablation_model.fit(X_train[ablation_columns], y_train)
    ablation_pred = ablation_model.predict(X_test[ablation_columns])
    ablation_metrics = _regression_metrics(y_test, ablation_pred)

    predictions_df = pd.DataFrame(
        {
            "product_id": list(id_test),
            "real_database_price": list(y_test),
            "baseline_predicted_price": predictions["price_prediction_baseline"],
            "performant_predicted_price": predictions["price_prediction_performant"],
            "has_sales_history": list(test_has_sales_history),
        }
    )
    predictions_path = config.processed_data_dir / "price_prediction_holdout_predictions.csv"
    predictions_df.to_csv(predictions_path, index=False)

    drift_train_test = _numeric_drift(X_train, X_test, config.features.numeric_features)
    drift_train_current = _numeric_drift(X_train, X, config.features.numeric_features)
    outliers = _outlier_summary(frame, config.features.numeric_features + [config.features.target_col])

    _plot_price_actual_vs_predicted(
        artifacts.plots_dir / f"price_prediction_actual_vs_predicted_{run_suffix}.png",
        y_test,
        predictions,
    )
    _plot_metric_bar(
        artifacts.plots_dir / f"price_prediction_model_metrics_{run_suffix}.png",
        {name: data["test"] for name, data in metrics.items()},
        ["mae", "rmse", "r2"],
    )

    leakage_forbidden = [col for col in ["price", "final_price", "category_id", "subcategory_id", "product_id"] if col in columns]
    result = {
        "data_source": "PostgreSQL products joined to categories, subcategories, order_items/orders, user_interactions, reviews, cart_items, and wishlists",
        "raw_rows": int(len(df_raw)),
        "cleaning_report": cleaning_report,
        "signal_availability": signal_availability,
        "rows_after_preprocessing": int(len(frame)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "split_strategy": {
            "type": "time_aware_product_created_at",
            "train_max_created_at": str(train_meta["created_at"].max()),
            "test_min_created_at": str(test_meta["created_at"].min()),
        },
        "models": metrics,
        "historical_proxy_ablation": {
            "removed_features": sorted(HISTORICAL_PRICE_PROXY_FEATURES.intersection(columns)),
            "performant_without_historical_price_proxies": ablation_metrics,
        },
        "real_database_validation": {
            "prediction_file": predictions_path,
            "target": "products.price",
        },
        "leakage_check": {
            "split_key": "product_id",
            "train_test_overlap_count": len(leakage_overlap),
            "forbidden_features_present": leakage_forbidden,
            "passed": len(leakage_overlap) == 0 and not leakage_forbidden,
        },
        "drift_check": {
            "train_vs_test": drift_train_test,
            "train_vs_current": drift_train_current,
        },
        "outlier_check": outliers,
        "artifacts": {
            "baseline_model": config.models_dir / "price_prediction_baseline.pkl",
            "performant_model": config.models_dir / "price_prediction_performant.pkl",
            "predictions": predictions_path,
        },
    }
    _save_json(config.reports_dir / "price_prediction_metrics.json", result)
    return result


def build_readiness_conclusion(report: dict[str, Any]) -> dict[str, Any]:
    price = report["price_prediction"]["models"]
    baseline_test = price["price_prediction_baseline"]["test"]
    performant_test = price["price_prediction_performant"]["test"]
    segmentation = report["client_segmentation"]
    db_passed = report["database_consistency"]["passed"]
    leakage_passed = (
        report["client_segmentation"]["leakage_check"]["passed"]
        and report["price_prediction"]["leakage_check"]["passed"]
    )
    performant_beats_baseline = (
        performant_test["rmse"] < baseline_test["rmse"]
        and performant_test["mae"] < baseline_test["mae"]
        and performant_test["r2"] > baseline_test["r2"]
    )
    acceptable_price_performance = performant_test["r2"] >= 0.2
    sales_history_metrics = price["price_prediction_performant"]["test_by_sales_history"]["with_sales_history"]
    cold_start_metrics = price["price_prediction_performant"]["test_by_sales_history"]["cold_start_no_sales_history"]
    existing_product_ready = bool(
        performant_beats_baseline
        and acceptable_price_performance
        and sales_history_metrics["rows"] >= 30
        and sales_history_metrics["metrics"] is not None
        and sales_history_metrics["metrics"]["r2"] >= 0.2
    )
    cold_start_ready = bool(
        cold_start_metrics["rows"] >= 30
        and cold_start_metrics["metrics"] is not None
        and cold_start_metrics["metrics"]["r2"] >= 0.2
    )
    ready = bool(
        db_passed
        and leakage_passed
        and existing_product_ready
        and cold_start_ready
        and performant_test["rmse"] > 0
        and segmentation["current_rows"] > 0
        and segmentation["test_metrics"]["silhouette_score"] is not None
        and segmentation["test_metrics"]["silhouette_score"] >= 0.1
    )
    recommendations = []
    if performant_test["r2"] < 0:
        recommendations.append("Price R2 is negative; add richer product attributes or real market/sales price signals.")
    if not performant_beats_baseline:
        recommendations.append("Performant price model does not beat the baseline on MAE, RMSE, and R2.")
    if not acceptable_price_performance:
        recommendations.append("Price model test R2 is below the minimum acceptance threshold of 0.20.")
    if not existing_product_ready:
        recommendations.append("Existing-product price readiness failed for products with sales history.")
    if not cold_start_ready:
        recommendations.append("Cold-start price readiness is not proven for products without sales history.")
    if segmentation["test_metrics"]["silhouette_score"] is None or segmentation["test_metrics"]["silhouette_score"] < 0.1:
        recommendations.append("Segmentation separation is weak; enrich user_features with recency/frequency/session/device signals.")
    if not db_passed:
        recommendations.append("Fix database consistency issues before promoting models.")
    if not leakage_passed:
        recommendations.append("Fix leakage or split-overlap issues before deployment.")
    return {
        "production_ready": ready,
        "summary": "Validation completed with real PostgreSQL data only.",
        "price_readiness_gate": {
            "performant_beats_baseline": performant_beats_baseline,
            "minimum_test_r2": 0.2,
            "actual_test_r2": performant_test["r2"],
            "existing_product_ready": existing_product_ready,
            "cold_start_ready": cold_start_ready,
        },
        "production_readiness_scope": {
            "existing_products_with_sales_history": existing_product_ready,
            "cold_start_products_without_sales_history": cold_start_ready,
        },
        "recommended_fixes": recommendations,
    }


def run_real_db_validation() -> dict[str, Any]:
    artifacts = create_validation_artifacts()
    logger.info("Writing validation artifacts to %s", artifacts.root_dir)
    db_checks = _db_consistency_check()
    segmentation = validate_client_segmentation(artifacts)
    price = validate_price_prediction(artifacts)
    report: dict[str, Any] = {
        "run_id": artifacts.run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_root": artifacts.root_dir,
        "data_source_verification": {
            "database_url": f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
            "segmentation_source": "user_features table",
            "price_source": "products/categories/subcategories plus sales, demand, reviews, cart, and wishlist tables",
            "cached_data_used": False,
            "hardcoded_datasets_used": False,
        },
        "database_consistency": db_checks,
        "client_segmentation": segmentation,
        "price_prediction": price,
    }
    report["production_readiness"] = build_readiness_conclusion(report)
    report_path = artifacts.reports_dir / f"ml_validation_report_{artifacts.run_id}.json"
    _save_json(report_path, report)
    (artifacts.root_dir / "README.txt").write_text(
        f"ML validation run: {artifacts.run_id}\nReport: {report_path}\n",
        encoding="utf-8",
    )

    print("\n" + "=" * 60)
    print("REAL DATABASE ML VALIDATION RESULT")
    print("=" * 60)
    print(f"Artifact root: {artifacts.root_dir}")
    print("Client segmentation:")
    print(f"- rows: {segmentation['current_rows']}")
    print(f"- selected_k: {segmentation['selected_k']}")
    print(f"- test silhouette: {segmentation['test_metrics']['silhouette_score']}")
    print("Price prediction:")
    for model_name, data in price["models"].items():
        test = data["test"]
        print(f"- {model_name}: MAE={test['mae']:.2f}, RMSE={test['rmse']:.2f}, R2={test['r2']:.4f}")
    print(f"Production ready: {report['production_readiness']['production_ready']}")
    print("=" * 60 + "\n")
    return report


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    run_real_db_validation()
