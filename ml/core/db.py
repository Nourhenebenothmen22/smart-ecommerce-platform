"""
Database connection helpers for ML services.

The pool is initialized lazily so tests and CLI utilities can import ML modules
without opening a PostgreSQL connection immediately.
"""
import contextlib
import logging

from psycopg2.pool import SimpleConnectionPool

from .config import settings

logger = logging.getLogger(__name__)

_pool: SimpleConnectionPool | None = None


def _init_pool() -> SimpleConnectionPool | None:
    global _pool
    try:
        _pool = SimpleConnectionPool(
            1,
            10,
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASS,
            port=settings.DB_PORT,
        )
        logger.info(
            "Database pool initialized: %s@%s:%s/%s",
            settings.DB_USER,
            settings.DB_HOST,
            settings.DB_PORT,
            settings.DB_NAME,
        )
    except Exception as exc:
        logger.error(
            "Database pool failed to initialize on %s:%s/%s: %s",
            settings.DB_HOST,
            settings.DB_PORT,
            settings.DB_NAME,
            exc,
        )
        _pool = None
    return _pool


def get_pool() -> SimpleConnectionPool | None:
    return _pool or _init_pool()


@contextlib.contextmanager
def get_db_cursor(commit: bool = False):
    """
    Yield a PostgreSQL cursor from the shared connection pool.
    """
    pool = get_pool()
    if not pool:
        raise RuntimeError(
            f"DB pool not initialized. Check {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME} "
            "and the DB_HOST/DB_PORT/DB_NAME or POSTGRES_* environment variables."
        )

    conn = pool.getconn()
    cur = None
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("Database operation failed: %s", exc)
        raise
    finally:
        if cur:
            cur.close()
        pool.putconn(conn)


def close_pool() -> None:
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
