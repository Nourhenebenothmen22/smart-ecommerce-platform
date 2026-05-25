"""
Generate or refresh product embeddings using versioned upserts.
"""

import logging
import os
import time

import psycopg2
from sentence_transformers import SentenceTransformer

from ml.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAME = settings.EMBEDDING_MODEL_NAME
MODEL_VERSION = settings.EMBEDDING_MODEL_VERSION
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))


def get_connection():
    try:
        return psycopg2.connect(**settings.db_config_dict)
    except Exception as exc:
        raise RuntimeError(
            f"Cannot connect to database on {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}: {exc}"
        ) from exc


def run():
    logger.info("1. Loading embedding model (%s v%s).", MODEL_NAME, MODEL_VERSION)
    model = SentenceTransformer(MODEL_NAME, local_files_only=not settings.ML_ALLOW_MODEL_DOWNLOADS)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO ml_models (model_name, model_version, model_type, algorithm, is_active, trained_at)
        VALUES (%s, %s, 'embedding', 'transformer', true, NOW())
        ON CONFLICT (model_name, model_version)
        DO UPDATE SET
            model_type = EXCLUDED.model_type,
            algorithm = EXCLUDED.algorithm,
            is_active = true,
            trained_at = NOW();
        """,
        (MODEL_NAME, MODEL_VERSION),
    )
    conn.commit()

    cur.execute("SELECT id, title, description, brand FROM products WHERE is_active = TRUE;")
    products = cur.fetchall()

    logger.info("2. Generating embeddings for %d active products.", len(products))
    start_time = time.time()

    inserted = 0
    for start in range(0, len(products), EMBEDDING_BATCH_SIZE):
        batch = products[start : start + EMBEDDING_BATCH_SIZE]
        texts_to_embed = [f"{title or ''}. {brand or ''}. {desc or ''}" for _, title, desc, brand in batch]
        vectors = model.encode(
            texts_to_embed,
            batch_size=EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
        )

        for (p_id, _title, _desc, _brand), vector in zip(batch, vectors):
            cur.execute(
                """
                INSERT INTO product_embeddings (product_id, model_name, model_version, embedding_vector)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (product_id, model_name, model_version)
                DO UPDATE SET embedding_vector = EXCLUDED.embedding_vector, created_at = NOW();
                """,
                (p_id, MODEL_NAME, MODEL_VERSION, vector.tolist()),
            )

        inserted += len(batch)
        logger.info("   [%d/%d] processed.", inserted, len(products))
        conn.commit()

    conn.commit()
    cur.close()
    conn.close()
    elapsed = time.time() - start_time
    logger.info("Success. %d embeddings upserted in %.2f seconds.", inserted, elapsed)


if __name__ == "__main__":
    run()
