import importlib
import os
import unittest


class ConfigAndSqlContractTests(unittest.TestCase):
    def test_database_url_drives_settings(self):
        env_keys = [
            "DB_HOST",
            "DB_PORT",
            "DB_NAME",
            "DB_USER",
            "DB_PASS",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
        ]
        original = {key: os.environ.get(key) for key in env_keys + ["DATABASE_URL"]}
        for key in env_keys:
            os.environ[key] = ""
        os.environ["DATABASE_URL"] = "postgresql://app:secret@db-host:5440/shop"
        config_module = importlib.reload(importlib.import_module("ml.core.config"))
        self.assertEqual(config_module.settings.DB_HOST, "db-host")
        self.assertEqual(config_module.settings.DB_PORT, 5440)
        self.assertEqual(config_module.settings.DB_NAME, "shop")
        self.assertIn("db-host:5440/shop", config_module.settings.sqlalchemy_url)
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        importlib.reload(config_module)

    def test_segmentation_features_match_user_features_table(self):
        from ml.customer_segmentation.config import cfg
        from ml.customer_segmentation.data_loader import _USER_SEGMENTATION_QUERY

        self.assertIn("FROM user_features", _USER_SEGMENTATION_QUERY)
        self.assertNotIn("v_user_behavior_features", _USER_SEGMENTATION_QUERY)
        self.assertIn("days_since_last_order", cfg.features.feature_cols)
        self.assertNotIn("recency_days", cfg.features.feature_cols)

    def test_embedding_generation_is_versioned_and_non_destructive(self):
        script_path = os.path.join(os.getcwd(), "ml", "scripts", "generate_embeddings.py")
        with open(script_path, encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn("TRUNCATE TABLE product_embeddings", content)
        self.assertNotIn("ALTER TABLE product_embeddings", content)
        self.assertIn("ON CONFLICT (product_id, model_name, model_version)", content)

    def test_vector_search_filters_embedding_model_version(self):
        script_path = os.path.join(os.getcwd(), "ml", "nlp", "retrieval", "vector_search.py")
        with open(script_path, encoding="utf-8") as f:
            content = f.read()

        self.assertIn("pe.model_name = %s", content)
        self.assertIn("pe.model_version = %s", content)


if __name__ == "__main__":
    unittest.main()
