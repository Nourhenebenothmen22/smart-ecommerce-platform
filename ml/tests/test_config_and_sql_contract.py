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
        self.assertIn("EMBEDDING_BATCH_SIZE", content)
        self.assertIn("show_progress_bar=False", content)
        self.assertNotIn("model.encode(text_to_embed)", content)

    def test_ml_model_schema_matches_training_persistence(self):
        sql_path = os.path.join(os.getcwd(), "backend", "src", "sql", "006_ml_schema.sql")
        persistence_path = os.path.join(os.getcwd(), "ml", "customer_segmentation", "persistence.py")
        embeddings_path = os.path.join(os.getcwd(), "ml", "scripts", "generate_embeddings.py")

        with open(sql_path, encoding="utf-8") as f:
            sql = f.read()
        with open(persistence_path, encoding="utf-8") as f:
            persistence = f.read()
        with open(embeddings_path, encoding="utf-8") as f:
            embeddings = f.read()

        self.assertIn("is_active BOOLEAN", sql)
        self.assertIn("trained_at TIMESTAMPTZ", sql)
        self.assertIn("algorithm VARCHAR", sql)
        self.assertIn("computed_at", sql)
        self.assertIn("algorithm = EXCLUDED.algorithm", persistence)
        self.assertIn("computed_at = NOW()", persistence)
        self.assertNotIn("assigned_at", persistence)
        self.assertIn("trained_at = NOW()", embeddings)

    def test_vector_search_filters_embedding_model_version(self):
        script_path = os.path.join(os.getcwd(), "ml", "nlp", "retrieval", "vector_search.py")
        with open(script_path, encoding="utf-8") as f:
            content = f.read()

        self.assertIn("pe.model_name = %s", content)
        self.assertIn("pe.model_version = %s", content)


if __name__ == "__main__":
    unittest.main()
