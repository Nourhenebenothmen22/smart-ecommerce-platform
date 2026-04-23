"""
Database connection pool with consistent port configuration.

Uses environment variables with defaults matching docker-compose.yml (port 5433).
No silent port fallback — fails explicitly if the configured port is wrong.
"""
import logging
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import os
import contextlib

logger = logging.getLogger(__name__)

# Single source of truth for DB config — matches docker-compose.yml defaults
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5433")  # docker-compose maps 5433:5432
DB_NAME = os.environ.get("DB_NAME", "ecommerce_ml_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")

_pool = None


def _init_pool():
    """Initialize the connection pool. Logs clearly on success or failure."""
    global _pool
    try:
        _pool = SimpleConnectionPool(
            1, 10,
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        logger.info(f"Database pool initialized: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    except Exception as e:
        logger.error(f"Database pool failed to initialize on {DB_HOST}:{DB_PORT}/{DB_NAME}: {e}")
        _pool = None


# Initialize on module load
_init_pool()


@contextlib.contextmanager
def get_db_cursor(commit=False):
    """
    Context manager to get a cursor from the connection pool.

    Usage:
        with get_db_cursor(commit=True) as cur:
            cur.execute("INSERT ...")

    Raises:
        Exception: If the DB pool is not initialized.
    """
    if not _pool:
        raise Exception(
            f"DB Pool not initialized. Check connection to {DB_HOST}:{DB_PORT}/{DB_NAME}. "
            f"Ensure PostgreSQL is running and environment variables are correct."
        )

    conn = _pool.getconn()
    cur = None
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database operation failed: {e}")
        raise
    finally:
        if cur:
            cur.close()
        _pool.putconn(conn)
