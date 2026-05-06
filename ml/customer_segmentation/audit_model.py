"""
audit_model.py
--------------
Deep audit of clustering performance, stability, and feature importance.
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import silhouette_samples
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestClassifier
import joblib
from pathlib import Path

# Mock config for direct script run
class AuditConfig:
    ARTIFACTS = Path("ml/artifacts/customer_segmentation")
    DATA      = ARTIFACTS / "data"
    MODELS    = ARTIFACTS / "models"
    REPORTS   = ARTIFACTS / "reports"
    PLOTS     = ARTIFACTS / "plots"

def run_audit():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Audit")
    
    cfg = AuditConfig()
    
    # 1. Load Data
    X_scaled = pd.read_csv(cfg.DATA / "users_preprocessed.csv")
    df_labelled = pd.read_csv(cfg.DATA / "kmeans_users_labelled.csv")
    feature_cols = [c for c in X_scaled.columns if c not in ["user_id", "kmeans_cluster"]]
    
    X = X_scaled[feature_cols].values
    labels = df_labelled["kmeans_cluster"].values
    
    logger.info("Starting Audit on %d users, %d features", len(X), len(feature_cols))

    # 2. Silhouette Analysis (Overfitting check)
    # If some clusters have negative silhouette, they are overlapping (Overfit/Forced)
    sample_silhouette_values = silhouette_samples(X, labels)
    df_labelled["silhouette"] = sample_silhouette_values
    
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="kmeans_cluster", y="silhouette", data=df_labelled)
    plt.axhline(y=0, color='r', linestyle='--')
    plt.title("Silhouette Distribution per Cluster (K-Means)")
    plt.savefig(cfg.PLOTS / "audit_silhouette_dist.png")
    
    neg_sil = (sample_silhouette_values < 0).sum()
    logger.info("Negative Silhouette samples: %d (%.1f%%) -> Lower is better", neg_sil, neg_sil/len(X)*100)

    # 3. Feature Importance (Noise Detection)
    # Use a Random Forest to see which features define the clusters
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X, labels)
    
    importances = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x='importance', y='feature', data=importances)
    plt.title("Feature Importance (How clusters are formed)")
    plt.savefig(cfg.PLOTS / "audit_feature_importance.png")
    
    logger.info("Feature Importances:\n%s", importances.to_string(index=False))

    # 4. Cluster Stability (Size check)
    counts = df_labelled["kmeans_cluster"].value_counts(normalize=True)
    logger.info("Cluster Size Distribution:\n%s", counts.to_string())
    
    if counts.min() < 0.05:
        logger.warning("Tiny cluster detected (%.1f%%) -> Potential Overfitting", counts.min()*100)

    # 5. Conclusion Generation
    with open(cfg.REPORTS / "audit_diagnostic.txt", "w") as f:
        f.write("=== CLUSTERING AUDIT REPORT ===\n\n")
        f.write(f"Negative Silhouette samples: {neg_sil} ({neg_sil/len(X)*100:.1f}%)\n")
        f.write("If >10%, the number of clusters is likely too high (Overfitting).\n\n")
        f.write("Top Important Features:\n")
        f.write(importances.head(3).to_string(index=False))
        f.write("\n\nBottom (Noise) Features:\n")
        f.write(importances.tail(2).to_string(index=False))
        f.write("\n\nRecommendation: If importance is < 0.05, drop the feature.\n")

if __name__ == "__main__":
    run_audit()
