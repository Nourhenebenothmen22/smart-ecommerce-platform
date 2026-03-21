import psycopg2
conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5433/ecommerce_ml_db")
cur = conn.cursor()
cur.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'chk_payment_status'")
res = cur.fetchone()
print("CONSTRAINT DEFINITION:", res[0] if res else "NOT FOUND")
