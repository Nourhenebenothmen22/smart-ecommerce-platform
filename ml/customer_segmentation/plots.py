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

# ─── 1. Data Understanding Distributions ──────────────────────────────────────
def plot_data_distributions(df: pd.DataFrame, config: Config = cfg) -> None:
    """
    Objectif : Comprendre les distributions des variables business importantes.
    """
    features = [
        "total_orders", "total_spent", "avg_order_value", "views_count",
        "clicks_count", "cart_add_count", "wishlist_add_count",
        "days_since_last_interaction", "purchase_to_view_ratio", "cart_to_click_ratio"
    ]
    
    # Filter only existing columns
    cols = [c for c in features if c in df.columns]
    n = len(cols)
    ncols = 2
    nrows = int(np.ceil(n / ncols))
    
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 5 * nrows))
    axes = axes.flatten()
    
    for i, col in enumerate(cols):
        sns.histplot(df[col].dropna(), kde=True, ax=axes[i], color="teal")
        axes[i].set_title(f"Distribution : {col}", fontsize=12, fontweight="bold")
        axes[i].set_xlabel(col)
        axes[i].set_ylabel("Frequence")
        
    for j in range(n, len(axes)):
        axes[j].set_visible(False)
        
    plt.suptitle("Data Understanding -- Feature Distributions", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    _save(fig, config.plots_dir / "eda_distributions_main.png", config)

# ─── 2. Correlation Matrix ───────────────────────────────────────────────────
def plot_correlation_matrix(df: pd.DataFrame, config: Config = cfg) -> None:
    """
    Objectif : Vérifier les relations entre les variables importantes et détecter les redondances.
    """
    features = [
        "total_orders", "total_spent", "avg_order_value", "views_count",
        "clicks_count", "cart_add_count", "wishlist_add_count",
        "days_since_last_interaction", "purchase_to_view_ratio", "cart_to_click_ratio"
    ]
    cols = [c for c in features if c in df.columns]
    corr = df[cols].corr()
    
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax, square=True)
    ax.set_title("Correlation Matrix : Important Features", fontsize=14, fontweight="bold")
    
    _save(fig, config.plots_dir / "correlation_matrix_important_features.png", config)

# ─── 3. Model Metric Comparison ──────────────────────────────────────────────
def plot_model_comparison(results: dict, config: Config = cfg) -> None:
    """
    Objectif : Comparer clairement K-Means, GMM et DBSCAN.
    Affiche : Silhouette, Davies-Bouldin, Calinski-Harabasz, n_clusters, noise_ratio, avg_confidence.
    """
    metrics = ["silhouette_score", "davies_bouldin_score", "calinski_harabasz_score", "n_clusters"]
    data = []
    
    for name, res in results.items():
        m = res.get("metrics", {})
        row = {"Model": name}
        row.update(m)
        # Add extra metrics
        if name == "DBSCAN":
            row["noise_ratio"] = m.get("noise_pct", 0) / 100
        if name == "GMM":
            row["avg_confidence"] = res.get("avg_confidence", 0)
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
        
    plt.suptitle("Model Performance Comparison", fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    _save(fig, config.plots_dir / "model_metric_comparison.png", config)

# ─── 4. Final Segment Distribution ───────────────────────────────────────────
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
        
    ax.set_title("Final Business Segment Distribution", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Users")
    
    _save(fig, config.plots_dir / "final_business_segment_distribution.png", config)
