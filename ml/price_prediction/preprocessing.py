"""
Preprocessing and feature engineering for product price prediction.
"""

import json
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

from .config import Config, cfg


def _one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # pragma: no cover - compatibility with older sklearn
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def _text_length(value: Any) -> int:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0
    return len(str(value).strip())


def _tag_count(value: Any) -> int:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0
    if isinstance(value, list):
        return len(value)
    if isinstance(value, tuple):
        return len(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        try:
            decoded = json.loads(text)
            if isinstance(decoded, list):
                return len(decoded)
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
    if value is None or (isinstance(value, float) and np.isnan(value)):
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


def build_feature_frame(df: pd.DataFrame, config: Config = cfg, include_target: bool = True) -> pd.DataFrame:
    """Create backend-compatible regression features from raw product rows."""
    work = df.copy()

    defaults: dict[str, Any] = {
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
    for column, default in defaults.items():
        if column not in work.columns:
            if isinstance(default, list):
                work[column] = [list(default) for _ in range(len(work))]
            else:
                work[column] = default

    work["title_length"] = work["title"].map(_text_length)
    work["description_length"] = work["description"].map(_text_length)
    work["tag_count"] = work["tags"].map(_tag_count)
    work["is_active_int"] = work["is_active"].map(_is_active_int)
    work["product_age_days"] = work["created_at"].map(_product_age_days)

    for column in config.features.numeric_features:
        work[column] = pd.to_numeric(work[column], errors="coerce").fillna(0)

    for column in config.features.categorical_features:
        work[column] = work[column].fillna("unknown").astype(str).str.strip().replace("", "unknown")

    selected = config.features.numeric_features + config.features.categorical_features
    if include_target:
        target = config.features.target_col
        if target not in work.columns:
            raise ValueError(f"Missing target column for price prediction: {target}")
        work[target] = pd.to_numeric(work[target], errors="coerce")
        work = work[work[target].notna() & (work[target] > 0)].copy()
        selected = selected + [target]

    return work[selected].reset_index(drop=True)


def split_features_target(df: pd.DataFrame, config: Config = cfg) -> tuple[pd.DataFrame, pd.Series]:
    """Return X/y for model training."""
    prepared = build_feature_frame(df, config=config, include_target=True)
    X = prepared[config.features.numeric_features + config.features.categorical_features]
    y = prepared[config.features.target_col].astype(float)
    return X, y


def build_preprocessor(config: Config = cfg) -> ColumnTransformer:
    """Build the reusable sklearn preprocessing transformer."""
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", RobustScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", _one_hot_encoder()),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, config.features.numeric_features),
            ("categorical", categorical_pipeline, config.features.categorical_features),
        ],
        remainder="drop",
    )
