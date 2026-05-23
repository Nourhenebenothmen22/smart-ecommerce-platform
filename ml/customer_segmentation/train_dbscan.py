"""
train_dbscan.py
---------------
DBSCAN training: epsilon grid search, min_samples tuning,
model persistence, and noise analysis.
"""

import logging
import numpy as np
import pandas as pd
import joblib
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

from .config import Config, cfg
from .plots import plot_dbscan_k_distance

logger = logging.getLogger(__name__)

def grid_search_dbscan(X: np.ndarray, config: Config = cfg) -> dict:
    """
    Dynamically tunes DBSCAN by analyzing data density (k-distance).
    """
    X_f = X.astype(np.float64)
    if len(X_f) < 3:
        raise ValueError("DBSCAN training requires at least 3 user feature rows.")
    
    # 1. Dynamically estimate a baseline epsilon using k-distance
    n_neighbors = min(config.dbscan.min_samples, len(X_f))
    nbrs = NearestNeighbors(n_neighbors=n_neighbors).fit(X_f)  # type: ignore
    distances, _ = nbrs.kneighbors(X_f)  # type: ignore
    avg_dist = float(distances[:, -1].mean())  # type: ignore
    
    # Create a dynamic range around the average distance
    dynamic_eps_range = np.linspace(avg_dist * 0.5, avg_dist * 2.0, 10)  # type: ignore
    
    best_params = {"eps": avg_dist, "min_samples": n_neighbors, "score": -1.0}
    
    for eps in dynamic_eps_range:
        for ms in [value for value in config.dbscan.min_samples_range if 2 <= value <= len(X_f)]:
            model = DBSCAN(eps=eps, min_samples=ms, metric=config.dbscan.metric)
            labels = model.fit_predict(X_f)  # type: ignore
            
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            noise_count = int((labels == -1).sum())
            noise_pct = (noise_count / len(labels)) * 100
            
            # Validity check: avoid single cluster or excessive noise, and respect max 3 clusters
            if 2 <= n_clusters <= 3 and noise_pct < 50:
                mask = labels != -1
                if len(set(labels[mask])) < 2:
                    continue
                score = silhouette_score(X_f[mask], labels[mask])  # type: ignore
                
                if score > best_params["score"]:
                    best_params["eps"] = eps
                    best_params["min_samples"] = ms
                    best_params["score"] = float(score)
            
    logger.info("Dynamic DBSCAN Tuning: eps=%.3f, min_samples=%d (Score: %.4f)", 
                best_params["eps"], best_params["min_samples"], best_params["score"])
    
    return best_params

def train_dbscan(X: np.ndarray, eps: float, min_samples: int, config: Config = cfg) -> DBSCAN:
    """Train DBSCAN with specific parameters."""
    model = DBSCAN(eps=eps, min_samples=min_samples, metric=config.dbscan.metric)
    model.fit(X.astype(np.float64))  # type: ignore
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
        metrics["silhouette_score"] = round(float(silhouette_score(X[mask], labels[mask])), 4)  # type: ignore
        metrics["davies_bouldin"] = round(float(davies_bouldin_score(X[mask], labels[mask])), 4)  # type: ignore
        metrics["calinski_harabasz"] = round(float(calinski_harabasz_score(X[mask], labels[mask])), 4)  # type: ignore
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
    
    plot_dbscan_k_distance(X, k=min(config.dbscan.min_samples, len(X)), config=config)
    
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
