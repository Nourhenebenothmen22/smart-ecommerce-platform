"""
Backfill product thumbnail/images using the seeder image URL strategy.
"""

import argparse
import json
import os
import sys

import psycopg2
from tqdm import tqdm

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

try:
    from ml.seeder.config import DB_CONFIG
    from ml.seeder.helpers import build_product_image_url
except ImportError:  # pragma: no cover - supports running from ml/
    from seeder.config import DB_CONFIG
    from seeder.helpers import build_product_image_url


def parse_args():
    parser = argparse.ArgumentParser(description="Backfill product image URLs.")
    parser.add_argument("--dry-run", action="store_true", help="Preview updates without writing to PostgreSQL.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of products to update.")
    return parser.parse_args()


def main():
    args = parse_args()
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT id, slug FROM categories")
        categories = {row[0]: row[1].replace("-", "_") for row in cursor.fetchall()}

        cursor.execute("SELECT id, slug FROM subcategories")
        subcategories = {row[0]: row[1].replace("-", "_") for row in cursor.fetchall()}

        query = "SELECT id, category_id, subcategory_id, title, slug FROM products ORDER BY id"
        params = ()
        if args.limit is not None:
            query += " LIMIT %s"
            params = (args.limit,)

        cursor.execute(query, params)
        products = cursor.fetchall()
        print(f"Found {len(products)} products to update.")

        updated_count = 0
        for pid, cat_id, sub_id, title, slug in tqdm(products, desc="Updating product images"):
            category = categories.get(cat_id, "default")
            subcategory = subcategories.get(sub_id, "product")
            thumbnail = build_product_image_url(category, subcategory, title, slug, "Thumbnail", 700, 700)
            images = [
                build_product_image_url(category, subcategory, title, slug, view, 900, 900)
                for view in ["Front View", "Side View", "Detail View", "Packaging"]
            ]

            if not args.dry_run:
                cursor.execute(
                    """
                    UPDATE products
                    SET thumbnail = %s, images = %s::jsonb, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (thumbnail, json.dumps(images), pid),
                )
            updated_count += 1

            if updated_count % 500 == 0 and not args.dry_run:
                conn.commit()

        if args.dry_run:
            conn.rollback()
            print(f"Dry run complete. {updated_count} products would be updated.")
        else:
            conn.commit()
            print(f"Successfully updated {updated_count} products.")

    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
