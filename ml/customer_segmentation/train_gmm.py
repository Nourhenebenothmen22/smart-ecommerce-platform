"""
train_gmm.py
------------
Gaussian Mixture Model training: BIC/AIC selection, model persistence.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

from .config import Config, cfg
from .visualization import plot_bic_aic, plot_silhouette_scores, plot_clusters_pca, \
    plot_silhouette_diagram, plot_cluster_sizes

logger = logging.getLogger(__name__)


# ─── Model Selection ─────────────────────────────────────────────────────────

def bic_aic_analysis(X: np.ndarray, config: Config = cfg) -> dict:
    """Compute BIC and AIC for each n_components in the configured range."""
    gc = config.gmm
    results = {"n": [], "bic": [], "aic": [], "silhouette": []}

    for n in gc.n_components_range:
        gmm = GaussianMixture(
            n_components=n,
            covariance_type=gc.covariance_type,
            n_init=gc.n_init,
            max_iter=gc.max_iter,
            random_state=config.random_state,
        )
        gmm.fit(X)
        labels = gmm.predict(X)
        sil = silhouette_score(X, labels) if n > 1 else 0.0

        results["n"].append(n)
        results["bic"].append(gmm.bic(X))
        results["aic"].append(gmm.aic(X))
        results["silhouette"].append(sil)
        logger.info("n=%d | BIC=%.2f | AIC=%.2f | sil=%.4f",
                    n, gmm.bic(X), gmm.aic(X), sil)

    plot_bic_aic(results["n"], results["bic"], results["aic"], config)
    plot_silhouette_scores(results["n"], results["silhouette"], config, model_name="GMM")
    return results


# ─── Training ────────────────────────────────────────────────────────────────

def train_gmm(X: np.ndarray, config: Config = cfg) -> GaussianMixture:
    gc = config.gmm
    logger.info("Training GMM with n_components=%d covariance_type=%s …",
                gc.n_components, gc.covariance_type)
    gmm = GaussianMixture(
        n_components=gc.n_components,
        covariance_type=gc.covariance_type,
        n_init=gc.n_init,
        max_iter=gc.max_iter,
        random_state=config.random_state,
    )
    gmm.fit(X)
    logger.info("GMM trained | converged=%s | BIC=%.2f", gmm.converged_, gmm.bic(X))
    return gmm


# ─── Evaluation ──────────────────────────────────────────────────────────────

def evaluate_gmm(X: np.ndarray, model: GaussianMixture) -> dict:
    labels = model.predict(X)
    metrics = {
        "bic":               round(model.bic(X), 4),
        "aic":               round(model.aic(X), 4),
        "log_likelihood":    round(model.score(X), 6),
        "silhouette_score":  round(silhouette_score(X, labels), 4),
        "davies_bouldin":    round(davies_bouldin_score(X, labels), 4),
        "calinski_harabasz": round(calinski_harabasz_score(X, labels), 4),
        "n_components":      model.n_components,
        "converged":         model.converged_,
    }
    for k, v in metrics.items():
        logger.info("  %-25s %s", k, v)
    return metrics


# ─── Persistence ─────────────────────────────────────────────────────────────

def save_gmm(model: GaussianMixture, config: Config = cfg) -> Path:
    path = config.models_dir / "gmm_model.pkl"
    joblib.dump(model, path)
    logger.info("GMM model saved → %s", path)
    return path


def load_gmm(config: Config = cfg) -> GaussianMixture:
    path = config.models_dir / "gmm_model.pkl"
    model = joblib.load(path)
    logger.info("GMM model loaded ← %s", path)
    return model


# ─── Full Run ─────────────────────────────────────────────────────────────────

def run_gmm(X: np.ndarray, df_clean, feature_cols: list, config: Config = cfg) -> dict:
    """End-to-end GMM pipeline."""
    logger.info("=== GMM Pipeline ===")
    selection = bic_aic_analysis(X, config)

    model = train_gmm(X, config)
    labels = model.predict(X)
    proba = model.predict_proba(X)
    metrics = evaluate_gmm(X, model)

    plot_clusters_pca(X, labels, config, model_name="GMM")
    plot_silhouette_diagram(X, labels, config, model_name="GMM")
    plot_cluster_sizes(labels, config, model_name="GMM")

    save_gmm(model, config)

    df_out = df_clean[["user_id"]].copy()
    df_out["gmm_cluster"] = labels
    max_proba_cols = [f"proba_cluster_{i}" for i in range(proba.shape[1])]
    df_proba = pd.DataFrame(proba, columns=max_proba_cols)
    df_out = pd.concat([df_out.reset_index(drop=True), df_proba], axis=1)
    out_path = config.data_dir / "gmm_labels.csv"
    df_out.to_csv(out_path, index=False)
    logger.info("GMM labels saved → %s", out_path)

    return {"model": model, "labels": labels, "proba": proba, "metrics": metrics, "selection": selection}
