"""
train_dbscan.py
---------------
DBSCAN training: epsilon grid search (knee method), min_samples tuning,
model persistence, and noise analysis.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

from .config import Config, cfg
from .visualization import plot_clusters_pca, plot_silhouette_diagram, plot_cluster_sizes

logger = logging.getLogger(__name__)


# ─── Epsilon Selection ────────────────────────────────────────────────────────

def plot_knn_distances(X: np.ndarray, k: int = 5, config: Config = cfg) -> None:
    """K-NN distance plot to find optimal epsilon (knee point)."""
    nbrs = NearestNeighbors(n_neighbors=k).fit(X)
    distances, _ = nbrs.kneighbors(X)
    kth_distances = np.sort(distances[:, k - 1])[::-1]

    fig, ax = plt.subplots(figsize=config.viz.figsize_default)
    ax.plot(kth_distances, linewidth=2, color="steelblue")
    ax.set_xlabel("Points (sorted by distance)")
    ax.set_ylabel(f"{k}-NN Distance")
    ax.set_title(f"K-NN Distance Plot (k={k}) -- Epsilon Selection", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = config.plots_dir / "dbscan_knn_distances.png"
    fig.savefig(path, dpi=config.viz.dpi, bbox_inches="tight")
    plt.show()
    logger.info("KNN distance plot saved → %s", path)


def grid_search_dbscan(X: np.ndarray, config: Config = cfg) -> pd.DataFrame:
    """
    Grid search over eps and min_samples.
    Skips configurations that produce a single cluster or all noise.
    """
    dc = config.dbscan
    records = []

    for eps in dc.eps_range:
        for ms in dc.min_samples_range:
            model = DBSCAN(eps=eps, min_samples=ms, metric=dc.metric)
            labels = model.fit_predict(X)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            noise_pct = round((labels == -1).mean() * 100, 2)

            if n_clusters < 2:
                sil, dbi, chi = np.nan, np.nan, np.nan
            else:
                mask = labels != -1
                sil = round(silhouette_score(X[mask], labels[mask]), 4)
                dbi = round(davies_bouldin_score(X[mask], labels[mask]), 4)
                chi = round(calinski_harabasz_score(X[mask], labels[mask]), 4)

            records.append({
                "eps": eps, "min_samples": ms,
                "n_clusters": n_clusters, "noise_pct": noise_pct,
                "silhouette": sil, "davies_bouldin": dbi, "calinski_harabasz": chi,
            })
            logger.info("eps=%.2f ms=%d | clusters=%d noise=%.1f%% sil=%s",
                        eps, ms, n_clusters, noise_pct, sil)

    df_grid = pd.DataFrame(records)
    path = config.reports_dir / "dbscan_grid_search.csv"
    df_grid.to_csv(path, index=False)
    logger.info("DBSCAN grid search results saved → %s", path)
    return df_grid


# ─── Training ────────────────────────────────────────────────────────────────

def train_dbscan(X: np.ndarray, config: Config = cfg) -> DBSCAN:
    dc = config.dbscan
    logger.info("Training DBSCAN eps=%.2f min_samples=%d …", dc.eps, dc.min_samples)
    model = DBSCAN(eps=dc.eps, min_samples=dc.min_samples, metric=dc.metric)
    model.fit(X)
    labels = model.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_pct = (labels == -1).mean() * 100
    logger.info("DBSCAN fitted | clusters=%d | noise=%.1f%%", n_clusters, noise_pct)
    return model


# ─── Evaluation ──────────────────────────────────────────────────────────────

def evaluate_dbscan(X: np.ndarray, model: DBSCAN) -> dict:
    labels = model.labels_
    mask = labels != -1
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_count = int((labels == -1).sum())

    metrics = {
        "n_clusters":    n_clusters,
        "noise_count":   noise_count,
        "noise_pct":     round((labels == -1).mean() * 100, 2),
    }

    if n_clusters >= 2:
        metrics["silhouette_score"]  = round(silhouette_score(X[mask], labels[mask]), 4)
        metrics["davies_bouldin"]    = round(davies_bouldin_score(X[mask], labels[mask]), 4)
        metrics["calinski_harabasz"] = round(calinski_harabasz_score(X[mask], labels[mask]), 4)
    else:
        metrics.update({"silhouette_score": np.nan, "davies_bouldin": np.nan, "calinski_harabasz": np.nan})
        logger.warning("DBSCAN produced <2 clusters -- adjust eps/min_samples.")

    for k, v in metrics.items():
        logger.info("  %-25s %s", k, v)
    return metrics


# ─── Persistence ─────────────────────────────────────────────────────────────

def save_dbscan(model: DBSCAN, config: Config = cfg) -> Path:
    path = config.models_dir / "dbscan_model.pkl"
    joblib.dump(model, path)
    logger.info("DBSCAN model saved → %s", path)
    return path


def load_dbscan(config: Config = cfg) -> DBSCAN:
    path = config.models_dir / "dbscan_model.pkl"
    model = joblib.load(path)
    logger.info("DBSCAN model loaded ← %s", path)
    return model


# ─── Full Run ─────────────────────────────────────────────────────────────────

def run_dbscan(X: np.ndarray, df_clean, feature_cols: list, config: Config = cfg) -> dict:
    """End-to-end DBSCAN pipeline."""
    logger.info("=== DBSCAN Pipeline ===")

    plot_knn_distances(X, k=config.dbscan.min_samples, config=config)
    grid_results = grid_search_dbscan(X, config)

    model = train_dbscan(X, config)
    labels = model.labels_
    metrics = evaluate_dbscan(X, model)

    plot_clusters_pca(X, labels, config, model_name="DBSCAN")
    plot_cluster_sizes(labels, config, model_name="DBSCAN")

    n_clusters = metrics["n_clusters"]
    if n_clusters >= 2:
        mask = labels != -1
        plot_silhouette_diagram(X[mask], labels[mask], config, model_name="DBSCAN")

    save_dbscan(model, config)

    df_out = df_clean[["user_id"]].copy()
    df_out["dbscan_cluster"] = labels
    out_path = config.data_dir / "dbscan_labels.csv"
    df_out.to_csv(out_path, index=False)
    logger.info("DBSCAN labels saved → %s", out_path)

    return {"model": model, "labels": labels, "metrics": metrics, "grid": grid_results}
