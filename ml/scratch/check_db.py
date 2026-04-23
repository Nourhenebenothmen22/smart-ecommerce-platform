import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.getcwd())

try:
    from ml.core.db import get_db_cursor
    with get_db_cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM products')
        p_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM product_embeddings')
        pe_count = cur.fetchone()[0]
        print(f"Products: {p_count}")
        print(f"Embeddings: {pe_count}")
        
        if p_count > 0:
            cur.execute('SELECT title, description, price, stock FROM products LIMIT 3')
            for row in cur.fetchall():
                print(f"Sample Product: {row}")
except Exception as e:
    print(f"Error: {e}")
