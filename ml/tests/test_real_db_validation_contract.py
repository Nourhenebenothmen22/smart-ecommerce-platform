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

    def test_validation_artifacts_are_versioned_and_non_destructive(self):
        source = inspect.getsource(real_db_validation.create_validation_artifacts)

        self.assertIn("artifacts", source)
        self.assertIn("validation", source)
        self.assertIn("_timestamp()", source)
        self.assertIn("exist_ok=False", source)
        self.assertIn("SEGMENTATION_MODEL_NAME", source)
        self.assertIn("PRICE_MODEL_NAME", source)

    def test_validation_checks_leakage_drift_and_real_targets(self):
        source = inspect.getsource(real_db_validation)

        self.assertIn("train_test_overlap_count", source)
        self.assertIn("forbidden_features_present", source)
        self.assertIn("drift_check", source)
        self.assertIn("real_database_price", source)
        self.assertIn("products.price", source)
        self.assertIn("user_features", source)


if __name__ == "__main__":
    unittest.main()

