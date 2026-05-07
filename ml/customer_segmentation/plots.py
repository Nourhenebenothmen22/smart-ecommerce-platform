"""
plots.py
--------
Centralized visualization logic for the Customer Segmentation pipeline.
Only 4 families of plots are maintained for maximum clarity and relevance.
"""

import logging
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .config import Config, cfg

logger = logging.getLogger(__name__)

def _save(fig: plt.Figure, path: Path, config: Config) -> None:
    fig.savefig(path, dpi=config.viz.dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Plot saved → %s", path)



# ─── 1. Model Metric Comparison ──────────────────────────────────────────────
def plot_model_comparison(results: dict, config: Config = cfg) -> None:
    """
    Objectif : Comparer clairement K-Means et DBSCAN.
    Affiche : Silhouette, Davies-Bouldin, Calinski-Harabasz, n_clusters.
    """
    metrics = ["silhouette_score", "davies_bouldin", "calinski_harabasz", "n_clusters"]
    data = []
    
    for name, res in results.items():
        m = res.get("metrics", {})
        row = {"Model": name}
        for met in metrics:
            row[met] = m.get(met, np.nan)
        data.append(row)
        
    df_metrics = pd.DataFrame(data)
    
    # Plotting
    metrics_to_show = [m for m in df_metrics.columns if m != "Model"]
    n = len(metrics_to_show)
    fig, axes = plt.subplots(int(np.ceil(n/2)), 2, figsize=(15, 5 * int(np.ceil(n/2))))
    axes = axes.flatten()
    
    for i, metric in enumerate(metrics_to_show):
        sns.barplot(x="Model", y=metric, data=df_metrics, ax=axes[i], palette="viridis")
        axes[i].set_title(f"Metric : {metric.replace('_', ' ').title()}", fontsize=12, fontweight="bold")
        # Add labels to explain metrics
        if "silhouette" in metric: axes[i].set_ylabel("Higher = Better")
        if "davies" in metric: axes[i].set_ylabel("Lower = Better")
        
    for j in range(n, len(axes)):
        axes[j].set_visible(False)
        
    plt.suptitle("K-Means vs DBSCAN — Model Comparison", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    _save(fig, config.plots_dir / "kmeans_vs_dbscan_comparison.png", config)

# ─── 2. Final Segment Distribution ───────────────────────────────────────────
def plot_final_segment_distribution(df_labelled: pd.DataFrame, config: Config = cfg) -> None:
    """
    Objectif : Vérifier la distribution finale des segments business.
    """
    if "segment_label" not in df_labelled.columns:
        logger.warning("No segment_label column found in df_labelled.")
        return
        
    counts = df_labelled["segment_label"].value_counts().reset_index()
    counts.columns = ["Segment", "Count"]
    
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.barplot(x="Count", y="Segment", data=counts, ax=ax, palette="coolwarm")
    
    # Add values on bars
    for i, v in enumerate(counts["Count"]):
        ax.text(v + 3, i, str(v), color='black', va='center', fontweight='bold')
        
    ax.set_title("Final Business Segment Distribution — Best Model", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Users")
    
    _save(fig, config.plots_dir / "final_best_model_segments.png", config)
