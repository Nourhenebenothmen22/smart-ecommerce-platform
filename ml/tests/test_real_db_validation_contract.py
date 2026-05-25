import inspect
import unittest

from ml.validation import real_db_validation


class RealDbValidationContractTests(unittest.TestCase):
    def test_validation_uses_database_loaders_without_cached_or_hardcoded_data(self):
        source = inspect.getsource(real_db_validation)

        self.assertIn("load_and_prepare(config, force_reload=True)", source)
        self.assertIn("load_product_training_data(config, force_reload=True)", source)
        self.assertIn("hardcoded_datasets_used", source)
        self.assertIn('"cached_data_used": False', source)
        self.assertNotIn("pd.DataFrame([", source)

    def test_validation_artifacts_are_latest_only(self):
        source = inspect.getsource(real_db_validation.create_validation_artifacts)

        self.assertIn("artifacts", source)
        self.assertIn("validation", source)
        self.assertIn("latest_validation", source)
        self.assertIn("_remove_tree", source)
        self.assertIn("data\" / \"raw", source)
        self.assertIn("data\" / \"processed", source)

    def test_validation_checks_leakage_drift_and_real_targets(self):
        source = inspect.getsource(real_db_validation)

        self.assertIn("train_test_overlap_count", source)
        self.assertIn("forbidden_features_present", source)
        self.assertIn("drift_check", source)
        self.assertIn("overfitting_check", source)
        self.assertIn("real_database_price", source)
        self.assertIn("products.price", source)
        self.assertIn("user_features", source)
        self.assertIn("price_prediction_baseline", source)
        self.assertIn("price_prediction_performant", source)
        self.assertIn("signal_availability", source)
        self.assertIn("time_aware_product_created_at", source)
        self.assertIn("historical_proxy_ablation", source)
        self.assertIn("cold_start_no_sales_history", source)

    def test_price_readiness_requires_model_quality_gates(self):
        report = {
            "database_consistency": {"passed": True},
            "client_segmentation": {
                "current_rows": 100,
                "test_metrics": {"silhouette_score": 0.3},
                "leakage_check": {"passed": True},
            },
            "price_prediction": {
                "leakage_check": {"passed": True},
                "models": {
                    "price_prediction_baseline": {
                        "test": {"mae": 100.0, "rmse": 150.0, "r2": 0.1},
                        "test_by_sales_history": {
                            "with_sales_history": {"rows": 50, "metrics": {"r2": 0.1}},
                            "cold_start_no_sales_history": {"rows": 50, "metrics": {"r2": 0.1}},
                        },
                    },
                    "price_prediction_performant": {
                        "test": {"mae": 90.0, "rmse": 120.0, "r2": 0.15},
                        "test_by_sales_history": {
                            "with_sales_history": {"rows": 50, "metrics": {"r2": 0.15}},
                            "cold_start_no_sales_history": {"rows": 50, "metrics": {"r2": 0.15}},
                        },
                    },
                },
            },
        }

        not_ready = real_db_validation.build_readiness_conclusion(report)
        self.assertFalse(not_ready["production_ready"])
        self.assertFalse(not_ready["price_readiness_gate"]["minimum_test_r2"] <= not_ready["price_readiness_gate"]["actual_test_r2"])

        report["price_prediction"]["models"]["price_prediction_performant"]["test"] = {
            "mae": 80.0,
            "rmse": 100.0,
            "r2": 0.35,
        }
        report["price_prediction"]["models"]["price_prediction_performant"]["test_by_sales_history"] = {
            "with_sales_history": {"rows": 50, "metrics": {"r2": 0.35}},
            "cold_start_no_sales_history": {"rows": 50, "metrics": {"r2": 0.35}},
        }
        ready = real_db_validation.build_readiness_conclusion(report)
        self.assertTrue(ready["price_readiness_gate"]["performant_beats_baseline"])
        self.assertTrue(ready["production_ready"])


if __name__ == "__main__":
    unittest.main()
