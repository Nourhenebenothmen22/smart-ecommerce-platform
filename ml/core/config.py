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
    APP_ENV = (os.getenv("APP_ENV") or os.getenv("NODE_ENV") or "development").lower()
    IS_PRODUCTION = APP_ENV in {"prod", "production"}
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
    ML_REQUIRE_SERVICE_TOKEN = (
        os.getenv("ML_REQUIRE_SERVICE_TOKEN", "true" if IS_PRODUCTION else "false").lower() == "true"
    )
    ML_CHAT_RATE_LIMIT_PER_MINUTE = int(os.getenv("ML_CHAT_RATE_LIMIT_PER_MINUTE", "120"))
    ML_PRICE_RATE_LIMIT_PER_MINUTE = int(os.getenv("ML_PRICE_RATE_LIMIT_PER_MINUTE", "60"))
    ML_ALLOW_MODEL_DOWNLOADS = os.getenv("ML_ALLOW_MODEL_DOWNLOADS", "false").lower() == "true"
    ML_ENABLE_LLM_CALLS = os.getenv("ML_ENABLE_LLM_CALLS", "true").lower() == "true"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))

    def verify_ml_service_token(self, token: str | None) -> bool:
        return bool(self.ML_SERVICE_TOKEN) and bool(token) and secrets.compare_digest(token, self.ML_SERVICE_TOKEN)

    def production_config_errors(self) -> list[str]:
        errors: list[str] = []
        if self.IS_PRODUCTION and not self.ML_SERVICE_TOKEN:
            errors.append("ML_SERVICE_TOKEN is required when APP_ENV=production.")
        if self.IS_PRODUCTION and self.DB_PASS in {"", "postgres"}:
            errors.append("A non-default PostgreSQL password is required when APP_ENV=production.")
        return errors

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
