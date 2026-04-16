import json
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from tqdm import tqdm
import psycopg2

from .config import (
    fake, DEFAULT_PASSWORD_HASH, INTERACTION_TYPES, 
    ORDER_STATUSES, PAYMENT_STATUSES, PAYMENT_METHODS
)
from .catalog import CATALOG
from .helpers import (
    make_unique_slug, money, random_bool, random_tags, 
    random_past_datetime, random_datetime_after, generate_thumbnail, 
    generate_product_images
)
from .generators import (
    generate_product_title, generate_product_description, 
    generate_review
)

# =========================================================
# UTILITIES
# =========================================================

def get_existing_ids(cursor, table_name):
    allowed_tables = {
        "users", "products", "categories", "subcategories",
        "reviews", "orders", "payments", "wishlists",
        "cart_items", "recommendations", "product_embeddings",
        "audit_logs", "voice_confirmations", "review_analysis",
        "user_interactions", "order_items",
        "user_features", "user_segments", "ml_models", "user_sessions"
    }
    if table_name not in allowed_tables:
        raise ValueError(f"Unauthorized table query: {table_name}")
    cursor.execute(f"SELECT id FROM {table_name}")
    return [row[0] for row in cursor.fetchall()]

def get_product_lookup(cursor):
    cursor.execute("""
        SELECT id, category_id, subcategory_id, final_price, title
        FROM products
    """)
    return cursor.fetchall()

def refresh_product_rating(cursor, product_id):
    cursor.execute("""
        SELECT COALESCE(AVG(rating), 0), COUNT(*)
        FROM reviews
        WHERE product_id = %s
    """, (product_id,))
    avg_rating, count_reviews = cursor.fetchone()
    cursor.execute("""
        UPDATE products
        SET rating_avg = ROUND(CAST(%s AS numeric), 2),
            review_count = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (avg_rating, count_reviews, product_id))

def update_all_product_ratings(cursor, conn):
    cursor.execute("SELECT id FROM products")
    product_ids = [row[0] for row in cursor.fetchall()]
    for pid in tqdm(product_ids, desc="Refreshing product aggregates"):
        refresh_product_rating(cursor, pid)
    conn.commit()

# =========================================================
# CORE SEEDING
# =========================================================

def clear_tables(cursor, conn):
    print("[RESET MODE] Wiping out existing Data... Please wait.")
    tables_to_truncate = [
        "user_segments", "user_features", "ml_models", "user_sessions",
        "audit_logs", "voice_confirmations", "wishlists",
        "product_embeddings", "review_analysis", "recommendations",
        "user_interactions", "payments", "order_items", "orders",
        "cart_items", "reviews", "users", "products",
        "subcategories", "categories"
    ]
    for table in tables_to_truncate:
        try:
            cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
            conn.commit()
        except psycopg2.Error:
            conn.rollback()

def get_or_create_categories_and_subcategories(cursor, conn):
    category_ids = {}
    subcategory_ids = {}
    subcategory_to_category = {}

    print("Provisioning Categories & Subcategories...")
    for category_name in CATALOG.keys():
        display_name = category_name.replace("_", " ").title()
        slug = category_name.replace("_", "-")
        description = f"High quality {display_name} section."
        cursor.execute("""
            INSERT INTO categories (name, slug, description, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (slug) DO NOTHING
        """, (display_name, slug, description))
    conn.commit()

    cursor.execute("SELECT id, slug FROM categories")
    for cid, slug in cursor.fetchall():
        category_ids[slug.replace("-", "_")] = cid

    for cat, sub_map in CATALOG.items():
        for sub in sub_map.keys():
            display_name = sub.replace("_", " ").title()
            slug = sub.replace("_", "-")
            description = f"Greatest collection of {display_name}."
            cursor.execute("""
                INSERT INTO subcategories (name, slug, category_id, description, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (slug) DO NOTHING
            """, (display_name, slug, category_ids[cat], description))
            subcategory_to_category[sub] = cat
    conn.commit()

    cursor.execute("SELECT id, slug FROM subcategories")
    for sid, slug in cursor.fetchall():
        subcategory_ids[slug.replace("-", "_")] = sid

    return category_ids, subcategory_ids, subcategory_to_category

def seed_users(cursor, conn, n_users):
    user_ids = []
    user_signup_dates = {}
    for _ in tqdm(range(n_users), desc="Pouring Users"):
        first_name = fake.first_name(); last_name = fake.last_name()
        email = f"{uuid.uuid4().hex[:8]}_{fake.unique.email()}"
        signup_date = random_past_datetime(min_days_ago=1, max_days_ago=540)
        cursor.execute("""
            INSERT INTO users
            (first_name, last_name, email, password_hash, phone, address_line,
             city, postal_code, country, role, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (first_name, last_name, email, DEFAULT_PASSWORD_HASH, fake.phone_number()[:30], 
              fake.address()[:100], fake.city()[:100], fake.postcode()[:20], fake.country()[:100],
              random.choice(["customer", "customer", "customer", "customer", "admin", "manager"]),
              random_bool(0.95), signup_date, signup_date + timedelta(hours=random.randint(0, 48))))
        uid = cursor.fetchone()[0]
        user_ids.append(uid)
        user_signup_dates[uid] = signup_date
    conn.commit()
    return user_ids, user_signup_dates

def seed_products(cursor, conn, category_ids, subcategory_ids, subcategory_to_category, n_products):
    product_ids = []
    all_subs = list(subcategory_ids.keys())
    for _ in tqdm(range(n_products), desc="Creating Inventory"):
        sub = random.choice(all_subs); sub_id = subcategory_ids[sub]
        cat = subcategory_to_category[sub]; cat_id = category_ids[cat]
        title, brand = generate_product_title(cat, sub)
        slug = make_unique_slug(title); description = generate_product_description(cat, sub, brand, title)
        price_val = 5.0 + random.expovariate(1 / 150.0) if random.random() < 0.8 else random.uniform(500, 3999)
        price = money(min(price_val, 4999.0)); discount = random.randint(5, 40) if random.random() < 0.35 else 0
        stock = random.randint(0, 300); thumbnail = generate_thumbnail(cat, sub, title, slug)
        images = generate_product_images(cat, sub, title, slug); tags = random_tags(cat, sub, brand); is_active = random_bool(0.9)
        product_date = random_past_datetime(min_days_ago=30, max_days_ago=730)
        cursor.execute("""
            INSERT INTO products
            (title, slug, description, brand, category_id, subcategory_id,
             price, discount_percent, rating_avg, review_count,
             stock, thumbnail, images, tags, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
            RETURNING id
        """, (title[:255], slug[:280], description, brand[:120], cat_id, sub_id, price, discount, 
              Decimal("0.00"), 0, stock, thumbnail, json.dumps(images), json.dumps(tags), 
              is_active, product_date, product_date + timedelta(days=random.randint(0, 10))))
        product_ids.append(cursor.fetchone()[0])
    conn.commit()
    return product_ids

def seed_reviews(cursor, conn, product_ids, all_user_ids, subcategory_to_category, user_signup_dates):
    if not product_ids or not all_user_ids: return
    product_meta = {}
    cursor.execute("SELECT p.id, s.slug FROM products p JOIN subcategories s ON p.subcategory_id = s.id WHERE p.id = ANY(%s)", (product_ids,))
    for pid, sub_slug in cursor.fetchall():
        sub = sub_slug.replace("-", "_")
        product_meta[pid] = (subcategory_to_category[sub], sub)

    for pid in tqdm(product_ids, desc="Generating NLP Reviews"):
        n_reviews = random.randint(5, 25)
        sentiments = random.choices(["positive", "neutral", "negative"], weights=[0.65, 0.20, 0.15], k=n_reviews)
        category, subcategory = product_meta[pid]
        for sentiment in sentiments:
            text, rating = generate_review(sentiment, category, subcategory)
            user_id = random.choice(all_user_ids); verified_purchase = random_bool(0.7)
            signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
            review_date = random_datetime_after(signup_dt)
            cursor.execute("""
                INSERT INTO reviews (product_id, user_id, rating, review_text, verified_purchase, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, product_id) DO NOTHING
            """, (pid, user_id, rating, text, verified_purchase, review_date))
    conn.commit()

def seed_wishlists_and_carts(cursor, conn, user_ids, product_ids, user_signup_dates):
    for user_id in tqdm(user_ids, desc="Filling Carts & Wishlists"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        wishlist_sample = random.sample(product_ids, k=min(random.randint(1, 10), len(product_ids)))
        for pid in wishlist_sample:
            action_date = random_datetime_after(signup_dt)
            cursor.execute("INSERT INTO wishlists (user_id, product_id, created_at) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (user_id, pid, action_date))
        cart_sample = random.sample(product_ids, k=min(random.randint(1, 5), len(product_ids)))
        for pid in cart_sample:
            action_date = random_datetime_after(signup_dt)
            cursor.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity, updated_at = EXCLUDED.updated_at
            """, (user_id, pid, random.randint(1, 4), action_date, action_date + timedelta(minutes=random.randint(1, 120))))
    conn.commit()

def seed_user_interactions(cursor, conn, user_ids, product_ids, user_signup_dates):
    for user_id in tqdm(user_ids, desc="Logging Interactions"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        sampled_products = random.sample(product_ids, k=min(random.randint(8, 30), len(product_ids)))
        for pid in sampled_products:
            interaction_type = random.choice(INTERACTION_TYPES); interaction_value = Decimal(str(round(random.uniform(1, 5), 2)))
            interaction_date = random_datetime_after(signup_dt)
            cursor.execute("""
                INSERT INTO user_interactions (user_id, product_id, interaction_type, interaction_value, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, pid, interaction_type, interaction_value, interaction_date))
    conn.commit()

def seed_orders_payments_voice(cursor, conn, user_ids, product_lookup, user_signup_dates):
    product_map = {pid: (final_price, title) for pid, _, _, final_price, title in product_lookup}
    product_ids = list(product_map.keys())
    for user_id in tqdm(user_ids, desc="Fabricating Transactions"):
        nb_orders = random.randint(1, 6); signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        order_dates = sorted([random_datetime_after(signup_dt) for _ in range(nb_orders)])
        for order_date in order_dates:
            status = random.choice(ORDER_STATUSES)
            cursor.execute("""
                INSERT INTO orders (user_id, status, total_amount, payment_status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """, (user_id, status, Decimal("0.00"), "pending", order_date, order_date + timedelta(minutes=random.randint(1, 120))))
            order_id = cursor.fetchone()[0]; selected_products = random.sample(product_ids, k=min(random.randint(1, 5), len(product_ids)))
            total_amount = Decimal("0.00")
            for pid in selected_products:
                qty = random.randint(1, 3); unit_price, title = product_map[pid]; subtotal = unit_price * qty
                total_amount += subtotal
                cursor.execute("INSERT INTO order_items (order_id, product_id, product_name_snapshot, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s, %s)", (order_id, pid, title, qty, unit_price, subtotal))
            payment_status = random.choice(PAYMENT_STATUSES)
            if status == "cancelled": payment_status = random.choice(["failed", "refunded", "pending"])
            updated_at = order_date + timedelta(hours=random.randint(1, 72))
            cursor.execute("UPDATE orders SET payment_status = %s, updated_at = %s WHERE id = %s", (payment_status, updated_at, order_id))
            paid_at = random_datetime_after(order_date, updated_at) if payment_status in ["paid", "refunded"] else None
            cursor.execute("INSERT INTO payments (order_id, payment_method, amount, status, transaction_ref, paid_at, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)", (order_id, random.choice(PAYMENT_METHODS), total_amount, payment_status, str(uuid.uuid4()), paid_at, order_date))
            voice_date = order_date + timedelta(hours=random.randint(0, 24)); confirmed_at = voice_date + timedelta(minutes=random.randint(5, 120)) if random_bool() else None
            cursor.execute("INSERT INTO voice_confirmations (order_id, phone_number, call_status, transcript, confirmed, confirmed_at, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)", (order_id, fake.phone_number()[:30], random.choice(["pending", "completed", "failed", "ignored"]), fake.sentence(nb_words=12), random_bool(0.65), confirmed_at, voice_date))
    conn.commit()

def seed_recommendations(cursor, conn, user_ids, product_ids, user_signup_dates):
    if len(product_ids) < 5 or not user_ids: return
    for user_id in tqdm(user_ids, desc="AI Recommendations"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        source_products = random.sample(product_ids, k=min(5, len(product_ids)))
        for source_pid in source_products:
            rec_candidates = [p for p in product_ids if p != source_pid]; recs = random.sample(rec_candidates, k=min(3, len(rec_candidates)))
            for rec_pid in recs:
                rec_date = random_datetime_after(signup_dt)
                cursor.execute("""
                    INSERT INTO recommendations (user_id, source_product_id, recommended_product_id, score, created_at)
                    VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
                """, (user_id, source_pid, rec_pid, Decimal(str(round(random.uniform(0.50, 0.99), 4))), rec_date))
    conn.commit()

def seed_audit_logs(cursor, conn, user_ids, product_ids, n_logs):
    if not user_ids or not product_ids: return
    actions = ["create", "update", "delete", "login", "checkout", "review_posted", "add_to_wishlist", "add_to_cart"]
    entity_types = ["product", "order", "review", "payment", "user", "wishlist", "cart_item"]
    for _ in tqdm(range(n_logs), desc="Securing Audi Trails"):
        metadata = {"ip": fake.ipv4(), "user_agent": fake.user_agent(), "session_id": uuid.uuid4().hex[:16], "source": random.choice(["web", "ios_app", "android_app", "admin_dashboard"])}
        cursor.execute("INSERT INTO audit_logs (user_id, action, entity_type, entity_id, metadata, created_at) VALUES (%s, %s, %s, %s, %s::jsonb, %s)", (random.choice(user_ids), random.choice(actions), random.choice(entity_types), random.choice(product_ids), json.dumps(metadata), random_past_datetime()))
    conn.commit()

def seed_user_sessions(cursor, conn, user_ids, user_signup_dates):
    device_types = ["mobile", "desktop", "tablet"]; source_channels = ["direct", "organic", "social", "ads"]
    for user_id in tqdm(user_ids, desc="Generating User Sessions"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        session_starts = sorted([random_datetime_after(signup_dt) for _ in range(random.randint(3, 25))])
        for start_dt in session_starts:
            duration = random.choices([random.randint(1, 5), random.randint(5, 30), random.randint(30, 120)], weights=[0.3, 0.5, 0.2])[0]
            end_dt = start_dt + timedelta(minutes=duration)
            cursor.execute("INSERT INTO user_sessions (user_id, session_started_at, session_ended_at, device_type, source_channel) VALUES (%s, %s, %s, %s, %s)", (user_id, start_dt, end_dt if random.random() < 0.92 else None, random.choice(device_types), random.choice(source_channels)))
    conn.commit()

import os

def seed_user_features(cursor, conn):
    print("Computing User Features (ML Upsert)...")
    
    # Path to the SQL file relative to the ml directory
    # Note: This assumes current working directory is the ml folder or we use absolute paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_path = os.path.join(base_dir, "data", "sql", "upsert_user_features.sql")
    
    try:
        with open(sql_path, "r") as f:
            upsert_sql = f.read()
        
        cursor.execute(upsert_sql)
        conn.commit()
    except Exception as e:
        print(f"Error reading or executing SQL from {sql_path}: {e}")
        conn.rollback()
        raise
