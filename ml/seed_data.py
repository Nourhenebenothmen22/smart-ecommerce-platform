import random
import uuid
import json
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import quote
import sys
import os

import psycopg2
from faker import Faker
from tqdm import tqdm


# =========================================================
# CONFIG
# =========================================================
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "ecommerce_ml_db",
    "user": "postgres",
    "password": "postgres",
}

# Settings for Generation
NB_PRODUCTS = 5000
NB_USERS = 1500
NB_AUDIT_LOGS = 5000
NB_EMBEDDINGS = 3000
NB_RECOMMENDATION_USERS = 1000
NB_ORDER_USERS = 1200
NB_INTERACTION_USERS = 1400

RANDOM_SEED = 42

if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)
    Faker.seed(RANDOM_SEED)

fake = Faker()


# =========================================================
# DATA CATALOG
# =========================================================
CATALOG = {
    "electronics": {
        "smartphones": {
            "brands": ["Apple", "Samsung", "Xiaomi", "OnePlus", "Huawei", "Google", "Oppo", "Sony", "Nokia"],
            "name_parts": ["Pro", "Max", "Lite", "Ultra", "Edge", "Plus", "Neo", "Prime", "Fold", "Flip"],
            "features": ["battery life", "camera", "screen quality", "performance", "charging speed", "build quality", "AI features"],
        },
        "laptops": {
            "brands": ["Dell", "HP", "Lenovo", "Asus", "Acer", "MSI", "Apple", "Razer", "Microsoft"],
            "name_parts": ["Book", "Air", "Pro", "Flex", "Think", "Studio", "Slim", "Core", "Zen", "Spectre"],
            "features": ["keyboard", "performance", "OLED screen", "battery life", "cooling system", "build quality", "weight"],
        },
        "tablets": {
            "brands": ["Apple", "Samsung", "Lenovo", "Huawei", "Xiaomi", "Amazon"],
            "name_parts": ["Tab", "Pad", "Air", "Mini", "Pro", "Go", "Fire"],
            "features": ["screen resolution", "battery life", "portability", "performance", "pencil support"],
        },
        "headphones": {
            "brands": ["Sony", "JBL", "Bose", "Apple", "Samsung", "Anker", "Logitech", "Sennheiser", "Audio-Technica"],
            "name_parts": ["Sound", "Beat", "Air", "Pods", "Studio", "Wave", "Tune", "Quiet", "Momentum"],
            "features": ["sound quality", "comfort", "battery life", "noise cancellation", "design", "mic quality"],
        },
        "cameras": {
            "brands": ["Canon", "Nikon", "Sony", "Fujifilm", "Panasonic", "GoPro", "DJI"],
            "name_parts": ["Shot", "Zoom", "Vision", "Capture", "Snap", "Focus", "Alpha"],
            "features": ["image quality", "zoom", "autofocus speed", "battery life", "video stabilization", "low light capability"],
        },
    },
    "beauty": {
        "skincare": {
            "brands": ["Cerave", "Vichy", "Nivea", "La Roche-Posay", "Garnier", "Bioderma", "Clinique"],
            "name_parts": ["Glow", "Hydra", "Pure", "Fresh", "Calm", "Care", "Vital", "Balance"],
            "features": ["texture", "hydration", "anti-aging", "price", "fragrance", "absorption"],
        },
        "makeup": {
            "brands": ["Maybelline", "L'Oreal", "Sephora", "NYX", "MAC", "Essence", "Fenty Beauty"],
            "name_parts": ["Color", "Shine", "Soft", "Velvet", "Matte", "Glow", "Lush", "Tint"],
            "features": ["coverage", "texture", "color palette", "durability", "pigmentation"],
        },
        "haircare": {
            "brands": ["Dove", "Pantene", "L'Oreal", "Garnier", "Elseve", "Head & Shoulders", "Kerastase"],
            "name_parts": ["Repair", "Smooth", "Silk", "Care", "Nutri", "Shine", "Volumize"],
            "features": ["fragrance", "shine effect", "texture", "effectiveness", "sulfate-free"],
        },
        "fragrance": {
            "brands": ["Dior", "Chanel", "YSL", "Armani", "Zara", "Versace", "Tom Ford", "Givenchy"],
            "name_parts": ["Bloom", "Secret", "Night", "Rose", "Fresh", "Aura", "Noir", "Oud"],
            "features": ["fragrance notes", "longevity", "bottle design", "uniqueness", "sillage"],
        },
    },
    "home_appliances": {
        "kitchen_appliances": {
            "brands": ["Philips", "Tefal", "Moulinex", "Bosch", "LG", "Samsung", "Panasonic", "KitchenAid"],
            "name_parts": ["Cook", "Chef", "Mix", "Smart", "Home", "Easy", "Blend", "Grill"],
            "features": ["power", "durability", "design", "ease of cleaning", "ease of use", "safety mechanisms"],
        },
        "cleaning_devices": {
            "brands": ["Dyson", "Philips", "Samsung", "Bosch", "Karcher", "Shark", "iRobot"],
            "name_parts": ["Clean", "Turbo", "Power", "Fresh", "Sweep", "Vac", "Bot"],
            "features": ["suction power", "durability", "battery life", "maneuverability", "smart navigation"],
        },
        "air_conditioning": {
            "brands": ["LG", "Samsung", "Gree", "Midea", "Hisense", "Daikin"],
            "name_parts": ["Cool", "Breeze", "Air", "Fresh", "Comfort", "Inverter"],
            "features": ["cooling speed", "noise level", "energy efficiency", "price", "smart controls"],
        },
    },
    "computers": {
        "desktop_pc": {
            "brands": ["Dell", "HP", "Lenovo", "Asus", "Acer", "MSI", "Corsair"],
            "name_parts": ["Tower", "Core", "Vision", "Pro", "Power", "Station", "Elite"],
            "features": ["gaming performance", "cooling", "design", "upgradeability", "price"],
        },
        "computer_accessories": {
            "brands": ["Logitech", "Razer", "Corsair", "HP", "Dell", "Asus", "Keychron"],
            "name_parts": ["Mouse", "Key", "Hub", "Link", "Pad", "Dock", "Switch"],
            "features": ["ergonomics", "comfort", "build quality", "connectivity", "price"],
        },
        "storage_devices": {
            "brands": ["Samsung", "Kingston", "SanDisk", "WD", "Seagate", "Crucial", "Corsair"],
            "name_parts": ["Drive", "Store", "Flash", "Secure", "Speed", "Vault", "NVMe"],
            "features": ["read/write speed", "storage capacity", "durability", "design", "price"],
        },
    },
    "gaming": {
        "gaming_consoles": {
            "brands": ["Sony", "Microsoft", "Nintendo", "Asus", "Valve"],
            "name_parts": ["Play", "Box", "Next", "Arena", "Game", "Zone", "Deck"],
            "features": ["performance", "exclusive games", "design", "price", "storage"],
        },
        "gaming_accessories": {
            "brands": ["Razer", "Logitech", "Corsair", "SteelSeries", "HyperX"],
            "name_parts": ["Gear", "Elite", "Pro", "Strike", "Boost", "Pulse", "Wired"],
            "features": ["comfort", "response time", "design", "durability", "price"],
        },
        "gaming_chairs": {
            "brands": ["DXRacer", "Secretlab", "Razer", "Corsair", "Asus", "Noblechairs"],
            "name_parts": ["Seat", "Comfort", "Throne", "Elite", "Pro", "Titan"],
            "features": ["lumbar support", "design", "durability", "adjustability", "material quality"],
        },
    }
}

PRODUCT_ADJECTIVES = [
    "Smart", "Premium", "Ultra", "Portable", "Compact", "Advanced",
    "Professional", "Modern", "Classic", "Dynamic", "Essential", "Wireless",
    "Eco", "Elegant", "Power", "Turbo", "Flex", "Mini", "Next-Gen", "Pro-Grade", 
    "Sleek", "Silent", "Limited Edition"
]

TOPICS_POOL = [
    "quality", "delivery", "price", "performance", "battery",
    "design", "comfort", "durability", "packaging", "value",
    "customer service", "unboxing", "instructions", "warranty"
]

INTERACTION_TYPES = ["view", "click", "add_to_cart", "add_to_wishlist", "purchase", "share", "search"]

ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled", "refunded"]
PAYMENT_STATUSES = ["pending", "paid", "failed", "refunded"]
PAYMENT_METHODS = ["credit_card", "paypal", "cash_on_delivery", "bank_transfer", "crypto", "apple_pay"]

CATEGORY_THEME = {
    "electronics": {"bg": "0f172a", "fg": "ffffff"},
    "beauty": {"bg": "ec4899", "fg": "ffffff"},
    "home_appliances": {"bg": "16a34a", "fg": "ffffff"},
    "computers": {"bg": "2563eb", "fg": "ffffff"},
    "gaming": {"bg": "7c3aed", "fg": "ffffff"},
    "default": {"bg": "334155", "fg": "ffffff"},
}


# =========================================================
# HELPERS
# =========================================================
def make_unique_slug(text: str) -> str:
    base = (
        text.lower()
        .strip()
        .replace(" ", "-")
        .replace("_", "-")
        .replace(",", "")
        .replace(".", "")
        .replace("/", "-")
        .replace("'", "")
    )
    base = "-".join(filter(None, base.split("-")))
    return f"{base}-{uuid.uuid4().hex[:10]}"


def money(val: float) -> Decimal:
    return Decimal(str(round(val, 2)))


def random_bool(weight_true=0.8):
    return random.random() < weight_true


def random_tags(category: str, subcategory: str, brand: str):
    pool = [
        category.replace("_", "-"),
        subcategory.replace("_", "-"),
        brand.lower().replace(" ", "-"),
        random.choice(["new", "trending", "popular", "premium", "budget", "eco", "smart"]),
        random.choice(["2026", "portable", "durable", "modern", "wireless", "compact"]),
        random.choice(["top-rated", "best-seller", "editor-choice", "daily-use", "gift-idea"]),
    ]
    return list(dict.fromkeys(pool))


def random_past_datetime(min_days_ago=0, max_days_ago=365):
    """Generate a random datetime between min_days_ago and max_days_ago in the past."""
    days_ago = random.uniform(min_days_ago, max_days_ago)
    return datetime.now() - timedelta(days=days_ago)


def random_datetime_after(start_dt, end_dt=None):
    """Generate a random datetime between start_dt and end_dt (default: now)."""
    if end_dt is None:
        end_dt = datetime.now()
    if start_dt >= end_dt:
        return end_dt
    delta = (end_dt - start_dt).total_seconds()
    random_seconds = random.uniform(0, delta)
    return start_dt + timedelta(seconds=random_seconds)


def get_user_signup_dates(cursor):
    """Fetch all user signup dates from the database."""
    cursor.execute("SELECT id, created_at FROM users")
    return {uid: created_at for uid, created_at in cursor.fetchall()}


def build_product_image_url(category: str, subcategory: str, title: str, slug: str, view_label: str, width=900, height=900):
    theme = CATEGORY_THEME.get(category, CATEGORY_THEME["default"])
    text = f"{subcategory.replace('_', ' ').title()} | {view_label} | {title}"
    encoded_text = quote(text)
    unique_path = quote(f"{slug}-{view_label.lower().replace(' ', '-')}")
    return f"https://placehold.co/{width}x{height}/{theme['bg']}/{theme['fg']}?text={encoded_text}&seed={unique_path}"


def generate_product_images(category: str, subcategory: str, title: str, slug: str):
    views = ["Front View", "Side View", "Detail View", "Packaging"]
    return [
        build_product_image_url(category, subcategory, title, slug, view, 900, 900)
        for view in views
    ]


def generate_thumbnail(category: str, subcategory: str, title: str, slug: str):
    return build_product_image_url(category, subcategory, title, slug, "Thumbnail", 700, 700)


def generate_product_title(category: str, subcategory: str):
    meta = CATALOG[category][subcategory]
    brand = random.choice(meta["brands"])
    part1 = random.choice(meta["name_parts"])
    part2 = random.choice(PRODUCT_ADJECTIVES)
    model = random.randint(100, 9999)

    title_patterns = [
        f"{brand} {part1} {part2} {model}",
        f"{brand} {part2} {part1} {model}",
        f"{brand} {part1} Series {model}",
        f"{brand} {part2} Edition {model}",
    ]
    return random.choice(title_patterns), brand


def generate_product_description(category: str, subcategory: str, brand: str, title: str):
    meta = CATALOG[category][subcategory]
    selected_features = random.sample(meta["features"], k=min(2, len(meta["features"])))
    feature1 = selected_features[0]
    feature2 = selected_features[1] if len(selected_features) > 1 else selected_features[0]

    sentences = [
        f"{title} by {brand} is designed for users who strongly value {feature1}.",
        f"This {subcategory.replace('_', ' ')} line up sets a new standard for {feature2}.",
        f"It is suitable for demanding routines and built to deliver reliable results under stress.",
        f"Customers continually praise its robust {feature1} and intuitive ease of use.",
        f"A magnificent choice in the {category.replace('_', ' ')} sector for advanced power-users and daily casuals alike."
    ]
    return " ".join(sentences)


def generate_topics(category: str, subcategory: str):
    feature_topics = CATALOG[category][subcategory]["features"]
    generic_topics = ["quality", "delivery", "price", "durability", "value"]
    pool = list(dict.fromkeys(feature_topics + generic_topics + TOPICS_POOL))
    return random.sample(pool, k=min(3, len(pool)))


def generate_review(sentiment: str, category: str, subcategory: str):
    features = CATALOG[category][subcategory]["features"]
    feature = random.choice(features)
    
    style = random.choice(["short", "long", "detailed", "emotional", "technical"])
    
    templates = {
        "positive": {
            "short": [
                "Great {feature}!", "Amazing {feature}.", "Loved the {feature}.", "Perfect {feature}.", "Five stars for {feature}."
            ],
            "long": [
                "I have been using this for a few weeks now and the {feature} is completely outstanding. It genuinely changed how I use the product on a daily basis. I highly recommend it.",
                "After doing a lot of research, I decided to go with this one because of its {feature}. I am not disappointed at all! The {feature} exceeded my expectations significantly.",
                "This is quite possibly the best purchase I have made all year. The {feature} alone is worth the price, not to mention the overall build quality and design."
            ],
            "detailed": [
                "Let me break down why this gets 5 stars: the {feature} is remarkably consistent. Unlike other brands where the {feature} degrades over time, this one holds up well under heavy daily use.",
                "In my 3 weeks of testing, the {feature} stood out the most. The integration is seamless and the overall experience is polished. Very reliable {feature}.",
                "Pros: impeccable {feature}, sturdy build, reasonable price. Cons: None so far. The {feature} works exactly in the way advertised."
            ],
            "emotional": [
                "I am absolutely in love with this! The {feature} brings so much joy and makes my life incredibly easier. I can't imagine living without it!",
                "Wow! Just wow! The {feature} blew my mind completely! I'm so happy I bought this, it's a game changer!",
                "This makes me feel so good every time I use it. The {feature} is gorgeous and my heart just melts using it."
            ],
            "technical": [
                "From a hardware and software perspective, the {feature} leverages an optimized architecture. Excellent engineering.",
                "The {feature} shows remarkable efficiency under load testing. It allows sustained performance at peak limits without thermal throttling.",
                "Integration with the {feature} API is flawless. The telemetry data confirms that the {feature} operates within a 1% error margin under stress."
            ]
        },
        "neutral": {
            "short": [
                "Okay {feature}.", "Average {feature}.", "Decent {feature}.", "Not bad {feature}."
            ],
            "long": [
                "It's an okay product but the {feature} leaves a bit to be desired. It works fine for basic tasks but struggles if you push it.",
                "I guess you get what you pay for. The {feature} is completely average. Don't expect to be blown away.",
                "Nothing special here. The {feature} is exactly as described, neither great nor terrible."
            ],
            "detailed": [
                "While the general build is okay, the {feature} feels a bit lacking in refinement. You'll notice some inconsistency when using the {feature} continuously.",
                "Testing the {feature} reveals moderate performance. It hits the baseline metrics but fails to reach the premium standard of its competitors.",
                "On paper, the {feature} looks great. In practice, it's just okay. The {feature} implementation is passable but there are better options out there."
            ],
            "emotional": [
                "I'm feeling so conflicted. The {feature} is okay, but I really wanted to love it. It just left me feeling indifferent.",
                "It's just 'meh'. I'm not angry, but the {feature} didn't spark any joy. Very underwhelming experience.",
                "To be honest, I'm slightly disappointed but not surprised. The {feature} is just barely doing its job."
            ],
            "technical": [
                "The {feature} benchmark results are strictly median. It demonstrates noticeable bottlenecks when the system is under 80% load.",
                "The architecture supporting the {feature} handles synchronous tasks fine, but asynchronous processes exhibit minor stuttering.",
                "There is a 15% variance in the {feature} output consistency. The module meets bare minimum specifications but lacks advanced optimization."
            ]
        },
        "negative": {
            "short": [
                "Terrible {feature}.", "Hate the {feature}.", "Awful {feature}.", "Do not buy.", "Broken {feature}."
            ],
            "long": [
                "I am incredibly frustrated with this purchase. The {feature} broke within the first week of use, and customer support was completely unhelpful.",
                "Save your money and avoid this brand. The {feature} is wildly misrepresented in the marketing and fails to work properly most of the time.",
                "This is undeniably the worst item I've bought on this site. The {feature} is fundamentally flawed and renders the whole product practically unusable."
            ],
            "detailed": [
                "Let's talk about the {feature}. It frequently disconnects or stops functioning entirely under normal use. Moreover, the construction feels incredibly cheap.",
                "During my first day of testing, the {feature} caused the unit to shut down entirely. This is a severe defect in the design. I am returning it immediately.",
                "The major issue lies in the {feature}. Due to poor quality control, it constantly underperforms and runs dangerously hot during basic operations."
            ],
            "emotional": [
                "I am utterly devastated! I saved up for this and the {feature} is a complete disaster. It honestly ruined my week.",
                "This makes me so angry! Honestly, the {feature} is a joke. I feel totally scammed and disrespected as a customer.",
                "I could literally cry. The {feature} completely failed during an important moment. Absolutely heartbreaking product."
            ],
            "technical": [
                "Critical failure in the {feature} subsystem. We detected severe memory leaks and thermal runaway when engaged for more than 10 minutes.",
                "The algorithmic complexity of the {feature} seems poorly optimized, leading to extreme latency spikes. The hardware cannot accommodate the software overhead.",
                "Total structural failure of the {feature} component. The tolerance allows for micro-fractures under standard operational stress."
            ]
        }
    }

    text = random.choice(templates[sentiment][style]).format(feature=feature)
    
    if style in ["short", "emotional"] and random.random() < 0.2:
        text = text.lower().replace("!", "").replace(".", "")
    
    if sentiment == "positive":
        rating = random.choices([4, 5], weights=[0.4, 0.6])[0]
    elif sentiment == "neutral":
        rating = 3
    else:
        rating = random.choices([1, 2], weights=[0.6, 0.4])[0]
        
    return text, rating


def clear_tables(cursor, conn):
    print("[RESET MODE] Wiping out existing Data... Please wait.")
    
    tables_to_truncate = [
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
        except psycopg2.Error as e:
            # Table might not exist (e.g., product_embeddings if pgvector is missing)
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


def get_existing_ids(cursor, table_name):
    allowed_tables = {
        "users", "products", "categories", "subcategories",
        "reviews", "orders", "payments", "wishlists",
        "cart_items", "recommendations", "product_embeddings",
        "audit_logs", "voice_confirmations", "review_analysis",
        "user_interactions", "order_items"
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
# SEED STEPS
# =========================================================
def seed_users(cursor, conn, n_users):
    user_ids = []
    user_signup_dates = {}

    for _ in tqdm(range(n_users), desc="Pouring Users"):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{uuid.uuid4().hex[:8]}_{fake.unique.email()}"

        # Spread signups over 18 months for realistic recency variance
        signup_date = random_past_datetime(min_days_ago=1, max_days_ago=540)

        cursor.execute("""
            INSERT INTO users
            (first_name, last_name, email, password_hash, phone, address_line,
             city, postal_code, country, role, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            first_name,
            last_name,
            email,
            fake.sha256(),
            fake.phone_number()[:30],
            fake.address()[:100],
            fake.city()[:100],
            fake.postcode()[:20],
            fake.country()[:100],
            random.choice(["customer", "customer", "customer", "customer", "admin", "manager"]),
            random_bool(0.95),
            signup_date,
            signup_date + timedelta(hours=random.randint(0, 48)),
        ))
        uid = cursor.fetchone()[0]
        user_ids.append(uid)
        user_signup_dates[uid] = signup_date

    conn.commit()
    return user_ids, user_signup_dates


def seed_products(cursor, conn, category_ids, subcategory_ids, subcategory_to_category, n_products):
    product_ids = []
    all_subs = list(subcategory_ids.keys())

    for _ in tqdm(range(n_products), desc="Creating Inventory"):
        sub = random.choice(all_subs)
        sub_id = subcategory_ids[sub]
        cat = subcategory_to_category[sub]
        cat_id = category_ids[cat]

        title, brand = generate_product_title(cat, sub)
        slug = make_unique_slug(title)
        description = generate_product_description(cat, sub, brand, title)

        # Realistic price distribution (most are cheap to mid-tier, some are high-end)
        price_val = 5.0 + random.expovariate(1 / 150.0) if random.random() < 0.8 else random.uniform(500, 3999)
        price = money(min(price_val, 4999.0))
        discount = random.randint(5, 40) if random.random() < 0.35 else 0

        stock = random.randint(0, 300)
        thumbnail = generate_thumbnail(cat, sub, title, slug)
        images = generate_product_images(cat, sub, title, slug)
        tags = random_tags(cat, sub, brand)
        is_active = random_bool(0.9)

        product_date = random_past_datetime(min_days_ago=30, max_days_ago=730)
        cursor.execute("""
            INSERT INTO products
            (
                title, slug, description, brand, category_id, subcategory_id,
                price, discount_percent, rating_avg, review_count,
                stock, thumbnail, images, tags, is_active, created_at, updated_at
            )
            VALUES
            (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s
            )
            RETURNING id
        """, (
            title[:255],
            slug[:280],
            description,
            brand[:120],
            cat_id,
            sub_id,
            price,
            discount,
            Decimal("0.00"),
            0,
            stock,
            thumbnail,
            json.dumps(images),
            json.dumps(tags),
            is_active,
            product_date,
            product_date + timedelta(days=random.randint(0, 10))
        ))
        product_ids.append(cursor.fetchone()[0])

    conn.commit()
    return product_ids


def seed_reviews_and_analysis(cursor, conn, product_ids, all_user_ids, subcategory_to_category, user_signup_dates):
    if not product_ids or not all_user_ids:
        return

    product_meta = {}
    cursor.execute("""
        SELECT p.id, s.slug
        FROM products p
        JOIN subcategories s ON p.subcategory_id = s.id
        WHERE p.id = ANY(%s)
    """, (product_ids,))
    
    for pid, sub_slug in cursor.fetchall():
        sub = sub_slug.replace("-", "_")
        cat = subcategory_to_category[sub]
        product_meta[pid] = (cat, sub)

    for pid in tqdm(product_ids, desc="Generating NLP Reviews"):
        n_reviews = random.randint(5, 25)  # Multiplied for NLP and recommendations
        sentiments = random.choices(
            ["positive", "neutral", "negative"],
            weights=[0.65, 0.20, 0.15],
            k=n_reviews
        )

        category, subcategory = product_meta[pid]

        for sentiment in sentiments:
            text, rating = generate_review(sentiment, category, subcategory)
            user_id = random.choice(all_user_ids)
            verified_purchase = random_bool(0.7)
            signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
            review_date = random_datetime_after(signup_dt)

            cursor.execute("""
                INSERT INTO reviews
                (product_id, user_id, rating, review_text, verified_purchase, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, product_id) DO NOTHING
                RETURNING id
            """, (
                pid,
                user_id,
                rating,
                text,
                verified_purchase,
                review_date
            ))
            
            res = cursor.fetchone()
            if not res:
                continue # Duplicate ignored
            review_id = res[0]

            keywords = fake.words(nb=random.randint(3, 8))
            topics = generate_topics(category, subcategory)
            score_range = {
                "positive": (0.6, 1.0),
                "neutral": (-0.2, 0.2),
                "negative": (-1.0, -0.6)
            }
            s_min, s_max = score_range[sentiment]

            cursor.execute("""
                INSERT INTO review_analysis
                (review_id, sentiment_label, sentiment_score, keywords, topics, model_name, created_at)
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
            """, (
                review_id,
                sentiment,
                round(random.uniform(s_min, s_max), 4),
                json.dumps(keywords),
                json.dumps(topics),
                "ecom-nlp-bert-v2",
                review_date
            ))
            
    conn.commit()


def seed_wishlists_and_carts(cursor, conn, user_ids, product_ids, user_signup_dates):
    if not user_ids or not product_ids: return

    for user_id in tqdm(user_ids, desc="Filling Carts & Wishlists"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))

        wishlist_sample = random.sample(product_ids, k=min(random.randint(1, 10), len(product_ids)))
        for pid in wishlist_sample:
            action_date = random_datetime_after(signup_dt)
            cursor.execute("""
                INSERT INTO wishlists (user_id, product_id, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, product_id) DO NOTHING
            """, (user_id, pid, action_date))

        cart_sample = random.sample(product_ids, k=min(random.randint(1, 5), len(product_ids)))
        for pid in cart_sample:
            action_date = random_datetime_after(signup_dt)
            cursor.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity,
                              updated_at = EXCLUDED.updated_at
            """, (user_id, pid, random.randint(1, 4), action_date, action_date + timedelta(minutes=random.randint(1, 120))))

    conn.commit()


def seed_user_interactions(cursor, conn, user_ids, product_ids, user_signup_dates):
    if not user_ids or not product_ids: return

    for user_id in tqdm(user_ids, desc="Logging Interactions"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        sampled_products = random.sample(product_ids, k=min(random.randint(8, 30), len(product_ids)))
        for pid in sampled_products:
            interaction_type = random.choice(INTERACTION_TYPES)
            interaction_value = Decimal(str(round(random.uniform(1, 5), 2)))
            interaction_date = random_datetime_after(signup_dt)
            cursor.execute("""
                INSERT INTO user_interactions
                (user_id, product_id, interaction_type, interaction_value, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                pid,
                interaction_type,
                interaction_value,
                interaction_date
            ))
    conn.commit()


def seed_orders_payments_voice(cursor, conn, user_ids, product_lookup, user_signup_dates):
    if not user_ids or not product_lookup: return
    
    # Extract map: pid: (final_price, title)
    product_map = {pid: (final_price, title) for pid, _, _, final_price, title in product_lookup}
    product_ids = list(product_map.keys())

    for user_id in tqdm(user_ids, desc="Fabricating Transactions"):
        nb_orders = random.randint(1, 6)
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))

        # Generate sorted order dates for realistic chronological ordering
        order_dates = sorted([random_datetime_after(signup_dt) for _ in range(nb_orders)])

        for order_date in order_dates:
            status = random.choice(ORDER_STATUSES)

            cursor.execute("""
                INSERT INTO orders
                (user_id, status, total_amount, payment_status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id,
                status,
                Decimal("0.00"),
                "pending",
                order_date,
                order_date + timedelta(minutes=random.randint(1, 120))
            ))
            order_id = cursor.fetchone()[0]

            selected_products = random.sample(product_ids, k=min(random.randint(1, 5), len(product_ids)))
            total_amount = Decimal("0.00")

            for pid in selected_products:
                qty = random.randint(1, 3)
                unit_price, title = product_map[pid]
                subtotal = unit_price * qty
                total_amount += subtotal

                cursor.execute("""
                    INSERT INTO order_items
                    (order_id, product_id, product_name_snapshot, quantity, unit_price, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    order_id,
                    pid,
                    title,
                    qty,
                    unit_price,
                    subtotal
                ))

            payment_status = random.choice(PAYMENT_STATUSES)
            if status == "cancelled":
                payment_status = random.choice(["failed", "refunded", "pending"])

            updated_at = order_date + timedelta(hours=random.randint(1, 72))
            cursor.execute("""
                UPDATE orders
                SET total_amount = %s,
                    payment_status = %s,
                    updated_at = %s
                WHERE id = %s
            """, (
                total_amount,
                payment_status,
                updated_at,
                order_id
            ))

            paid_at = random_datetime_after(order_date, updated_at) if payment_status in ["paid", "refunded"] else None
            
            payment_table_status = "completed" if payment_status == "paid" else payment_status

            cursor.execute("""
                INSERT INTO payments
                (order_id, payment_method, amount, status, transaction_ref, paid_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                random.choice(PAYMENT_METHODS),
                total_amount,
                payment_table_status,
                str(uuid.uuid4()),
                paid_at,
                order_date
            ))

            voice_date = order_date + timedelta(hours=random.randint(0, 24))
            confirmed_at = voice_date + timedelta(minutes=random.randint(5, 120)) if random_bool() else None
            cursor.execute("""
                INSERT INTO voice_confirmations
                (order_id, phone_number, call_status, transcript, confirmed, confirmed_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                fake.phone_number()[:30],
                random.choice(["pending", "completed", "failed", "ignored"]),
                fake.sentence(nb_words=12),
                random_bool(0.65),
                confirmed_at,
                voice_date
            ))

    conn.commit()


def seed_recommendations(cursor, conn, user_ids, product_ids, user_signup_dates):
    if len(product_ids) < 5 or not user_ids: return

    for user_id in tqdm(user_ids, desc="AI Recommendations"):
        signup_dt = user_signup_dates.get(user_id, datetime.now() - timedelta(days=180))
        source_products = random.sample(product_ids, k=min(5, len(product_ids)))
        for source_pid in source_products:
            rec_candidates = [p for p in product_ids if p != source_pid]
            recs = random.sample(rec_candidates, k=min(3, len(rec_candidates)))

            for rec_pid in recs:
                rec_date = random_datetime_after(signup_dt)
                cursor.execute("""
                    INSERT INTO recommendations
                    (user_id, source_product_id, recommended_product_id, score, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, source_product_id, recommended_product_id) DO NOTHING
                """, (
                    user_id,
                    source_pid,
                    rec_pid,
                    Decimal(str(round(random.uniform(0.50, 0.99), 4))),
                    rec_date
                ))
    conn.commit()


def seed_product_embeddings(cursor, conn, product_ids, n_embeddings):
    # Vector length strict: 1536 as defined in DB schema (vector(1536))
    VECTOR_DIM = 1536
    chosen_products = random.sample(product_ids, k=min(n_embeddings, len(product_ids)))

    try:
        # Check if pgvector table exists before attempting inserts to prevent crashes
        cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'product_embeddings'")
        if not cursor.fetchone():
            print("\n⚠️ Table 'product_embeddings' manquante (pgvector non installé). Embeddings ignorés.")
            conn.rollback()
            return
            
        for pid in tqdm(chosen_products, desc="Generative AI Embeddings"):
            vector = [round(random.uniform(-1, 1), 6) for _ in range(VECTOR_DIM)]
            cursor.execute("""
                INSERT INTO product_embeddings
                (product_id, model_name, embedding_vector, created_at)
                VALUES (%s, %s, %s::vector, NOW())
                ON CONFLICT (product_id, model_name) DO NOTHING
            """, (
                pid,
                "openai-ada-002-emulated", # Realistic AI Model
                json.dumps(vector) 
            ))
        conn.commit()
    except psycopg2.Error as e:
        print(f"\n⚠️ Erreur lors de l'insertion des embeddings : {e}")
        conn.rollback()


def seed_audit_logs(cursor, conn, user_ids, product_ids, n_logs):
    if not user_ids or not product_ids: return

    actions = ["create", "update", "delete", "login", "checkout", "review_posted", "add_to_wishlist", "add_to_cart"]
    entity_types = ["product", "order", "review", "payment", "user", "wishlist", "cart_item"]

    for _ in tqdm(range(n_logs), desc="Securing Audi Trails"):
        metadata = {
            "ip": fake.ipv4(),
            "user_agent": fake.user_agent(),
            "session_id": uuid.uuid4().hex[:16],
            "source": random.choice(["web", "ios_app", "android_app", "admin_dashboard"])
        }

        log_date = random_past_datetime(min_days_ago=0, max_days_ago=540)
        cursor.execute("""
            INSERT INTO audit_logs
            (user_id, action, entity_type, entity_id, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
        """, (
            random.choice(user_ids),
            random.choice(actions),
            random.choice(entity_types),
            random.choice(product_ids),
            json.dumps(metadata),
            log_date
        ))
    conn.commit()


# =========================================================
# MAIN
# =========================================================
def main():
    parser = argparse.ArgumentParser(description="eCommerce Mock Data Seeder - ML Ready")
    parser.add_argument("--mode", choices=["reset", "append"], default="append", 
                        help="Mode of initialization: 'reset' cleans the DB first, 'append' adds more data.")
    args = parser.parse_args()

    conn = None
    cursor = None

    try:
        print(f"\nStarting Database Seeder in [{args.mode.upper()}] Mode...")
        # To avoid external docker port issues if mapping is missing, 
        # connect locally or allow host overwrites
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        if args.mode == "reset":
            clear_tables(cursor, conn)

        category_ids, subcategory_ids, subcategory_to_category = get_or_create_categories_and_subcategories(cursor, conn)

        user_ids, user_signup_dates = seed_users(cursor, conn, NB_USERS)
        product_ids = seed_products(cursor, conn, category_ids, subcategory_ids, subcategory_to_category, NB_PRODUCTS)

        all_user_ids = get_existing_ids(cursor, "users")
        all_product_ids = get_existing_ids(cursor, "products")
        product_lookup = get_product_lookup(cursor)

        # Get ALL signup dates (including pre-existing users from previous runs)
        all_signup_dates = get_user_signup_dates(cursor)

        seed_reviews_and_analysis(cursor, conn, product_ids, all_user_ids, subcategory_to_category, all_signup_dates)
        
        interaction_users = random.sample(all_user_ids, k=min(NB_INTERACTION_USERS, len(all_user_ids)))
        order_users = random.sample(all_user_ids, k=min(NB_ORDER_USERS, len(all_user_ids)))
        recom_users = random.sample(all_user_ids, k=min(NB_RECOMMENDATION_USERS, len(all_user_ids)))

        seed_wishlists_and_carts(cursor, conn, interaction_users, all_product_ids, all_signup_dates)
        seed_user_interactions(cursor, conn, interaction_users, all_product_ids, all_signup_dates)
        seed_orders_payments_voice(cursor, conn, order_users, product_lookup, all_signup_dates)
        seed_recommendations(cursor, conn, recom_users, all_product_ids, all_signup_dates)
        seed_product_embeddings(cursor, conn, all_product_ids, NB_EMBEDDINGS)
        seed_audit_logs(cursor, conn, all_user_ids, all_product_ids, NB_AUDIT_LOGS)

        update_all_product_ratings(cursor, conn)

        print(f"Total Users inserted this session: {len(user_ids)}")
        print(f"Total Products inserted this session: {len(product_ids)}")

    except Exception as e:
        if conn:
            conn.rollback()
        print("\nError during seeding:")
        print(e)
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    main()