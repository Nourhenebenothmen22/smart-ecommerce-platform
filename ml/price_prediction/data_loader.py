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


_PRODUCT_SIGNAL_CTES = """
    WITH order_stats AS (
        SELECT
            oi.product_id,
            COUNT(*)::float AS order_line_count,
            COALESCE(SUM(oi.quantity), 0)::float AS total_quantity_sold,
            COALESCE(AVG(oi.quantity), 0)::float AS avg_order_quantity,
            COALESCE(MAX(oi.quantity), 0)::float AS max_order_quantity,
            COALESCE(SUM(oi.subtotal), 0)::float AS total_order_revenue,
            AVG(oi.unit_price)::float AS avg_historical_unit_price,
            MIN(oi.unit_price)::float AS min_historical_unit_price,
            MAX(oi.unit_price)::float AS max_historical_unit_price,
            COALESCE(STDDEV_POP(oi.unit_price), 0)::float AS historical_unit_price_stddev,
            COUNT(DISTINCT o.user_id)::float AS distinct_buyers,
            COUNT(*) FILTER (WHERE o.status IN ('delivered', 'completed', 'shipped'))::float AS fulfilled_order_lines,
            COALESCE(SUM(oi.quantity) FILTER (WHERE o.status IN ('delivered', 'completed', 'shipped')), 0)::float AS fulfilled_quantity_sold,
            MIN(o.created_at) AS first_order_at,
            MAX(o.created_at) AS last_order_at
        FROM order_items oi
        LEFT JOIN orders o ON o.id = oi.order_id
        WHERE oi.product_id IS NOT NULL
        GROUP BY oi.product_id
    ),
    interaction_stats AS (
        SELECT
            ui.product_id,
            COUNT(*)::float AS interaction_count,
            COUNT(DISTINCT ui.user_id)::float AS distinct_interaction_users,
            COALESCE(AVG(ui.interaction_value), 0)::float AS avg_interaction_value,
            COUNT(*) FILTER (WHERE ui.interaction_type = 'view')::float AS view_count,
            COUNT(*) FILTER (WHERE ui.interaction_type = 'click')::float AS click_count,
            COUNT(*) FILTER (WHERE ui.interaction_type = 'add_to_cart')::float AS add_to_cart_count,
            COUNT(*) FILTER (WHERE ui.interaction_type = 'add_to_wishlist')::float AS wishlist_interaction_count,
            COUNT(*) FILTER (WHERE ui.interaction_type = 'purchase')::float AS purchase_interaction_count,
            COUNT(*) FILTER (WHERE ui.interaction_type = 'share')::float AS share_count,
            COUNT(*) FILTER (WHERE ui.interaction_type = 'search')::float AS search_count,
            MAX(ui.created_at) AS last_interaction_at
        FROM user_interactions ui
        GROUP BY ui.product_id
    ),
    review_stats AS (
        SELECT
            r.product_id,
            COUNT(*)::float AS review_rows_count,
            COUNT(*) FILTER (WHERE r.verified_purchase IS TRUE)::float AS verified_review_count,
            COALESCE(AVG(r.rating), 0)::float AS avg_review_rating,
            COUNT(*) FILTER (WHERE r.rating <= 2)::float AS negative_review_count,
            COUNT(*) FILTER (WHERE r.rating >= 4)::float AS positive_review_count
        FROM reviews r
        GROUP BY r.product_id
    ),
    cart_stats AS (
        SELECT
            ci.product_id,
            COALESCE(SUM(ci.quantity), 0)::float AS current_cart_quantity,
            COUNT(DISTINCT ci.user_id)::float AS current_cart_users
        FROM cart_items ci
        GROUP BY ci.product_id
    ),
    wishlist_stats AS (
        SELECT
            w.product_id,
            COUNT(*)::float AS wishlist_count
        FROM wishlists w
        GROUP BY w.product_id
    )
"""


_PRODUCT_SELECT_COLUMNS = """
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
        p.created_at,
        COALESCE(os.order_line_count, 0)::float AS order_line_count,
        COALESCE(os.total_quantity_sold, 0)::float AS total_quantity_sold,
        COALESCE(os.avg_order_quantity, 0)::float AS avg_order_quantity,
        COALESCE(os.max_order_quantity, 0)::float AS max_order_quantity,
        COALESCE(os.fulfilled_order_lines, 0)::float AS fulfilled_order_lines,
        COALESCE(os.fulfilled_quantity_sold, 0)::float AS fulfilled_quantity_sold,
        COALESCE(os.total_order_revenue, 0)::float AS total_order_revenue,
        COALESCE(os.avg_historical_unit_price, 0)::float AS avg_historical_unit_price,
        COALESCE(os.min_historical_unit_price, 0)::float AS min_historical_unit_price,
        COALESCE(os.max_historical_unit_price, 0)::float AS max_historical_unit_price,
        COALESCE(os.historical_unit_price_stddev, 0)::float AS historical_unit_price_stddev,
        COALESCE(os.distinct_buyers, 0)::float AS distinct_buyers,
        os.first_order_at,
        os.last_order_at,
        COALESCE(ins.interaction_count, 0)::float AS interaction_count,
        COALESCE(ins.distinct_interaction_users, 0)::float AS distinct_interaction_users,
        COALESCE(ins.avg_interaction_value, 0)::float AS avg_interaction_value,
        COALESCE(ins.view_count, 0)::float AS view_count,
        COALESCE(ins.click_count, 0)::float AS click_count,
        COALESCE(ins.add_to_cart_count, 0)::float AS add_to_cart_count,
        COALESCE(ins.wishlist_interaction_count, 0)::float AS wishlist_interaction_count,
        COALESCE(ins.purchase_interaction_count, 0)::float AS purchase_interaction_count,
        COALESCE(ins.share_count, 0)::float AS share_count,
        COALESCE(ins.search_count, 0)::float AS search_count,
        ins.last_interaction_at,
        COALESCE(cs.current_cart_quantity, 0)::float AS current_cart_quantity,
        COALESCE(cs.current_cart_users, 0)::float AS current_cart_users,
        COALESCE(ws.wishlist_count, 0)::float AS wishlist_count,
        COALESCE(rs.review_rows_count, 0)::float AS review_rows_count,
        COALESCE(rs.verified_review_count, 0)::float AS verified_review_count,
        COALESCE(rs.avg_review_rating, 0)::float AS avg_review_rating,
        COALESCE(rs.negative_review_count, 0)::float AS negative_review_count,
        COALESCE(rs.positive_review_count, 0)::float AS positive_review_count
"""


_PRODUCT_JOIN_CLAUSE = """
    FROM products p
    JOIN categories c ON c.id = p.category_id
    JOIN subcategories sc ON sc.id = p.subcategory_id
    LEFT JOIN order_stats os ON os.product_id = p.id
    LEFT JOIN interaction_stats ins ON ins.product_id = p.id
    LEFT JOIN review_stats rs ON rs.product_id = p.id
    LEFT JOIN cart_stats cs ON cs.product_id = p.id
    LEFT JOIN wishlist_stats ws ON ws.product_id = p.id
"""


_PRODUCT_PRICE_QUERY = (
    _PRODUCT_SIGNAL_CTES
    + """
    SELECT
"""
    + _PRODUCT_SELECT_COLUMNS.replace("p.created_at,", "p.created_at,\n        p.price::float AS price,")
    + _PRODUCT_JOIN_CLAUSE
    + """
    WHERE p.price > 0
    ORDER BY p.updated_at DESC, p.id;
"""
)

_PRODUCT_FEATURE_QUERY = (
    _PRODUCT_SIGNAL_CTES
    + """
    SELECT
"""
    + _PRODUCT_SELECT_COLUMNS
    + _PRODUCT_JOIN_CLAUSE
    + """
    WHERE p.id = :product_id
    LIMIT 1;
"""
)


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
