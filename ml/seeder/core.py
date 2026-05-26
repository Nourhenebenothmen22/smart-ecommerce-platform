"""
core.py — Core database seeding functions for the eCommerce ML platform.
Handles table clearing, entity creation, and data population.
"""
import json
import os
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import psycopg2
from tqdm import tqdm

from .config import (
    fake, DEFAULT_PASSWORD_HASH, INTERACTION_TYPES,
    ORDER_STATUSES, PAYMENT_STATUSES, PAYMENT_METHODS
)
from .catalog import CATALOG
from .helpers import (
    make_unique_slug, money, random_bool, random_tags,
    random_past_datetime, random_datetime_after, generate_thumbnail,
    generate_product_images, compute_product_price, value_for_money_score
)
from .generators import (
    generate_product_title, generate_product_description,
    generate_review
)

# =========================================================
# UTILITIES
# =========================================================

def get_existing_ids(cursor, table_name: str) -> list[int]:
    """Fetch all IDs from a whitelisted table."""
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
    """Fetch product info needed for order generation."""
    cursor.execute("""
        SELECT id, category_id, subcategory_id, final_price, title,
               price, brand_tier, product_tier, condition, supplier_cost
        FROM products
    """)
    return cursor.fetchall()


def refresh_product_rating(cursor, product_id: int) -> None:
    """Recalculate rating_avg and review_count for a single product."""
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


def update_all_product_ratings(cursor, conn) -> None:
    """Recalculate rating aggregates for all products."""
    cursor.execute("SELECT id FROM products")
    product_ids = [row[0] for row in cursor.fetchall()]
    for pid in tqdm(product_ids, desc="Refreshing product aggregates"):
        refresh_product_rating(cursor, pid)
    conn.commit()


def fake_e164_phone() -> str:
    """Generate a deterministic-shape phone number accepted by backend validators."""
    return f"+1{random.randint(2000000000, 9999999999)}"


# =========================================================
# CORE SEEDING FUNCTIONS
# =========================================================

def clear_tables(cursor, conn) -> None:
    """Truncate all tables in dependency-safe order."""
    print("[RESET MODE] Wiping out existing data... Please wait.")
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
    """Create categories and subcategories from the CATALOG, return ID lookups."""
    category_ids = {}
    subcategory_ids = {}
    subcategory_to_category = {}

    print("Provisioning Categories & Subcategories...")
    for category_name in CATALOG:
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
        for sub in sub_map:
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


def seed_users(cursor, conn, n_users: int):
    """Seed user accounts. Returns (user_ids, signup_dates_dict)."""
    user_ids = []
    user_signup_dates = {}
    for _ in tqdm(range(n_users), desc="Pouring Users"):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{uuid.uuid4().hex[:8]}_{fake.unique.email()}"
        signup_date = random_past_datetime(min_days_ago=1, max_days_ago=540)
        cursor.execute("""
            INSERT INTO users
            (first_name, last_name, email, password_hash, phone, address_line,
             city, postal_code, country, role, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            first_name, last_name, email, DEFAULT_PASSWORD_HASH,
            fake_e164_phone(), fake.address()[:100],
            fake.city()[:100], fake.postcode()[:20], fake.country()[:100],
            random.choice(["customer", "customer", "customer", "customer", "admin", "manager"]),
            random_bool(0.95),
            signup_date,
            signup_date + timedelta(hours=random.randint(0, 48))
        ))
        uid = cursor.fetchone()[0]
        user_ids.append(uid)
        user_signup_dates[uid] = signup_date
    conn.commit()
    return user_ids, user_signup_dates


def seed_products(cursor, conn, category_ids, subcategory_ids, subcategory_to_category, n_products: int):
    """
    Seed products with realistic, driver-based prices.
    """
    all_subs = list(subcategory_ids.keys())
    product_ids = []
    
    for _ in tqdm(range(n_products), desc="Creating Inventory"):
        sub = random.choice(all_subs)
        sub_id = subcategory_ids[sub]
        cat = subcategory_to_category[sub]
        cat_id = category_ids[cat]
        title, brand = generate_product_title(cat, sub)
        slug = make_unique_slug(title)
        description = generate_product_description(cat, sub, brand, title)
        
        # Draw attributes dynamically from the catalog
        sub_cat_data = CATALOG[cat][sub]
        brand_tier = sub_cat_data["brand_tiers"].get(brand, 2)
        
        # product_tier weights: 1=entry, 2=mid, 3=high, 4=flagship
        product_tier = random.choices([1, 2, 3, 4], weights=[0.35, 0.40, 0.18, 0.07], k=1)[0]
        
        # supplier_cost
        min_cost, max_cost = sub_cat_data["price_range"]
        tier_fraction = (product_tier - 1) / 3.0
        base_supplier = min_cost + tier_fraction * (max_cost - min_cost)
        supplier_cost = base_supplier * random.uniform(0.9, 1.1)
        supplier_cost = float(round(max(min_cost, min(max_cost, supplier_cost)), 2))
        
        # margin_pct based on brand_tier
        margin_map = {1: (15, 30), 2: (30, 45), 3: (45, 60), 4: (60, 80)}
        min_m, max_m = margin_map.get(brand_tier, (30, 45))
        margin_pct = float(round(random.uniform(min_m, max_m), 2))
        
        # condition
        condition = random.choices(["new", "refurbished", "open_box", "used"], weights=[0.70, 0.15, 0.10, 0.05], k=1)[0]
        
        # release_year
        release_year = random.randint(2020, 2026)
        
        # Calculate price based on drivers
        price_val = compute_product_price(supplier_cost, margin_pct, condition, release_year)
        price = money(price_val)
        
        discount = random.randint(5, 40) if random.random() < 0.35 else 0
        stock = random.randint(0, 300)
        thumbnail = generate_thumbnail(cat, sub, title, slug)
        images = generate_product_images(cat, sub, title, slug)
        tags = random_tags(cat, sub, brand)
        is_active = random_bool(0.9)
        product_date = random_past_datetime(min_days_ago=30, max_days_ago=730)
        
        cursor.execute("""
            INSERT INTO products
            (title, slug, description, brand, category_id, subcategory_id,
             price, discount_percent, rating_avg, review_count,
             stock, thumbnail, images, tags, is_active, created_at, updated_at,
             supplier_cost, margin_pct, brand_tier, product_tier, condition, release_year)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            title[:255], slug[:280], description, brand[:120], cat_id, sub_id,
            price, discount, Decimal("0.00"), 0, stock, thumbnail,
            json.dumps(images), json.dumps(tags), is_active,
            product_date, product_date + timedelta(days=random.randint(0, 10)),
            supplier_cost, margin_pct, brand_tier, product_tier, condition, release_year
        ))
        product_ids.append(cursor.fetchone()[0])
    conn.commit()
    return product_ids


def seed_reviews(cursor, conn, product_ids, all_user_ids, subcategory_to_category, user_signup_dates):
    """
    Seed a MASSIVE corpus of reviews for NLP/Sentiment Analysis.
    
    Strategy:
    - Each product gets 15-40 reviews for a rich NLP dataset.
    - Uses ON CONFLICT to skip duplicate (user_id, product_id) pairs.
    - Uses NULL user_id for ~20% of reviews (anonymous reviews) to bypass 
      the unique constraint and maximize total review count.
    - Sentiment distribution: influenced by brand tier, product tier, and value-for-money.
    """
    if not product_ids or not all_user_ids:
        return

    # Build product metadata lookup with price drivers
    product_meta = {}
    cursor.execute(
        "SELECT p.id, s.slug, p.price, p.brand_tier, p.product_tier, p.condition, p.supplier_cost, p.stock "
        "FROM products p "
        "JOIN subcategories s ON p.subcategory_id = s.id "
        "WHERE p.id = ANY(%s)", (product_ids,)
    )
    for pid, sub_slug, price, brand_tier, product_tier, condition, supplier_cost, stock in cursor.fetchall():
        sub = sub_slug.replace("-", "_")
        product_meta[pid] = {
            "category": subcategory_to_category[sub],
            "subcategory": sub,
            "price": float(price),
            "brand_tier": brand_tier,
            "product_tier": product_tier,
            "condition": condition,
            "supplier_cost": float(supplier_cost) if supplier_cost is not None else None,
            "stock": stock
        }

    batch_count = 0
    for pid in tqdm(product_ids, desc="Generating NLP Reviews"):
        meta = product_meta[pid]
        category = meta["category"]
        subcategory = meta["subcategory"]
        price = meta["price"]
        brand_tier = meta["brand_tier"]
        product_tier = meta["product_tier"]
        supplier_cost = meta["supplier_cost"]
        stock = meta["stock"]
        
        # Calculate Value for Money Score
        vfm = value_for_money_score(price, brand_tier, product_tier, supplier_cost)
        
        # Base weights for [positive, neutral, negative]
        w_pos, w_neu, w_neg = 0.55, 0.25, 0.20
        
        # High quality increases positive reviews
        w_pos += (brand_tier + product_tier - 4) * 0.05
        
        # Value for money adjustments
        if vfm > 1.2:
            w_pos += 0.12
            w_neg -= 0.06
        elif vfm < 0.8:
            w_neg += 0.15
            w_pos -= 0.08
            
        # Budget brand and low stock increases complaints
        if brand_tier == 1 and stock < 10:
            w_neg += 0.15
            w_pos -= 0.10
            
        # Ensure non-negative/positive weights
        w_pos = max(0.01, w_pos)
        w_neu = max(0.01, w_neu)
        w_neg = max(0.01, w_neg)
        
        total_w = w_pos + w_neu + w_neg
        weights = [w_pos / total_w, w_neu / total_w, w_neg / total_w]
        
        n_reviews = random.randint(15, 40)
        sentiments = random.choices(
            ["positive", "neutral", "negative"],
            weights=weights,
            k=n_reviews
        )

        for sentiment in sentiments:
            text, rating = generate_review(sentiment, category, subcategory)
            verified_purchase = random_bool(0.7)

            # 20% anonymous reviews (user_id=NULL) to bypass unique constraint
            if random.random() < 0.20:
                user_id = None
                review_date = random_past_datetime(min_days_ago=1, max_days_ago=365)
            else:
                user_id = random.choice(all_user_ids)
                signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
                review_date = random_datetime_after(signup_dt)

            cursor.execute("""
                INSERT INTO reviews (product_id, user_id, rating, review_text, verified_purchase, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, product_id) DO NOTHING
            """, (pid, user_id, rating, text, verified_purchase, review_date))

        batch_count += 1
        # Commit every 500 products to avoid memory bloat
        if batch_count % 500 == 0:
            conn.commit()

    conn.commit()


def seed_wishlists_and_carts(cursor, conn, user_ids, product_ids, user_signup_dates):
    """Seed wishlist and cart entries for users, making them price-dependent."""
    # Fetch product prices to compute weights
    cursor.execute("SELECT id, price FROM products")
    products_metadata = {row[0]: float(row[1]) for row in cursor.fetchall()}
    
    # Calculate weights once
    wishlist_weights = []
    cart_weights = []
    for pid in product_ids:
        price = products_metadata.get(pid, 100.0)
        
        # Expensive products are wishlisted more (aspirational)
        if price > 500.0:
            w_w = 3.0
            c_w = 0.3
        elif price > 100.0:
            w_w = 1.5
            c_w = 1.5
        elif price > 50.0:
            w_w = 0.8
            c_w = 3.0
        else:
            w_w = 0.5
            c_w = 2.0
        wishlist_weights.append(w_w)
        cart_weights.append(c_w)
        
    for user_id in tqdm(user_ids, desc="Filling Carts & Wishlists"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        
        # Sample using weights
        wishlist_sample = list(set(random.choices(product_ids, weights=wishlist_weights, k=min(random.randint(1, 15), len(product_ids)))))[:random.randint(1, 10)]
        for pid in wishlist_sample:
            action_date = random_datetime_after(signup_dt)
            cursor.execute(
                "INSERT INTO wishlists (user_id, product_id, created_at) "
                "VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (user_id, pid, action_date)
            )
            
        cart_sample = list(set(random.choices(product_ids, weights=cart_weights, k=min(random.randint(1, 8), len(product_ids)))))[:random.randint(1, 5)]
        for pid in cart_sample:
            action_date = random_datetime_after(signup_dt)
            cursor.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity,
                             updated_at = EXCLUDED.updated_at
            """, (
                user_id, pid, random.randint(1, 4),
                action_date,
                action_date + timedelta(minutes=random.randint(1, 120))
            ))
    conn.commit()


def seed_user_interactions(cursor, conn, user_ids, product_ids, user_signup_dates):
    """Seed user interaction events (views, clicks, cart adds, etc.) depending on price drivers."""
    # Fetch product metadata
    cursor.execute("SELECT id, price, brand_tier, discount_percent FROM products")
    products_metadata = {
        row[0]: {
            "price": float(row[1]),
            "brand_tier": row[2],
            "discount_percent": row[3]
        }
        for row in cursor.fetchall()
    }
    
    for user_id in tqdm(user_ids, desc="Logging Interactions"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        sampled_products = random.sample(product_ids, k=min(random.randint(8, 30), len(product_ids)))
        for pid in sampled_products:
            meta = products_metadata.get(pid, {"brand_tier": 2, "discount_percent": 0, "price": 100.0})
            brand_tier = meta["brand_tier"]
            discount_percent = meta["discount_percent"]
            
            # Base weights for: ["view", "click", "add_to_cart", "add_to_wishlist", "purchase", "share", "search"]
            weights = {
                "view": 0.40,
                "click": 0.25,
                "add_to_cart": 0.12,
                "add_to_wishlist": 0.08,
                "purchase": 0.05,
                "share": 0.04,
                "search": 0.06
            }
            
            # Adjust weights based on brand_tier
            if brand_tier >= 3:
                # Premium/Luxury brands get more views/searches/shares but fewer purchases
                weights["view"] += 0.15
                weights["search"] += 0.05
                weights["share"] += 0.03
                weights["purchase"] = max(0.005, weights["purchase"] - 0.03)
            elif brand_tier == 1:
                # Budget brands get fewer views/clicks but higher conversion
                weights["view"] = max(0.10, weights["view"] - 0.15)
                weights["click"] = max(0.10, weights["click"] - 0.05)
                weights["purchase"] += 0.10
                
            # Discounted products get more cart adds
            if discount_percent > 0:
                weights["add_to_cart"] += 0.15
                weights["click"] += 0.05
                
            # Normalize
            type_list = list(weights.keys())
            weight_list = [weights[t] for t in type_list]
            total_w = sum(weight_list)
            weight_list = [w / total_w for w in weight_list]
            
            interaction_type = random.choices(type_list, weights=weight_list, k=1)[0]
            interaction_value = Decimal(str(round(random.uniform(1, 5), 2)))
            interaction_date = random_datetime_after(signup_dt)
            cursor.execute("""
                INSERT INTO user_interactions (user_id, product_id, interaction_type, interaction_value, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, pid, interaction_type, interaction_value, interaction_date))
    conn.commit()


def seed_orders_payments_voice(cursor, conn, user_ids, product_lookup, user_signup_dates):
    """Seed orders, payments, and voice confirmations."""
    # product_map fields: pid: (final_price, title, price, brand_tier, product_tier, condition, supplier_cost)
    product_map = {
        row[0]: (
            row[3], # final_price
            row[4], # title
            float(row[5]) if row[5] is not None else 0.0, # price
            row[6], # brand_tier
            row[7], # product_tier
            row[8], # condition
            float(row[9]) if row[9] is not None else 0.0 # supplier_cost
        )
        for row in product_lookup
    }
    product_ids = list(product_map.keys())
    
    # Calculate purchase weights based on price
    purchase_weights = []
    for pid in product_ids:
        final_price, _, price, _, _, _, _ = product_map[pid]
        p_val = float(final_price)
        if p_val > 500.0:
            w = 0.4
        elif p_val > 100.0:
            w = 1.5
        elif p_val > 50.0:
            w = 2.5
        else:
            w = 4.0
        purchase_weights.append(w)
        
    for user_id in tqdm(user_ids, desc="Fabricating Transactions"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        
        # Cheaper products mean more orders per user
        nb_orders = random.randint(1, 6)
        order_dates = sorted([random_datetime_after(signup_dt) for _ in range(nb_orders)])
        
        for order_date in order_dates:
            # We will sample products first to determine the total price and cancellation probability
            selected_products = list(set(random.choices(product_ids, weights=purchase_weights, k=min(random.randint(1, 5), len(product_ids)))))[:random.randint(1, 4)]
            if not selected_products:
                continue
                
            total_amount = Decimal("0.00")
            for pid in selected_products:
                # Expensive products are bought in smaller quantities
                final_price_val, _, price, _, _, _, _ = product_map[pid]
                p_val = float(final_price_val)
                if p_val > 500.0:
                    qty = 1
                elif p_val > 100.0:
                    qty = random.randint(1, 2)
                else:
                    qty = random.randint(1, 4)
                
                unit_price = final_price_val
                subtotal = unit_price * qty
                total_amount += subtotal
                
            # Order cancellation rate increases with price
            total_amount_val = float(total_amount)
            cancellation_prob = 0.08
            if total_amount_val > 1000.0:
                cancellation_prob = 0.35
            elif total_amount_val > 400.0:
                cancellation_prob = 0.22
            elif total_amount_val > 100.0:
                cancellation_prob = 0.12
                
            if random.random() < cancellation_prob:
                status = "cancelled"
            else:
                non_cancelled = [s for s in ORDER_STATUSES if s != "cancelled"]
                status = random.choice(non_cancelled)
                
            cursor.execute("""
                INSERT INTO orders (user_id, status, total_amount, payment_status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                user_id, status, total_amount, "pending",
                order_date, order_date + timedelta(minutes=random.randint(1, 120))
            ))
            order_id = cursor.fetchone()[0]
            
            # Now insert the selected product items
            for pid in selected_products:
                final_price_val, title, price, _, _, _, _ = product_map[pid]
                p_val = float(final_price_val)
                if p_val > 500.0:
                    qty = 1
                elif p_val > 100.0:
                    qty = random.randint(1, 2)
                else:
                    qty = random.randint(1, 4)
                unit_price = final_price_val
                subtotal = unit_price * qty
                cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, product_name_snapshot, quantity, unit_price, subtotal) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (order_id, pid, title, qty, unit_price, subtotal)
                )
                
            payment_status = random.choice(PAYMENT_STATUSES)
            if status == "cancelled":
                payment_status = random.choice(["failed", "refunded", "pending"])
            updated_at = order_date + timedelta(hours=random.randint(1, 72))
            cursor.execute(
                "UPDATE orders SET payment_status = %s, updated_at = %s WHERE id = %s",
                (payment_status, updated_at, order_id)
            )
            paid_at = random_datetime_after(order_date, updated_at) if payment_status in ["paid", "refunded"] else None
            cursor.execute(
                "INSERT INTO payments (order_id, payment_method, amount, status, transaction_ref, paid_at, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (order_id, random.choice(PAYMENT_METHODS), total_amount, payment_status, str(uuid.uuid4()), paid_at, order_date)
            )
            voice_date = order_date + timedelta(hours=random.randint(0, 24))
            confirmed_at = voice_date + timedelta(minutes=random.randint(5, 120)) if random_bool() else None
            cursor.execute(
                "INSERT INTO voice_confirmations (order_id, phone_number, call_status, transcript, confirmed, confirmed_at, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (order_id, fake_e164_phone(),
                 random.choice(["pending", "completed", "failed", "cancelled"]),
                 fake.sentence(nb_words=12), random_bool(0.65), confirmed_at, voice_date)
            )
    conn.commit()


def seed_recommendations(cursor, conn, user_ids, product_ids, user_signup_dates):
    """Seed product recommendations."""
    if len(product_ids) < 5 or not user_ids:
        return
    for user_id in tqdm(user_ids, desc="AI Recommendations"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        source_products = random.sample(product_ids, k=min(5, len(product_ids)))
        for source_pid in source_products:
            rec_candidates = [p for p in product_ids if p != source_pid]
            recs = random.sample(rec_candidates, k=min(3, len(rec_candidates)))
            for rec_pid in recs:
                rec_date = random_datetime_after(signup_dt)
                cursor.execute("""
                    INSERT INTO recommendations (user_id, source_product_id, recommended_product_id, score, created_at)
                    VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
                """, (user_id, source_pid, rec_pid, Decimal(str(round(random.uniform(0.50, 0.99), 4))), rec_date))
    conn.commit()


def seed_audit_logs(cursor, conn, user_ids, product_ids, n_logs: int):
    """Seed audit trail entries."""
    if not user_ids or not product_ids:
        return
    actions = ["create", "update", "delete", "login", "checkout", "review_posted", "add_to_wishlist", "add_to_cart"]
    entity_types = ["product", "order", "review", "payment", "user", "wishlist", "cart_item"]
    for _ in tqdm(range(n_logs), desc="Securing Audit Trails"):
        metadata = {
            "ip": fake.ipv4(),
            "user_agent": fake.user_agent(),
            "session_id": uuid.uuid4().hex[:16],
            "source": random.choice(["web", "ios_app", "android_app", "admin_dashboard"])
        }
        cursor.execute(
            "INSERT INTO audit_logs (user_id, action, entity_type, entity_id, metadata, created_at) "
            "VALUES (%s, %s, %s, %s, %s::jsonb, %s)",
            (random.choice(user_ids), random.choice(actions), random.choice(entity_types),
             random.choice(product_ids), json.dumps(metadata), random_past_datetime())
        )
    conn.commit()


def seed_user_sessions(cursor, conn, user_ids, user_signup_dates):
    """Seed user browsing session data."""
    device_types = ["mobile", "desktop", "tablet"]
    source_channels = ["direct", "organic", "social", "ads"]
    for user_id in tqdm(user_ids, desc="Generating User Sessions"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        session_starts = sorted([random_datetime_after(signup_dt) for _ in range(random.randint(3, 25))])
        for start_dt in session_starts:
            duration = random.choices(
                [random.randint(1, 5), random.randint(5, 30), random.randint(30, 120)],
                weights=[0.3, 0.5, 0.2]
            )[0]
            end_dt = start_dt + timedelta(minutes=duration)
            cursor.execute(
                "INSERT INTO user_sessions (user_id, session_started_at, session_ended_at, device_type, source_channel) "
                "VALUES (%s, %s, %s, %s, %s)",
                (user_id, start_dt, end_dt if random.random() < 0.92 else None,
                 random.choice(device_types), random.choice(source_channels))
            )
    conn.commit()


def seed_user_features(cursor, conn) -> None:
    """Compute and upsert user feature vectors from the SQL script."""
    print("Computing User Features (ML Upsert)...")
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
