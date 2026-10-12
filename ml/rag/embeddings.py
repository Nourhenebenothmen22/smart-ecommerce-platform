"""
ml/rag/embeddings.py — Product Embedding Generation and Indexing.

Structures catalog records into dense, 128-token semantic representations
and upserts vectors into PostgreSQL with model versioning.
"""

import logging
import os
import sys
import time
from typing import List, Tuple

try:
    import psycopg2
    from sentence_transformers import SentenceTransformer
    from ml.core.config import settings
except ImportError:  # pragma: no cover
    import psycopg2
    from sentence_transformers import SentenceTransformer
    from core.config import settings

logger = logging.getLogger(__name__)

MODEL_NAME = getattr(settings, "EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
MODEL_VERSION = getattr(settings, "EMBEDDING_MODEL_VERSION", "1.0")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))



def format_embedding_text(title: str, brand: str, cat: str, subcat: str, desc: str, price: float) -> str:
    """
    Format product attributes into a dense string safely under the 128-token limit.
    Prioritizes Title > Brand > Category > Price > First 60 keywords of description.
    """
    parts = []
    if title:
        parts.append(title.strip())
    if brand:
        parts.append(f"Marque: {brand.strip()}")
    if cat or subcat:
        category_str = f"{cat} / {subcat}" if (cat and subcat and cat != subcat) else (cat or subcat)
        parts.append(f"Categorie: {category_str.strip()}")
    if price:
        parts.append(f"Prix: {price} EUR")
    if desc:
        words = desc.strip().split()[:60]
        parts.append(" ".join(words))
    return ". ".join(parts)


def get_connection():
    try:
        return psycopg2.connect(**settings.db_config_dict)
    except Exception as exc:
        raise RuntimeError(
            f"Cannot connect to database on {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}: {exc}"
        ) from exc


def generate_product_embeddings(batch_size: int = 64) -> int:
    """
    Generate or refresh dense vector embeddings for all active products.
    Upserts into product_embeddings table without modifying database schema.
    """
    logger.info("Loading embedding model (%s v%s)...", MODEL_NAME, MODEL_VERSION)
    allow_downloads = getattr(settings, "ML_ALLOW_MODEL_DOWNLOADS", True)
    model = SentenceTransformer(MODEL_NAME, local_files_only=not allow_downloads)

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

    cur.execute(
        """
        SELECT p.id, p.title, p.description, p.brand,
               c.name AS category_name, s.name AS subcategory_name, p.price
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        LEFT JOIN subcategories s ON s.id = p.subcategory_id
        WHERE p.is_active = TRUE;
        """
    )
    products = cur.fetchall()
    logger.info("Generating embeddings for %d active products.", len(products))

    start_time = time.time()
    inserted = 0

    for start in range(0, len(products), batch_size):
        batch = products[start : start + batch_size]
        texts_to_embed = [
            format_embedding_text(title, brand, cat, subcat, desc, price)
            for _, title, desc, brand, cat, subcat, price in batch
        ]
        vectors = model.encode(texts_to_embed, batch_size=batch_size, show_progress_bar=False)

        for (p_id, *_), vector in zip(batch, vectors):
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
        conn.commit()

    cur.close()
    conn.close()
    elapsed = time.time() - start_time
    logger.info("Successfully upserted %d product embeddings in %.2f seconds.", inserted, elapsed)
    return inserted
