"""
train_dbscan.py
---------------
DBSCAN training: epsilon grid search, min_samples tuning,
model persistence, and noise analysis.
"""

import logging
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import joblib
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

from .config import Config, cfg
from .plots import plot_dbscan_k_distance

logger = logging.getLogger(__name__)

def grid_search_dbscan(X: np.ndarray, config: Config = cfg) -> dict:
    """
    Grid search over eps and min_samples.
    Returns best parameters based on silhouette score (with validity checks).
    """
    dc = config.dbscan
    best_params = {"eps": float(dc.eps), "min_samples": int(dc.min_samples), "score": -1.0}
    
    for eps in dc.eps_range:
        for ms in dc.min_samples_range:
            model = DBSCAN(eps=eps, min_samples=ms, metric=dc.metric)
            # Use Any to bypass strict type checking for ndarray in fit_predict
            labels = model.fit_predict(X.astype(np.float64))
            
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            noise_count = int((labels == -1).sum())
            noise_pct = (noise_count / len(labels)) * 100
            
            # Handle invalid results
            is_valid = n_clusters >= 2 and noise_pct < 90
            
            if is_valid:
                mask = labels != -1
                score = silhouette_score(X[mask], labels[mask])
                
                if score > best_params["score"]:
                    best_params["eps"] = float(eps)
                    best_params["min_samples"] = int(ms)
                    best_params["score"] = float(score)
            
    logger.info("DBSCAN Tuning: Best Params -> eps=%.2f, min_samples=%d (score=%.4f)", 
                best_params["eps"], best_params["min_samples"], best_params["score"])
    
    return best_params

def train_dbscan(X: np.ndarray, eps: float, min_samples: int, config: Config = cfg) -> DBSCAN:
    """Train DBSCAN with specific parameters."""
    model = DBSCAN(eps=eps, min_samples=min_samples, metric=config.dbscan.metric)
    model.fit(X.astype(np.float64))
    return model

def evaluate_dbscan(X: np.ndarray, model: DBSCAN) -> dict:
    """Return clustering quality metrics."""
    labels = model.labels_
    mask = labels != -1
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_count = int((labels == -1).sum())
    noise_pct = (noise_count / len(labels)) * 100
    
    # Use get_params() to be safe with IDE attribute checks
    params = model.get_params()
    
    metrics = {
        "n_clusters": n_clusters,
        "noise_count": noise_count,
        "noise_pct": round(noise_pct, 2),
        "eps": params.get("eps", 0.5),
        "min_samples": params.get("min_samples", 5)
    }

    if n_clusters >= 2:
        metrics["silhouette_score"] = round(silhouette_score(X[mask], labels[mask]), 4)
        metrics["davies_bouldin"] = round(davies_bouldin_score(X[mask], labels[mask]), 4)
        metrics["calinski_harabasz"] = round(calinski_harabasz_score(X[mask], labels[mask]), 4)
    else:
        # Invalid model metrics
        metrics.update({
            "silhouette_score": -1.0, 
            "davies_bouldin": 99.0, 
            "calinski_harabasz": 0.0
        })
        
    return metrics

def run_dbscan_pipeline(X: np.ndarray, df_clean: pd.DataFrame, config: Config = cfg) -> dict:
    """End-to-end DBSCAN pipeline."""
    logger.info("=== DBSCAN Pipeline ===")
    
    plot_dbscan_k_distance(X, k=config.dbscan.min_samples, config=config)
    
    best_params = grid_search_dbscan(X, config)
    model = train_dbscan(X, best_params["eps"], best_params["min_samples"], config)
    metrics = evaluate_dbscan(X, model)
    
    # Save model
    model_path = config.models_dir / "dbscan_model.pkl"
    joblib.dump(model, model_path)
    logger.info("DBSCAN model saved → %s", model_path)
    
    # Save labels
    df_out = df_clean[["user_id"]].copy()
    df_out["dbscan_cluster"] = model.labels_
    df_out.to_csv(config.data_dir / "dbscan_labels.csv", index=False)
    
    return {
        "model": model, 
        "labels": model.labels_, 
        "metrics": metrics
    }
