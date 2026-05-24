"""
Preprocessing and feature engineering for product price prediction.
"""

import json
import re
from datetime import datetime, timezone
from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

from .config import Config, cfg

PreprocessingProfile = Literal["legacy", "improved"]


class TargetMeanEncoder(BaseEstimator, TransformerMixin):
    """
    Train-only target mean encoder for category/subcategory/brand price priors.

    The encoder is fitted inside the sklearn pipeline after the train/test
    split, so holdout rows never influence their own category price priors.
    """

    def __init__(self, smoothing: float = 20.0):
        self.smoothing = smoothing

    @staticmethod
    def _normalise_frame(X, columns=None) -> pd.DataFrame:
        frame = pd.DataFrame(X, columns=columns)
        return frame.apply(lambda column: column.map(_normalise_text))

    def fit(self, X, y=None):
        if y is None:
            raise ValueError("TargetMeanEncoder requires y during fit.")
        frame = self._normalise_frame(X)
        target = pd.Series(y, index=frame.index, dtype="float64")
        self.columns_ = list(frame.columns)
        self.global_mean_ = float(target.mean()) if len(target) else 0.0
        self.maps_: dict[str, dict[str, float]] = {}
        for column in self.columns_:
            stats = target.groupby(frame[column]).agg(["count", "mean"])
            smoothed = (
                stats["count"] * stats["mean"] + self.smoothing * self.global_mean_
            ) / (stats["count"] + self.smoothing)
            self.maps_[column] = {str(key): float(value) for key, value in smoothed.items()}
        return self

    def transform(self, X):
        frame = self._normalise_frame(X, columns=getattr(self, "columns_", None))
        encoded = []
        for column in self.columns_:
            encoded.append(frame[column].map(self.maps_[column]).fillna(self.global_mean_).to_numpy())
        return np.vstack(encoded).T if encoded else np.empty((len(frame), 0))

    def get_feature_names_out(self, input_features=None):
        columns = input_features if input_features is not None else getattr(self, "columns_", [])
        return np.array([f"{column}_target_mean_price" for column in columns], dtype=object)


def _one_hot_encoder(config: Config) -> OneHotEncoder:
    try:
        return OneHotEncoder(
            handle_unknown="infrequent_if_exist",
            min_frequency=config.features.rare_category_min_frequency,
            sparse_output=False,
        )
    except TypeError:  # pragma: no cover - compatibility with older sklearn
        try:
            return OneHotEncoder(
                handle_unknown="infrequent_if_exist",
                min_frequency=config.features.rare_category_min_frequency,
                sparse=False,
            )
        except TypeError:
            return OneHotEncoder(handle_unknown="ignore", sparse=False)


def _text_length(value: Any) -> int:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0
    return len(str(value).strip())


def _normalise_text(value: Any, default: str = "unknown") -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    clean = re.sub(r"\s+", " ", str(value).strip().lower())
    return clean or default


def _tag_count(value: Any) -> int:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0
    if isinstance(value, list):
        return len([item for item in value if str(item).strip()])
    if isinstance(value, tuple):
        return len([item for item in value if str(item).strip()])
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        try:
            decoded = json.loads(text)
            if isinstance(decoded, list):
                return len([item for item in decoded if str(item).strip()])
        except json.JSONDecodeError:
            pass
        return len([item for item in text.split(",") if item.strip()])
    return 0


def _is_active_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        return int(value.strip().lower() in {"true", "1", "yes", "active"})
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 1
    return int(bool(value))


def _product_age_days(value: Any) -> float:
    if value is None or pd.isna(value):
        return 0.0
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return 0.0
    elif isinstance(value, pd.Timestamp):
        dt = value.to_pydatetime()
    elif isinstance(value, datetime):
        dt = value
    else:
        return 0.0

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).days, 0)


def _days_since(value: Any, missing_value: float = 0.0) -> float:
    if value is None or pd.isna(value):
        return missing_value
    days = _product_age_days(value)
    if days == 0 and not isinstance(value, (datetime, pd.Timestamp, str)):
        return missing_value
    return days


def _safe_ratio(numerator: pd.Series, denominator: pd.Series, default: float = 0.0) -> pd.Series:
    denominator = denominator.astype(float)
    ratio = numerator.astype(float) / denominator.replace(0, np.nan)
    return ratio.replace([np.inf, -np.inf], np.nan).fillna(default)


def _stock_bucket(stock: float) -> str:
    if stock <= 0:
        return "out_of_stock"
    if stock <= 10:
        return "low_stock"
    if stock <= 100:
        return "available"
    return "deep_stock"


def _popularity_bucket(review_count: float) -> str:
    if review_count <= 0:
        return "no_reviews"
    if review_count < 10:
        return "low_reviews"
    if review_count < 100:
        return "active_reviews"
    return "high_reviews"


def _discount_bucket(discount_percent: float) -> str:
    if discount_percent <= 0:
        return "no_discount"
    if discount_percent < 10:
        return "small_discount"
    if discount_percent < 30:
        return "medium_discount"
    return "large_discount"


def _demand_bucket(score: float) -> str:
    if score <= 0:
        return "no_demand"
    if score < 5:
        return "low_demand"
    if score < 25:
        return "medium_demand"
    return "high_demand"


RAW_PRICE_SIGNAL_DEFAULTS: dict[str, Any] = {
    "order_line_count": 0,
    "total_quantity_sold": 0,
    "avg_order_quantity": 0,
    "max_order_quantity": 0,
    "fulfilled_order_lines": 0,
    "fulfilled_quantity_sold": 0,
    "total_order_revenue": 0,
    "avg_historical_unit_price": 0,
    "min_historical_unit_price": 0,
    "max_historical_unit_price": 0,
    "historical_unit_price_stddev": 0,
    "distinct_buyers": 0,
    "first_order_at": None,
    "last_order_at": None,
    "interaction_count": 0,
    "distinct_interaction_users": 0,
    "avg_interaction_value": 0,
    "view_count": 0,
    "click_count": 0,
    "add_to_cart_count": 0,
    "wishlist_interaction_count": 0,
    "purchase_interaction_count": 0,
    "share_count": 0,
    "search_count": 0,
    "last_interaction_at": None,
    "current_cart_quantity": 0,
    "current_cart_users": 0,
    "wishlist_count": 0,
    "review_rows_count": 0,
    "verified_review_count": 0,
    "avg_review_rating": 0,
    "negative_review_count": 0,
    "positive_review_count": 0,
}


def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    defaults: dict[str, Any] = {
        "product_id": None,
        "title": "",
        "description": "",
        "brand": "unknown",
        "category_name": "unknown",
        "subcategory_name": "unknown",
        "category_id": 0,
        "subcategory_id": 0,
        "discount_percent": 0,
        "rating_avg": 0,
        "review_count": 0,
        "stock": 0,
        "tags": [],
        "is_active": True,
        "created_at": None,
    }
    defaults.update(RAW_PRICE_SIGNAL_DEFAULTS)
    for column, default in defaults.items():
        if column not in work.columns:
            if isinstance(default, list):
                work[column] = [list(default) for _ in range(len(work))]
            else:
                work[column] = default
    return work


def clean_price_data(
    df: pd.DataFrame,
    config: Config = cfg,
    include_target: bool = True,
    remove_target_outliers: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Clean raw product rows before improved feature engineering.

    The legacy profile intentionally does not call this helper so old vs new
    comparisons measure the preprocessing impact.
    """
    work = _ensure_columns(df)
    report: dict[str, Any] = {"rows_before": int(len(work))}

    if "product_id" in work.columns and work["product_id"].notna().any():
        before = len(work)
        work = work.drop_duplicates(subset=["product_id"], keep="last")
        report["duplicate_product_rows_removed"] = int(before - len(work))
    else:
        before = len(work)
        work = work.drop_duplicates(subset=["title", "brand", "category_name", "subcategory_name"], keep="last")
        report["duplicate_product_rows_removed"] = int(before - len(work))

    numeric_inputs = [
        "category_id",
        "subcategory_id",
        "discount_percent",
        "rating_avg",
        "review_count",
        "stock",
        *[column for column, default in RAW_PRICE_SIGNAL_DEFAULTS.items() if isinstance(default, (int, float))],
    ]
    for column in numeric_inputs:
        work[column] = pd.to_numeric(work[column], errors="coerce")

    work["discount_percent"] = work["discount_percent"].fillna(0).clip(lower=0, upper=100)
    work["rating_avg"] = work["rating_avg"].fillna(0).clip(lower=0, upper=5)
    work["review_count"] = work["review_count"].fillna(0).clip(lower=0)
    work["stock"] = work["stock"].fillna(0).clip(lower=0)
    work["category_id"] = work["category_id"].fillna(0).clip(lower=0)
    work["subcategory_id"] = work["subcategory_id"].fillna(0).clip(lower=0)
    for column in [column for column, default in RAW_PRICE_SIGNAL_DEFAULTS.items() if isinstance(default, (int, float))]:
        work[column] = work[column].fillna(0).clip(lower=0)

    for column in ["brand", "category_name", "subcategory_name"]:
        work[column] = work[column].map(_normalise_text)

    work["title"] = work["title"].fillna("").astype(str).str.strip()
    work["description"] = work["description"].fillna("").astype(str).str.strip()
    work["is_active"] = work["is_active"].map(_is_active_int)

    if include_target:
        target = config.features.target_col
        if target not in work.columns:
            raise ValueError(f"Missing target column for price prediction: {target}")

        work[target] = pd.to_numeric(work[target], errors="coerce")
        before = len(work)
        valid_target = work[target].notna() & (work[target] > 0) & (work[target] <= config.features.max_valid_price)
        work = work[valid_target].copy()
        report["invalid_price_rows_removed"] = int(before - len(work))

        if remove_target_outliers and len(work) >= 50:
            lower = float(work[target].quantile(config.features.outlier_lower_quantile))
            upper = float(work[target].quantile(config.features.outlier_upper_quantile))
            before = len(work)
            work = work[(work[target] >= lower) & (work[target] <= upper)].copy()
            report["price_outlier_rows_removed"] = int(before - len(work))
            report["price_outlier_bounds"] = {"lower": lower, "upper": upper}
        else:
            report["price_outlier_rows_removed"] = 0

    report["rows_after"] = int(len(work))
    return work.reset_index(drop=True), report


def _add_basic_features(work: pd.DataFrame) -> pd.DataFrame:
    work = _ensure_columns(work)
    work["title_length"] = work["title"].map(_text_length)
    work["description_length"] = work["description"].map(_text_length)
    work["tag_count"] = work["tags"].map(_tag_count)
    work["is_active_int"] = work["is_active"].map(_is_active_int)
    work["product_age_days"] = work["created_at"].map(_product_age_days)
    return work


def _add_advanced_features(work: pd.DataFrame) -> pd.DataFrame:
    work = _add_basic_features(work)

    work["discount_ratio"] = work["discount_percent"] / 100.0
    work["has_discount"] = (work["discount_percent"] > 0).astype(int)
    work["log_stock"] = np.log1p(work["stock"].astype(float))
    work["log_review_count"] = np.log1p(work["review_count"].astype(float))
    work["description_to_title_ratio"] = work["description_length"] / work["title_length"].clip(lower=1)
    work["text_richness_score"] = np.log1p(work["title_length"] + work["description_length"]) * (1 + work["tag_count"] / 10)
    work["rating_review_score"] = work["rating_avg"].astype(float) * work["log_review_count"]
    work["historical_price_range"] = (
        work["max_historical_unit_price"].astype(float) - work["min_historical_unit_price"].astype(float)
    ).clip(lower=0)
    work["historical_price_std_ratio"] = _safe_ratio(
        work["historical_unit_price_stddev"],
        work["avg_historical_unit_price"],
    )
    current_discount_multiplier = (1 - work["discount_ratio"]).clip(lower=0.0)
    estimated_current_final_price = work["avg_historical_unit_price"].astype(float) * current_discount_multiplier
    work["historical_discount_gap_pct"] = _safe_ratio(
        work["avg_historical_unit_price"].astype(float) - estimated_current_final_price,
        work["avg_historical_unit_price"],
    ).clip(lower=0, upper=1)

    work["days_since_first_order"] = work["first_order_at"].map(lambda value: _days_since(value, 0.0))
    work["days_since_last_order"] = work["last_order_at"].map(lambda value: _days_since(value, 9999.0))
    work["days_since_last_interaction"] = work["last_interaction_at"].map(lambda value: _days_since(value, 9999.0))
    work["log_order_line_count"] = np.log1p(work["order_line_count"].astype(float))
    work["log_total_quantity_sold"] = np.log1p(work["total_quantity_sold"].astype(float))
    work["log_total_order_revenue"] = np.log1p(work["total_order_revenue"].astype(float))
    work["sales_velocity"] = _safe_ratio(
        work["total_quantity_sold"],
        work["product_age_days"].astype(float).clip(lower=1),
    )
    work["revenue_per_buyer"] = _safe_ratio(work["total_order_revenue"], work["distinct_buyers"])
    work["quantity_per_buyer"] = _safe_ratio(work["total_quantity_sold"], work["distinct_buyers"])
    work["buyer_per_order_ratio"] = _safe_ratio(work["distinct_buyers"], work["order_line_count"])

    work["demand_score"] = (
        work["view_count"].astype(float) * 0.05
        + work["click_count"].astype(float) * 0.10
        + work["add_to_cart_count"].astype(float) * 0.35
        + work["wishlist_interaction_count"].astype(float) * 0.25
        + work["purchase_interaction_count"].astype(float) * 0.75
        + work["total_quantity_sold"].astype(float)
        + work["current_cart_quantity"].astype(float) * 0.5
        + work["wishlist_count"].astype(float) * 0.25
    )
    work["conversion_rate"] = _safe_ratio(work["purchase_interaction_count"] + work["order_line_count"], work["view_count"] + work["click_count"])
    work["cart_to_view_rate"] = _safe_ratio(work["add_to_cart_count"] + work["current_cart_quantity"], work["view_count"])
    work["purchase_to_view_rate"] = _safe_ratio(work["purchase_interaction_count"] + work["total_quantity_sold"], work["view_count"])
    work["wishlist_to_view_rate"] = _safe_ratio(work["wishlist_interaction_count"] + work["wishlist_count"], work["view_count"])
    work["stock_to_sales_ratio"] = _safe_ratio(work["stock"], work["total_quantity_sold"], default=float(work["stock"].median() or 0))

    work["brand_category"] = work["brand"] + "__" + work["category_name"]
    work["category_subcategory"] = work["category_name"] + "__" + work["subcategory_name"]
    work["stock_bucket"] = work["stock"].map(_stock_bucket)
    work["popularity_bucket"] = work["review_count"].map(_popularity_bucket)
    work["discount_bucket"] = work["discount_percent"].map(_discount_bucket)
    work["has_sales_history"] = np.where(work["order_line_count"].astype(float) > 0, "yes", "no")
    work["has_interaction_history"] = np.where(work["interaction_count"].astype(float) > 0, "yes", "no")
    work["has_cart_pressure"] = np.where(work["current_cart_quantity"].astype(float) > 0, "yes", "no")
    work["has_wishlist_pressure"] = np.where(work["wishlist_count"].astype(float) > 0, "yes", "no")
    work["demand_bucket"] = work["demand_score"].map(_demand_bucket)
    return work


def feature_columns(config: Config = cfg, profile: PreprocessingProfile = "improved") -> list[str]:
    if profile == "legacy":
        return config.features.legacy_numeric_features + config.features.legacy_categorical_features
    return config.features.numeric_features + config.features.categorical_features


def build_legacy_feature_frame(df: pd.DataFrame, config: Config = cfg, include_target: bool = True) -> pd.DataFrame:
    """Create the original feature frame used before preprocessing improvements."""
    work = _add_basic_features(_ensure_columns(df))

    for column in config.features.legacy_numeric_features:
        work[column] = pd.to_numeric(work[column], errors="coerce").fillna(0)
    for column in config.features.legacy_categorical_features:
        work[column] = work[column].fillna("unknown").astype(str).str.strip().replace("", "unknown")

    selected = feature_columns(config, "legacy")
    if include_target:
        target = config.features.target_col
        if target not in work.columns:
            raise ValueError(f"Missing target column for price prediction: {target}")
        work[target] = pd.to_numeric(work[target], errors="coerce")
        work = work[work[target].notna() & (work[target] > 0)].copy()
        selected = selected + [target]
    return work[selected].reset_index(drop=True)


def build_feature_frame(
    df: pd.DataFrame,
    config: Config = cfg,
    include_target: bool = True,
    return_report: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, Any]]:
    """Create the improved backend-compatible regression feature frame."""
    cleaned, report = clean_price_data(df, config=config, include_target=include_target)
    work = _add_advanced_features(cleaned)

    for column in config.features.numeric_features:
        work[column] = pd.to_numeric(work[column], errors="coerce").fillna(0)
    for column in config.features.categorical_features:
        work[column] = work[column].map(_normalise_text)

    selected = feature_columns(config, "improved")
    if include_target:
        selected = selected + [config.features.target_col]

    frame = work[selected].reset_index(drop=True)
    if return_report:
        return frame, report
    return frame


def build_feature_frame_for_profile(
    df: pd.DataFrame,
    config: Config = cfg,
    profile: PreprocessingProfile = "improved",
    include_target: bool = True,
    return_report: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, Any]]:
    if profile == "legacy":
        frame = build_legacy_feature_frame(df, config=config, include_target=include_target)
        report = {
            "rows_before": int(len(df)),
            "rows_after": int(len(frame)),
            "profile": "legacy",
            "notes": "Legacy preprocessing keeps ID-like category features and does minimal cleaning.",
        }
        return (frame, report) if return_report else frame
    return build_feature_frame(df, config=config, include_target=include_target, return_report=return_report)


def split_features_target(
    df: pd.DataFrame,
    config: Config = cfg,
    profile: PreprocessingProfile = "improved",
) -> tuple[pd.DataFrame, pd.Series]:
    """Return X/y for model training."""
    prepared = build_feature_frame_for_profile(df, config=config, profile=profile, include_target=True)
    assert isinstance(prepared, pd.DataFrame)
    X = prepared[feature_columns(config, profile)]
    y = prepared[config.features.target_col].astype(float)
    return X, y


def build_preprocessor(config: Config = cfg, profile: PreprocessingProfile = "improved") -> ColumnTransformer:
    """Build the reusable sklearn preprocessing transformer."""
    numeric_features = (
        config.features.legacy_numeric_features
        if profile == "legacy"
        else config.features.numeric_features
    )
    categorical_features = (
        config.features.legacy_categorical_features
        if profile == "legacy"
        else config.features.categorical_features
    )

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", RobustScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", _one_hot_encoder(config)),
        ]
    )

    transformers = [
        ("numeric", numeric_pipeline, numeric_features),
        ("categorical", categorical_pipeline, categorical_features),
    ]
    if profile != "legacy" and config.features.target_encoded_features:
        transformers.append(
            (
                "target_price_prior",
                TargetMeanEncoder(smoothing=config.features.target_encoding_smoothing),
                config.features.target_encoded_features,
            )
        )

    return ColumnTransformer(transformers=transformers, remainder="drop")
