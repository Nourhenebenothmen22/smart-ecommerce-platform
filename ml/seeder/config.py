import random
import bcrypt
from faker import Faker

# =========================================================
# CONFIG
# =========================================================
from core.config import settings

DB_CONFIG = settings.db_config_dict

# Settings for Generation
NB_PRODUCTS = 4000
NB_USERS = 1200
NB_AUDIT_LOGS = 4000
NB_EMBEDDINGS = 2400
NB_RECOMMENDATION_USERS = 800
NB_ORDER_USERS = 960
NB_INTERACTION_USERS = 1100

RANDOM_SEED = 42

if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)
    Faker.seed(RANDOM_SEED)

fake = Faker()

# Pre-calculate a secure hash for all mock users to speed up seeding
# Real password for all: "password123"
_plain_password = "password123"
DEFAULT_PASSWORD_HASH = bcrypt.hashpw(_plain_password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')

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
