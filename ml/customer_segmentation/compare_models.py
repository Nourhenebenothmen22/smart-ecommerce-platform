"""
compare_models.py
-----------------
Cross-model benchmarking: compare KMeans and DBSCAN using a composite scoring rule.
"""

import logging
import numpy as np
import pandas as pd
from .config import Config, cfg
from .plots import plot_model_comparison

logger = logging.getLogger(__name__)

def calculate_model_score(metrics: dict, labels: np.ndarray, all_chi: list | None = None) -> float:
    """
    Composite clustering quality score.

    Score = silhouette + 0.3 * (chi / max_chi) - (davies / 10) - penalties

    CH is normalised across all competing models so that a model with a
    naturally higher CH (e.g. KMeans at k=2) is not unfairly rewarded over
    a model whose CH is lower due to a different cluster geometry.
    """
    sil = metrics.get("silhouette_score", -1.0)
    dbi = metrics.get("davies_bouldin", 99.0)
    chi = metrics.get("calinski_harabasz", 0.0)
    n_clusters = metrics.get("n_clusters", 0)

    if n_clusters < 2 or n_clusters > 5:
        return -999.0

    # Normalise CH so it contributes proportionally regardless of scale
    max_chi = max(all_chi) if all_chi else (chi if chi > 0 else 1.0)
    chi_norm = (chi / max_chi) * 0.3 if max_chi > 0 else 0.0

    score = sil + chi_norm - (dbi / 10.0)

    # Penalty: tiny clusters (< 5% of ALL users, not just non-noise)
    n_total = len(labels)
    mask = labels != -1
    if mask.any():
        counts = pd.Series(labels[mask]).value_counts(normalize=False)
        min_cluster_size = int(0.05 * n_total)  # keep dtype as int to satisfy Series[int].__lt__
        if (counts < min_cluster_size).any():
            score -= 0.5
            logger.info("Penalty applied: Tiny clusters found (< 5%% of all users).")

    # Penalty: High noise rate (DBSCAN specific)
    noise_pct = float(metrics.get("noise_pct", 0.0))
    if noise_pct > 30:
        score -= 1.0
        logger.info("Penalty applied: High noise (%.1f%%).", noise_pct)
    elif noise_pct > 15:
        score -= 0.3
        logger.info("Penalty applied: Elevated noise (%.1f%%).", noise_pct)

    return score

def compare_models(kmeans_results: dict, dbscan_results: dict, config: Config = cfg) -> tuple:
    """
    Compare models and select the best one.
    """
    logger.info("=== Comparing Models ===")

    results = {
        "KMeans": kmeans_results,
        "DBSCAN": dbscan_results
    }

    # Collect all CH values for normalisation
    all_chi = [
        res["metrics"].get("calinski_harabasz", 0.0)
        for res in results.values()
        if res["metrics"].get("calinski_harabasz") is not None
    ]

    # Calculate scores
    scores = {}
    for name, res in results.items():
        score = calculate_model_score(res["metrics"], res["labels"], all_chi=all_chi)
        scores[name] = score
        logger.info("%s Final Score: %.4f", name, score)
    
    # Select best model using explicit keys to avoid IDE confusion
    model_names = list(scores.keys())
    best_model_name = max(model_names, key=lambda k: scores[k])
    best_model_data = results[best_model_name]
    
    # Comparison table
    comp_data = []
    for name, res in results.items():
        m = res["metrics"].copy()
        m["model"] = name
        m["final_score"] = scores[name]
        comp_data.append(m)
    
    df_comp = pd.DataFrame(comp_data).set_index("model")
    df_comp.to_csv(config.reports_dir / "model_comparison.csv")
    
    # Plot comparison
    plot_model_comparison(results, config)
    
    # Reason
    winner_score = scores[best_model_name]
    reason = f"The {best_model_name} model was selected because it achieved a higher composite score ({winner_score:.3f}) "
    reason += "based on silhouette stability, cluster separation, and reasonable segment sizes."
    
    logger.info("🏆 Best Model: %s", best_model_name)
    
    return best_model_name, best_model_data, reason, df_comp
