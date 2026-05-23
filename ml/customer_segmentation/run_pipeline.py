"""
run_pipeline.py
---------------
Main orchestrator for the Customer Segmentation ML pipeline.
"""

import logging
import sys
import shutil
import pandas as pd
from .config import cfg, ARTIFACTS_DIR
from .data_loader import load_and_prepare
from .preprocessing import preprocess
from .train_kmeans import run_kmeans_pipeline
from .train_dbscan import run_dbscan_pipeline
from .compare_models import compare_models
from .business_interpretation import interpret_and_save
from .persistence import register_segmentation_model, persist_user_segments
from .plots import plot_final_segment_distribution

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("pipeline")

def cleanup_artifacts():
    """Delete model/plot/report artifacts but preserve the raw data snapshot.
    
    The raw CSV (users_raw.csv) is intentionally kept so that:
    1. Re-runs use the same DB snapshot → consistent recency features.
    2. Database is not hammered on every training run.
    Use force_reload=True in load_raw_data() to explicitly refresh.
    """
    logger.info("🧹 Cleaning up old artifacts...")
    for sub_dir in ["plots", "reports", "models"]:  # data excluded intentionally
        target = ARTIFACTS_DIR / sub_dir
        if target.exists():
            for item in target.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception as e:
                    logger.warning(f"Could not delete {item}: {e}")
    logger.info("✨ Cleanup complete.")

def run_segmentation_pipeline():
    logger.info("🚀 STARTING MACHINE LEARNING PIPELINE")
    
    # 0. Force cleanup
    cleanup_artifacts()
    
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
    
    # 7. Persist selected model metadata and user segment assignments
    model_file = "kmeans_model.pkl" if winner_name.lower().startswith("k") else "dbscan_model.pkl"
    register_segmentation_model(
        algorithm=winner_name,
        metrics=winner_data["metrics"],
        artifact_path=str(cfg.models_dir / model_file),
        config=cfg,
    )
    persisted_count = persist_user_segments(df_labelled, cfg)
    logger.info("Persisted %d user segment assignments.", persisted_count)

    # 8. Final Plot
    plot_final_segment_distribution(df_labelled, cfg)
    
    # 9. Print Final Result
    print("\n" + "="*50)
    print("FINAL MACHINE LEARNING PIPELINE RESULT")
    print("="*50)
    
    km = kmeans_results["metrics"]
    print("\nK-Means:")
    print(f"- best_k = {km['n_clusters']}")
    print(f"- silhouette_score = {km['silhouette_score']:.4f}")
    
    db = dbscan_results["metrics"]
    print("\nDBSCAN:")
    print(f"- best_eps = {db['eps']:.2f}")
    print(f"- noise_pct = {db['noise_pct']}%")
    
    print("\nBEST MODEL SELECTED:")
    print(f"- {winner_name}")
    
    print("\nReason:")
    print(reason)
    print("="*50 + "\n")

if __name__ == "__main__":
    run_segmentation_pipeline()
