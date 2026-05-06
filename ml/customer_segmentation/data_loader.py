"""
data_loader.py
--------------
Responsible for extracting user behavioural data from PostgreSQL
and persisting the raw dataset as a CSV artifact.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

from .config import Config, cfg

logger = logging.getLogger(__name__)

# ─── SQL Query ────────────────────────────────────────────────────────────────
_USER_SEGMENTATION_QUERY = """
    SELECT
        user_id,
        total_orders,
        total_spent,
        avg_order_value,
        views_count,
        clicks_count,
        cart_add_count,
        wishlist_add_count,
        last_order_at,
        last_interaction_at
    FROM v_user_behavior_features
    ORDER BY total_spent DESC;
"""


# ─── Core Functions ───────────────────────────────────────────────────────────

def get_engine(config: Config = cfg):
    """Create and return a SQLAlchemy engine from config."""
    engine = create_engine(config.db.url, pool_pre_ping=True)
    logger.info("Database engine created -> %s:%s/%s", config.db.host, config.db.port, config.db.name)
    return engine


def load_raw_data(config: Config = cfg, force_reload: bool = False) -> pd.DataFrame:
    """
    Load raw user behavioural data.

    Tries the cached CSV first (unless force_reload=True), then falls back
    to a live DB query.

    Parameters
    ----------
    config       : Config  – pipeline config
    force_reload : bool    – bypass cache and re-query the DB

    Returns
    -------
    pd.DataFrame with columns:
        user_id, registration_date, total_orders, total_spent,
        avg_order_value, last_order_date, total_reviews,
        avg_rating, unique_products_bought
    """
    cache_path: Path = config.data_dir / "users_raw.csv"

    if cache_path.exists() and not force_reload:
        logger.info("Loading from cache -> %s", cache_path)
        df = pd.read_csv(cache_path, parse_dates=["registration_date", "last_order_date"])
        logger.info("Cached dataset loaded -- shape: %s", df.shape)
        return df

    logger.info("Querying database …")
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


def add_recency(df: pd.DataFrame, snapshot_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """
    Compute recency in days from last_order_date.

    Users with no orders receive recency = 9999 (dormant sentinel).
    """
    if snapshot_date is None:
        snapshot_date = pd.Timestamp.now(tz="UTC")

    df = df.copy()
    df["last_order_date"] = pd.to_datetime(df["last_order_date"], utc=True)
    df["recency_days"] = (snapshot_date - df["last_order_date"]).dt.days
    df["recency_days"] = df["recency_days"].fillna(9999).astype(int)
    logger.info("Recency computed (snapshot: %s)", snapshot_date.date())
    return df


def load_and_prepare(config: Config = cfg, force_reload: bool = False) -> pd.DataFrame:
    """
    Load data from behavior view and compute interaction features.
    """
    df = load_raw_data(config=config, force_reload=force_reload)
    
    # 1. Compute recency features
    now = pd.Timestamp.now(tz="UTC")
    if "last_order_at" in df.columns:
        df["last_order_at"] = pd.to_datetime(df["last_order_at"], utc=True)
        df["recency_days"] = (now - df["last_order_at"]).dt.days.fillna(999).astype(int)
    
    if "last_interaction_at" in df.columns:
        df["last_interaction_at"] = pd.to_datetime(df["last_interaction_at"], utc=True)
        df["days_since_last_interaction"] = (now - df["last_interaction_at"]).dt.days.fillna(999).astype(int)
    
    # 2. Compute interaction ratios
    # Handle division by zero
    df["purchase_to_view_ratio"] = (df["total_orders"] / df["views_count"].replace(0, np.nan)).fillna(0)
    df["cart_to_click_ratio"] = (df["cart_add_count"] / df["clicks_count"].replace(0, np.nan)).fillna(0)
    
    logger.info("Feature preparation complete: recency and ratios computed.")
    return df
