"""
Generate or refresh product embeddings using versioned upserts.
"""

import logging
import time

import psycopg2
from sentence_transformers import SentenceTransformer

from ml.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAME = settings.EMBEDDING_MODEL_NAME
MODEL_VERSION = settings.EMBEDDING_MODEL_VERSION


def get_connection():
    try:
        return psycopg2.connect(**settings.db_config_dict)
    except Exception as exc:
        raise RuntimeError(
            f"Cannot connect to database on {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}: {exc}"
        ) from exc


def run():
    logger.info("1. Loading embedding model (%s v%s).", MODEL_NAME, MODEL_VERSION)
    model = SentenceTransformer(MODEL_NAME)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO ml_models (model_name, model_version, model_type, algorithm, is_active)
        VALUES (%s, %s, 'embedding', 'transformer', true)
        ON CONFLICT (model_name, model_version)
        DO UPDATE SET model_type = EXCLUDED.model_type, algorithm = EXCLUDED.algorithm, is_active = true;
        """,
        (MODEL_NAME, MODEL_VERSION),
    )
    conn.commit()

    cur.execute("SELECT id, title, description, brand FROM products WHERE is_active = TRUE;")
    products = cur.fetchall()

    logger.info("2. Generating embeddings for %d active products.", len(products))
    start_time = time.time()

    inserted = 0
    for p_id, title, desc, brand in products:
        text_to_embed = f"{title or ''}. {brand or ''}. {desc or ''}"
        vector = model.encode(text_to_embed).tolist()

        cur.execute(
            """
            INSERT INTO product_embeddings (product_id, model_name, model_version, embedding_vector)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (product_id, model_name, model_version)
            DO UPDATE SET embedding_vector = EXCLUDED.embedding_vector, created_at = NOW();
            """,
            (p_id, MODEL_NAME, MODEL_VERSION, vector),
        )

        inserted += 1
        if inserted % 500 == 0:
            logger.info("   [%d/%d] processed.", inserted, len(products))
            conn.commit()

    conn.commit()
    cur.close()
    conn.close()
    elapsed = time.time() - start_time
    logger.info("Success. %d embeddings upserted in %.2f seconds.", inserted, elapsed)


if __name__ == "__main__":
    run()
