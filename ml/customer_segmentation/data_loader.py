"""
Load backend-compatible customer segmentation features from PostgreSQL.
"""

import logging
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from .config import Config, cfg

logger = logging.getLogger(__name__)

_USER_SEGMENTATION_QUERY = """
    SELECT
        user_id,
        total_orders,
        total_spent,
        avg_order_value,
        total_items_bought,
        views_count,
        clicks_count,
        cart_add_count,
        wishlist_add_count,
        purchase_interaction_count,
        search_count,
        share_count,
        reviews_count,
        avg_rating_given,
        wishlist_count,
        cart_count,
        COALESCE(days_since_last_order, 999) AS days_since_last_order,
        COALESCE(days_since_last_interaction, 999) AS days_since_last_interaction,
        COALESCE(days_since_signup, 999) AS days_since_signup,
        purchase_to_view_ratio,
        cart_to_click_ratio,
        review_to_purchase_ratio,
        computed_at
    FROM user_features
    ORDER BY total_spent DESC;
"""


def get_engine(config: Config = cfg):
    """Create and return a SQLAlchemy engine from config."""
    engine = create_engine(config.db.url, pool_pre_ping=True)
    logger.info("Database engine created -> %s:%s/%s", config.db.host, config.db.port, config.db.name)
    return engine


def load_raw_data(config: Config = cfg, force_reload: bool = False) -> pd.DataFrame:
    """
    Load user_features rows.

    The DB is queried by default to avoid stale training data. Set
    ML_USE_FEATURE_CACHE=true for local experiments that intentionally reuse the
    cached CSV.
    """
    cache_path: Path = config.data_dir / "users_raw.csv"
    use_cache = os.getenv("ML_USE_FEATURE_CACHE", "false").lower() == "true"

    if use_cache and cache_path.exists() and not force_reload:
        logger.info("Loading from cache -> %s", cache_path)
        df = pd.read_csv(cache_path)
        logger.info("Cached dataset loaded -- shape: %s", df.shape)
        return df

    logger.info("Querying user_features table.")
    engine = get_engine(config)
    with engine.connect() as conn:
        df = pd.read_sql(text(_USER_SEGMENTATION_QUERY), conn)

    logger.info("DB query complete -- shape: %s", df.shape)
    _save_raw(df, cache_path)
    return df


def _save_raw(df: pd.DataFrame, path: Path) -> None:
    """Persist raw dataframe to CSV."""
    df.to_csv(path, index=False)
    logger.info("Raw data saved -> %s", path)


def load_and_prepare(config: Config = cfg, force_reload: bool = False) -> pd.DataFrame:
    """
    Load backend-generated features and validate the training contract.
    """
    df = load_raw_data(config=config, force_reload=force_reload)

    missing = [col for col in config.features.feature_cols if col not in df.columns]
    if missing:
        raise ValueError(f"user_features is missing required ML columns: {missing}")

    for col in config.features.feature_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    logger.info("Feature preparation complete from user_features table.")
    return df
