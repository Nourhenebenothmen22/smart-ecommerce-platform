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
from .visualization import plot_elbow, plot_silhouette_scores, plot_clusters_pca, \
    plot_silhouette_diagram, plot_cluster_sizes

logger = logging.getLogger(__name__)


# ─── Model Selection ─────────────────────────────────────────────────────────

def elbow_analysis(X: np.ndarray, config: Config = cfg) -> dict:
    """Compute inertia and silhouette for each k in k_range."""
    results = {"k": [], "inertia": [], "silhouette": []}
    kc = config.kmeans

    for k in kc.k_range:
        km = KMeans(n_clusters=k, init=kc.init, n_init=kc.n_init,
                    max_iter=kc.max_iter, random_state=config.random_state)
        km.fit(X)
        sil = silhouette_score(X, km.labels_) if k > 1 else 0.0
        results["k"].append(k)
        results["inertia"].append(km.inertia_)
        results["silhouette"].append(sil)
        logger.info("k=%d | inertia=%.2f | silhouette=%.4f", k, km.inertia_, sil)

    plot_elbow(results["k"], results["inertia"], config)
    plot_silhouette_scores(results["k"], results["silhouette"], config, model_name="KMeans")
    return results


# ─── Training ────────────────────────────────────────────────────────────────

def train_kmeans(X: np.ndarray, config: Config = cfg) -> KMeans:
    """Train K-Means with the configured n_clusters."""
    kc = config.kmeans
    logger.info("Training K-Means with k=%d …", kc.n_clusters)
    km = KMeans(
        n_clusters=kc.n_clusters,
        init=kc.init,
        n_init=kc.n_init,
        max_iter=kc.max_iter,
        random_state=config.random_state,
    )
    km.fit(X)
    logger.info("K-Means trained | inertia=%.2f", km.inertia_)
    return km


# ─── Evaluation ──────────────────────────────────────────────────────────────

def evaluate_kmeans(X: np.ndarray, model: KMeans) -> dict:
    """Return clustering quality metrics."""
    labels = model.labels_
    metrics = {
        "inertia":            round(model.inertia_, 4),
        "silhouette_score":   round(silhouette_score(X, labels), 4),
        "davies_bouldin":     round(davies_bouldin_score(X, labels), 4),
        "calinski_harabasz":  round(calinski_harabasz_score(X, labels), 4),
        "n_clusters":         model.n_clusters,
    }
    for k, v in metrics.items():
        logger.info("  %-25s %s", k, v)
    return metrics


# ─── Persistence ─────────────────────────────────────────────────────────────

def save_kmeans(model: KMeans, config: Config = cfg) -> Path:
    path = config.models_dir / "kmeans_model.pkl"
    joblib.dump(model, path)
    logger.info("K-Means model saved → %s", path)
    return path


def load_kmeans(config: Config = cfg) -> KMeans:
    path = config.models_dir / "kmeans_model.pkl"
    model = joblib.load(path)
    logger.info("K-Means model loaded ← %s", path)
    return model


# ─── Full Run ─────────────────────────────────────────────────────────────────

def run_kmeans(X: np.ndarray, df_clean, feature_cols: list, config: Config = cfg) -> dict:
    """
    End-to-end K-Means pipeline:
    1. Elbow + silhouette analysis
    2. Train final model
    3. Evaluate & plot
    4. Save model & labels

    Returns
    -------
    dict: { 'model', 'labels', 'metrics', 'selection_results' }
    """
    logger.info("=== K-Means Pipeline ===")
    selection = elbow_analysis(X, config)

    model = train_kmeans(X, config)
    labels = model.labels_
    metrics = evaluate_kmeans(X, model)

    plot_clusters_pca(X, labels, config, model_name="KMeans", centers=model.cluster_centers_)
    plot_silhouette_diagram(X, labels, config, model_name="KMeans")
    plot_cluster_sizes(labels, config, model_name="KMeans")

    save_kmeans(model, config)

    # Save labels
    import pandas as pd
    df_out = df_clean[["user_id"]].copy()
    df_out["kmeans_cluster"] = labels
    out_path = config.data_dir / "kmeans_labels.csv"
    df_out.to_csv(out_path, index=False)
    logger.info("K-Means labels saved → %s", out_path)

    return {"model": model, "labels": labels, "metrics": metrics, "selection": selection}
