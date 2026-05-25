"""
Centralized configuration for product price prediction.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any, List

try:
    from ml.core.config import settings
except ImportError:  # pragma: no cover - supports running from inside ml/
    from core.config import settings


ML_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ML_ROOT / "artifacts" / "price_prediction"
PLOTS_DIR = ARTIFACTS_DIR / "plots"
REPORTS_DIR = ARTIFACTS_DIR / "reports"
MODELS_DIR = ARTIFACTS_DIR / "model"
DATA_DIR = ARTIFACTS_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
METADATA_DIR = ARTIFACTS_DIR / "metadata"

for _dir in [PLOTS_DIR, REPORTS_DIR, MODELS_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, METADATA_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)


@dataclass
class DBConfig:
    user: str = settings.DB_USER
    password: str = settings.DB_PASS
    host: str = settings.DB_HOST
    port: str = str(settings.DB_PORT)
    name: str = settings.DB_NAME

    @property
    def url(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class FeatureConfig:
    target_col: str = "price"
    legacy_numeric_features: List[str] = field(
        default_factory=lambda: [
            "category_id",
            "subcategory_id",
            "discount_percent",
            "rating_avg",
            "review_count",
            "stock",
            "title_length",
            "description_length",
            "tag_count",
            "product_age_days",
            "is_active_int",
        ]
    )
    legacy_categorical_features: List[str] = field(
        default_factory=lambda: [
            "brand",
            "category_name",
            "subcategory_name",
        ]
    )
    numeric_features: List[str] = field(
        default_factory=lambda: [
            "discount_percent",
            "discount_ratio",
            "has_discount",
            "rating_avg",
            "review_count",
            "log_review_count",
            "stock",
            "log_stock",
            "title_length",
            "description_length",
            "description_to_title_ratio",
            "tag_count",
            "text_richness_score",
            "rating_review_score",
            "product_age_days",
            "is_active_int",
            "order_line_count",
            "total_quantity_sold",
            "avg_order_quantity",
            "max_order_quantity",
            "fulfilled_order_lines",
            "fulfilled_quantity_sold",
            "distinct_buyers",
            "days_since_first_order",
            "days_since_last_order",
            "log_order_line_count",
            "log_total_quantity_sold",
            "sales_velocity",
            "quantity_per_buyer",
            "buyer_per_order_ratio",
            "view_count",
            "click_count",
            "add_to_cart_count",
            "wishlist_interaction_count",
            "purchase_interaction_count",
            "share_count",
            "search_count",
            "interaction_count",
            "distinct_interaction_users",
            "avg_interaction_value",
            "days_since_last_interaction",
            "current_cart_quantity",
            "current_cart_users",
            "wishlist_count",
            "review_rows_count",
            "verified_review_count",
            "avg_review_rating",
            "negative_review_count",
            "positive_review_count",
            "demand_score",
            "conversion_rate",
            "cart_to_view_rate",
            "purchase_to_view_rate",
            "wishlist_to_view_rate",
            "stock_to_sales_ratio",
        ]
    )
    historical_price_proxy_features: List[str] = field(
        default_factory=lambda: [
            "total_order_revenue",
            "avg_historical_unit_price",
            "min_historical_unit_price",
            "max_historical_unit_price",
            "historical_unit_price_stddev",
            "historical_price_range",
            "historical_price_std_ratio",
            "historical_discount_gap_pct",
            "log_total_order_revenue",
            "revenue_per_buyer",
        ]
    )
    categorical_features: List[str] = field(
        default_factory=lambda: [
            "brand",
            "category_name",
            "subcategory_name",
            "brand_category",
            "category_subcategory",
            "stock_bucket",
            "popularity_bucket",
            "discount_bucket",
            "has_sales_history",
            "has_interaction_history",
            "has_cart_pressure",
            "has_wishlist_pressure",
            "demand_bucket",
        ]
    )
    target_encoded_features: List[str] = field(
        default_factory=lambda: [
            "brand",
            "category_name",
            "subcategory_name",
            "brand_category",
            "category_subcategory",
        ]
    )
    rare_category_min_frequency: int = 3
    target_encoding_smoothing: float = 20.0
    max_valid_price: float = 50000.0
    outlier_lower_quantile: float = 0.005
    outlier_upper_quantile: float = 0.995


@dataclass
class ModelConfig:
    baseline_name: str = "linear_regression"
    medium_name: str = "random_forest_regressor"
    strong_name: str = "xgboost_regressor"
    performant_name: str = "random_forest_regressor"
    test_size: float = 0.2
    min_training_rows: int = 10
    random_state: int = 42
    n_estimators: int = 120
    max_depth: int | None = 14
    min_samples_leaf: int = 2
    baseline_use_log_target: bool = True
    medium_use_log_target: bool = True
    strong_use_log_target: bool = True
    performant_use_log_target: bool = True
    log_target_options: tuple[bool, ...] = (False, True)
    minimum_publish_r2: float = 0.0
    max_overfit_r2_gap: float = 0.35
    random_forest_grid: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {"n_estimators": 80, "max_depth": 8, "min_samples_leaf": 4},
            {"n_estimators": 120, "max_depth": 12, "min_samples_leaf": 3},
            {"n_estimators": 160, "max_depth": 14, "min_samples_leaf": 2},
        ]
    )
    xgboost_grid: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "n_estimators": 220,
                "max_depth": 3,
                "learning_rate": 0.05,
                "subsample": 0.85,
                "colsample_bytree": 0.85,
                "reg_lambda": 5.0,
            },
            {
                "n_estimators": 320,
                "max_depth": 4,
                "learning_rate": 0.03,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "reg_lambda": 10.0,
            },
        ]
    )


@dataclass
class VizConfig:
    dpi: int = 150
    figsize_default: tuple = (12, 7)
    palette: str = "viridis"
    save_format: str = "png"


@dataclass
class Config:
    db: DBConfig = field(default_factory=DBConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    viz: VizConfig = field(default_factory=VizConfig)

    artifacts_dir: Path = ARTIFACTS_DIR
    plots_dir: Path = PLOTS_DIR
    reports_dir: Path = REPORTS_DIR
    models_dir: Path = MODELS_DIR
    data_dir: Path = DATA_DIR
    raw_data_dir: Path = RAW_DATA_DIR
    processed_data_dir: Path = PROCESSED_DATA_DIR
    metadata_dir: Path = METADATA_DIR

    n_jobs: int = int(os.getenv("PRICE_MODEL_N_JOBS", "1"))
    price_model_name: str = settings.PRICE_MODEL_NAME
    price_model_version: str = settings.PRICE_MODEL_VERSION


cfg = Config()
