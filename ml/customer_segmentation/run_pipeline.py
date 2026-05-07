"""
run_pipeline.py
---------------
Orchestration entry-point for the Customer Segmentation pipeline.

Usage
-----
    python -m ml.customer_segmentation.run_pipeline
    python -m ml.customer_segmentation.run_pipeline --models kmeans gmm
    python -m ml.customer_segmentation.run_pipeline --force-reload
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from .config import Config, cfg
from .data_loader import load_and_prepare
from .data_understanding import run_eda
from .preprocessing import preprocess
from .train_kmeans import run_kmeans
from .train_dbscan import run_dbscan
from .business_interpretation import interpret
from .compare_models import run_comparison
from .plots import (
    plot_data_distributions,
    plot_correlation_matrix,
    plot_model_comparison,
    plot_final_segment_distribution
)

# ─── Logging Setup ────────────────────────────────────────────────────────────
# Force UTF-8 on stdout to avoid cp1252 errors on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
_file_handler = logging.FileHandler(cfg.reports_dir / "pipeline.log", mode="a", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
logging.basicConfig(level=logging.INFO, handlers=[_stream_handler, _file_handler])
logger = logging.getLogger(__name__)


# ─── Pipeline Steps ───────────────────────────────────────────────────────────

def step_load(config: Config, force_reload: bool) -> "pd.DataFrame":
    logger.info("--- STEP 1/6 -- Data Loading ---")
    df = load_and_prepare(config=config, force_reload=force_reload)
    logger.info("Loaded %d users.", len(df))
    return df


def step_eda(df, config: Config) -> dict:
    logger.info("--- STEP 2/6 -- Exploratory Data Analysis ---")
    plot_data_distributions(df, config)
    plot_correlation_matrix(df, config)
    return run_eda(df, config.features.feature_cols, config)


def step_preprocess(df, config: Config):
    logger.info("--- STEP 3/6 -- Preprocessing ---")
    return preprocess(df, config=config, fit=True)


def step_train(X, df_clean, feature_cols, models: list[str], config: Config) -> dict:
    logger.info("--- STEP 4/6 -- Model Training ---")
    results = {}
    if "kmeans" in models:
        results["KMeans"] = run_kmeans(X, df_clean, feature_cols, config)
        results["KMeans"]["X"] = X
    if "dbscan" in models:
        results["DBSCAN"] = run_dbscan(X, df_clean, feature_cols, config)
        results["DBSCAN"]["X"] = X
    return results





def step_compare(results: dict, config: Config) -> tuple[str, str]:
    logger.info("--- STEP 6/6 -- Model Comparison ---")
    plot_model_comparison(results, config)
    if len(results) > 1:
        return run_comparison(results, config)
    else:
        winner = list(results.keys())[0]
        return winner, f"Selected {winner} as it was the only model trained."


# ─── Main Orchestrator ────────────────────────────────────────────────────────

def run(models: list[str] | None = None, force_reload: bool = False,
        eda: bool = False, config: Config = cfg) -> dict:
    """
    Run the full segmentation pipeline.

    Parameters
    ----------
    models       : list of model names to train, e.g. ['kmeans', 'dbscan']
    force_reload : if True, re-query DB instead of using cached CSV
    eda          : if True, generate EDA plots
    config       : Config instance

    Returns
    -------
    dict with pipeline results
    """
    if models is None:
        models = ["kmeans", "dbscan"]

    start = time.time()
    logger.info("=" * 54)
    logger.info("  Customer Segmentation Pipeline -- START")
    logger.info("  Models: %s", ", ".join(models))
    logger.info("=" * 54)

    try:
        # 1. Load & Prepare
        df                               = step_load(config, force_reload)
        
        # 2. EDA (Separate plots handled in step_eda)
        if eda:
            _                            = step_eda(df, config)
        
        # 3. Preprocess
        X, df_clean, scaler, feature_cols = step_preprocess(df, config)
        
        # 4. Train
        results                          = step_train(X, df_clean, feature_cols, models, config)
        
        # 5. Compare & Select Best Model (Audit integrated here)
        winner_name, winner_reason       = step_compare(results, config)
        
        # 6. Profile & Interpret ONLY the best model
        logger.info("━━━ FINAL STEP -- Interpreting Winner: %s ━━━", winner_name)
        res = results[winner_name]
        
        # Business interpretation on RAW data
        df_labelled = interpret(
            df_raw=df,
            df_clean=df_clean,
            labels=res["labels"],
            cluster_col=f"{winner_name.lower()}_cluster",
            feature_cols=feature_cols,
            profile=None, # profile will be re-calculated inside interpret if needed
            config=config,
            model_name=winner_name
        )
        
        # 7. Final Business Visualization
        plot_final_segment_distribution(df_labelled, config)
        
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        raise

    elapsed = time.time() - start
    logger.info("=" * 54)
    logger.info("  FINAL MODEL SELECTED: %s", winner_name)
    logger.info("  Reason: %s", winner_reason)
    logger.info("  Pipeline COMPLETE in %.1fs", elapsed)
    logger.info("  Reports & Plots -> %s", config.reports_dir)
    logger.info("=" * 54)
    
    return {
        "results": results,
        "winner": winner_name,
        "winner_reason": winner_reason,
        "labelled_data": df_labelled,
        "output_paths": {
            "reports_dir": str(config.reports_dir),
            "plots_dir": str(config.plots_dir),
            "models_dir": str(config.models_dir)
        }
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _parse_args():
    parser = argparse.ArgumentParser(description="Customer Segmentation Pipeline")
    parser.add_argument(
        "--models", nargs="+", default=["kmeans", "dbscan"],
        choices=["kmeans", "dbscan"],
        help="Which models to train (default: all).",
    )
    parser.add_argument(
        "--force-reload", action="store_true",
        help="Re-query the database instead of loading from cache.",
    )
    parser.add_argument(
        "--eda", action="store_true",
        help="Generate EDA plots.",
    )
    parser.add_argument(
        "--k", type=int, default=None,
        help="Override n_clusters for K-Means.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    # Apply CLI overrides to config
    if args.k:
        cfg.kmeans.n_clusters = args.k

    run(models=args.models, force_reload=args.force_reload, eda=args.eda, config=cfg)
