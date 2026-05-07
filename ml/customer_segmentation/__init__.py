"""
Customer Segmentation ML Package
=================================
End-to-end pipeline for unsupervised user segmentation on the
e-commerce intelligent platform.

Modules
-------
- config                : Centralised configuration & paths
- data_loader           : DB extraction & raw data loading
- data_understanding    : EDA helpers & statistical profiling
- preprocessing         : Feature engineering & scaling
- train_kmeans          : K-Means training & evaluation
- train_dbscan          : DBSCAN training & evaluation
- visualization         : All reusable plot functions
- business_interpretation: Segment labelling & business mapping
- compare_models        : Cross-model benchmarking metrics
- run_pipeline          : Orchestration entry-point
"""

from .config import Config  # noqa: F401

__version__ = "1.0.0"
__author__  = "E-Commerce ML Team"
