"""
seed.py — Main entry point for the eCommerce database seeder.
Populates all business and ML-ready source data tables.

Usage:
    python -m scripts.seed --mode reset   # Wipe and re-seed everything
    python -m scripts.seed --mode append  # Add more data on top of existing
"""
import argparse
import random
import sys
import os
import time

# ── Ensure the 'ml' directory is in sys.path ──────────────
_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

import psycopg2

from seeder.config import (
    DB_CONFIG, NB_USERS, NB_PRODUCTS, NB_AUDIT_LOGS,
    NB_ORDER_USERS, NB_INTERACTION_USERS
)
from seeder.helpers import get_user_signup_dates
from seeder.core import (
    clear_tables, get_or_create_categories_and_subcategories,
    seed_users, seed_products, seed_reviews,
    seed_wishlists_and_carts, seed_user_interactions,
    seed_orders_payments_voice, seed_audit_logs,
    seed_user_sessions, update_all_product_ratings,
    get_existing_ids, get_product_lookup
)


def main():
    parser = argparse.ArgumentParser(
        description="eCommerce Mock Data Seeder — AI Training Source Data Preparation"
    )
    parser.add_argument(
        "--mode", choices=["reset", "append"], default="append",
        help="Mode: 'reset' wipes all tables first, 'append' adds more data."
    )
    args = parser.parse_args()

    conn = None
    cursor = None
    start_time = time.time()

    try:
        print(f"\n{'='*60}")
        print(f"  Starting Seeder in [{args.mode.upper()}] Mode")
        print(f"{'='*60}")

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        if args.mode == "reset":
            clear_tables(cursor, conn)

        # ── 1. Base Setup ──────────────────────────────────────────
        category_ids, subcategory_ids, subcategory_to_category = (
            get_or_create_categories_and_subcategories(cursor, conn)
        )

        # ── 2. Core Entities ───────────────────────────────────────
        user_ids, _ = seed_users(cursor, conn, NB_USERS)
        product_ids = seed_products(
            cursor, conn, category_ids, subcategory_ids,
            subcategory_to_category, NB_PRODUCTS
        )

        # ── 3. Refresh lookups for dependencies ────────────────────
        all_user_ids = get_existing_ids(cursor, "users")
        all_product_ids = get_existing_ids(cursor, "products")
        product_lookup = get_product_lookup(cursor)
        all_signup_dates = get_user_signup_dates(cursor)

        # ── 4. NLP Reviews (massive for future NLP/Sentiment) ──────
        seed_reviews(
            cursor, conn, all_product_ids, all_user_ids,
            subcategory_to_category, all_signup_dates
        )

        # ── 5. Behavioral & Transactional Data ─────────────────────
        interaction_users = random.sample(
            all_user_ids, k=min(NB_INTERACTION_USERS, len(all_user_ids))
        )
        order_users = random.sample(
            all_user_ids, k=min(NB_ORDER_USERS, len(all_user_ids))
        )

        seed_wishlists_and_carts(cursor, conn, all_user_ids, all_product_ids, all_signup_dates)
        seed_user_interactions(cursor, conn, interaction_users, all_product_ids, all_signup_dates)
        seed_orders_payments_voice(cursor, conn, order_users, product_lookup, all_signup_dates)
        seed_audit_logs(cursor, conn, all_user_ids, all_product_ids, NB_AUDIT_LOGS)

        # ── 6. ML Analytics ────────────────────────────────────────
        seed_user_sessions(cursor, conn, all_user_ids, all_signup_dates)

        # ── 7. Aggregates ──────────────────────────────────────────
        update_all_product_ratings(cursor, conn)

        # ── Summary ────────────────────────────────────────────────
        elapsed = time.time() - start_time
        cursor.execute("SELECT count(*) FROM reviews")
        total_reviews = cursor.fetchone()[0]

        print(f"\n{'='*60}")
        print(f"  Seeding Complete — AI Source Data Prepared")
        print(f"{'='*60}")
        print(f"  Total Users:    {len(all_user_ids):>8,}")
        print(f"  Total Products: {len(all_product_ids):>8,}")
        print(f"  Total Reviews:  {total_reviews:>8,}  (NLP-ready)")
        print(f"  Time Elapsed:   {elapsed:>8.1f}s")
        print(f"{'='*60}\n")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\nERROR during seeding: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    main()