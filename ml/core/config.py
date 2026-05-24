import os
import secrets
from urllib.parse import urlparse
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ML_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

for dotenv_path in (
    os.path.join(PROJECT_ROOT, ".env"),
    os.path.join(ML_ROOT, ".env"),
):
    load_dotenv(dotenv_path, override=False)


def _database_parts_from_url(database_url: str | None) -> dict[str, str]:
    if not database_url:
        return {}

    parsed = urlparse(database_url.replace("postgresql+psycopg2://", "postgresql://", 1))
    if parsed.scheme not in {"postgres", "postgresql"}:
        return {}

    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5433),
        "database": parsed.path.lstrip("/") or "ecommerce_ml_db",
        "user": parsed.username or "postgres",
        "password": parsed.password or "postgres",
    }


_url_parts = _database_parts_from_url(os.getenv("DATABASE_URL"))

class Settings:
    DB_HOST = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST") or _url_parts.get("host", "localhost")
    DB_PORT = int(os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT") or _url_parts.get("port", "5433"))
    DB_NAME = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB") or _url_parts.get("database", "ecommerce_ml_db")
    DB_USER = os.getenv("DB_USER") or os.getenv("POSTGRES_USER") or _url_parts.get("user", "postgres")
    DB_PASS = os.getenv("DB_PASS") or os.getenv("POSTGRES_PASSWORD") or _url_parts.get("password", "postgres")
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2")
    EMBEDDING_MODEL_VERSION = os.getenv("EMBEDDING_MODEL_VERSION", "1.0")
    SEGMENTATION_MODEL_NAME = os.getenv("SEGMENTATION_MODEL_NAME", "customer_segmentation")
    SEGMENTATION_MODEL_VERSION = os.getenv("SEGMENTATION_MODEL_VERSION", "1.0")
    PRICE_MODEL_NAME = os.getenv("PRICE_MODEL_NAME", "product_price_prediction")
    PRICE_MODEL_VERSION = os.getenv("PRICE_MODEL_VERSION", "1.0")
    ALLOW_UNVERIFIED_CHAT_USER_ID = os.getenv("ALLOW_UNVERIFIED_CHAT_USER_ID", "false").lower() == "true"
    ML_SERVICE_TOKEN = os.getenv("ML_SERVICE_TOKEN", "")

    def verify_ml_service_token(self, token: str | None) -> bool:
        return bool(self.ML_SERVICE_TOKEN) and bool(token) and secrets.compare_digest(token, self.ML_SERVICE_TOKEN)

    @property
    def database_url(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def sqlalchemy_url(self):
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def db_config_dict(self):
        return {
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "database": self.DB_NAME,
            "user": self.DB_USER,
            "password": self.DB_PASS,
        }

settings = Settings()
