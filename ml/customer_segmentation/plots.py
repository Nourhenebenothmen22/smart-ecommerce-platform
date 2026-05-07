"""
plots.py
--------
Centralized visualization logic for the Customer Segmentation pipeline.
Only required plots are maintained for maximum clarity and relevance.
"""

import logging
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import NearestNeighbors
from .config import Config, cfg

logger = logging.getLogger(__name__)

def _save(fig: plt.Figure, path: Path, config: Config) -> None:
    fig.savefig(path, dpi=config.viz.dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Plot saved → %s", path)

# ─── 1. K-Means Elbow Plot ───────────────────────────────────────────────────
def plot_kmeans_elbow(k_range, inertias, config: Config = cfg) -> None:
    fig, ax = plt.subplots(figsize=config.viz.figsize_default)
    ax.plot(k_range, inertias, "bo-", markersize=8, linewidth=2)
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Inertia (WCSS)")
    ax.set_title("K-Means Elbow Method", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _save(fig, config.plots_dir / "kmeans_elbow.png", config)

# ─── 2. K-Means Silhouette Plot ──────────────────────────────────────────────
def plot_kmeans_silhouette(k_range, scores, config: Config = cfg) -> None:
    fig, ax = plt.subplots(figsize=config.viz.figsize_default)
    ax.plot(k_range, scores, "gs-", markersize=8, linewidth=2)
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Silhouette Score")
    ax.set_title("K-Means Silhouette Analysis", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _save(fig, config.plots_dir / "kmeans_silhouette.png", config)

# ─── 3. DBSCAN K-Distance Plot ────────────────────────────────────────────────
def plot_dbscan_k_distance(X: np.ndarray, k: int = 5, config: Config = cfg) -> None:
    """K-NN distance plot to help identify optimal epsilon."""
    # Use astype(np.float64) to help with some IDE type inference
    nbrs = NearestNeighbors(n_neighbors=k).fit(X.astype(np.float64))
    distances, _ = nbrs.kneighbors(X.astype(np.float64))
    kth_distances = np.sort(distances[:, k - 1])[::-1]

    fig, ax = plt.subplots(figsize=config.viz.figsize_default)
    ax.plot(kth_distances, linewidth=2, color="steelblue")
    ax.set_xlabel("Points (sorted by distance)")
    ax.set_ylabel(f"{k}-NN Distance")
    ax.set_title(f"DBSCAN K-Distance Plot (k={k})", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _save(fig, config.plots_dir / "dbscan_k_distance.png", config)

# ─── 4. K-Means vs DBSCAN Comparison Plot ────────────────────────────────────
def plot_model_comparison(results: dict, config: Config = cfg) -> None:
    """
    Side-by-side comparison of K-Means and DBSCAN metrics.
    """
    metrics = ["silhouette_score", "davies_bouldin", "calinski_harabasz"]
    data = []
    
    for name, res in results.items():
        m = res.get("metrics", {})
        row = {"Model": name}
        for met in metrics:
            row[met] = m.get(met, np.nan)
        data.append(row)
        
    df_metrics = pd.DataFrame(data)
    
    # Meltdown for easier plotting
    df_melt = df_metrics.melt(id_vars="Model", var_name="Metric", value_name="Score")
    
    fig, ax = plt.subplots(figsize=(12, 7))
    # Cast ax to Any to satisfy strict linting if needed
    sns.barplot(x="Metric", y="Score", hue="Model", data=df_melt, ax=ax, palette="viridis")
    
    ax.set_title("K-Means vs DBSCAN Comparison", fontsize=16, fontweight="bold")
    ax.set_ylabel("Score")
    ax.set_xlabel("")
    plt.xticks(rotation=0)
    ax.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    _save(fig, config.plots_dir / "kmeans_vs_dbscan_comparison.png", config)

# ─── 5. Final Best Model Segment Distribution ────────────────────────────────
def plot_final_segment_distribution(df_labelled: pd.DataFrame, config: Config = cfg) -> None:
    """
    Distribution of final business segments for the selected best model.
    """
    if "segment" not in df_labelled.columns:
        # Fallback to cluster if segment not yet mapped
        col = "cluster" if "cluster" in df_labelled.columns else None
        if not col:
            logger.warning("No segment or cluster column found for distribution plot.")
            return
    else:
        col = "segment"
        
    counts = df_labelled[col].value_counts().reset_index()
    counts.columns = ["Segment", "Count"]
    
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.barplot(x="Count", y="Segment", data=counts, ax=ax, palette="magma")
    
    # Add labels on bars
    for i, v in enumerate(counts["Count"]):
        ax.text(v + 0.5, i, str(v), color='black', va='center', fontweight='bold')
        
    ax.set_title("Final Model Segment Distribution", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Users")
    
    plt.tight_layout()
    _save(fig, config.plots_dir / "final_best_model_segments.png", config)
