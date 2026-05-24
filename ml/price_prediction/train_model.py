"""
Performant regression model for product price prediction.
"""

from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor
import numpy as np

from .config import Config, cfg
from .preprocessing import PreprocessingProfile, build_preprocessor


def build_performant_pipeline(
    config: Config = cfg,
    profile: PreprocessingProfile = "improved",
    use_log_target: bool | None = None,
):
    """RandomForest handles nonlinear category/stock/rating effects robustly."""
    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(config, profile=profile)),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=config.model.n_estimators,
                    max_depth=config.model.max_depth,
                    min_samples_leaf=config.model.min_samples_leaf,
                    random_state=config.model.random_state,
                    n_jobs=config.n_jobs,
                ),
            ),
        ]
    )
    should_log_target = config.model.performant_use_log_target if use_log_target is None else use_log_target
    if should_log_target:
        return TransformedTargetRegressor(regressor=pipeline, func=np.log1p, inverse_func=np.expm1)
    return pipeline
