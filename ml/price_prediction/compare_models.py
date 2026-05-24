"""
Evaluation and model comparison helpers for price prediction.
"""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .config import Config, cfg


def evaluate_regression(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    """Return standard price-regression metrics."""
    mse = float(mean_squared_error(y_true, y_pred))
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(y_true, y_pred)) if len(y_true) > 1 else 0.0,
    }


def select_best_model(results: dict[str, dict[str, Any]]) -> str:
    """
    Select the best model using RMSE first, then MAE as a tie-breaker.
    """
    return min(
        results.keys(),
        key=lambda name: (
            results[name]["metrics"]["rmse"],
            results[name]["metrics"]["mae"],
        ),
    )


def comparison_frame(results: dict[str, dict[str, Any]], config: Config = cfg) -> pd.DataFrame:
    """Create and persist a model-comparison dataframe."""
    rows = []
    for name, data in results.items():
        row = {"model": name}
        row.update(data["metrics"])
        rows.append(row)

    df = pd.DataFrame(rows).sort_values(["rmse", "mae"]).reset_index(drop=True)
    df.to_csv(config.reports_dir / "model_comparison.csv", index=False)
    return df

