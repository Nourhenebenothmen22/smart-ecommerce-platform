"""
preprocessing.py
----------------
Feature engineering, outlier removal, log-transformation and scaling.
Outputs a clean, scaled numpy array ready for clustering.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

from .config import Config, cfg

logger = logging.getLogger(__name__)

_SCALERS = {
    "standard": StandardScaler,
    "minmax":   MinMaxScaler,
    "robust":   RobustScaler,
}


# ─── Outlier Removal ─────────────────────────────────────────────────────────

def remove_outliers_iqr(df: pd.DataFrame, cols: list[str], factor: float = 1.5) -> pd.DataFrame:
    """Remove rows where any feature is beyond IQR * factor."""
    mask = pd.Series([True] * len(df), index=df.index)
    for col in cols:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        mask &= df[col].between(q1 - factor * iqr, q3 + factor * iqr)
    removed = (~mask).sum()
    logger.info("IQR outlier removal: %d rows removed (%.1f%%)", removed, removed / len(df) * 100)
    return df[mask].reset_index(drop=True)


def remove_outliers_zscore(df: pd.DataFrame, cols: list[str], threshold: float = 3.0) -> pd.DataFrame:
    """Remove rows where any feature Z-score exceeds the threshold."""
    mask = pd.Series([True] * len(df), index=df.index)
    for col in cols:
        z = (df[col] - df[col].mean()) / df[col].std()
        mask &= z.abs() <= threshold
    removed = (~mask).sum()
    logger.info("Z-score outlier removal: %d rows removed (%.1f%%)", removed, removed / len(df) * 100)
    return df[mask].reset_index(drop=True)


# ─── Transformations ──────────────────────────────────────────────────────────

def log_transform(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Apply log1p to right-skewed columns (handles zeros)."""
    df = df.copy()
    for col in cols:
        df[col] = np.log1p(df[col])
        logger.debug("log1p applied → %s", col)
    return df


def impute_missing(df: pd.DataFrame, cols: list[str], strategy: str = "median") -> pd.DataFrame:
    """Simple imputation for remaining NaNs."""
    df = df.copy()
    for col in cols:
        if df[col].isnull().any():
            fill_val = df[col].median() if strategy == "median" else df[col].mean()
            df[col] = df[col].fillna(fill_val)
            logger.info("Imputed '%s' with %s=%.4f", col, strategy, fill_val)
    return df


# ─── Scaling ──────────────────────────────────────────────────────────────────

def fit_scaler(X: np.ndarray, scaler_type: str = "standard"):
    """Fit and return a scaler."""
    scaler_cls = _SCALERS.get(scaler_type, StandardScaler)
    scaler = scaler_cls()
    scaler.fit(X)
    logger.info("Scaler fitted: %s", scaler_cls.__name__)
    return scaler


def scale_features(X: np.ndarray, scaler) -> np.ndarray:
    return scaler.transform(X)


def save_scaler(scaler, config: Config = cfg) -> Path:
    path = config.models_dir / "scaler.pkl"
    joblib.dump(scaler, path)
    logger.info("Scaler saved → %s", path)
    return path


def load_scaler(config: Config = cfg):
    path = config.models_dir / "scaler.pkl"
    scaler = joblib.load(path)
    logger.info("Scaler loaded ← %s", path)
    return scaler


# ─── Full Pipeline ────────────────────────────────────────────────────────────

def preprocess(df: pd.DataFrame, config: Config = cfg, fit: bool = True):
    """
    End-to-end preprocessing pipeline.

    Steps
    -----
    1. Select feature columns
    2. Impute missing values
    3. Log-transform skewed features (Better for outlier detection on skewed data)
    4. Remove outliers (IQR or Z-score)
    5. Scale features
    """
    fc = config.features
    logger.info("=== Preprocessing Start -- %d rows, %d features ===", len(df), len(fc.feature_cols))

    # 1. Select features
    df_feat = df[["user_id"] + fc.feature_cols].copy()

    # 2. Impute
    df_feat = impute_missing(df_feat, fc.feature_cols)

    # 3. Log transform (Move BEFORE outlier removal)
    df_feat = log_transform(df_feat, fc.log_transform_cols)

    # 4. Outlier removal
    if fc.outlier_method == "iqr":
        df_clean = remove_outliers_iqr(df_feat, fc.feature_cols)
    elif fc.outlier_method == "zscore":
        df_clean = remove_outliers_zscore(df_feat, fc.feature_cols, fc.outlier_threshold)
    else:
        df_clean = df_feat.copy()

    # 5. Scale
    X = df_clean[fc.feature_cols].values
    if fit:
        scaler = fit_scaler(X, fc.scaler)
        save_scaler(scaler, config)
    else:
        scaler = load_scaler(config)

    X_scaled = scale_features(X, scaler)

    # Persist cleaned data
    clean_path = config.data_dir / "users_preprocessed.csv"
    df_clean.to_csv(clean_path, index=False)
    logger.info("Preprocessed data saved → %s  |  shape: %s", clean_path, X_scaled.shape)

    return X_scaled, df_clean, scaler, fc.feature_cols
