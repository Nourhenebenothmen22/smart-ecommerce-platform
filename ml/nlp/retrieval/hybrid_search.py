"""
Hybrid Retriever — Reciprocal Rank Fusion (RRF) of BM25 + Vector search.

Combines the strengths of both retrievers:
- BM25: Exact keyword matching (good for product names, brands, model numbers)
- Vector: Semantic understanding (good for intent, synonyms, descriptions)

Uses RRF formula: score(d) = Σ 1 / (k + rank(d))
"""
import logging
import re
import unicodedata
from typing import List, Dict, Any
import sys
import os

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

from nlp.retrieval.bm25_search import BM25Retriever
from nlp.retrieval.vector_search import DenseVectorRetriever
from core.db import get_db_cursor

logger = logging.getLogger(__name__)

# RRF constant — standard value from the original paper (Cormack et al., 2009)
RRF_K = 60

_EXPENSIVE_RE = re.compile(
    r"\b(plus\s+cher|plus\s+chers|cher\s+produit|chers\s+produits|expensive|highest\s+price|most\s+expensive)\b",
    re.IGNORECASE,
)
_CHEAP_RE = re.compile(
    r"\b(moins?\s+cher|moins?\s+chers?|pas\s+cher|pas\s+chers?|cheap|cheapest|lowest\s+price)\b",
    re.IGNORECASE,
)

_PRICE_CONSTRAINT_RE = re.compile(
    r"(?:under|less\s+than|below|sous|moins\s+de|inferieur\s+a|inférieur\s+à|"
    r"max|maximum|at\s+most|up\s+to|not\s+exceeding|"
    r"pas\s+plus\s+cher\s+que|<=?)\s*\$?(?:eur|usd)?\s*(\d+(?:[.,]\d+)?)|"
    r"(?:over|more\s+than|above|plus\s+de|supérieur\s+à|superieur\s+a|"
    r"min|minimum|at\s+least|>=?)\s*\$?(?:eur|usd)?\s*(\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)

_PRICE_TOKEN_RE = re.compile(
    r"\$\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?\s*(?:dollars?|euros?|usd|eur)",
    re.IGNORECASE,
)
_COMPARISON_RE = re.compile(
    r"\b(compare|comparer|comparaison|versus|vs|difference|diff[eé]rence|entre)\b",
    re.IGNORECASE,
)
_WORD_SPLIT_RE = re.compile(r"[^\w\-']+")
_QUERY_STOPWORDS = {
    "a", "about", "and", "avec", "compare", "comparer", "comparaison", "de",
    "des", "du", "et", "for", "i", "je", "la", "le", "les", "me", "montre",
    "existe", "moins", "pas", "pour", "produit", "produits", "qui", "show",
    "sous", "the", "to", "un", "under", "une", "veut", "veux", "want", "with",
}
_MIN_TEXT_SCORE = 0.01
_MIN_VECTOR_SCORE = 0.15


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _query_terms(query: str) -> list[str]:
    clean = _normalize_text(_remove_price_tokens(query))
    terms = _WORD_SPLIT_RE.split(clean)
    return [term for term in terms if len(term) > 2 and term not in _QUERY_STOPWORDS]


def _product_row(row, score: float, source: str) -> Dict[str, Any]:
    item = {
        "product_id": row[0],
        "name": row[1],
        "brand": row[2],
        "price": float(row[3]) if row[3] else 0.0,
        "final_price": float(row[4]) if row[4] else 0.0,
        "description": row[5] or "",
        "rating_avg": float(row[6]) if row[6] else 0.0,
        "stock": row[7] or 0,
        "score": round(float(score), 4),
        "source": source,
    }
    if len(row) > 8:
        item["category"] = row[8] or ""
    if len(row) > 9:
        item["subcategory"] = row[9] or ""
    return item


def _extract_price_constraint(query: str) -> tuple[str | None, float | None]:
    m = _PRICE_CONSTRAINT_RE.search(query)
    if not m:
        return None, None
    if m.group(1):
        return "max", float(m.group(1).replace(",", "."))
    if m.group(2):
        return "min", float(m.group(2).replace(",", "."))
    return None, None


def _remove_price_tokens(text: str) -> str:
    return _PRICE_TOKEN_RE.sub("", text).strip()


def _search_products_by_price(order: str, top_k: int) -> List[Dict[str, Any]]:
    direction = "DESC" if order == "desc" else "ASC"
    with get_db_cursor() as cur:
        cur.execute(f"""
            SELECT p.id, p.title, p.brand, p.price, p.final_price,
                   LEFT(p.description, 1000) AS description_preview,
                   p.rating_avg, p.stock,
                   c.name AS category_name,
                   s.name AS subcategory_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN subcategories s ON s.id = p.subcategory_id
            WHERE p.is_active = TRUE
              AND p.stock > 0
              AND p.price IS NOT NULL
              AND p.price > 0
            ORDER BY COALESCE(NULLIF(p.final_price, 0), p.price) {direction}, p.id ASC
            LIMIT %s
        """, (top_k,))

        results = []
        for rank, row in enumerate(cur.fetchall(), 1):
            results.append(_product_row(row, 1 / rank, "catalog_price_desc" if order == "desc" else "catalog_price_asc"))
        return results


class HybridRetriever:
    """
    Hybrid retriever combining BM25 (lexical) and Dense Vector (semantic) search
    using Reciprocal Rank Fusion for result merging.
    """

    def __init__(self):
        logger.info("Initializing HybridRetriever...")
        self.bm25 = BM25Retriever()
        self.vector = DenseVectorRetriever()
        logger.info("HybridRetriever ready (BM25 + Vector).")

    def _apply_price_filter(self, results: List[Dict[str, Any]], constraint: tuple[str | None, float | None]) -> List[Dict[str, Any]]:
        direction, value = constraint
        if direction is None or value is None:
            return results
        filtered = []
        for item in results:
            effective_price = float(item.get("final_price") or item.get("price") or 0)
            if direction == "max" and effective_price <= value:
                filtered.append(item)
            elif direction == "min" and effective_price >= value:
                filtered.append(item)
        return filtered

    def _filter_relevant(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        filtered = []
        for item in results:
            source = str(item.get("source", ""))
            score = float(item.get("score") or 0)
            if source.startswith("vector") and score < _MIN_VECTOR_SCORE:
                continue
            if source == "bm25_fallback" and score < 2:
                continue
            if source.startswith("bm25") and score < _MIN_TEXT_SCORE:
                continue
            filtered.append(item)
        return filtered

    def _find_catalog_entities(self, query: str) -> list[dict[str, Any]]:
        normalized_query = _normalize_text(query)
        terms = set(_query_terms(query))
        entities: list[dict[str, Any]] = []

        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT 'brand' AS entity_type, brand AS name, COUNT(*) AS product_count
                FROM products
                WHERE is_active = TRUE AND stock > 0 AND brand IS NOT NULL
                GROUP BY brand
                UNION ALL
                SELECT 'category' AS entity_type, c.name AS name, COUNT(*) AS product_count
                FROM categories c
                JOIN products p ON p.category_id = c.id
                WHERE p.is_active = TRUE AND p.stock > 0
                GROUP BY c.name
                UNION ALL
                SELECT 'subcategory' AS entity_type, s.name AS name, COUNT(*) AS product_count
                FROM subcategories s
                JOIN products p ON p.subcategory_id = s.id
                WHERE p.is_active = TRUE AND p.stock > 0
                GROUP BY s.name
                ORDER BY product_count DESC
                """
            )
            for row in cur.fetchall():
                entity_type, name, product_count = row
                normalized_name = _normalize_text(str(name))
                name_terms = set(_WORD_SPLIT_RE.split(normalized_name))
                if normalized_name and (
                    normalized_name in normalized_query
                    or bool(name_terms.intersection(terms))
                ):
                    position = normalized_query.find(normalized_name)
                    if position < 0:
                        positions = [normalized_query.find(term) for term in name_terms if normalized_query.find(term) >= 0]
                        position = min(positions) if positions else 10_000
                    entities.append({
                        "type": entity_type,
                        "name": name,
                        "product_count": product_count,
                        "position": position,
                    })

        deduped: list[dict[str, Any]] = []
        seen = set()
        for entity in entities:
            key = (entity["type"], _normalize_text(entity["name"]))
            if key not in seen:
                seen.add(key)
                deduped.append(entity)
        return sorted(deduped, key=lambda item: (item["position"], -int(item["product_count"])))

    def _search_by_combined_entities(
        self,
        entities: list[dict[str, Any]],
        top_k: int,
        price_constraint: tuple[str | None, float | None],
    ) -> List[Dict[str, Any]]:
        brands = [entity["name"] for entity in entities if entity["type"] == "brand"]
        categories = [entity["name"] for entity in entities if entity["type"] == "category"]
        subcategories = [entity["name"] for entity in entities if entity["type"] == "subcategory"]
        if not brands or not (categories or subcategories):
            return []

        where = ["p.brand = ANY(%s)", "p.is_active = TRUE", "p.stock > 0"]
        params: list[Any] = [brands]
        if categories and subcategories:
            where.append("(c.name = ANY(%s) OR s.name = ANY(%s))")
            params.extend([categories, subcategories])
        elif categories:
            where.append("c.name = ANY(%s)")
            params.append(categories)
        else:
            where.append("s.name = ANY(%s)")
            params.append(subcategories)

        if price_constraint[0] == "max" and price_constraint[1] is not None:
            where.append("COALESCE(NULLIF(p.final_price, 0), p.price) <= %s")
            params.append(price_constraint[1])
        elif price_constraint[0] == "min" and price_constraint[1] is not None:
            where.append("COALESCE(NULLIF(p.final_price, 0), p.price) >= %s")
            params.append(price_constraint[1])

        params.append(top_k)
        with get_db_cursor() as cur:
            cur.execute(f"""
                SELECT p.id, p.title, p.brand, p.price, p.final_price,
                       LEFT(p.description, 1000) AS description_preview,
                       p.rating_avg, p.stock,
                       c.name AS category_name,
                       s.name AS subcategory_name
                FROM products p
                JOIN categories c ON c.id = p.category_id
                JOIN subcategories s ON s.id = p.subcategory_id
                WHERE {" AND ".join(where)}
                ORDER BY p.rating_avg DESC,
                         COALESCE(NULLIF(p.final_price, 0), p.price) ASC,
                         p.id ASC
                LIMIT %s
            """, tuple(params))
            results = []
            for rank, row in enumerate(cur.fetchall(), 1):
                item = _product_row(row, 1 / rank, "entity_combined")
                item["matched_entity"] = ", ".join(brands + categories + subcategories)
                results.append(item)
            return results

    def _search_by_entities(
        self,
        entities: list[dict[str, Any]],
        top_k: int,
        price_constraint: tuple[str | None, float | None],
    ) -> List[Dict[str, Any]]:
        if not entities:
            return []

        per_entity_limit = max(1, min(3, top_k))
        results: list[dict[str, Any]] = []
        seen_products: set[int] = set()

        with get_db_cursor() as cur:
            for entity in entities[:4]:
                if entity["type"] == "brand":
                    predicate = "p.brand = %s"
                elif entity["type"] == "category":
                    predicate = "c.name = %s"
                else:
                    predicate = "s.name = %s"

                price_sql = ""
                params: list[Any] = [entity["name"]]
                if price_constraint[0] == "max" and price_constraint[1] is not None:
                    price_sql = "AND COALESCE(NULLIF(p.final_price, 0), p.price) <= %s"
                    params.append(price_constraint[1])
                elif price_constraint[0] == "min" and price_constraint[1] is not None:
                    price_sql = "AND COALESCE(NULLIF(p.final_price, 0), p.price) >= %s"
                    params.append(price_constraint[1])

                params.append(per_entity_limit)
                cur.execute(f"""
                    SELECT p.id, p.title, p.brand, p.price, p.final_price,
                           LEFT(p.description, 1000) AS description_preview,
                           p.rating_avg, p.stock,
                           c.name AS category_name,
                           s.name AS subcategory_name
                    FROM products p
                    JOIN categories c ON c.id = p.category_id
                    JOIN subcategories s ON s.id = p.subcategory_id
                    WHERE {predicate}
                      AND p.is_active = TRUE
                      AND p.stock > 0
                      {price_sql}
                    ORDER BY p.rating_avg DESC,
                             COALESCE(NULLIF(p.final_price, 0), p.price) ASC,
                             p.id ASC
                    LIMIT %s
                """, tuple(params))

                for rank, row in enumerate(cur.fetchall(), 1):
                    pid = int(row[0])
                    if pid in seen_products:
                        continue
                    seen_products.add(pid)
                    item = _product_row(row, 1 / rank, f"entity_{entity['type']}")
                    item["matched_entity"] = entity["name"]
                    item["matched_entity_type"] = entity["type"]
                    results.append(item)

        return results[:top_k]

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Execute both BM25 and Vector search, then fuse results using RRF.
        Always runs both retrievers for proper hybrid fusion.
        Extracts price constraints from natural language queries.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        price_constraint = _extract_price_constraint(clean_query)
        search_query = _remove_price_tokens(clean_query) or clean_query
        entities = self._find_catalog_entities(search_query)

        try:
            if _EXPENSIVE_RE.search(search_query):
                results = _search_products_by_price("desc", top_k)
                logger.info("Catalog price intent returned %s expensive products for '%s'", len(results), search_query)
                if price_constraint[0]:
                    results = self._apply_price_filter(results, price_constraint)
                return results
            if _CHEAP_RE.search(search_query):
                results = _search_products_by_price("asc", top_k)
                logger.info("Catalog price intent returned %s cheap products for '%s'", len(results), search_query)
                if price_constraint[0]:
                    results = self._apply_price_filter(results, price_constraint)
                return results
        except Exception as e:
            logger.warning("Catalog price intent failed, continuing with hybrid retrieval: %s", e)

        if _COMPARISON_RE.search(search_query) or len(entities) >= 2:
            combined_results = self._search_by_combined_entities(entities, top_k, price_constraint)
            if combined_results:
                logger.info("Combined entity retrieval returned %s products for entities=%s", len(combined_results), entities)
                return combined_results
            entity_results = self._search_by_entities(entities, top_k, price_constraint)
            if entity_results:
                logger.info("Entity retrieval returned %s products for entities=%s", len(entity_results), entities)
                return entity_results

        fetch_k = top_k * 2

        bm25_results = []
        vector_results = []

        try:
            bm25_results = self.bm25.search(search_query, top_k=fetch_k)
            bm25_results = self._filter_relevant(bm25_results)
            logger.info(f"BM25 returned {len(bm25_results)} results for '{search_query}'")
        except Exception as e:
            logger.warning(f"BM25 search failed, continuing with vector only: {e}")

        try:
            vector_results = self.vector.search(search_query, top_k=fetch_k)
            vector_results = self._filter_relevant(vector_results)
            logger.info(f"Vector returned {len(vector_results)} results for '{search_query}'")
        except Exception as e:
            logger.warning(f"Vector search failed, continuing with BM25 only: {e}")

        if not bm25_results and not vector_results:
            entity_results = self._search_by_entities(entities, top_k, price_constraint)
            if entity_results:
                return entity_results
            logger.warning(f"Both retrievers returned 0 results for '{search_query}'")
            return []

        if not bm25_results:
            results = vector_results[:top_k]
            if price_constraint[0]:
                results = self._apply_price_filter(results, price_constraint)
                if not results:
                    entity_results = self._search_by_entities(entities, top_k, price_constraint)
                    if entity_results:
                        return entity_results
            return results
        if not vector_results:
            results = bm25_results[:top_k]
            if price_constraint[0]:
                results = self._apply_price_filter(results, price_constraint)
                if not results:
                    entity_results = self._search_by_entities(entities, top_k, price_constraint)
                    if entity_results:
                        return entity_results
            return results

        rrf_scores: Dict[int, float] = {}
        product_data: Dict[int, Dict[str, Any]] = {}

        for rank, result in enumerate(vector_results):
            pid = result["product_id"]
            rrf_scores[pid] = rrf_scores.get(pid, 0) + 1 / (RRF_K + rank + 1)
            product_data[pid] = result

        for rank, result in enumerate(bm25_results):
            pid = result["product_id"]
            rrf_scores[pid] = rrf_scores.get(pid, 0) + 1 / (RRF_K + rank + 1)
            if pid not in product_data:
                product_data[pid] = result

        sorted_pids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        results = []
        for pid in sorted_pids[:top_k]:
            item = product_data[pid].copy()
            item["score"] = round(rrf_scores[pid], 4)
            item["source"] = "hybrid"
            results.append(item)

        if price_constraint[0]:
            results = self._apply_price_filter(results, price_constraint)
            if not results:
                entity_results = self._search_by_entities(entities, top_k, price_constraint)
                if entity_results:
                    return entity_results

        logger.info(f"Hybrid RRF returned {len(results)} merged results (from {len(bm25_results)} BM25 + {len(vector_results)} vector)")
        return results
