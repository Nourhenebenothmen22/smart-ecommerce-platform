import json
import os
import shutil
import tempfile
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from ml.price_prediction.config import Config
from ml.price_prediction.data_loader import _PRODUCT_FEATURE_QUERY, _PRODUCT_PRICE_QUERY
from ml.price_prediction.prediction import predict_price
from ml.price_prediction.preprocessing import build_feature_frame, clean_price_data, feature_columns
from ml.price_prediction.run_pipeline import train_price_prediction_models
from ml.price_prediction.compare_models import production_gate


@contextmanager
def _workspace_tempdir():
    root = Path(os.getenv("ML_TEST_TMPDIR", tempfile.gettempdir())) / "ml-price-tests" / f"run-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    path = root / "case"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(root, ignore_errors=True)


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
    config.model.min_training_rows = 10
    config.model.test_size = 0.25
    config.model.n_estimators = 20
    config.model.max_depth = 6
    config.model.random_forest_grid = [{"n_estimators": 25, "max_depth": 6, "min_samples_leaf": 1}]
    config.model.xgboost_grid = [
        {
            "n_estimators": 40,
            "max_depth": 3,
            "learning_rate": 0.12,
            "subsample": 1.0,
            "colsample_bytree": 1.0,
            "reg_lambda": 1.0,
        }
    ]
    config.model.log_target_options = (False, True)
    config.n_jobs = 1
    return config


def _sample_products() -> pd.DataFrame:
    rows = []
    brands = ["Acme", "Nova", "Zenith", "Orion"]
    categories = [(1, "Phones"), (2, "Computers"), (3, "Beauty")]
    subcategories = [(10, "Smartphones"), (20, "Laptops"), (30, "Perfume")]
    for idx in range(1, 81):
        cat_id, category_name = categories[idx % len(categories)]
        sub_id, subcategory_name = subcategories[idx % len(subcategories)]
        stock = 5 + (idx * 7) % 130
        rating = 2.5 + (idx % 5) * 0.45
        review_count = idx * 4
        discount_percent = idx % 25
        demand_curve = 0.08 * (stock - 65) ** 2
        brand_category_key = (brands[idx % len(brands)], category_name)
        category_interaction = 85 if brand_category_key in {
            ("Nova", "Computers"),
            ("Orion", "Phones"),
        } else 0
        bucket_jump = 45 if discount_percent >= 18 and stock < 55 else 0
        base = 120 + cat_id * 22 + rating * 18 + demand_curve + category_interaction + bucket_jump
        
        # New price driver columns
        brand_tier = idx % 4 + 1
        product_tier = idx % 3 + 1
        condition = ["new", "refurbished", "open_box", "used"][idx % 4]
        release_year = 2020 + idx % 7
        supplier_cost = round(base * 0.6, 2)
        margin_pct = round(15.0 + brand_tier * 10, 2)
        
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
                "price": round(base + (review_count % 11) * 3.5, 2),
                "discount_percent": discount_percent,
                "rating_avg": rating,
                "review_count": review_count,
                "stock": stock,
                "tags": ["quality", "value", category_name.lower()],
                "is_active": True,
                "created_at": f"2025-01-{1 + idx % 10:02d}T00:00:00+00:00",
                "order_line_count": 2 + idx % 4,
                "total_quantity_sold": 3 + idx,
                "avg_order_quantity": 1.5 + (idx % 3) * 0.5,
                "max_order_quantity": 4 + idx % 3,
                "fulfilled_order_lines": 1 + idx % 2,
                "fulfilled_quantity_sold": 2 + idx,
                "total_order_revenue": round((base + stock * 0.4) * (2 + idx % 5), 2),
                "avg_historical_unit_price": round(base + stock * 0.4, 2),
                "min_historical_unit_price": round((base + stock * 0.4) * 0.9, 2),
                "max_historical_unit_price": round((base + stock * 0.4) * 1.05, 2),
                "historical_unit_price_stddev": 3.5 + idx % 5,
                "distinct_buyers": 1 + idx % 7,
                "first_order_at": "2025-02-01T00:00:00+00:00",
                "last_order_at": "2025-04-01T00:00:00+00:00",
                "interaction_count": 10 + idx,
                "distinct_interaction_users": 4 + idx % 5,
                "avg_interaction_value": 1.0 + (idx % 4) * 0.2,
                "view_count": 20 + idx,
                "click_count": 8 + idx % 8,
                "add_to_cart_count": 3 + idx % 4,
                "wishlist_interaction_count": 2 + idx % 3,
                "purchase_interaction_count": 1 + idx % 2,
                "share_count": idx % 4,
                "search_count": idx % 5,
                "last_interaction_at": "2025-05-01T00:00:00+00:00",
                "current_cart_quantity": idx % 6,
                "current_cart_users": idx % 4,
                "wishlist_count": idx % 9,
                "review_rows_count": review_count,
                "verified_review_count": review_count // 2,
                "avg_review_rating": rating,
                "negative_review_count": idx % 3,
                "positive_review_count": idx % 6,
                "brand_tier": brand_tier,
                "product_tier": product_tier,
                "condition": condition,
                "release_year": release_year,
                "supplier_cost": supplier_cost,
                "margin_pct": margin_pct,
            }
        )
    return pd.DataFrame(rows)


class PricePredictionPipelineTests(unittest.TestCase):
    def test_data_loader_queries_backend_product_tables(self):
        self.assertIn("FROM products p", _PRODUCT_PRICE_QUERY)
        self.assertIn("JOIN categories c", _PRODUCT_PRICE_QUERY)
        self.assertIn("JOIN subcategories sc", _PRODUCT_PRICE_QUERY)
        self.assertIn("FROM order_items oi", _PRODUCT_PRICE_QUERY)
        self.assertIn("FROM user_interactions ui", _PRODUCT_PRICE_QUERY)
        self.assertIn("FROM reviews r", _PRODUCT_PRICE_QUERY)
        self.assertIn("FROM cart_items ci", _PRODUCT_PRICE_QUERY)
        self.assertIn("FROM wishlists w", _PRODUCT_PRICE_QUERY)
        self.assertIn("avg_historical_unit_price", _PRODUCT_PRICE_QUERY)
        self.assertIn("WHERE p.price > 0", _PRODUCT_PRICE_QUERY)
        self.assertIn("WHERE p.id = :product_id", _PRODUCT_FEATURE_QUERY)
        self.assertNotIn("p.price::float AS price", _PRODUCT_FEATURE_QUERY)
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
        self.assertIn("log_total_quantity_sold", frame.columns)
        self.assertIn("demand_score", frame.columns)
        self.assertIn("conversion_rate", frame.columns)
        self.assertIn("has_sales_history", frame.columns)
        self.assertIn("demand_bucket", frame.columns)
        self.assertIn("brand_category", frame.columns)
        self.assertIn("category_subcategory", frame.columns)
        self.assertNotIn("category_id", frame.columns)
        self.assertNotIn("subcategory_id", frame.columns)
        self.assertIn(config.features.target_col, frame.columns)
        self.assertGreater(frame["tag_count"].iloc[0], 0)
        for proxy_feature in config.features.historical_price_proxy_features:
            self.assertNotIn(proxy_feature, frame.columns)
            self.assertNotIn(proxy_feature, config.features.numeric_features)

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
            for legacy_dir in ["models", "training_runs"]:
                path = tmp_dir / legacy_dir
                path.mkdir(parents=True, exist_ok=True)
                (path / "stale.txt").write_text("stale", encoding="utf-8")

            results = train_price_prediction_models(_sample_products(), config=config)

            self.assertTrue(results["published"], results.get("rejection_reason"))
            self.assertEqual(results["best_profile"], "improved")
            self.assertEqual(len(results["metrics_by_model"]), 3)
            self.assertIn(config.model.baseline_name, results["metrics_by_model"])
            self.assertIn(config.model.medium_name, results["metrics_by_model"])
            self.assertIn(config.model.strong_name, results["metrics_by_model"])
            self.assertNotEqual(config.model.baseline_name, results["best_model"])
            for metrics in results["metrics_by_model"].values():
                self.assertIn("mae", metrics)
                self.assertIn("mse", metrics)
                self.assertIn("rmse", metrics)
                self.assertIn("r2", metrics)
                self.assertIn("mape", metrics)

            self.assertTrue((config.models_dir / "best_model.pkl").exists())
            self.assertTrue((config.models_dir / "preprocessing_pipeline.pkl").exists())
            self.assertFalse((config.models_dir / f"improved_{config.model.baseline_name}.pkl").exists())
            self.assertTrue((config.metadata_dir / "metadata.json").exists())
            self.assertTrue((config.metadata_dir / "feature_list.json").exists())
            self.assertTrue((config.raw_data_dir / "products_price_raw.csv").exists())
            self.assertTrue((config.processed_data_dir / "products_price_preprocessed.csv").exists())
            self.assertTrue((config.reports_dir / "model_comparison.csv").exists())
            self.assertTrue((config.reports_dir / "metrics_report.json").exists())
            self.assertTrue((config.reports_dir / "preprocessing_report.json").exists())
            self.assertTrue((config.plots_dir / "price_distribution.png").exists())
            self.assertTrue((config.plots_dir / "feature_correlation.png").exists())
            self.assertTrue((config.plots_dir / "actual_vs_predicted_price.png").exists())
            self.assertTrue((config.plots_dir / "model_performance_comparison.png").exists())
            self.assertFalse((tmp_dir / "models").exists())
            self.assertFalse((tmp_dir / "training_runs").exists())

            metadata = json.loads((config.metadata_dir / "metadata.json").read_text(encoding="utf-8"))
            self.assertIn("train_metrics", metadata)
            self.assertEqual(metadata["artifact_schema_version"], "latest-valid-v4")
            self.assertTrue(metadata["production_ready"])
            self.assertTrue(metadata["published"])
            self.assertIn("best_preprocessing_strategy", metadata)
            self.assertIn("data_quality_report", metadata)
            self.assertEqual(metadata["feature_columns"], feature_columns(config, "improved"))
            self.assertEqual(
                json.loads((config.metadata_dir / "feature_list.json").read_text(encoding="utf-8")),
                feature_columns(config, "improved"),
            )
            self.assertEqual(metadata["split_strategy"]["type"], "time_aware_product_created_at")
            for proxy_feature in config.features.historical_price_proxy_features:
                self.assertNotIn(proxy_feature, metadata["feature_columns"])

            payload = _sample_products().iloc[0].drop(labels=["price"]).to_dict()
            payload.pop("product_id")
            prediction = predict_price(payload, config=config)

            self.assertGreaterEqual(prediction["predicted_price"], 0)
            self.assertEqual(prediction["model_name"], config.price_model_name)
            self.assertEqual(prediction["model_version"], config.price_model_version)
            self.assertEqual(prediction["preprocessing_profile"], "improved")
            self.assertEqual(prediction["preprocessing_strategy"], metadata["best_preprocessing_strategy"])
            self.assertIn("features_used", prediction)

    def test_prediction_hides_legacy_metadata_metrics(self):
        with _workspace_tempdir() as tmp_dir:
            config = _config(tmp_dir)
            results = train_price_prediction_models(_sample_products(), config=config)
            metadata_path = config.metadata_dir / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            best_key = results["best_model"]
            metadata["best_result_key"] = f"improved__{best_key}"
            metadata["metrics"] = {
                "legacy__linear_regression": {"mae": 999, "mse": 999, "rmse": 999, "r2": -99, "mape": 999},
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

    def test_prediction_rejects_stale_feature_metadata(self):
        with _workspace_tempdir() as tmp_dir:
            config = _config(tmp_dir)
            train_price_prediction_models(_sample_products(), config=config)
            metadata_path = config.metadata_dir / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["feature_columns"] = metadata["feature_columns"] + ["stale_feature"]
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

            payload = _sample_products().iloc[0].drop(labels=["price", "product_id"]).to_dict()
            with self.assertRaisesRegex(RuntimeError, "stale or incompatible"):
                predict_price(payload, config=config)

    def test_production_gate_requires_positive_r2_and_baseline_improvement(self):
        config = Config()
        results = {
            config.model.baseline_name: {
                "metrics": {"rmse": 100.0, "mae": 50.0, "r2": 0.10},
                "diagnostics": {},
            },
            config.model.medium_name: {
                "metrics": {"rmse": 90.0, "mae": 55.0, "r2": 0.20},
                "diagnostics": {},
            },
            config.model.strong_name: {
                "metrics": {"rmse": 80.0, "mae": 60.0, "r2": -0.01},
                "diagnostics": {},
            },
        }

        passed, reasons = production_gate(config.model.medium_name, results, config.model.baseline_name, config)
        self.assertTrue(passed, reasons)
        passed, reasons = production_gate(config.model.strong_name, results, config.model.baseline_name, config)
        self.assertFalse(passed)
        self.assertIn("test_r2_not_positive", reasons)

    def test_rejected_training_without_previous_artifact_does_not_create_empty_artifact(self):
        with _workspace_tempdir() as tmp_dir:
            config = _config(tmp_dir)
            shutil.rmtree(tmp_dir)
            config.model.minimum_publish_r2 = 999.0

            results = train_price_prediction_models(_sample_products(), config=config)

            self.assertFalse(results["published"])
            self.assertTrue((tmp_dir / "reports" / "latest_rejection_report.json").exists())
            self.assertFalse((tmp_dir / "model" / "best_model.pkl").exists())
            self.assertFalse((tmp_dir.parent / ".staging").exists())

    def test_price_prediction_request_requires_complete_payload_without_product_id(self):
        from pydantic import ValidationError
        from ml.api.schemas import PricePredictionRequest

        with self.assertRaises(ValidationError):
            PricePredictionRequest(title="Only a title")

        self.assertEqual(PricePredictionRequest(product_id=10).product_id, 10)
        complete = PricePredictionRequest(
            brand="Acme",
            category_name="Phones",
            subcategory_name="Smartphones",
            discount_percent=10,
            rating_avg=4.2,
            review_count=12,
            stock=20,
        )
        self.assertEqual(complete.brand, "Acme")

    def test_leakage_exclusion_rules(self):
        config = Config()
        cols = feature_columns(config, "improved")
        self.assertNotIn("supplier_cost", cols)
        self.assertNotIn("margin_pct", cols)
        
    def test_gate_realism_and_overfitting_checks(self):
        config = Config()
        results = {
            config.model.baseline_name: {
                "metrics": {"rmse": 10.0, "mae": 5.0, "r2": 0.50},
                "diagnostics": {"r2_gap": 0.05},
            },
            config.model.medium_name: {
                "metrics": {"rmse": 8.0, "mae": 4.0, "r2": 0.60},
                "diagnostics": {"r2_gap": 0.40}, # Exceeds 0.35 threshold
            }
        }
        passed, reasons = production_gate(config.model.medium_name, results, config.model.baseline_name, config)
        self.assertFalse(passed)
        self.assertIn("overfitting_gap_exceeded", reasons)
        
    def test_residual_analysis_and_realism_presence_in_results(self):
        with _workspace_tempdir() as tmp_dir:
            config = _config(tmp_dir)
            results = train_price_prediction_models(_sample_products(), config=config)
            self.assertTrue(results["published"])
            
            metadata = results["metadata"]
            self.assertIn("residual_analysis", metadata)
            self.assertIn("realism_check", metadata)
            
            baseline_res = metadata["residual_analysis"][config.model.baseline_name]
            self.assertIn("residuals_summary", baseline_res)
            self.assertIn("error_by_segment", baseline_res)
            
            baseline_realism = metadata["realism_check"][config.model.baseline_name]
            self.assertIn("max_training_price", baseline_realism)
            self.assertIn("unrealistic_count", baseline_realism)


if __name__ == "__main__":
    unittest.main()
