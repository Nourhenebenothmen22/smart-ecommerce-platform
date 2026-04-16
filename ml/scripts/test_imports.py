"""Quick import verification script."""
import sys
import os

# Add ml/ root to sys.path
_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

errors = []

try:
    from core.config import settings
    print("[OK] core.config")
except ImportError as e:
    errors.append(f"[FAIL] core.config: {e}")
    print(errors[-1])

try:
    from seeder.config import DB_CONFIG, NB_USERS, NB_PRODUCTS
    print("[OK] seeder.config")
except ImportError as e:
    errors.append(f"[FAIL] seeder.config: {e}")
    print(errors[-1])

try:
    from seeder.catalog import CATALOG, PRODUCT_ADJECTIVES, TOPICS_POOL
    print("[OK] seeder.catalog")
except ImportError as e:
    errors.append(f"[FAIL] seeder.catalog: {e}")
    print(errors[-1])

try:
    from seeder.helpers import get_user_signup_dates, make_unique_slug, money
    print("[OK] seeder.helpers")
except ImportError as e:
    errors.append(f"[FAIL] seeder.helpers: {e}")
    print(errors[-1])

try:
    from seeder.generators import generate_review, generate_product_title
    print("[OK] seeder.generators")
except ImportError as e:
    errors.append(f"[FAIL] seeder.generators: {e}")
    print(errors[-1])

try:
    from seeder.core import (
        clear_tables, seed_users, seed_products, seed_reviews,
        get_existing_ids, get_product_lookup
    )
    print("[OK] seeder.core")
except ImportError as e:
    errors.append(f"[FAIL] seeder.core: {e}")
    print(errors[-1])

print("\n" + "=" * 40)
if errors:
    print(f"FAILED: {len(errors)} import(s) broken")
    for err in errors:
        print(f"  {err}")
else:
    print("ALL IMPORTS OK")
    db = DB_CONFIG
    print(f"DB Target: {db['database']}@{db['host']}:{db['port']}")
print("=" * 40)
