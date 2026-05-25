"""
run_pipeline.py
---------------
Main orchestrator for the Customer Segmentation ML pipeline.
"""

import logging
import json
import sys
from .config import cfg
from ml.core.artifacts import (
    begin_latest_artifact_run,
    discard_staged_artifact,
    publish_latest_artifact,
    validate_artifact_files,
)
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

def _required_segmentation_artifact_files(model_file: str) -> list[str]:
    return [
        f"model/{model_file}",
        "model/kmeans_model.pkl",
        "model/dbscan_model.pkl",
        "model/scaler.pkl",
        "model/winsorization_bounds.json",
        "model/segment_map.json",
        "metadata/training_metadata.json",
        "reports/model_comparison.csv",
        "data/raw/users_raw.csv",
        "data/processed/users_preprocessed.csv",
        "data/processed/kmeans_labels.csv",
        "data/processed/dbscan_labels.csv",
        "data/processed/best_model_users_labelled.csv",
        "plots/kmeans_elbow.png",
        "plots/kmeans_silhouette.png",
        "plots/dbscan_k_distance.png",
        "plots/kmeans_vs_dbscan_comparison.png",
        "plots/final_best_model_segments.png",
    ]

def run_segmentation_pipeline():
    logger.info("STARTING MACHINE LEARNING PIPELINE")
    artifact_run, local_cfg = begin_latest_artifact_run(cfg)
    try:
        # 1. Load fresh DB data. Training never reuses cached CSVs.
        df_raw = load_and_prepare(local_cfg, force_reload=True)

        # 2. Preprocess
        X_scaled, df_clean, scaler, features = preprocess(df_raw, local_cfg)

        # 3. Train K-Means
        kmeans_results = run_kmeans_pipeline(X_scaled, df_clean, local_cfg)

        # 4. Train DBSCAN
        dbscan_results = run_dbscan_pipeline(X_scaled, df_clean, local_cfg)

        # 5. Compare & Select Best Model
        winner_name, winner_data, reason, comp_df = compare_models(kmeans_results, dbscan_results, local_cfg)
        analysis_winner = winner_name
        if not winner_name.lower().startswith("k"):
            logger.warning(
                "%s won the offline comparison, but production inference only supports KMeans predict(). "
                "Publishing KMeans as the production segmentation model.",
                winner_name,
            )
            winner_name = "KMeans"
            winner_data = kmeans_results
            reason = (
                f"{analysis_winner} had the best offline score, but KMeans was selected for production "
                "because DBSCAN does not support deterministic prediction for unseen users."
            )

        # 6. Business Interpretation
        df_labelled = interpret_and_save(df_raw, df_clean, winner_data["labels"], features, local_cfg)

        # 7. Final Plot
        plot_final_segment_distribution(df_labelled, local_cfg)

        model_file = "kmeans_model.pkl" if winner_name.lower().startswith("k") else "dbscan_model.pkl"
        metadata = {
            "model_name": local_cfg.segmentation_model_name,
            "model_version": local_cfg.segmentation_model_version,
            "winner": winner_name,
            "analysis_winner": analysis_winner,
            "production_model_type": "KMeans",
            "metrics": winner_data["metrics"],
            "features": features,
            "artifact_policy": "latest_valid_only",
            "reason": reason,
        }
        with open(local_cfg.metadata_dir / "training_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        validate_artifact_files(artifact_run.staging_root, _required_segmentation_artifact_files(model_file))
        publish_latest_artifact(cfg, artifact_run)

        # 8. Persist selected model metadata and user segment assignments
        register_segmentation_model(
            algorithm=winner_name,
            metrics=winner_data["metrics"],
            artifact_path=str(cfg.models_dir / model_file),
            config=cfg,
        )
        persisted_count = persist_user_segments(df_labelled, cfg)
        logger.info("Persisted %d user segment assignments.", persisted_count)
    except Exception:
        discard_staged_artifact(cfg, artifact_run)
        raise

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
