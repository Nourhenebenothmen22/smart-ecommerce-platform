"""
Customer Segmentation ML Package
=================================
End-to-end pipeline for unsupervised user segmentation.
Focuses on K-Means and DBSCAN comparison.

Modules
-------
- config                : Centralised configuration & paths
- data_loader           : DB extraction & raw data loading
- preprocessing         : Feature engineering & scaling
- train_kmeans          : K-Means training & evaluation
- train_dbscan          : DBSCAN training & evaluation
- plots                : Required visualization functions
- business_interpretation: Segment labelling & business mapping
- compare_models        : Cross-model benchmarking metrics
- run_pipeline          : Orchestration entry-point
"""

from .config import Config  # noqa: F401

__version__ = "2.0.0"
__author__  = "Senior ML Engineer Audit"
