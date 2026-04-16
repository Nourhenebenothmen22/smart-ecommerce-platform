import psycopg2
import sys
import os

# Ensure the 'ml' directory is in sys.path to allow for imports of 'seeder' and 'core'
MOD_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if MOD_PATH not in sys.path:
    sys.path.insert(0, MOD_PATH)



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
