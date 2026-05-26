import numpy as np
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline

from .config import Config, cfg
from .preprocessing import PreprocessingProfile, build_preprocessor


def build_baseline_pipeline(
    config: Config = cfg,
    profile: PreprocessingProfile = "improved",
    use_log_target: bool | None = None,
):
    """Linear regression baseline used as a simple, real reference model."""
    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(config, profile=profile, strategy="linear_regression")),
            ("model", LinearRegression()),
        ]
    )
    should_log_target = config.model.baseline_use_log_target if use_log_target is None else use_log_target
    if should_log_target:
        return TransformedTargetRegressor(regressor=pipeline, func=np.log1p, inverse_func=np.expm1)
    return pipeline
