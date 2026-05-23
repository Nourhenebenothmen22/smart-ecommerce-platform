"""
Quick PostgreSQL sanity check for local ML development.
"""

import os
import sys

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJECT_ROOT = os.path.dirname(_ML_ROOT)
for path in (_PROJECT_ROOT, _ML_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from ml.core.config import settings
from ml.core.db import get_db_cursor


def main():
    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM products")
        product_count = cur.fetchone()[0]
        cur.execute(
            """
            SELECT COUNT(*)
            FROM product_embeddings
            WHERE model_name = %s AND model_version = %s
            """,
            (settings.EMBEDDING_MODEL_NAME, settings.EMBEDDING_MODEL_VERSION),
        )
        embedding_count = cur.fetchone()[0]

        print(f"Products: {product_count}")
        print(f"Current embeddings: {embedding_count}")
        print(f"Embedding model: {settings.EMBEDDING_MODEL_NAME} v{settings.EMBEDDING_MODEL_VERSION}")

        cur.execute("SELECT title, description, price, stock FROM products ORDER BY id LIMIT 3")
        for row in cur.fetchall():
            print(f"Sample product: {row}")


if __name__ == "__main__":
    main()
