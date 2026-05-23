"""
Dense Vector Retriever — Semantic Search via pgvector.

Uses a multilingual SentenceTransformer model for French-compatible embeddings
and returns enriched product data with business filters.
"""
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import sys
import os

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

from core.db import get_db_cursor
from core.config import settings

logger = logging.getLogger(__name__)

# Multilingual model — supports French, English, and 50+ languages (384 dimensions)
DEFAULT_MODEL = settings.EMBEDDING_MODEL_NAME
DEFAULT_MODEL_VERSION = settings.EMBEDDING_MODEL_VERSION


class DenseVectorRetriever:
    """
    Implements semantic search using multilingual sentence embeddings and cosine similarity.
    Queries the PostgreSQL pgvector database with business filters.
    """

    def __init__(self, embedding_model: str = DEFAULT_MODEL, model_version: str = DEFAULT_MODEL_VERSION):
        logger.info(f"Loading SentenceTransformer: {embedding_model}...")
        self.model_name = embedding_model
        self.model_version = model_version
        self.model = SentenceTransformer(embedding_model)
        logger.info(f"SentenceTransformer loaded: {embedding_model}")

    def _get_embedding(self, text: str) -> List[float]:
        """Convert text query to dense vector."""
        return self.model.encode(text).tolist()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a semantic search in pgvector.
        Returns enriched product data including price, brand, description, rating, stock.
        Filters out inactive products and zero-stock items.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        vector = self._get_embedding(clean_query)
        results = []

        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.title, p.brand, p.price, p.final_price,
                           LEFT(p.description, 1000) AS description_preview,
                           p.rating_avg, p.stock,
                           1 - (pe.embedding_vector <=> %s::vector) AS similarity
                    FROM products p
                    JOIN product_embeddings pe ON p.id = pe.product_id
                    WHERE p.is_active = TRUE
                      AND p.stock > 0
                      AND pe.model_name = %s
                      AND pe.model_version = %s
                    ORDER BY pe.embedding_vector <=> %s::vector
                    LIMIT %s
                """, (vector, self.model_name, self.model_version, vector, top_k))

                for row in cur.fetchall():
                    results.append({
                        "product_id": row[0],
                        "name": row[1],
                        "brand": row[2],
                        "price": float(row[3]) if row[3] else 0.0,
                        "final_price": float(row[4]) if row[4] else 0.0,
                        "description": row[5] or "",
                        "rating_avg": float(row[6]) if row[6] else 0.0,
                        "stock": row[7] or 0,
                        "score": round(float(row[8]), 4) if row[8] else 0.0,
                        "source": "vector"
                    })

        except Exception as e:
            logger.error(f"Vector search error: {e}", exc_info=True)

        return results
