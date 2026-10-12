import os
import unittest
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    with open(_BASE_DIR / path, encoding="utf-8") as f:
        return f.read()


class SeederScriptsContractTests(unittest.TestCase):
    def test_seed_reset_recomputes_user_features(self):
        content = _read("ml/scripts/seed.py")
        self.assertIn("seed_user_features", content)
        self.assertIn("SELECT count(*) FROM user_features", content)

    def test_health_check_uses_unified_settings(self):
        content = _read("ml/scripts/health_check_db.py")
        self.assertIn("settings.db_config_dict", content)
        self.assertNotIn("ports_to_try", content)
        self.assertIn("EMBEDDING_MODEL_NAME", content)
        self.assertIn("EMBEDDING_MODEL_VERSION", content)
        self.assertIn("ML_HEALTH_MAX_MISSING_EMBEDDINGS", content)

    def test_update_images_reuses_seeder_helper(self):
        content = _read("ml/scripts/update_images.py")
        self.assertIn("build_product_image_url", content)
        self.assertIn("--dry-run", content)
        self.assertNotIn("SUBCATEGORY_KEYWORDS = {", content)

    def test_scripts_resolve_project_paths(self):
        for path in [
            "ml/scripts/seed.py",
            "ml/scripts/generate_embeddings.py",
            "ml/scripts/update_images.py",
            "ml/scripts/health_check_db.py",
        ]:
            content = _read(path)
            self.assertIn("_ML_ROOT", content)
            self.assertNotIn("os.getcwd()", content)


if __name__ == "__main__":
    unittest.main()
