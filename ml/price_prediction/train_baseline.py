"""
Baseline model for product price prediction.
"""

from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline

from .config import Config, cfg
from .preprocessing import build_preprocessor


def build_baseline_pipeline(config: Config = cfg) -> Pipeline:
    """Median-price baseline used as the minimum acceptable benchmark."""
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(config)),
            ("model", DummyRegressor(strategy="median")),
        ]
    )

