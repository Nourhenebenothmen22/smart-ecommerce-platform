"""
Performant regression model for product price prediction.
"""

from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline

from .config import Config, cfg
from .preprocessing import build_preprocessor


def build_performant_pipeline(config: Config = cfg) -> Pipeline:
    """RandomForest handles nonlinear category/stock/rating effects robustly."""
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(config)),
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

