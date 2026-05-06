"""
visualization.py
----------------
Reusable, model-agnostic plotting utilities for the segmentation pipeline.
All functions save PNGs to config.plots_dir and optionally display inline.
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_samples, silhouette_score

from .config import Config, cfg

logger = logging.getLogger(__name__)


def _save(fig: plt.Figure, path: Path, config: Config) -> None:
    fig.savefig(path, dpi=config.viz.dpi, bbox_inches="tight")
    logger.info("Plot saved → %s", path)


def plot_elbow(k_range, inertias, config: Config = cfg) -> None:
    fig, ax = plt.subplots(figsize=config.viz.figsize_default)
    ax.plot(k_range, inertias, "bo-", markersize=8, linewidth=2)
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Inertia (WCSS)")
    ax.set_title("Elbow Method -- K-Means", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _save(fig, config.plots_dir / "kmeans_elbow.png", config)
    plt.show()


def plot_silhouette_scores(k_range, scores, config: Config = cfg, model_name: str = "Model") -> None:
    fig, ax = plt.subplots(figsize=config.viz.figsize_default)
    ax.plot(k_range, scores, "gs-", markersize=8, linewidth=2)
    ax.set_xlabel("Number of Clusters")
    ax.set_ylabel("Silhouette Score")
    ax.set_title(f"Silhouette Analysis -- {model_name}", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _save(fig, config.plots_dir / f"{model_name.lower()}_silhouette_curve.png", config)
    plt.show()


def plot_bic_aic(n_range, bic, aic, config: Config = cfg) -> None:
    fig, ax = plt.subplots(figsize=config.viz.figsize_default)
    ax.plot(n_range, bic, "b^-", label="BIC", markersize=8, linewidth=2)
    ax.plot(n_range, aic, "rs-", label="AIC", markersize=8, linewidth=2)
    ax.set_xlabel("Number of Components")
    ax.set_ylabel("Score")
    ax.set_title("GMM -- BIC & AIC Selection", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _save(fig, config.plots_dir / "gmm_bic_aic.png", config)
    plt.show()


def plot_clusters_pca(X, labels, config: Config = cfg,
                      model_name: str = "Model", centers=None) -> None:
    """2D PCA projection of clusters."""
    pca = PCA(n_components=2, random_state=config.random_state)
    X2d = pca.fit_transform(X)
    unique_labels = np.unique(labels)
    palette = plt.cm.get_cmap(config.viz.palette, len(unique_labels))

    fig, ax = plt.subplots(figsize=(10, 7))
    for i, lab in enumerate(unique_labels):
        mask = labels == lab
        color = "grey" if lab == -1 else palette(i)
        label_str = "Noise" if lab == -1 else f"Cluster {lab}"
        ax.scatter(X2d[mask, 0], X2d[mask, 1], s=40, alpha=0.6,
                   color=color, label=label_str, edgecolors="white", linewidth=0.3)

    if centers is not None:
        c2d = pca.transform(centers)
        ax.scatter(c2d[:, 0], c2d[:, 1], s=200, marker="X", c="red", zorder=5, label="Centroids")

    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
    ax.set_title(f"{model_name} -- PCA Cluster Projection", fontsize=14, fontweight="bold")
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.2)
    plt.tight_layout()
    _save(fig, config.plots_dir / f"{model_name.lower()}_pca_clusters.png", config)
    plt.show()


def plot_silhouette_diagram(X, labels, config: Config = cfg, model_name: str = "Model") -> None:
    """Per-sample silhouette diagram."""
    unique = [l for l in np.unique(labels) if l != -1]
    if len(unique) < 2:
        logger.warning("Silhouette diagram requires >=2 clusters.")
        return
    mask = labels != -1
    X_v, lab_v = X[mask], labels[mask]
    sil_vals = silhouette_samples(X_v, lab_v)
    avg = silhouette_score(X_v, lab_v)

    palette = plt.cm.get_cmap(config.viz.palette, len(unique))
    fig, ax = plt.subplots(figsize=(10, 7))
    y_lower = 10
    for i, lab in enumerate(unique):
        vals = np.sort(sil_vals[lab_v == lab])
        y_upper = y_lower + vals.shape[0]
        ax.fill_betweenx(np.arange(y_lower, y_upper), 0, vals,
                         facecolor=palette(i), edgecolor=palette(i), alpha=0.7)
        ax.text(-0.05, y_lower + 0.5 * vals.shape[0], str(lab))
        y_lower = y_upper + 10

    ax.axvline(x=avg, color="red", linestyle="--", label=f"Avg={avg:.3f}")
    ax.set_xlabel("Silhouette Coefficient")
    ax.set_ylabel("Cluster")
    ax.set_title(f"{model_name} -- Silhouette Diagram", fontsize=14, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    _save(fig, config.plots_dir / f"{model_name.lower()}_silhouette_diagram.png", config)
    plt.show()


def plot_cluster_profiles(df_clean, labels, feature_cols, config: Config = cfg,
                          model_name: str = "Model") -> pd.DataFrame:
    """Normalised bar chart of cluster feature means."""
    df = df_clean.copy()
    df["cluster"] = labels
    profile = df.groupby("cluster")[feature_cols].mean()
    profile_norm = (profile - profile.min()) / (profile.max() - profile.min() + 1e-9)

    ax = profile_norm.T.plot(kind="bar", figsize=(14, 6), colormap=config.viz.palette,
                              edgecolor="white", alpha=0.85)
    ax.set_title(f"{model_name} -- Cluster Feature Profiles", fontsize=14, fontweight="bold")
    ax.set_xlabel("Feature")
    ax.set_ylabel("Normalised Mean")
    ax.legend(title="Cluster", bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    _save(ax.get_figure(), config.plots_dir / f"{model_name.lower()}_cluster_profiles.png", config)
    plt.show()

    csv_path = config.reports_dir / f"{model_name.lower()}_cluster_profiles.csv"
    profile.to_csv(csv_path)
    logger.info("Cluster profile saved → %s", csv_path)
    return profile


def plot_cluster_sizes(labels, config: Config = cfg, model_name: str = "Model") -> None:
    unique, counts = np.unique(labels, return_counts=True)
    palette = plt.cm.get_cmap(config.viz.palette, len(unique))
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        [f"Cluster {l}" if l != -1 else "Noise" for l in unique],
        counts, color=[palette(i) for i in range(len(unique))], edgecolor="white"
    )
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(count), ha="center", va="bottom", fontsize=10)
    ax.set_title(f"{model_name} -- Cluster Size Distribution", fontsize=14, fontweight="bold")
    ax.set_ylabel("Number of Users")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    _save(fig, config.plots_dir / f"{model_name.lower()}_cluster_sizes.png", config)
    plt.show()
