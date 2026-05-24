"""
Production inference for product price prediction.
"""

import json
from typing import Any

import joblib
import pandas as pd

from .config import Config, cfg
from .data_loader import load_product_features
from .preprocessing import build_feature_frame_for_profile, feature_columns


def _load_metadata(config: Config) -> dict[str, Any]:
    path = config.models_dir / "metadata.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_best_model(config: Config):
    path = config.models_dir / "best_model.pkl"
    if not path.exists():
        raise FileNotFoundError(f"Price prediction model artifact not found: {path}")
    model = joblib.load(path)
    if not hasattr(model, "predict"):
        raise TypeError("Loaded price prediction artifact does not support prediction.")
    return model


def _merge_product_payload(payload: dict[str, Any], config: Config) -> dict[str, Any]:
    product_id = payload.get("product_id")
    if not product_id:
        return payload

    db_payload = load_product_features(int(product_id), config=config)
    clean_overrides = {key: value for key, value in payload.items() if value is not None}
    db_payload.update(clean_overrides)
    return db_payload


def predict_price(payload: dict[str, Any], config: Config = cfg) -> dict[str, Any]:
    """
    Predict a product price from either a product_id or explicit product fields.
    """
    merged_payload = _merge_product_payload(dict(payload), config=config)
    model = _load_best_model(config)
    metadata = _load_metadata(config)
    profile = metadata.get("best_profile", "improved")

    df = pd.DataFrame([merged_payload])
    feature_frame = build_feature_frame_for_profile(df, config=config, profile=profile, include_target=False)
    assert isinstance(feature_frame, pd.DataFrame)
    X = feature_frame[feature_columns(config, profile)]

    prediction = float(model.predict(X)[0])
    prediction = max(prediction, 0.0)

    return {
        "product_id": merged_payload.get("product_id"),
        "predicted_price": round(prediction, 2),
        "currency": "EUR",
        "model_name": config.price_model_name,
        "model_version": config.price_model_version,
        "model_algorithm": metadata.get("best_result_key", metadata.get("best_model", "unknown")),
        "preprocessing_profile": profile,
        "metrics": metadata.get("metrics", {}),
        "features_used": feature_columns(config, profile),
    }
