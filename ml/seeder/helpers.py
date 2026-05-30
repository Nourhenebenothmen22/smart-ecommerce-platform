import uuid
import hashlib
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import random

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
    return datetime.now(timezone.utc) - timedelta(days=days_ago)

def random_datetime_after(start_dt, end_dt=None):
    """Generate a random datetime between start_dt and end_dt (default: now)."""
    if end_dt is None:
        end_dt = datetime.now(timezone.utc)
    if start_dt >= end_dt:
        return end_dt
    delta = (end_dt - start_dt).total_seconds()
    random_seconds = random.uniform(0, delta)
    return start_dt + timedelta(seconds=random_seconds)

def get_user_signup_dates(cursor):
    """Fetch all user signup dates from the database."""
    cursor.execute("SELECT id, created_at FROM users")
    return {uid: created_at for uid, created_at in cursor.fetchall()}

SUBCATEGORY_KEYWORDS = {
    # 1. Electronics
    "smartphones": "smartphone",
    "laptops": "laptop",
    "tablets": "tablet",
    "headphones": "headphones",
    "cameras": "camera",
    "smartwatches": "smartwatch",
    "televisions": "television",
    # 2. Beauty
    "skincare": "skincare",
    "makeup": "makeup",
    "haircare": "haircare",
    "fragrance": "perfume",
    "personal_hygiene": "soap",
    # 3. Home Appliances
    "kitchen_appliances": "blender",
    "cleaning_devices": "vacuum",
    "air_conditioning": "airconditioner",
    "washing_machines": "washingmachine",
    "refrigerators": "refrigerator",
    # 4. Computers
    "desktop_pc": "computer",
    "computer_accessories": "keyboard",
    "storage_devices": "usb",
    "monitors": "monitor",
    # 5. Gaming
    "gaming_consoles": "console",
    "gaming_accessories": "controller",
    "gaming_chairs": "officechair",
    "gaming_headsets": "headset",
    # 6. Sports
    "fitness_equipment": "treadmill",
    "running_shoes": "shoes",
    "cycling": "bicycle",
    "sportswear": "sportswear",
    # 7. Fashion
    "mens_clothing": "menswear",
    "womens_clothing": "dress",
    "footwear": "shoes",
    "bags_accessories": "backpack",
    # 8. Books & Stationery
    "fiction_books": "novel",
    "non_fiction_books": "book",
    "stationery": "notebook",
    # 9. Food & Beverages
    "coffee_tea": "coffee",
    "snacks": "cookie",
    "supplements": "vitamins",
    # 10. Toys & Kids
    "educational_toys": "toy",
    "action_figures": "toy",
    "board_games": "boardgame",
    # 11. Automotive
    "car_electronics": "gps",
    "car_care": "carwash",
    "car_accessories": "caraccessories",
    # 12. Health & Wellness
    "medical_devices": "medical",
    "vitamins_supplements": "vitamins",
    "yoga_recovery": "yoga",
    # 13. Home Decor & Furniture
    "furniture": "furniture",
    "lighting": "lamp",
    "bedding_bath": "bedding",
    # 14. Office
    "office_furniture": "desk",
    "office_supplies": "stationery",
    "printers_scanners": "printer",
    # 15. Pet Supplies
    "dog_supplies": "dog",
    "cat_supplies": "cat",
    "aquarium_supplies": "aquarium"
}

def build_product_image_url(category: str, subcategory: str, title: str, slug: str, view_label: str, width=900, height=900):
    # Compute a deterministic lock integer from the slug + view_label
    # using MD5 to be stable across process restarts
    key = f"{slug}-{view_label}"
    md5_hash = hashlib.md5(key.encode("utf-8")).hexdigest()
    lock_val = int(md5_hash[:8], 16) % 10000
    
    # Map subcategory to a clean, recognized keyword for loremflickr
    keyword = SUBCATEGORY_KEYWORDS.get(subcategory, subcategory.replace("_", "").replace("-", ""))
    
    return f"https://loremflickr.com/{width}/{height}/{keyword}?lock={lock_val}"

def generate_product_images(category: str, subcategory: str, title: str, slug: str):
    views = ["Front View", "Side View", "Detail View", "Packaging"]
    return [
        build_product_image_url(category, subcategory, title, slug, view, 900, 900)
        for view in views
    ]

def generate_thumbnail(category: str, subcategory: str, title: str, slug: str):
    return build_product_image_url(category, subcategory, title, slug, "Thumbnail", 700, 700)


def compute_product_price(supplier_cost: float, margin_pct: float, condition: str, release_year: int) -> float:
    # 1. Base price
    base_price = supplier_cost * (1.0 + margin_pct / 100.0)
    
    # 2. Condition multiplier
    cond_multipliers = {
        "new": 1.0,
        "open_box": 0.85,
        "refurbished": 0.70,
        "used": 0.50
    }
    cond_mult = cond_multipliers.get(condition, 1.0)
    
    # 3. Release year depreciation (base year 2026, 5% depreciation per year, min 0.4 multiplier)
    years_old = max(0, 2026 - release_year)
    depreciation_mult = max(0.4, 1.0 - (years_old * 0.05))
    
    # 4. Apply multipliers
    adjusted_price = base_price * cond_mult * depreciation_mult
    
    # 5. Add small noise (+-3%)
    noise = random.uniform(0.97, 1.03)
    final_price = adjusted_price * noise
    
    return float(round(final_price, 2))


def value_for_money_score(price: float, brand_tier: int, product_tier: int, supplier_cost: float = None) -> float:
    if price <= 0:
        return 1.0
    if supplier_cost is None or supplier_cost <= 0:
        # Estimate supplier cost if not available
        supplier_cost = price * 0.65
    
    # Expected markup based on brand tier and product tier
    # budget = 15-30%, luxury = 60-80%
    expected_margin_pct = 15.0 + (brand_tier - 1) * 15.0 + (product_tier - 1) * 5.0
    expected_price = supplier_cost * (1.0 + expected_margin_pct / 100.0)
    
    # Value for money is expected price divided by actual price
    # e.g., if we paid less than expected, value is high (>1.0)
    return float(expected_price / price)

