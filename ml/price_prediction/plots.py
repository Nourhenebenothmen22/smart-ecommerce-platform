"""
Descriptive plots for price prediction.
"""

import logging
from pathlib import Path
from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure

from .config import Config, cfg

logger = logging.getLogger(__name__)


def _save(fig: Figure, path: Path, config: Config) -> None:
    fig.savefig(path, dpi=config.viz.dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Plot saved -> %s", path)


def plot_price_distribution(df: pd.DataFrame, config: Config = cfg) -> None:
    """Plot the distribution of product prices."""
    fig, ax = plt.subplots(figsize=config.viz.figsize_default)
    sns.histplot(df[config.features.target_col].astype(float), kde=True, ax=cast(Any, ax), color="#2f80ed")
    ax.set_title("Product Price Distribution", fontsize=14, fontweight="bold")
    ax.set_xlabel("Price")
    ax.set_ylabel("Products")
    ax.grid(axis="y", alpha=0.25)
    _save(fig, config.plots_dir / "price_distribution.png", config)


def plot_feature_correlation(df: pd.DataFrame, config: Config = cfg) -> None:
    """Plot numeric feature correlation including target price."""
    columns = config.features.numeric_features + [config.features.target_col]
    corr = df[columns].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(12, 9))
    sns.heatmap(corr, annot=False, cmap="coolwarm", center=0, ax=cast(Any, ax))
    ax.set_title("Price Feature Correlation", fontsize=14, fontweight="bold")
    _save(fig, config.plots_dir / "feature_correlation.png", config)


def plot_actual_vs_predicted(y_true: pd.Series, y_pred, model_name: str, config: Config = cfg) -> None:
    """Plot actual prices against model predictions."""
    fig, ax = plt.subplots(figsize=config.viz.figsize_default)
    sns.scatterplot(x=y_true.astype(float), y=y_pred, ax=cast(Any, ax), color="#27ae60", edgecolor="white")
    min_value = min(float(y_true.min()), float(min(y_pred)))
    max_value = max(float(y_true.max()), float(max(y_pred)))
    ax.plot([min_value, max_value], [min_value, max_value], linestyle="--", color="#e74c3c", linewidth=2)
    ax.set_title(f"Actual vs Predicted Price - {model_name}", fontsize=14, fontweight="bold")
    ax.set_xlabel("Actual price")
    ax.set_ylabel("Predicted price")
    ax.grid(alpha=0.25)
    _save(fig, config.plots_dir / "actual_vs_predicted_price.png", config)


def plot_model_performance(metrics_by_model: dict[str, dict[str, float]], config: Config = cfg) -> None:
    """Plot MAE, RMSE, MSE, and R2 for the compared models."""
    rows = []
    for model_name, metrics in metrics_by_model.items():
        for metric, value in metrics.items():
            rows.append({"Model": model_name, "Metric": metric.upper(), "Value": value})

    df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=config.viz.figsize_default)
    sns.barplot(data=df, x="Metric", y="Value", hue="Model", ax=cast(Any, ax), palette="Set2")
    ax.set_title("Price Prediction Model Performance", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    _save(fig, config.plots_dir / "model_performance_comparison.png", config)

