import psycopg2

conn = psycopg2.connect(host='localhost', port=5433, dbname='ecommerce_ml_db', user='postgres', password='postgres')
cur = conn.cursor()
cur.execute("SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name = 'product_embeddings';")
cols = cur.fetchall()
print("product_embeddings columns:")
for c in cols:
    print(c)
