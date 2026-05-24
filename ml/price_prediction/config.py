"""
Centralized configuration for product price prediction.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import List

try:
    from ml.core.config import settings
except ImportError:  # pragma: no cover - supports running from inside ml/
    from core.config import settings


ML_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ML_ROOT / "artifacts" / "price_prediction"
PLOTS_DIR = ARTIFACTS_DIR / "plots"
REPORTS_DIR = ARTIFACTS_DIR / "reports"
MODELS_DIR = ARTIFACTS_DIR / "models"
DATA_DIR = ARTIFACTS_DIR / "data"

for _dir in [PLOTS_DIR, REPORTS_DIR, MODELS_DIR, DATA_DIR]:
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
    numeric_features: List[str] = field(
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
    categorical_features: List[str] = field(
        default_factory=lambda: [
            "brand",
            "category_name",
            "subcategory_name",
        ]
    )


@dataclass
class ModelConfig:
    baseline_name: str = "median_baseline"
    performant_name: str = "random_forest_regressor"
    test_size: float = 0.2
    min_training_rows: int = 10
    random_state: int = 42
    n_estimators: int = 120
    max_depth: int | None = 14
    min_samples_leaf: int = 2


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

    plots_dir: Path = PLOTS_DIR
    reports_dir: Path = REPORTS_DIR
    models_dir: Path = MODELS_DIR
    data_dir: Path = DATA_DIR

    n_jobs: int = int(os.getenv("PRICE_MODEL_N_JOBS", "1"))
    price_model_name: str = settings.PRICE_MODEL_NAME
    price_model_version: str = settings.PRICE_MODEL_VERSION


cfg = Config()
