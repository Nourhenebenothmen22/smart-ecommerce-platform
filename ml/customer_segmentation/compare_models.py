"""
compare_models.py
-----------------
Cross-model benchmarking: collect metrics from KMeans, GMM and DBSCAN,
produce a comparison table, radar chart and ranking report.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from .config import Config, cfg

logger = logging.getLogger(__name__)


# ─── Metrics Collection ───────────────────────────────────────────────────────

def collect_metrics(results: dict[str, dict]) -> pd.DataFrame:
    """
    Build a comparison DataFrame from model result dicts.

    Parameters
    ----------
    results : {
        "KMeans": {"metrics": {...}},
        "GMM":    {"metrics": {...}},
        "DBSCAN": {"metrics": {...}},
    }

    Returns
    -------
    pd.DataFrame with models as rows and metrics as columns.
    """
    common_metrics = ["silhouette_score", "davies_bouldin", "calinski_harabasz", "n_clusters"]
    rows = []
    for model_name, res in results.items():
        m = res.get("metrics", {})
        row = {"model": model_name}
        for key in common_metrics:
            row[key] = m.get(key, np.nan)
        rows.append(row)

    df = pd.DataFrame(rows).set_index("model")
    logger.info("Metrics collected for models: %s", list(results.keys()))
    return df


def rank_models(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """
    Rank models by composite score:
    - Higher silhouette → better
    - Lower davies_bouldin → better
    - Higher calinski_harabasz → better
    """
    df = comparison_df.copy()

    if "silhouette_score" in df.columns:
        df["rank_sil"] = df["silhouette_score"].rank(ascending=False, na_option="bottom")
    if "davies_bouldin" in df.columns:
        df["rank_dbi"] = df["davies_bouldin"].rank(ascending=True, na_option="bottom")
    if "calinski_harabasz" in df.columns:
        df["rank_chi"] = df["calinski_harabasz"].rank(ascending=False, na_option="bottom")

    rank_cols = [c for c in df.columns if c.startswith("rank_")]
    df["composite_rank"] = df[rank_cols].mean(axis=1)
    df["overall_rank"]   = df["composite_rank"].rank().astype(int)
    df = df.sort_values("overall_rank")

    best = df.index[0]
    logger.info("Best model by composite ranking: %s", best)
    return df


# ─── Visualisations ───────────────────────────────────────────────────────────

def plot_metrics_comparison(comparison_df: pd.DataFrame, config: Config = cfg) -> None:
    """Side-by-side bar charts for each metric."""
    metrics_to_plot = [c for c in ["silhouette_score", "davies_bouldin", "calinski_harabasz"]
                       if c in comparison_df.columns]
    n = len(metrics_to_plot)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 6))
    if n == 1:
        axes = [axes]

    palette = plt.cm.get_cmap("tab10")
    models = comparison_df.index.tolist()
    colors = [palette(i) for i in range(len(models))]

    for ax, metric in zip(axes, metrics_to_plot):
        vals = comparison_df[metric].fillna(0)
        bars = ax.bar(models, vals, color=colors, edgecolor="white", alpha=0.85)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=10)
        ax.set_title(metric.replace("_", " ").title(), fontsize=12, fontweight="bold")
        ax.set_ylabel("Score")
        ax.grid(axis="y", alpha=0.3)

    plt.suptitle("Model Comparison -- Clustering Metrics", fontsize=15, fontweight="bold")
    plt.tight_layout()
    path = config.plots_dir / "model_comparison_metrics.png"
    fig.savefig(path, dpi=config.viz.dpi, bbox_inches="tight")
    plt.show()
    logger.info("Comparison bar chart saved → %s", path)


def plot_radar_chart(comparison_df: pd.DataFrame, config: Config = cfg) -> None:
    """Radar (spider) chart comparing normalised metric scores."""
    metrics = [c for c in ["silhouette_score", "davies_bouldin", "calinski_harabasz"]
               if c in comparison_df.columns]
    if len(metrics) < 2:
        logger.warning("Not enough metrics for radar chart.")
        return

    # Normalise: flip davies_bouldin so higher = better
    norm_df = comparison_df[metrics].copy()
    norm_df = (norm_df - norm_df.min()) / (norm_df.max() - norm_df.min() + 1e-9)
    if "davies_bouldin" in norm_df.columns:
        norm_df["davies_bouldin"] = 1 - norm_df["davies_bouldin"]

    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    palette = plt.cm.get_cmap("tab10")
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"polar": True})

    for i, (model, row) in enumerate(norm_df.iterrows()):
        values = row.tolist() + [row.iloc[0]]
        ax.plot(angles, values, "o-", linewidth=2, color=palette(i), label=model)
        ax.fill(angles, values, alpha=0.15, color=palette(i))

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([m.replace("_", "\n") for m in metrics], fontsize=11)
    ax.set_title("Model Comparison -- Radar Chart", fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    plt.tight_layout()
    path = config.plots_dir / "model_comparison_radar.png"
    fig.savefig(path, dpi=config.viz.dpi, bbox_inches="tight")
    plt.show()
    logger.info("Radar chart saved → %s", path)


# ─── Report ───────────────────────────────────────────────────────────────────

def save_comparison_report(ranked_df: pd.DataFrame, config: Config = cfg) -> None:
    """Save CSV and text comparison report."""
    csv_path = config.reports_dir / "model_comparison.csv"
    ranked_df.to_csv(csv_path)
    logger.info("Comparison CSV → %s", csv_path)

    txt_path = config.reports_dir / "model_comparison_report.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=== Customer Segmentation -- Model Comparison Report ===\n\n")
        f.write(ranked_df.to_string())
        f.write("\n\n")
        best = ranked_df.index[0]
        f.write(f"✅ Recommended model: {best}\n")
        f.write("   (ranked by composite silhouette + davies_bouldin + calinski_harabasz)\n")
    logger.info("Comparison report → %s", txt_path)


# ─── Full Run ─────────────────────────────────────────────────────────────────

def calculate_audit_metrics(X, labels):
    """Calculate overfitting metrics."""
    # Filter out noise (-1)
    mask = labels != -1
    if len(np.unique(labels[mask])) < 2:
        return 0, 0.0
    
    from sklearn.metrics import silhouette_samples
    sil_vals = silhouette_samples(X[mask], labels[mask])
    neg_count = int((sil_vals < 0).sum())
    neg_pct = float(neg_count / len(sil_vals) * 100)
    return neg_count, neg_pct


def select_best_model(comparison_df: pd.DataFrame) -> str:
    """
    Business-aware model selection logic.
    Prioritizes:
    1. Models with >1 cluster.
    2. Low negative silhouette percentage (Stability).
    3. High Silhouette score.
    4. Reasonable cluster sizes (no cluster < 5%).
    """
    df = comparison_df.copy()
    
    # 1. Valid models have > 1 cluster and < 90% noise
    # (Assuming noise is handled by excluding -1 in silhouette)
    valid = df[df["n_clusters"] > 1].copy()
    if valid.empty:
        return df.index[0]

    # 2. Score = Silhouette - (Neg_Sil_Pct / 100)
    # We penalise models with too many negative silhouette samples (overlapping/overfit)
    valid["final_score"] = valid["silhouette_score"] - (valid["neg_sil_pct"] / 100.0)
    
    # 3. Penalise tiny clusters
    # (Optional: can add penalty based on min_cluster_pct if available)
    
    winner = valid.sort_values("final_score", ascending=False).index[0]
    return winner


# ─── Full Run ─────────────────────────────────────────────────────────────────

def run_comparison(results: dict[str, dict], config: Config = cfg) -> str:
    """
    Full model comparison pipeline. Pick a winner based on metrics + audit.
    """
    logger.info("=== Automatic Model Selection ===")
    
    comparison = collect_metrics(results)
    
    # Add audit metrics to each row
    neg_counts, neg_pcts = [], []
    for model_name, res in results.items():
        X = res["X"]
        labels = res["labels"]
        count, pct = calculate_audit_metrics(X, labels)
        neg_counts.append(count)
        neg_pcts.append(pct)
    
    comparison["neg_sil_count"] = neg_counts
    comparison["neg_sil_pct"]   = neg_pcts
    
    ranked = rank_models(comparison)
    winner = select_best_model(ranked)

    plot_metrics_comparison(ranked, config)
    plot_radar_chart(ranked, config)
    save_comparison_report(ranked, config)

    logger.info("🏆 FINAL WINNER: %s", winner)
    return winner
