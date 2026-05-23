"""
config.py
---------
Centralised configuration for the Customer Segmentation pipeline.
All paths, hyper-parameters and DB settings live here.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List

try:
    from ml.core.config import settings
except ImportError:  # pragma: no cover - supports running from inside ml/
    from core.config import settings

# ─── Root Paths ──────────────────────────────────────────────────────────────
ML_ROOT       = Path(__file__).resolve().parent.parent          # ml/
ARTIFACTS_DIR = ML_ROOT / "artifacts" / "customer_segmentation"
PLOTS_DIR     = ARTIFACTS_DIR / "plots"
REPORTS_DIR   = ARTIFACTS_DIR / "reports"
MODELS_DIR    = ARTIFACTS_DIR / "models"
DATA_DIR      = ARTIFACTS_DIR / "data"

# Ensure directories exist at import time
for _dir in [PLOTS_DIR, REPORTS_DIR, MODELS_DIR, DATA_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)


# ─── Database ─────────────────────────────────────────────────────────────────
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


# ─── Feature Engineering ──────────────────────────────────────────────────────
@dataclass
class FeatureConfig:
    # Columns to use for clustering
    # avg_order_value removed: it is a linear combination of total_spent / total_orders
    # (multicollinearity inflates the weight of spending behaviour)
    feature_cols: List[str] = field(default_factory=lambda: [
        "days_since_last_order",
        "total_orders",
        "total_spent",
        "views_count",
        "clicks_count",
        "cart_add_count",
        "wishlist_add_count",
        "days_since_last_interaction",
        "purchase_to_view_ratio",
        "cart_to_click_ratio",
    ])
    # Columns that need log1p transformation (right-skewed)
    # recency columns added: the 999 sentinel for users with no history
    # is heavily right-skewed and must be compressed before scaling.
    log_transform_cols: List[str] = field(default_factory=lambda: [
        "total_spent",
        "total_orders",
        "views_count",
        "clicks_count",
        "cart_add_count",
        "wishlist_add_count",
        "days_since_last_order",
        "days_since_last_interaction",
    ])
    scaler: str = "robust"   # "standard" | "minmax" | "robust"
    outlier_method: str = "iqr"  # "iqr" | "zscore" | "none"
    outlier_threshold: float = 3.0


# ─── K-Means ──────────────────────────────────────────────────────────────────
@dataclass
class KMeansConfig:
    k_range: List[int] = field(default_factory=lambda: [2, 3, 4, 5])
    n_clusters: int = 5          # maximum requested
    init: str = "k-means++"
    n_init: int = 50
    max_iter: int = 500
    random_state: int = 42


# ─── DBSCAN ───────────────────────────────────────────────────────────────────
@dataclass
class DBSCANConfig:
    eps_range: List[float] = field(default_factory=lambda: [0.3, 0.5, 0.7, 1.0, 1.5])
    min_samples_range: List[int] = field(default_factory=lambda: [3, 5, 10, 15])
    eps: float = 1.2
    min_samples: int = 5
    metric: str = "euclidean"


# ─── Visualisation ────────────────────────────────────────────────────────────
@dataclass
class VizConfig:
    dpi: int = 150
    figsize_default: tuple = (12, 7)
    palette: str = "tab10"
    save_format: str = "png"


# ─── Master Config ────────────────────────────────────────────────────────────
@dataclass
class Config:
    db:       DBConfig      = field(default_factory=DBConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    kmeans:   KMeansConfig  = field(default_factory=KMeansConfig)
    dbscan:   DBSCANConfig  = field(default_factory=DBSCANConfig)
    viz:      VizConfig     = field(default_factory=VizConfig)

    # Convenience path shortcuts
    plots_dir:   Path = PLOTS_DIR
    reports_dir: Path = REPORTS_DIR
    models_dir:  Path = MODELS_DIR
    data_dir:    Path = DATA_DIR

    random_state: int = 42
    n_jobs: int = -1
    segmentation_model_name: str = settings.SEGMENTATION_MODEL_NAME
    segmentation_model_version: str = settings.SEGMENTATION_MODEL_VERSION
    embedding_model_name: str = settings.EMBEDDING_MODEL_NAME
    embedding_model_version: str = settings.EMBEDDING_MODEL_VERSION


# Singleton-style default instance
cfg = Config()
