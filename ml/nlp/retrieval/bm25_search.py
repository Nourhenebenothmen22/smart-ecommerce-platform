"""
BM25 Retriever — PostgreSQL Full-Text Search Implementation.

Uses plainto_tsquery for safe query parsing and returns enriched product data
with business filters (is_active, stock > 0).
"""
import logging
from typing import List, Dict, Any
import sys
import os

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

from core.db import get_db_cursor

logger = logging.getLogger(__name__)


class BM25Retriever:
    """
    Implements BM25-like retrieval using PostgreSQL native full-text search.
    Uses plainto_tsquery for safe input handling (no special character crashes).
    Searches across title, description, and brand.
    """

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search products using PostgreSQL full-text search.
        Returns enriched product data including price, brand, description, rating, stock.
        """
        results = []
        clean_query = query.strip()
        if not clean_query:
            return results

        try:
            with get_db_cursor() as cur:
                # Try pre-computed search_vector column first (requires 011_fts_search.sql migration)
                # Falls back to expression-based search if column doesn't exist
                try:
                    cur.execute("""
                        SELECT p.id, p.title, p.brand, p.price, p.final_price,
                               LEFT(p.description, 200) AS description_preview,
                               p.rating_avg, p.stock,
                               ts_rank(p.search_vector, plainto_tsquery('french', %s)) AS score
                        FROM products p
                        WHERE p.search_vector @@ plainto_tsquery('french', %s)
                          AND p.is_active = TRUE
                          AND p.stock > 0
                        ORDER BY score DESC
                        LIMIT %s
                    """, (clean_query, clean_query, top_k))
                except Exception:
                    # Fallback: expression-based FTS (works without migration, slower)
                    logger.info("search_vector column not found, using expression-based FTS")
                    cur.execute("""
                        SELECT p.id, p.title, p.brand, p.price, p.final_price,
                               LEFT(p.description, 200) AS description_preview,
                               p.rating_avg, p.stock,
                               ts_rank(
                                   to_tsvector('french', p.title || ' ' || p.description || ' ' || p.brand),
                                   plainto_tsquery('french', %s)
                               ) AS score
                        FROM products p
                        WHERE to_tsvector('french', p.title || ' ' || p.description || ' ' || p.brand)
                              @@ plainto_tsquery('french', %s)
                          AND p.is_active = TRUE
                          AND p.stock > 0
                        ORDER BY score DESC
                        LIMIT %s
                    """, (clean_query, clean_query, top_k))

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
                        "source": "bm25"
                    })

        except Exception as e:
            logger.error(f"BM25 search error: {e}", exc_info=True)

        return results
