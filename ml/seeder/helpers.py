import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from urllib.parse import quote
import random
from .config import CATEGORY_THEME

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
