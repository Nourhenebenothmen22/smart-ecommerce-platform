"""
count_rows.py — Utility script to display row counts for all tables in the database.
Usage: python -m scripts.count_rows
"""
import sys
import os

import psycopg2

# ── Ensure the 'ml' directory is in sys.path ──────────────
_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

from seeder.config import DB_CONFIG


def get_counts():
    """Fetch and display row counts for all tables in the public schema."""
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Get all tables in public schema
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        )
        tables = [r[0] for r in cur.fetchall()]

        counts = []
        for table in tables:
            try:
                cur.execute(f"SELECT count(*) FROM {table}")  # noqa: S608 — table names are from information_schema
                count = cur.fetchone()[0]
                counts.append((table, count))
            except psycopg2.Error:
                conn.rollback()

        # Sort by count descending
        counts.sort(key=lambda x: x[1], reverse=True)

        total = sum(c[1] for c in counts)

        print("-" * 40)
        print(f"{'Table':<25} | {'Rows':>8}")
        print("-" * 40)
        for table, count in counts:
            print(f"{table:<25} | {count:>8,}")
        print("-" * 40)
        print(f"{'TOTAL':<25} | {total:>8,}")
        print("-" * 40)

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    get_counts()
