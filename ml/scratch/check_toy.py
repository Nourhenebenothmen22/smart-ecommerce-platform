"""
Inspect one toy product's generated image URLs.
"""

import os
import sys

import psycopg2

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

try:
    from ml.seeder.config import DB_CONFIG
except ImportError:  # pragma: no cover - supports running from ml/
    from seeder.config import DB_CONFIG


def main():
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT title, thumbnail, images
                FROM products
                WHERE title ILIKE %s
                ORDER BY id
                LIMIT 1;
                """,
                ("%Fisher-Price%",),
            )
            row = cur.fetchone()

    if row:
        print(f"Product: {row[0]}")
        print(f"Thumbnail: {row[1]}")
        print(f"Images: {row[2]}")
    else:
        print("No Fisher-Price toy products found.")


if __name__ == "__main__":
    main()
