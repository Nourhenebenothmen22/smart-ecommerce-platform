"""
train_kmeans.py
---------------
K-Means training: elbow method, silhouette selection, model persistence.
"""

import logging
from pathlib import Path
import numpy as np
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
    results = {"k": [], "inertia": [], "silhouette": []}
    kc = config.kmeans

    for k in kc.k_range:
        km = KMeans(n_clusters=k, init=kc.init, n_init=kc.n_init,
                    max_iter=kc.max_iter, random_state=config.random_state)
        km.fit(X)
        sil = silhouette_score(X, km.labels_)
        results["k"].append(k)
        results["inertia"].append(km.inertia_)
        results["silhouette"].append(sil)
        logger.info("K-Means Tuning: k=%d | inertia=%.2f | silhouette=%.4f", k, km.inertia_, sil)

    plot_kmeans_elbow(results["k"], results["inertia"], config)
    plot_kmeans_silhouette(results["k"], results["silhouette"], config)
    
    best_k = results["k"][np.argmax(results["silhouette"])]
    logger.info("Best k selected by silhouette score: %d", best_k)
    return best_k

def train_kmeans(X: np.ndarray, k: int, config: Config = cfg) -> KMeans:
    """Train K-Means with a specific k."""
    kc = config.kmeans
    km = KMeans(
        n_clusters=k,
        init=kc.init,
        n_init=kc.n_init,
        max_iter=kc.max_iter,
        random_state=config.random_state,
    )
    km.fit(X)
    return km

def evaluate_kmeans(X: np.ndarray, model: KMeans) -> dict:
    """Return clustering quality metrics."""
    labels = model.labels_
    metrics = {
        "silhouette_score":   round(silhouette_score(X, labels), 4),
        "davies_bouldin":     round(davies_bouldin_score(X, labels), 4),
        "calinski_harabasz":  round(calinski_harabasz_score(X, labels), 4),
        "inertia":            round(model.inertia_, 4),
        "n_clusters":         model.n_clusters,
    }
    return metrics

def run_kmeans_pipeline(X: np.ndarray, df_clean, config: Config = cfg) -> dict:
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
    df_out["kmeans_cluster"] = model.labels_
    df_out.to_csv(config.data_dir / "kmeans_labels.csv", index=False)
    
    return {
        "model": model, 
        "labels": model.labels_, 
        "metrics": metrics,
        "best_k": best_k
    }
