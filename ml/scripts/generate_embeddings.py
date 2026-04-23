"""
generate_embeddings.py — Generate product embeddings using a multilingual model.

Uses paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions) for French-compatible
semantic embeddings. Encodes title + brand + description for each product.
"""
import os
import psycopg2
from sentence_transformers import SentenceTransformer
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "ecommerce_ml_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5433")

# Multilingual model — supports French, English, 50+ languages (384 dimensions)
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
MODEL_VERSION = "1.0"


def get_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASS
        )
    except Exception as e:
        raise Exception(f"Cannot connect to database on {DB_HOST}:{DB_PORT}/{DB_NAME}: {e}")


def run():
    logger.info(f"1. Loading multilingual model ({MODEL_NAME})...")
    model = SentenceTransformer(MODEL_NAME)

    conn = get_connection()
    cur = conn.cursor()

    # Ensure vector column is 384 dimensions (matches model output)
    logger.info("2. Updating pgvector schema for 384 dimensions...")
    cur.execute("ALTER TABLE product_embeddings ALTER COLUMN embedding_vector TYPE vector(384);")
    conn.commit()

    # Register model in ml_models to satisfy FK constraint
    try:
        cur.execute("""
            INSERT INTO ml_models (model_name, model_version, model_type, algorithm)
            VALUES (%s, %s, 'embedding', 'transformer')
            ON CONFLICT (model_name, model_version) DO NOTHING;
        """, (MODEL_NAME, MODEL_VERSION))
        conn.commit()
        logger.info(f"   Model '{MODEL_NAME}' v{MODEL_VERSION} registered in ml_models.")
    except Exception as e:
        logger.warning(f"   ml_models insert check: {e}")
        conn.rollback()

    cur.execute("SELECT id, title, description, brand FROM products;")
    products = cur.fetchall()

    logger.info(f"3. {len(products)} products found. Clearing existing embeddings...")
    cur.execute("TRUNCATE TABLE product_embeddings RESTART IDENTITY;")
    conn.commit()

    logger.info("4. Generating embeddings... This may take a few minutes.")
    start_time = time.time()

    inserted = 0
    for row in products:
        p_id, title, desc, brand = row
        # Combine all searchable text fields for rich semantic representation
        text_to_embed = f"{title}. {brand}. {desc}"

        vector = model.encode(text_to_embed).tolist()

        cur.execute("""
            INSERT INTO product_embeddings (product_id, model_name, model_version, embedding_vector)
            VALUES (%s, %s, %s, %s)
        """, (p_id, MODEL_NAME, MODEL_VERSION, vector))

        inserted += 1
        if inserted % 500 == 0:
            logger.info(f"   [{inserted}/{len(products)}] processed...")
            conn.commit()

    conn.commit()
    cur.close()
    conn.close()
    elapsed = time.time() - start_time
    logger.info(f"Success! {inserted} multilingual embeddings generated in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    run()
