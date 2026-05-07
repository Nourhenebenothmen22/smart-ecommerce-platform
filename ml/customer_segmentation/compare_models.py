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

def calculate_model_score(metrics: dict, labels: np.ndarray) -> float:
    """
    Score = Silhouette + (Calinski / 1000) - (Davies / 10) - Penalties
    """
    sil = float(metrics.get("silhouette_score", -1.0))
    dbi = float(metrics.get("davies_bouldin", 99.0))
    chi = float(metrics.get("calinski_harabasz", 0.0))
    n_clusters = int(metrics.get("n_clusters", 0))
    
    # Invalid model check
    if n_clusters < 2:
        return -999.0
    
    # Base score
    score = sil + (chi / 1000.0) - (dbi / 10.0)
    
    # Penalty: Tiny clusters (< 5% of data)
    mask = labels != -1
    if mask.any():
        counts = pd.Series(labels[mask]).value_counts(normalize=True)
        if (counts < 0.05).any():
            score -= 0.5
            logger.info("Penalty applied: Tiny clusters found.")
        
    # Penalty: High noise (DBSCAN specific)
    noise_pct = float(metrics.get("noise_pct", 0.0))
    if noise_pct > 30:
        score -= 1.0
        logger.info("Penalty applied: High noise (%.1f%%).", noise_pct)
    elif noise_pct > 15:
        score -= 0.3
        
    return float(score)

def compare_models(kmeans_results: dict, dbscan_results: dict, config: Config = cfg) -> tuple:
    """
    Compare models and select the best one.
    """
    logger.info("=== Comparing Models ===")
    
    results = {
        "KMeans": kmeans_results,
        "DBSCAN": dbscan_results
    }
    
    # Calculate scores
    scores = {}
    for name, res in results.items():
        score = calculate_model_score(res["metrics"], res["labels"])
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
