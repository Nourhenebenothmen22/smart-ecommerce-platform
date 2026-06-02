import logging
import re
import unicodedata
from typing import List, Dict, Any
import sys
import os

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

from core.db import get_db_cursor

logger = logging.getLogger(__name__)

_WORD_SPLIT_RE = re.compile(r"[^\w\-']+")
_MIN_WORD_LENGTH = 2
_STOPWORDS = {
    "a", "about", "and", "avec", "compare", "comparaison", "de", "des", "du",
    "et", "for", "give", "i", "je", "le", "la", "les", "me", "montre",
    "existe", "moins", "pas", "pour", "produit", "produits", "qui", "show",
    "sous", "the", "to", "un", "under", "une", "veut", "veux", "want", "with",
}


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _extract_search_terms(raw_query: str) -> list[str]:
    query = _normalize_text(raw_query.strip())
    query = re.sub(r"\$?\d+(?:[.,]\d+)?(?:dollars?|euros?|usd|eur)?", " ", query)
    words = _WORD_SPLIT_RE.split(query)
    words = [w for w in words if len(w) > _MIN_WORD_LENGTH and w not in _STOPWORDS]
    return words


class BM25Retriever:
    """
    Full-text search using per-term OR logic for natural language queries.
    Each word in the query is searched independently; products matching any
    term are returned, ranked by how many terms match.
    """
    def __init__(self):
        pass

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        results = []

        clean_query = query.strip()
        if not clean_query:
            return results

        terms = _extract_search_terms(clean_query)
        if not terms:
            logger.info("No search terms extracted from '%s'", clean_query)
            return results

        try:
            with get_db_cursor() as cur:
                results = self._fts_or_search(cur, terms, top_k)
                if not results:
                    results = self._like_or_search(cur, terms, top_k)
        except Exception as e:
            logger.error("BM25 search error: %s", e, exc_info=True)

        return results

    @staticmethod
    def _fts_or_search(cur, terms: list[str], top_k: int) -> List[Dict[str, Any]]:
        tsvector = (
            "to_tsvector('french', "
            "COALESCE(p.title, '') || ' ' || "
            "COALESCE(p.brand, '') || ' ' || "
            "COALESCE(p.description, '')"
            ")"
        )

        where_clauses = []
        rank_exprs = []
        params = []

        for term in terms:
            tsq_param = f"websearch_to_tsquery('french', %s)"
            where_clauses.append(f"{tsvector} @@ {tsq_param}")
            rank_exprs.append(f"COALESCE(ts_rank({tsvector}, {tsq_param}), 0)")
            params.extend([term, term])

        rank_sum = " + ".join(rank_exprs)
        where_combined = " OR ".join(where_clauses)

        sql = f"""
            SELECT p.id, p.title, p.brand, p.price, p.final_price,
                   LEFT(p.description, 1000) AS description_preview,
                   p.rating_avg, p.stock,
                   c.name AS category_name,
                   s.name AS subcategory_name,
                   ({rank_sum}) AS score
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN subcategories s ON s.id = p.subcategory_id
            WHERE ({where_combined})
              AND p.is_active = TRUE
              AND p.stock > 0
            ORDER BY score DESC
            LIMIT %s
        """
        params.append(top_k)

        try:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            results = []
            for row in rows:
                results.append({
                    "product_id": row[0],
                    "name": row[1],
                    "brand": row[2],
                    "price": float(row[3]) if row[3] else 0.0,
                    "final_price": float(row[4]) if row[4] else 0.0,
                    "description": row[5] or "",
                    "rating_avg": float(row[6]) if row[6] else 0.0,
                    "stock": row[7] or 0,
                    "category": row[8] or "",
                    "subcategory": row[9] or "",
                    "score": round(float(row[10]), 4) if row[10] else 0.0,
                    "source": "bm25"
                })
            logger.info("FTS OR search returned %s results for terms=%s", len(results), terms)
            return results
        except Exception as e:
            logger.error("FTS OR search error: %s", e, exc_info=True)
            return []

    @staticmethod
    def _like_or_search(cur, terms: list[str], top_k: int) -> List[Dict[str, Any]]:
        like_clauses = []
        params = []
        for term in terms:
            pattern = f"%{term}%"
            like_clauses.append(
                f"(p.title ILIKE %s OR p.brand ILIKE %s OR p.description ILIKE %s)"
            )
            params.extend([pattern, pattern, pattern])

        score_expr = " + ".join(
            f"(CASE WHEN p.title ILIKE %s THEN 3 WHEN p.brand ILIKE %s THEN 2 WHEN p.description ILIKE %s THEN 1 ELSE 0 END)"
            for _ in terms
        )
        for term in terms:
            pattern = f"%{term}%"
            params.extend([pattern, pattern, pattern])

        where_combined = " OR ".join(like_clauses)
        params.append(top_k)

        sql = f"""
            SELECT p.id, p.title, p.brand, p.price, p.final_price,
                   LEFT(p.description, 1000) AS description_preview,
                   p.rating_avg, p.stock,
                   c.name AS category_name,
                   s.name AS subcategory_name,
                   ({score_expr}) AS score
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN subcategories s ON s.id = p.subcategory_id
            WHERE ({where_combined})
              AND p.is_active = TRUE
              AND p.stock > 0
            ORDER BY score DESC
            LIMIT %s
        """

        try:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            results = []
            for row in rows:
                results.append({
                    "product_id": row[0],
                    "name": row[1],
                    "brand": row[2],
                    "price": float(row[3]) if row[3] else 0.0,
                    "final_price": float(row[4]) if row[4] else 0.0,
                    "description": row[5] or "",
                    "rating_avg": float(row[6]) if row[6] else 0.0,
                    "stock": row[7] or 0,
                    "category": row[8] or "",
                    "subcategory": row[9] or "",
                    "score": round(float(row[10]), 4) if row[10] else 0.0,
                    "source": "bm25_fallback"
                })
            logger.info("ILIKE OR search returned %s results for terms=%s", len(results), terms)
            return results
        except Exception as e:
            logger.error("ILIKE OR search error: %s", e, exc_info=True)
            return []
