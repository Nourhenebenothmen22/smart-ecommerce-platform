"""
Load product price training and inference data from PostgreSQL.
"""

import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text

from .config import Config, cfg

logger = logging.getLogger(__name__)


_PRODUCT_PRICE_QUERY = """
    SELECT
        p.id AS product_id,
        p.title,
        p.description,
        p.brand,
        p.category_id,
        p.subcategory_id,
        c.name AS category_name,
        sc.name AS subcategory_name,
        p.price::float AS price,
        p.discount_percent,
        p.rating_avg::float AS rating_avg,
        p.review_count,
        p.stock,
        p.tags,
        p.is_active,
        p.created_at
    FROM products p
    JOIN categories c ON c.id = p.category_id
    JOIN subcategories sc ON sc.id = p.subcategory_id
    WHERE p.price > 0
    ORDER BY p.updated_at DESC, p.id;
"""

_PRODUCT_FEATURE_QUERY = """
    SELECT
        p.id AS product_id,
        p.title,
        p.description,
        p.brand,
        p.category_id,
        p.subcategory_id,
        c.name AS category_name,
        sc.name AS subcategory_name,
        p.discount_percent,
        p.rating_avg::float AS rating_avg,
        p.review_count,
        p.stock,
        p.tags,
        p.is_active,
        p.created_at
    FROM products p
    JOIN categories c ON c.id = p.category_id
    JOIN subcategories sc ON sc.id = p.subcategory_id
    WHERE p.id = :product_id
    LIMIT 1;
"""


def get_engine(config: Config = cfg):
    """Create a SQLAlchemy engine from ML database settings."""
    engine = create_engine(config.db.url, pool_pre_ping=True)
    logger.info("Database engine created -> %s:%s/%s", config.db.host, config.db.port, config.db.name)
    return engine


def load_product_training_data(config: Config = cfg, force_reload: bool = False) -> pd.DataFrame:
    """
    Load dynamic product data from PostgreSQL.

    A local CSV cache is only used when ML_USE_PRICE_CACHE=true. This keeps
    training aligned with the live backend catalog by default.
    """
    cache_path: Path = config.data_dir / "products_price_raw.csv"
    use_cache = os.getenv("ML_USE_PRICE_CACHE", "false").lower() == "true"

    if use_cache and cache_path.exists() and not force_reload:
        logger.info("Loading cached price dataset -> %s", cache_path)
        return pd.read_csv(cache_path)

    logger.info("Querying products table for price prediction training data.")
    engine = get_engine(config)
    with engine.connect() as conn:
        df = pd.read_sql(text(_PRODUCT_PRICE_QUERY), conn)

    logger.info("Loaded product price dataset -- shape: %s", df.shape)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache_path, index=False)
    return df


def load_product_features(product_id: int, config: Config = cfg) -> dict[str, Any]:
    """Load one product's inference features from PostgreSQL."""
    engine = get_engine(config)
    with engine.connect() as conn:
        df = pd.read_sql(text(_PRODUCT_FEATURE_QUERY), conn, params={"product_id": product_id})

    if df.empty:
        raise ValueError(f"Product not found for price prediction: {product_id}")

    return df.iloc[0].to_dict()

