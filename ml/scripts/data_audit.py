import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5433")
DB_NAME = os.environ.get("DB_NAME", "ecommerce_ml_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def run_audit():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        report = {}
        
        # 1. Row counts & Duplicates (Emails) for Users
        cur.execute("SELECT COUNT(*) as total FROM users;")
        report['users_total'] = cur.fetchone()['total']
        
        cur.execute("SELECT email, COUNT(*) as cnt FROM users GROUP BY email HAVING COUNT(*) > 1;")
        report['users_duplicate_emails'] = len(cur.fetchall())
        
        # 2. Products Audit (Nulls, Zero prices)
        cur.execute("SELECT COUNT(*) as total FROM products;")
        report['products_total'] = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as cnt FROM products WHERE price <= 0 OR price IS NULL;")
        report['products_invalid_price'] = cur.fetchone()['cnt']
        
        cur.execute("SELECT COUNT(*) as cnt FROM products WHERE stock < 0;")
        report['products_negative_stock'] = cur.fetchone()['cnt']
        
        # 3. Orders Audit (Orphans, Anomalies)
        cur.execute("SELECT COUNT(*) as total FROM orders;")
        report['orders_total'] = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as cnt FROM orders WHERE user_id NOT IN (SELECT id FROM users);")
        report['orders_orphan_users'] = cur.fetchone()['cnt']
        
        cur.execute("SELECT status, COUNT(*) as cnt FROM orders GROUP BY status;")
        report['orders_by_status'] = {row['status']: row['cnt'] for row in cur.fetchall()}
        
        # 4. Reviews Audit
        cur.execute("SELECT COUNT(*) as total FROM reviews;")
        report['reviews_total'] = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as cnt FROM reviews WHERE rating < 1 OR rating > 5;")
        report['reviews_invalid_rating'] = cur.fetchone()['cnt']
        
        # 5. ML Data (User Features & Embeddings)
        cur.execute("SELECT COUNT(*) as total FROM user_features;")
        report['user_features_total'] = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM product_embeddings;")
        report['product_embeddings_total'] = cur.fetchone()['total']
        
        print("AUDIT_JSON_START")
        print(json.dumps(report, indent=2))
        print("AUDIT_JSON_END")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error during audit: {e}")

if __name__ == "__main__":
    run_audit()
