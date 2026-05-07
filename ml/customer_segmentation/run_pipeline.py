"""
run_pipeline.py
---------------
Main orchestrator for the Customer Segmentation ML pipeline.
"""

import logging
import sys
import pandas as pd
from .config import cfg
from .data_loader import load_and_prepare
from .preprocessing import preprocess
from .train_kmeans import run_kmeans_pipeline
from .train_dbscan import run_dbscan_pipeline
from .compare_models import compare_models
from .business_interpretation import interpret_and_save
from .plots import plot_final_segment_distribution

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("pipeline")

def run_segmentation_pipeline():
    logger.info("🚀 STARTING MACHINE LEARNING PIPELINE")
    
    # 1. Load data
    df_raw = load_and_prepare(cfg)
    
    # 2. Preprocess
    X_scaled, df_clean, scaler, features = preprocess(df_raw, cfg)
    
    # 3. Train K-Means
    kmeans_results = run_kmeans_pipeline(X_scaled, df_clean, cfg)
    
    # 4. Train DBSCAN
    dbscan_results = run_dbscan_pipeline(X_scaled, df_clean, cfg)
    
    # 5. Compare & Select Best Model
    winner_name, winner_data, reason, comp_df = compare_models(kmeans_results, dbscan_results, cfg)
    
    # 6. Business Interpretation
    df_labelled = interpret_and_save(df_raw, df_clean, winner_data["labels"], features, cfg)
    
    # 7. Final Plot
    plot_final_segment_distribution(df_labelled, cfg)
    
    # 8. Print Final Result
    print("\n" + "="*50)
    print("FINAL MACHINE LEARNING PIPELINE RESULT")
    print("="*50)
    
    km = kmeans_results["metrics"]
    print("\nK-Means:")
    print(f"- best_k = {km['n_clusters']}")
    print(f"- silhouette_score = {km['silhouette_score']:.4f}")
    print(f"- davies_bouldin = {km['davies_bouldin']:.4f}")
    print(f"- calinski_harabasz = {km['calinski_harabasz']:.4f}")
    
    db = dbscan_results["metrics"]
    print("\nDBSCAN:")
    print(f"- best_eps = {db['eps']:.2f}")
    print(f"- best_min_samples = {db['min_samples']}")
    print(f"- noise_pct = {db['noise_pct']}%")
    print(f"- silhouette_score = {db['silhouette_score']:.4f}")
    print(f"- davies_bouldin = {db['davies_bouldin']:.4f}")
    print(f"- calinski_harabasz = {db['calinski_harabasz']:.4f}")
    
    print("\nBEST MODEL SELECTED:")
    print(f"- {winner_name}")
    
    print("\nReason:")
    print(reason)
    print("="*50 + "\n")

if __name__ == "__main__":
    run_segmentation_pipeline()
