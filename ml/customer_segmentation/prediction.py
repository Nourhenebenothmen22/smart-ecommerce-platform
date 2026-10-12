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


_SEGMENT_MAP_CACHE: dict[str, tuple[float, dict[int, dict[str, str]]]] = {}
_TRAINING_METADATA_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_KMEANS_CACHE: dict[str, tuple[float, KMeans]] = {}


def _load_segment_map(config: Config) -> dict[int, dict[str, str]]:
    path = config.models_dir / "segment_map.json"
    if not path.exists():
        return {}
    mtime = path.stat().st_mtime
    cached = _SEGMENT_MAP_CACHE.get(str(path))
    if cached and cached[0] == mtime:
        return cached[1]
    with open(path) as f:
        data = {int(k): v for k, v in json.load(f).items()}
    _SEGMENT_MAP_CACHE[str(path)] = (mtime, data)
    return data


def _load_training_metadata(config: Config) -> dict[str, Any]:
    path = config.metadata_dir / "training_metadata.json"
    if not path.exists():
        return {}
    mtime = path.stat().st_mtime
    cached = _TRAINING_METADATA_CACHE.get(str(path))
    if cached and cached[0] == mtime:
        return cached[1]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    _TRAINING_METADATA_CACHE[str(path)] = (mtime, data)
    return data


def _load_kmeans(config: Config) -> KMeans:
    path = config.models_dir / "kmeans_model.pkl"
    if not path.exists():
        raise FileNotFoundError(f"K-Means model artifact not found: {path}")
    mtime = path.stat().st_mtime
    cached = _KMEANS_CACHE.get(str(path))
    if cached and cached[0] == mtime:
        return cached[1]
    model = joblib.load(path)
    if not hasattr(model, "predict"):
        raise TypeError("Loaded segmentation artifact does not support production prediction.")
    _KMEANS_CACHE[str(path)] = (mtime, model)
    return model


def predict_segment(features: dict[str, Any], config: Config = cfg) -> dict[str, Any]:
    """
    Predict a user segment from one backend user_features-shaped payload.
    """
    payload = dict(features)
    payload.setdefault("user_id", 0)
    df = pd.DataFrame([payload])
    X_scaled, _, _, _ = preprocess(df, config=config, fit=False)

    metadata = _load_training_metadata(config)
    production_model_type = metadata.get("production_model_type", "KMeans")
    if str(production_model_type).lower() != "kmeans":
        raise TypeError(
            f"Unsupported production segmentation model type: {production_model_type}. "
            "Retrain with a KMeans production artifact before serving predictions."
        )

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
