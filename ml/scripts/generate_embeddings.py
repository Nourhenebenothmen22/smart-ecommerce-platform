import os
import psycopg2
from sentence_transformers import SentenceTransformer
import time

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "ecommerce_ml_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")

def get_connection():
    ports_to_try = [os.environ.get("DB_PORT", "5432"), "5433", "5432"]
    for p in ports_to_try:
        try:
            return psycopg2.connect(host=DB_HOST, port=p, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        except Exception:
            pass
    raise Exception("Impossible de se connecter")

def run():
    print("1. Chargement du modèle ML (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    conn = get_connection()
    cur = conn.cursor()
    
    # On garantit que la dimension de la colonne est 384 (pour MiniLM)
    print("2. Mise à jour du schéma pgvector pour accepter 384 dimensions...")
    cur.execute("ALTER TABLE product_embeddings ALTER COLUMN embedding_vector TYPE vector(384);")
    conn.commit()
    
    cur.execute("SELECT id, title, description, brand FROM products;")
    products = cur.fetchall()
    
    print(f"3. {len(products)} produits trouvés. Nettoyage de la table existante...")
    cur.execute("TRUNCATE TABLE product_embeddings RESTART IDENTITY;")
    conn.commit()

    print("4. Génération des embeddings en cours. Cela peut prendre quelques minutes...")
    start_time = time.time()
    
    inserted = 0
    for row in products:
        p_id, title, desc, brand = row
        text_to_embed = f"{title}. {brand}. {desc}"
        
        vector = model.encode(text_to_embed).tolist()
        
        cur.execute("""
            INSERT INTO product_embeddings (product_id, model_name, model_version, embedding_vector)
            VALUES (%s, %s, %s, %s)
        """, (p_id, 'all-MiniLM-L6-v2', '1.0', vector))
        
        inserted += 1
        if inserted % 500 == 0:
            print(f"   [{inserted}/{len(products)}] traités...")
            conn.commit()
            
    conn.commit()
    cur.close()
    conn.close()
    elapsed = time.time() - start_time
    print(f"Succès total ! {inserted} embeddings mathématiques ajoutés à Postgres en {elapsed:.2f} secondes.")

if __name__ == "__main__":
    run()
