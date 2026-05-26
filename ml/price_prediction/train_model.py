import numpy as np
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

from .config import Config, cfg
from .preprocessing import PreprocessingProfile, build_preprocessor


def _with_optional_log_target(pipeline: Pipeline, use_log_target: bool):
    if use_log_target:
        return TransformedTargetRegressor(regressor=pipeline, func=np.log1p, inverse_func=np.expm1)
    return pipeline


def build_random_forest_pipeline(
    config: Config = cfg,
    profile: PreprocessingProfile = "improved",
    params: dict | None = None,
    use_log_target: bool | None = None,
):
    """RandomForest medium model for nonlinear product pricing signals."""
    rf_params = {
        "n_estimators": config.model.n_estimators,
        "max_depth": config.model.max_depth,
        "min_samples_leaf": config.model.min_samples_leaf,
    }
    if params:
        rf_params.update(params)
    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(config, profile=profile, strategy="random_forest")),
            (
                "model",
                RandomForestRegressor(
                    **rf_params,
                    random_state=config.model.random_state,
                    n_jobs=config.n_jobs,
                ),
            ),
        ]
    )
    should_log_target = config.model.medium_use_log_target if use_log_target is None else use_log_target
    return _with_optional_log_target(pipeline, should_log_target)


def build_xgboost_pipeline(
    config: Config = cfg,
    profile: PreprocessingProfile = "improved",
    params: dict | None = None,
    use_log_target: bool | None = None,
):
    """XGBoost strong model using the project-pinned xgboost package."""
    xgb_params = {
        "n_estimators": 220,
        "max_depth": 3,
        "learning_rate": 0.05,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "reg_lambda": 5.0,
    }
    if params:
        xgb_params.update(params)
    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(config, profile=profile, strategy="xgboost")),
            (
                "model",
                XGBRegressor(
                    **xgb_params,
                    objective="reg:squarederror",
                    tree_method="hist",
                    random_state=config.model.random_state,
                    n_jobs=config.n_jobs,
                ),
            ),
        ]
    )
    should_log_target = config.model.strong_use_log_target if use_log_target is None else use_log_target
    return _with_optional_log_target(pipeline, should_log_target)


def build_performant_pipeline(
    config: Config = cfg,
    profile: PreprocessingProfile = "improved",
    use_log_target: bool | None = None,
):
    """Backward-compatible alias for the RandomForest medium model."""
    return build_random_forest_pipeline(config=config, profile=profile, use_log_target=use_log_target)
