"""
Production inference helpers for customer segmentation.
"""

import json
from typing import Any

import joblib
import pandas as pd
from sklearn.cluster import KMeans

from .config import Config, cfg
from .preprocessing import preprocess


def _load_segment_map(config: Config) -> dict[int, dict[str, str]]:
    path = config.models_dir / "segment_map.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return {int(k): v for k, v in json.load(f).items()}


def _load_kmeans(config: Config) -> KMeans:
    path = config.models_dir / "kmeans_model.pkl"
    if not path.exists():
        raise FileNotFoundError(f"K-Means model artifact not found: {path}")
    model = joblib.load(path)
    if not hasattr(model, "predict"):
        raise TypeError("Loaded segmentation artifact does not support production prediction.")
    return model


def predict_segment(features: dict[str, Any], config: Config = cfg) -> dict[str, Any]:
    """
    Predict a user segment from one backend user_features-shaped payload.
    """
    payload = dict(features)
    payload.setdefault("user_id", 0)
    df = pd.DataFrame([payload])
    X_scaled, _, _, _ = preprocess(df, config=config, fit=False)

    model = _load_kmeans(config)
    cluster = int(model.predict(X_scaled)[0])
    segment_map = _load_segment_map(config)
    segment = segment_map.get(cluster, {})

    return {
        "user_id": int(payload["user_id"]),
        "segment_id": cluster,
        "segment_label": segment.get("label", f"Cluster {cluster}"),
        "model_name": config.segmentation_model_name,
        "model_version": config.segmentation_model_version,
    }
