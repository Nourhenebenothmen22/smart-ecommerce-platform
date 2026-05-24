import json
import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from ml.price_prediction.config import Config
from ml.price_prediction.data_loader import _PRODUCT_FEATURE_QUERY, _PRODUCT_PRICE_QUERY
from ml.price_prediction.prediction import predict_price
from ml.price_prediction.preprocessing import build_feature_frame, clean_price_data
from ml.price_prediction.run_pipeline import train_price_prediction_models


@contextmanager
def _workspace_tempdir():
    root = Path(__file__).resolve().parents[2] / ".tmp" / "ml-price-tests"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _config(tmp: Path) -> Config:
    config = Config()
    config.data_dir = tmp / "data"
    config.models_dir = tmp / "models"
    config.plots_dir = tmp / "plots"
    config.reports_dir = tmp / "reports"
    for path in [config.data_dir, config.models_dir, config.plots_dir, config.reports_dir]:
        path.mkdir(parents=True, exist_ok=True)
    config.model.min_training_rows = 10
    config.model.test_size = 0.25
    config.model.n_estimators = 20
    config.model.max_depth = 6
    config.n_jobs = 1
    return config


def _sample_products() -> pd.DataFrame:
    rows = []
    brands = ["Acme", "Nova", "Zenith", "Orion"]
    categories = [(1, "Phones"), (2, "Computers"), (3, "Beauty")]
    subcategories = [(10, "Smartphones"), (20, "Laptops"), (30, "Perfume")]
    for idx in range(1, 21):
        cat_id, category_name = categories[idx % len(categories)]
        sub_id, subcategory_name = subcategories[idx % len(subcategories)]
        stock = 5 + idx * 3
        rating = 2.5 + (idx % 5) * 0.45
        review_count = idx * 4
        base = 40 + cat_id * 35 + sub_id * 1.5 + rating * 30 + review_count * 0.8
        rows.append(
            {
                "product_id": idx,
                "title": f"Product {idx}",
                "description": "Durable premium product with useful features" * (1 + idx % 3),
                "brand": brands[idx % len(brands)],
                "category_id": cat_id,
                "subcategory_id": sub_id,
                "category_name": category_name,
                "subcategory_name": subcategory_name,
                "price": round(base + stock * 0.4, 2),
                "discount_percent": idx % 25,
                "rating_avg": rating,
                "review_count": review_count,
                "stock": stock,
                "tags": ["quality", "value", category_name.lower()],
                "is_active": True,
                "created_at": "2025-01-01T00:00:00+00:00",
            }
        )
    return pd.DataFrame(rows)


class PricePredictionPipelineTests(unittest.TestCase):
    def test_data_loader_queries_backend_product_tables(self):
        self.assertIn("FROM products p", _PRODUCT_PRICE_QUERY)
        self.assertIn("JOIN categories c", _PRODUCT_PRICE_QUERY)
        self.assertIn("JOIN subcategories sc", _PRODUCT_PRICE_QUERY)
        self.assertIn("WHERE p.price > 0", _PRODUCT_PRICE_QUERY)
        self.assertIn("WHERE p.id = :product_id", _PRODUCT_FEATURE_QUERY)
        self.assertNotIn("hardcoded", _PRODUCT_PRICE_QUERY.lower())

    def test_feature_engineering_creates_backend_compatible_features(self):
        config = Config()
        frame = build_feature_frame(_sample_products().head(2), config=config, include_target=True)

        self.assertIn("title_length", frame.columns)
        self.assertIn("description_length", frame.columns)
        self.assertIn("tag_count", frame.columns)
        self.assertIn("has_discount", frame.columns)
        self.assertIn("log_stock", frame.columns)
        self.assertIn("rating_review_score", frame.columns)
        self.assertIn("brand_category", frame.columns)
        self.assertIn("category_subcategory", frame.columns)
        self.assertNotIn("category_id", frame.columns)
        self.assertNotIn("subcategory_id", frame.columns)
        self.assertIn(config.features.target_col, frame.columns)
        self.assertGreater(frame["tag_count"].iloc[0], 0)

        without_optional = _sample_products().head(1).drop(columns=["tags", "created_at"])
        optional_frame = build_feature_frame(without_optional, config=config, include_target=True)
        self.assertEqual(optional_frame["tag_count"].iloc[0], 0)

    def test_cleaning_removes_invalid_rows_and_normalizes_ranges(self):
        config = Config()
        dirty = _sample_products().head(3)
        dirty = pd.concat(
            [
                dirty,
                dirty.head(1),
                pd.DataFrame([
                    {
                        "product_id": 999,
                        "title": "Broken",
                        "description": None,
                        "brand": "  ACME  ",
                        "category_name": " Phones ",
                        "subcategory_name": " Smartphones ",
                        "price": -5,
                        "discount_percent": 150,
                        "rating_avg": 9,
                        "review_count": -1,
                        "stock": -3,
                    }
                ]),
            ],
            ignore_index=True,
        )

        cleaned, report = clean_price_data(dirty, config=config, include_target=True)

        self.assertEqual(report["duplicate_product_rows_removed"], 1)
        self.assertEqual(report["invalid_price_rows_removed"], 1)
        self.assertLessEqual(cleaned["discount_percent"].max(), 100)
        self.assertLessEqual(cleaned["rating_avg"].max(), 5)
        self.assertGreaterEqual(cleaned["review_count"].min(), 0)
        self.assertIn("nova", set(cleaned["brand"]))

    def test_training_comparison_artifacts_and_prediction_flow(self):
        with _workspace_tempdir() as tmp_dir:
            config = _config(tmp_dir)
            results = train_price_prediction_models(_sample_products(), config=config)

            self.assertEqual(results["best_profile"], "improved")
            self.assertEqual(len(results["metrics_by_model"]), 2)
            self.assertIn(config.model.baseline_name, results["metrics_by_model"])
            self.assertIn(config.model.performant_name, results["metrics_by_model"])
            for metrics in results["metrics_by_model"].values():
                self.assertIn("mae", metrics)
                self.assertIn("mse", metrics)
                self.assertIn("rmse", metrics)
                self.assertIn("r2", metrics)

            self.assertTrue((config.models_dir / "best_model.pkl").exists())
            self.assertTrue((config.models_dir / "metadata.json").exists())
            self.assertTrue((config.reports_dir / "model_comparison.csv").exists())
            self.assertTrue((config.reports_dir / "preprocessing_report.json").exists())
            self.assertTrue((config.plots_dir / "price_distribution.png").exists())
            self.assertTrue((config.plots_dir / "feature_correlation.png").exists())
            self.assertTrue((config.plots_dir / "actual_vs_predicted_price.png").exists())
            self.assertTrue((config.plots_dir / "model_performance_comparison.png").exists())

            payload = _sample_products().iloc[0].drop(labels=["price"]).to_dict()
            payload.pop("product_id")
            prediction = predict_price(payload, config=config)

            self.assertGreaterEqual(prediction["predicted_price"], 0)
            self.assertEqual(prediction["model_name"], config.price_model_name)
            self.assertEqual(prediction["model_version"], config.price_model_version)
            self.assertEqual(prediction["preprocessing_profile"], "improved")
            self.assertIn("features_used", prediction)

    def test_prediction_hides_legacy_metadata_metrics(self):
        with _workspace_tempdir() as tmp_dir:
            config = _config(tmp_dir)
            results = train_price_prediction_models(_sample_products(), config=config)
            metadata_path = config.models_dir / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            best_key = results["best_model"]
            metadata["best_result_key"] = f"improved__{best_key}"
            metadata["metrics"] = {
                "legacy__median_baseline": {"mae": 999, "mse": 999, "rmse": 999, "r2": -99},
                f"improved__{best_key}": results["metrics_by_model"][best_key],
            }
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

            payload = _sample_products().iloc[0].drop(labels=["price", "product_id"]).to_dict()
            prediction = predict_price(payload, config=config)

            self.assertEqual(prediction["model_algorithm"], best_key)
            self.assertEqual(set(prediction["metrics"].keys()), {best_key})
            for metric_key in prediction["metrics"]:
                self.assertNotIn("legacy__", metric_key)
                self.assertNotIn("improved__", metric_key)


if __name__ == "__main__":
    unittest.main()
