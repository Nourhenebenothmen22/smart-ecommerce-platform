"""
preprocessing.py
----------------
Feature engineering, outlier removal, log-transformation and scaling.
Outputs a clean, scaled numpy array ready for clustering.
"""

import json
import logging
from pathlib import Path
from typing import Any, Tuple

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

def remove_outliers_iqr(
    df: pd.DataFrame,
    cols: list,
    factor: float = 3.0,
    bounds_path: Path | None = None,
) -> pd.DataFrame:
    """
    Cap extreme outliers (Winsorization) instead of dropping them.
    High-value customers (VIPs) are capped to upper bounds rather than deleted.

    Parameters
    ----------
    bounds_path : Path | None
        If provided, computed clip bounds are persisted to this JSON file so
        that the same caps can be applied at inference time.
    """
    df_clean = df.copy()
    bounds: dict = {}
    for col in cols:
        if col not in df_clean.columns:
            continue
        q1, q3 = df_clean[col].quantile(0.25), df_clean[col].quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr):
            continue
        lower_bound = float(q1 - factor * iqr)
        upper_bound = float(q3 + factor * iqr)
        bounds[col] = {"lower": lower_bound, "upper": upper_bound}
        df_clean[col] = df_clean[col].clip(lower=lower_bound, upper=upper_bound)

    if bounds_path is not None:
        bounds_path.parent.mkdir(parents=True, exist_ok=True)
        with open(bounds_path, "w") as f:
            json.dump(bounds, f, indent=2)
        logger.info("Winsorization bounds saved → %s", bounds_path)

    logger.info("IQR outlier handling: Extreme values capped (Winsorized, %d cols).", len(bounds))
    return df_clean


def apply_outlier_bounds(df: pd.DataFrame, bounds_path: Path, cols: list) -> pd.DataFrame:
    """Apply training-time winsorization bounds during inference."""
    df_clean = df.copy()
    if not bounds_path.exists():
        raise FileNotFoundError(f"Winsorization bounds not found: {bounds_path}")

    with open(bounds_path) as f:
        bounds = json.load(f)

    for col in cols:
        if col in df_clean.columns and col in bounds:
            df_clean[col] = df_clean[col].clip(
                lower=bounds[col]["lower"],
                upper=bounds[col]["upper"],
            )

    logger.info("Applied saved winsorization bounds from %s", bounds_path)
    return df_clean

def remove_outliers_zscore(df: pd.DataFrame, cols: list, threshold: float = 3.0) -> pd.DataFrame:
    """Remove rows where any feature Z-score exceeds the threshold."""
    mask = pd.Series([True] * len(df), index=df.index)
    for col in cols:
        if col not in df.columns:
            continue
        z = (df[col] - df[col].mean()) / df[col].std()
        mask &= z.abs() <= threshold
    
    df_clean = df[mask].reset_index(drop=True)
    removed = len(df) - len(df_clean)
    logger.info("Z-score outlier removal: %d rows removed (%.1f%%)", removed, (removed / len(df) * 100) if len(df) > 0 else 0)
    return df_clean

# ─── Transformations ──────────────────────────────────────────────────────────

def log_transform(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Apply log1p to right-skewed columns (handles zeros)."""
    df_out = df.copy()
    for col in cols:
        if col not in df_out.columns:
            continue
        # Only log-transform non-negative columns
        if (df_out[col] >= 0).all():
            df_out[col] = np.log1p(df_out[col].astype(float))
            logger.debug("log1p applied → %s", col)
        else:
            logger.warning("Skipping log1p for '%s': contains negative values.", col)
    return df_out

def impute_missing(df: pd.DataFrame, cols: list, strategy: str = "median") -> pd.DataFrame:
    """Simple imputation for remaining NaNs."""
    df_out = df.copy()
    for col in cols:
        if col in df_out.columns and df_out[col].isnull().any():
            fill_val = df_out[col].median() if strategy == "median" else df_out[col].mean()
            df_out[col] = df_out[col].fillna(fill_val)
            logger.info("Imputed '%s' with %s=%.4f", col, strategy, fill_val)
    return df_out

# ─── Full Pipeline ────────────────────────────────────────────────────────────

def preprocess(df: pd.DataFrame, config: Config = cfg, fit: bool = True) -> Tuple[Any, pd.DataFrame, Any, list]:
    """
    End-to-end preprocessing pipeline.
    """
    fc = config.features
    logger.info("=== Preprocessing Start -- %d rows ===", len(df))

    # 1. Select features
    required_cols = ["user_id"] + fc.feature_cols
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required preprocessing columns: {missing}")
    df_feat = df[[c for c in required_cols if c in df.columns]].copy()

    # 2. Impute
    df_feat = impute_missing(df_feat, fc.feature_cols)

    # 3. Log transform
    df_feat = log_transform(df_feat, fc.log_transform_cols)

    # 4. Outlier removal
    if fc.outlier_method == "iqr":
        bounds_path = config.models_dir / "winsorization_bounds.json"
        if fit:
            df_clean = remove_outliers_iqr(df_feat, fc.feature_cols, bounds_path=bounds_path)
        else:
            df_clean = apply_outlier_bounds(df_feat, bounds_path, fc.feature_cols)
    elif fc.outlier_method == "zscore":
        df_clean = remove_outliers_zscore(df_feat, fc.feature_cols, fc.outlier_threshold)
    else:
        df_clean = df_feat.copy()

    # 5. Scale
    X = df_clean[fc.feature_cols].values.astype(np.float64)
    scaler_cls = _SCALERS.get(fc.scaler, StandardScaler)
    
    if fit:
        scaler = scaler_cls()
        scaler.fit(X)
        joblib.dump(scaler, config.models_dir / "scaler.pkl")
        logger.info("Scaler fitted and saved: %s", scaler_cls.__name__)
    else:
        scaler = joblib.load(config.models_dir / "scaler.pkl")
        logger.info("Scaler loaded.")

    X_scaled = scaler.transform(X)

    # Persist cleaned data
    df_clean.to_csv(config.data_dir / "users_preprocessed.csv", index=False)
    
    return X_scaled, df_clean, scaler, fc.feature_cols
