"""
train_kmeans.py
---------------
K-Means training: elbow method, silhouette selection, model persistence.
"""

import logging
from typing import Any, Dict
import numpy as np
import pandas as pd
import joblib
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

from .config import Config, cfg
from .plots import plot_kmeans_elbow, plot_kmeans_silhouette

logger = logging.getLogger(__name__)

def run_kmeans_tuning(X: np.ndarray, config: Config = cfg) -> int:
    """
    Tune k using Elbow and Silhouette.
    Returns the best_k based on highest silhouette score.
    """
    X_f = X.astype(np.float64)
    if len(X_f) < 3:
        raise ValueError("K-Means training requires at least 3 user feature rows.")

    ks = [k for k in config.kmeans.k_range if 2 <= k < len(X_f)]
    if not ks:
        raise ValueError(f"No valid K-Means cluster count for {len(X_f)} rows.")
    inertias = []
    silhouettes = []

    for k in ks:
        km = KMeans(
            n_clusters=k, 
            init=config.kmeans.init,  # type: ignore
            n_init=config.kmeans.n_init,
            max_iter=config.kmeans.max_iter, 
            random_state=config.random_state
        )
        km.fit(X_f)
        sil = float(silhouette_score(X_f, km.labels_))  # type: ignore
        
        inertias.append(km.inertia_)
        silhouettes.append(sil)
        logger.info("K-Means Tuning: k=%d | inertia=%.2f | silhouette=%.4f", k, km.inertia_, sil)

    plot_kmeans_elbow(ks, inertias, config)
    plot_kmeans_silhouette(ks, silhouettes, config)
    
    if not silhouettes:
        return 2
        
    best_k = ks[np.argmax(silhouettes)]
    logger.info("Best k selected by silhouette score: %d", best_k)
    return best_k

def train_kmeans(X: np.ndarray, k: int, config: Config = cfg) -> KMeans:
    """Train K-Means with a specific k."""
    km = KMeans(
        n_clusters=k,
        init=config.kmeans.init,  # type: ignore
        n_init=config.kmeans.n_init,
        max_iter=config.kmeans.max_iter,
        random_state=config.random_state,
    )
    km.fit(X.astype(np.float64))
    return km

def evaluate_kmeans(X: np.ndarray, model: KMeans) -> Dict[str, Any]:
    """Return clustering quality metrics."""
    X_f = X.astype(np.float64)
    labels = model.labels_
    metrics = {
        "silhouette_score":   round(float(silhouette_score(X_f, labels)), 4),  # type: ignore
        "davies_bouldin":     round(float(davies_bouldin_score(X_f, labels)), 4),  # type: ignore
        "calinski_harabasz":  round(float(calinski_harabasz_score(X_f, labels)), 4),  # type: ignore
        "inertia":            round(model.inertia_, 4),
        "n_clusters":         model.get_params().get("n_clusters", 0),
    }
    return metrics

def run_kmeans_pipeline(X: np.ndarray, df_clean: pd.DataFrame, config: Config = cfg) -> Dict[str, Any]:
    """End-to-end K-Means pipeline."""
    logger.info("=== K-Means Pipeline ===")
    
    best_k = run_kmeans_tuning(X, config)
    model = train_kmeans(X, best_k, config)
    metrics = evaluate_kmeans(X, model)
    
    # Save model
    model_path = config.models_dir / "kmeans_model.pkl"
    joblib.dump(model, model_path)
    logger.info("K-Means model saved → %s", model_path)
    
    # Save labels
    df_out = df_clean[["user_id"]].copy()
    df_out["kmeans_cluster"] = model.labels_.astype(int)
    df_out.to_csv(config.data_dir / "kmeans_labels.csv", index=False)
    
    return {
        "model": model, 
        "labels": model.labels_, 
        "metrics": metrics,
        "best_k": best_k
    }
