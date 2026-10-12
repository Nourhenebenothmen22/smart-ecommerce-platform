import unittest
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from ml.customer_segmentation.config import Config
from ml.customer_segmentation.prediction import predict_segment
from ml.customer_segmentation.preprocessing import preprocess
from ml.customer_segmentation.train_dbscan import grid_search_dbscan
from ml.customer_segmentation.train_kmeans import run_kmeans_tuning


@contextmanager
def _workspace_tempdir():
    root = Path(__file__).resolve().parents[3] / ".tmp" / "ml-tests"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _config(tmp: Path) -> Config:
    config = Config()
    config.artifacts_dir = tmp
    config.data_dir = tmp / "data"
    config.raw_data_dir = config.data_dir / "raw"
    config.processed_data_dir = config.data_dir / "processed"
    config.models_dir = tmp / "model"
    config.plots_dir = tmp / "plots"
    config.reports_dir = tmp / "reports"
    config.metadata_dir = tmp / "metadata"
    for path in [
        config.raw_data_dir,
        config.processed_data_dir,
        config.models_dir,
        config.plots_dir,
        config.reports_dir,
        config.metadata_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)
    config.kmeans.k_range = [2, 3, 4, 5]
    config.dbscan.min_samples = 3
    config.dbscan.min_samples_range = [2, 3, 5]
    return config


def _features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            [1, 5, 500, 30, 12, 4, 2, 10, 5, 0.16, 0.33],
            [2, 6, 700, 35, 14, 5, 3, 7, 4, 0.17, 0.35],
            [3, 1, 50, 80, 10, 1, 6, 100, 80, 0.01, 0.10],
            [4, 1, 80, 90, 11, 1, 8, 120, 95, 0.01, 0.09],
            [5, 3, 250, 25, 20, 10, 4, 30, 12, 0.12, 0.50],
            [6, 4, 300, 28, 21, 9, 5, 20, 10, 0.14, 0.43],
        ],
        columns=[
            "user_id",
            "total_orders",
            "total_spent",
            "views_count",
            "clicks_count",
            "cart_add_count",
            "wishlist_add_count",
            "days_since_last_order",
            "days_since_last_interaction",
            "purchase_to_view_ratio",
            "cart_to_click_ratio",
        ],
    )


class SegmentationPipelineTests(unittest.TestCase):
    def test_preprocess_fit_and_inference_share_artifacts(self):
        with _workspace_tempdir() as tmp_dir:
            config = _config(tmp_dir)
            X_train, df_clean, _, features = preprocess(_features(), config, fit=True)
            self.assertEqual(X_train.shape, (6, len(features)))
            self.assertTrue((config.models_dir / "scaler.pkl").exists())
            self.assertTrue((config.models_dir / "winsorization_bounds.json").exists())

            X_pred, _, _, _ = preprocess(_features().head(1), config, fit=False)
            self.assertEqual(X_pred.shape, (1, len(config.features.feature_cols)))
            self.assertIn("user_id", df_clean.columns)

    def test_training_guards_small_and_valid_datasets(self):
        with _workspace_tempdir() as tmp_dir:
            config = _config(tmp_dir)
            X = np.array(
                [
                    [0.0, 0.0],
                    [0.1, 0.1],
                    [5.0, 5.0],
                    [5.1, 5.1],
                    [9.0, 9.0],
                    [9.1, 9.1],
                ]
            )
            self.assertIn(run_kmeans_tuning(X, config), [2, 3, 4, 5])
            self.assertGreaterEqual(grid_search_dbscan(X, config)["min_samples"], 2)
            with self.assertRaises(ValueError):
                run_kmeans_tuning(X[:2], config)

    def test_production_prediction_flow(self):
        with _workspace_tempdir() as tmp_dir:
            config = _config(tmp_dir)
            X_train, _, _, _ = preprocess(_features(), config, fit=True)
            model = KMeans(n_clusters=2, n_init=10, random_state=42).fit(X_train)
            joblib.dump(model, config.models_dir / "kmeans_model.pkl")
            (config.models_dir / "segment_map.json").write_text(
                '{"0": {"label": "VIP Customers"}, "1": {"label": "Regular Customers"}}',
                encoding="utf-8",
            )

            result = predict_segment(_features().iloc[0].to_dict(), config)
            self.assertEqual(result["user_id"], 1)
            self.assertIn(result["segment_label"], {"VIP Customers", "Regular Customers"})
            self.assertEqual(result["model_name"], config.segmentation_model_name)


if __name__ == "__main__":
    unittest.main()
