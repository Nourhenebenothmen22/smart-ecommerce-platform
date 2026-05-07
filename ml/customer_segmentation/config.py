"""
config.py
---------
Centralised configuration for the Customer Segmentation pipeline.
All paths, hyper-parameters and DB settings live here.
"""

# Load ml/.env BEFORE any os.getenv call
from pathlib import Path as _Path
try:
    from dotenv import load_dotenv as _load_dotenv
    _env_file = _Path(__file__).resolve().parent.parent / ".env"  # ml/.env
    if _env_file.exists():
        _load_dotenv(dotenv_path=_env_file, override=False)
except ImportError:
    pass  # python-dotenv not installed -- rely on shell environment

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

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
    user:     str = os.getenv("POSTGRES_USER",     "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    host:     str = os.getenv("POSTGRES_HOST",     "localhost")
    port:     str = os.getenv("POSTGRES_PORT",     "5432")
    name:     str = os.getenv("POSTGRES_DB",       "ecommerce_db")

    @property
    def url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


# ─── Feature Engineering ──────────────────────────────────────────────────────
@dataclass
class FeatureConfig:
    # Columns to use for clustering (Full e-commerce behavioral set)
    feature_cols: List[str] = field(default_factory=lambda: [
        "recency_days",
        "total_orders",
        "total_spent",
        "avg_order_value",
        "views_count",
        "clicks_count",
        "cart_add_count",
        "wishlist_add_count",
        "days_since_last_interaction",
        "purchase_to_view_ratio",
        "cart_to_click_ratio",
    ])
    # Columns that need log1p transformation (right-skewed)
    log_transform_cols: List[str] = field(default_factory=lambda: [
        "total_spent",
        "avg_order_value",
        "total_orders",
        "views_count",
        "clicks_count",
        "cart_add_count",
        "wishlist_add_count",
    ])
    scaler: str = "robust"   # "standard" | "minmax" | "robust"
    outlier_method: str = "iqr"  # "iqr" | "zscore" | "none"
    outlier_threshold: float = 3.0


# ─── K-Means ──────────────────────────────────────────────────────────────────
@dataclass
class KMeansConfig:
    k_range: List[int] = field(default_factory=lambda: list(range(2, 13)))
    n_clusters: int = 8          # final k chosen after elbow/silhouette
    init: str = "k-means++"
    n_init: int = 20
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


# Singleton-style default instance
cfg = Config()
