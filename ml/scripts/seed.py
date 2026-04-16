import argparse
import random
import psycopg2
import sys
import os

# Automatically add the current directory and the 'ml' directory to the path 
# to allow running from root or from within the ml folder.
base_ml_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_ml_dir not in sys.path:
    sys.path.append(base_ml_dir)

from seeder.config import DB_CONFIG, NB_USERS, NB_PRODUCTS, NB_AUDIT_LOGS, NB_ORDER_USERS, NB_INTERACTION_USERS
from seeder.helpers import get_user_signup_dates
from seeder.core import (
    clear_tables, get_or_create_categories_and_subcategories, seed_users, 
    seed_products, seed_reviews, seed_wishlists_and_carts, seed_user_interactions,
    seed_orders_payments_voice, seed_audit_logs, 
    update_all_product_ratings, get_existing_ids, get_product_lookup
)

def main():
    parser = argparse.ArgumentParser(description="eCommerce Mock Data Seeder - Core Business + Interactions")
    parser.add_argument("--mode", choices=["reset", "append"], default="append", 
                        help="Mode of initialization: 'reset' cleans the DB first, 'append' adds more data.")
    args = parser.parse_args()

    conn = None
    cursor = None

    try:
        print(f"\nStarting Seeder in [{args.mode.upper()}] Mode...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        if args.mode == "reset":
            clear_tables(cursor, conn)

        # 1. Base Setup
        category_ids, subcategory_ids, subcategory_to_category = get_or_create_categories_and_subcategories(cursor, conn)

        # 2. Core Entities
        user_ids, _ = seed_users(cursor, conn, NB_USERS)
        product_ids = seed_products(cursor, conn, category_ids, subcategory_ids, subcategory_to_category, NB_PRODUCTS)

        # 3. Refresh lookups for dependencies
        all_user_ids = get_existing_ids(cursor, "users")
        all_product_ids = get_existing_ids(cursor, "products")
        product_lookup = get_product_lookup(cursor)
        all_signup_dates = get_user_signup_dates(cursor)

        # 4. Behavioral & Transactional Data
        seed_reviews(cursor, conn, product_ids, all_user_ids, subcategory_to_category, all_signup_dates)
        
        interaction_users = random.sample(all_user_ids, k=min(NB_INTERACTION_USERS, len(all_user_ids)))
        order_users = random.sample(all_user_ids, k=min(NB_ORDER_USERS, len(all_user_ids)))

        seed_wishlists_and_carts(cursor, conn, all_user_ids, all_product_ids, all_signup_dates)
        seed_user_interactions(cursor, conn, interaction_users, all_product_ids, all_signup_dates)
        seed_orders_payments_voice(cursor, conn, order_users, product_lookup, all_signup_dates)
        seed_audit_logs(cursor, conn, all_user_ids, all_product_ids, NB_AUDIT_LOGS)

        # 5. Aggregates
        update_all_product_ratings(cursor, conn)

        print(f"\n--- Seeding Complete! ---")
        print(f"Total Users: {len(all_user_ids)}")
        print(f"Total Products: {len(all_product_ids)}")

    except Exception as e:
        if conn: conn.rollback()
        print(f"\nERROR during seeding: {e}")
        raise
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == "__main__":
    main()