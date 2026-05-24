"""
Baseline model for product price prediction.
"""

from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor
import numpy as np

from .config import Config, cfg
from .preprocessing import PreprocessingProfile, build_preprocessor


def build_baseline_pipeline(
    config: Config = cfg,
    profile: PreprocessingProfile = "improved",
    use_log_target: bool | None = None,
):
    """Median-price baseline used as the minimum acceptable benchmark."""
    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(config, profile=profile)),
            ("model", DummyRegressor(strategy="median")),
        ]
    )
    should_log_target = config.model.baseline_use_log_target if use_log_target is None else use_log_target
    if should_log_target:
        return TransformedTargetRegressor(regressor=pipeline, func=np.log1p, inverse_func=np.expm1)
    return pipeline
