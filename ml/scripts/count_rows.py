import psycopg2
import sys
import os

# Set PYTHONPATH to include ml
sys.path.append('ml')
from seeder.config import DB_CONFIG

def get_counts():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get all tables in public schema
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = [r[0] for r in cur.fetchall()]
    
    counts = []
    for table in tables:
        try:
            cur.execute(f"SELECT count(*) FROM {table}")
            count = cur.fetchone()[0]
            counts.append((table, count))
        except:
            pass
            
    # Sort by count descending
    counts.sort(key=lambda x: x[1], reverse=True)
    
    total = sum(c[1] for c in counts)
    
    print("-" * 30)
    print(f"{'Table':<20} | {'Rows':<8}")
    print("-" * 30)
    for table, count in counts:
        print(f"{table:<20} | {count:<8}")
    print("-" * 30)
    print(f"{'TOTAL':<20} | {total:<8}")
    print("-" * 30)
    
    conn.close()

if __name__ == "__main__":
    get_counts()
