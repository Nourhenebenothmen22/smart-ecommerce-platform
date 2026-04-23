import psycopg2
from psycopg2.pool import SimpleConnectionPool
import os
import contextlib

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "ecommerce_ml_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")

# Try initializing pool with typical ports
_pool = None
for port in [os.environ.get("DB_PORT", "5432"), "5433", "5432"]:
    try:
        _pool = SimpleConnectionPool(1, 10,
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=port
        )
        break
    except Exception:
        continue

if not _pool:
    # Just a placeholder if DB really is down, so app doesn't crash on boot out of context
    print("Warning: Database pool failed to initialize.")

@contextlib.contextmanager
def get_db_cursor(commit=False):
    """
    Context manager to easily get a cursor from the pool.
    Example:
        with get_db_cursor(commit=True) as cur:
            cur.execute("INSERT ...")
    """
    if not _pool:
        raise Exception("DB Pool not initialized")
        
    conn = _pool.getconn()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        _pool.putconn(conn)
