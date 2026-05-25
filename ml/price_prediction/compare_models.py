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
    y_pred = np.maximum(np.asarray(y_pred, dtype=float), 0.0)
    y_true_values = np.asarray(y_true, dtype=float)
    mse = float(mean_squared_error(y_true_values, y_pred))
    non_zero = y_true_values != 0
    if non_zero.any():
        mape = float(np.mean(np.abs((y_true_values[non_zero] - y_pred[non_zero]) / y_true_values[non_zero])) * 100)
    else:
        mape = 0.0
    return {
        "mae": float(mean_absolute_error(y_true_values, y_pred)),
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(y_true_values, y_pred)) if len(y_true_values) > 1 else 0.0,
        "mape": mape,
    }


def train_test_diagnostics(
    train_metrics: dict[str, float],
    test_metrics: dict[str, float],
    config: Config = cfg,
) -> dict[str, Any]:
    """Compare train and test metrics to flag overfitting or weak signal."""
    r2_gap = float(train_metrics.get("r2", 0.0) - test_metrics.get("r2", 0.0))
    rmse_train = float(train_metrics.get("rmse", 0.0))
    rmse_test = float(test_metrics.get("rmse", 0.0))
    rmse_gap_pct = 0.0 if rmse_train <= 0 else float((rmse_test - rmse_train) / rmse_train)
    return {
        "r2_gap": r2_gap,
        "rmse_gap_pct": rmse_gap_pct,
        "overfitting": bool(r2_gap > config.model.max_overfit_r2_gap and rmse_gap_pct > 0.25),
        "underfitting": bool(train_metrics.get("r2", 0.0) <= 0 and test_metrics.get("r2", 0.0) <= 0),
    }


def production_gate(
    model_name: str,
    results: dict[str, dict[str, Any]],
    baseline_name: str,
    config: Config = cfg,
) -> tuple[bool, list[str]]:
    """Return whether a non-baseline model is eligible for publication."""
    reasons: list[str] = []
    if model_name == baseline_name:
        reasons.append("baseline_reference_only")
    model_metrics = results[model_name]["metrics"]
    baseline_metrics = results[baseline_name]["metrics"]
    if model_metrics.get("r2", 0.0) <= config.model.minimum_publish_r2:
        reasons.append("test_r2_not_positive")
    if model_metrics.get("rmse", float("inf")) >= baseline_metrics.get("rmse", float("inf")):
        reasons.append("rmse_does_not_beat_linear_regression")
    if model_metrics.get("mae", float("inf")) > baseline_metrics.get("mae", float("inf")):
        reasons.append("mae_worse_than_linear_regression")
    if results[model_name].get("diagnostics", {}).get("overfitting"):
        reasons.append("overfitting_gap_too_high")
    return len(reasons) == 0, reasons


def select_best_model(results: dict[str, dict[str, Any]], baseline_name: str, config: Config = cfg) -> str | None:
    """
    Select the best publishable non-baseline model from real test metrics.
    """
    publishable = []
    for name in results:
        passed, _reasons = production_gate(name, results, baseline_name=baseline_name, config=config)
        if passed:
            publishable.append(name)
    if not publishable:
        return None
    return min(
        publishable,
        key=lambda name: (
            results[name]["metrics"]["rmse"],
            results[name]["metrics"]["mae"],
            -results[name]["metrics"]["r2"],
        ),
    )


def comparison_frame(results: dict[str, dict[str, Any]], config: Config = cfg) -> pd.DataFrame:
    """Create and persist a model-comparison dataframe."""
    rows = []
    for name, data in results.items():
        row = {
            "result_key": name,
            "profile": data.get("profile", "unknown"),
            "model": data.get("model_name", name),
            "use_log_target": bool(data.get("use_log_target", False)),
            "params": data.get("params", {}),
        }
        row.update({f"test_{key}": value for key, value in data["metrics"].items()})
        row.update({f"train_{key}": value for key, value in data.get("train_metrics", {}).items()})
        row.update(data.get("diagnostics", {}))
        row["publishable"] = bool(data.get("publishable", False))
        row["gate_reasons"] = ", ".join(data.get("gate_reasons", []))
        rows.append(row)

    df = pd.DataFrame(rows).sort_values(["publishable", "test_rmse", "test_mae"], ascending=[False, True, True]).reset_index(drop=True)
    df.to_csv(config.reports_dir / "model_comparison.csv", index=False)
    return df
