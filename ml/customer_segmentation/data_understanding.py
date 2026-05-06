"""
data_understanding.py
---------------------
EDA helpers: statistical profiling, missing value analysis,
distribution summaries and correlation reporting.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from .config import Config, cfg

logger = logging.getLogger(__name__)


# ─── Statistical Profile ──────────────────────────────────────────────────────

def statistical_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extended descriptive statistics including skewness and kurtosis.

    Returns
    -------
    pd.DataFrame indexed by column name.
    """
    numeric = df.select_dtypes(include=[np.number])
    summary = numeric.describe().T
    summary["skewness"] = numeric.skew()
    summary["kurtosis"] = numeric.kurtosis()
    summary["missing"]  = df.isnull().sum()
    summary["missing%"] = (df.isnull().mean() * 100).round(2)
    logger.info("Statistical summary computed for %d features.", len(summary))
    return summary


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Return a sorted DataFrame of missing value counts and percentages."""
    miss = pd.DataFrame({
        "missing_count": df.isnull().sum(),
        "missing_pct":   (df.isnull().mean() * 100).round(2),
    })
    return miss[miss["missing_count"] > 0].sort_values("missing_pct", ascending=False)


def outlier_report(df: pd.DataFrame, cols: list[str], method: str = "iqr") -> pd.DataFrame:
    """
    Detect outliers per column using IQR or Z-score method.

    Parameters
    ----------
    df     : pd.DataFrame
    cols   : list of numeric column names to analyse
    method : 'iqr' | 'zscore'

    Returns
    -------
    pd.DataFrame with outlier count and percentage per column.
    """
    records = []
    for col in cols:
        series = df[col].dropna()
        if method == "iqr":
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            mask = (series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)
        else:  # zscore
            mask = ((series - series.mean()) / series.std()).abs() > 3
        records.append({
            "column":  col,
            "outliers": int(mask.sum()),
            "outlier%": round(mask.mean() * 100, 2),
        })
    return pd.DataFrame(records).sort_values("outlier%", ascending=False)


# ─── Visualisations ───────────────────────────────────────────────────────────




def run_eda(df: pd.DataFrame, feature_cols: list[str], config: Config = cfg) -> dict:
    """Run full EDA pipeline and export reports."""
    logger.info("=== Starting EDA ===")
    
    # 1. Compute components
    stats    = statistical_summary(df)
    missing  = missing_report(df)
    outliers = outlier_report(df, feature_cols, method=config.features.outlier_method)

    # 2. Save statistical summary
    stats_path = config.reports_dir / "eda_statistical_summary.csv"
    stats.to_csv(stats_path)
    logger.info("Statistical summary saved → %s", stats_path)

    return {"stats": stats, "missing": missing, "outliers": outliers}
