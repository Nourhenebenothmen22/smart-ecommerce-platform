import os
from dotenv import load_dotenv

load_dotenv()

class settings:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5433"))
    DB_NAME = os.getenv("DB_NAME", "ecommerce_ml_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASS = os.getenv("DB_PASS", "postgres")

    @property
    def database_url(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def db_config_dict(self):
        return {
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "database": self.DB_NAME,
            "user": self.DB_USER,
            "password": self.DB_PASS,
        }

settings = settings()
