"""
ml/rag/retrieval.py — Hybrid Information Retrieval Engine for DarStore.

Combines:
1. Lexical Search (BM25): PostgreSQL Full-Text Search via pre-computed search_vector (GIN-indexed).
2. Semantic Search (Dense Vector): Multilingual sentence embeddings via pgvector (<=> cosine distance).
3. Reciprocal Rank Fusion (Weighted RRF): Dynamically blends ranks with query-dependent channel weights.
4. Entity Extraction & Caching: In-memory TTL cache (5 min) for active catalog brands and categories.
"""

import logging
import os
import re
import sys
import time
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

try:
    from ml.core.db import get_db_cursor
    from ml.core.config import settings
except ImportError:  # pragma: no cover
    from core.db import get_db_cursor
    from core.config import settings

logger = logging.getLogger(__name__)

# Constants
RRF_K = 60
DEFAULT_MODEL = getattr(settings, "EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
DEFAULT_MODEL_VERSION = getattr(settings, "EMBEDDING_MODEL_VERSION", "1.0")

_MIN_TEXT_SCORE = 0.01
_MIN_VECTOR_SCORE = 0.30

# Regular expressions
_WORD_SPLIT_RE = re.compile(r"[^\w\-']+")
_MIN_WORD_LENGTH = 2

_EXPENSIVE_RE = re.compile(
    r"\b(plus\s+cher|plus\s+chers|cher\s+produit|chers\s+produits|expensive|highest\s+price|most\s+expensive)\b",
    re.IGNORECASE,
)
_CHEAP_RE = re.compile(
    r"\b(moins?\s+cher|moins?\s+chers?|pas\s+cher|pas\s+chers?|cheap|cheapest|lowest\s+price|"
    r"prix\s+min(?:imum|imal)?|le\s+moins\s+co[uû]teux|plus?\s+(?:abordable|accessible)|"
    r"economique|économique|petit\s+prix|budget\s+serr[eé])\b",
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

_STOPWORDS = {
    "a", "about", "and", "avec", "compare", "comparaison", "de", "des", "du",
    "et", "for", "give", "i", "je", "le", "la", "les", "me", "montre",
    "existe", "moins", "pas", "pour", "produit", "produits", "qui", "show",
    "sous", "the", "to", "un", "under", "une", "veut", "veux", "want", "with",
    "bon", "bonne", "meilleur", "meilleure", "cherche", "trouve", "donne", "svp", "stp",
}


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _extract_price_constraint(query: str) -> Tuple[Optional[str], Optional[float]]:
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


def _extract_search_terms(raw_query: str) -> list[str]:
    query = _normalize_text(raw_query.strip())
    query = re.sub(r"\$?\d+(?:[.,]\d+)?(?:dollars?|euros?|usd|eur)?", " ", query)
    words = _WORD_SPLIT_RE.split(query)
    return [w for w in words if len(w) > _MIN_WORD_LENGTH and w not in _STOPWORDS]


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


# ── In-Memory TTL Cache pour les entités catalogue ──────────────────────────
_CATALOG_ENTITIES_CACHE: list[tuple[str, str, int, str, set[str]]] = []
_CATALOG_ENTITIES_TIMESTAMP: float = 0.0
_CATALOG_ENTITIES_TTL: float = 300.0  # 5 minutes


def _get_raw_catalog_entities() -> list[tuple[str, str, int, str, set[str]]]:
    global _CATALOG_ENTITIES_CACHE, _CATALOG_ENTITIES_TIMESTAMP
    now = time.monotonic()
    if _CATALOG_ENTITIES_CACHE and (now - _CATALOG_ENTITIES_TIMESTAMP) < _CATALOG_ENTITIES_TTL:
        return _CATALOG_ENTITIES_CACHE

    raw: list[tuple[str, str, int, str, set[str]]] = []
    try:
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
                raw.append((entity_type, name, int(product_count), normalized_name, name_terms))
        _CATALOG_ENTITIES_CACHE = raw
        _CATALOG_ENTITIES_TIMESTAMP = now
    except Exception as exc:
        logger.warning("Failed to refresh catalog entities: %s", exc)
    return _CATALOG_ENTITIES_CACHE


# ── 1. MOTEUR DE RECHERCHE LEXICALE (BM25 / FTS) ─────────────────────────────
class BM25Retriever:
    """
    Lexical retrieval using PostgreSQL Full-Text Search.
    Leverages pre-computed GIN index on search_vector with dynamic fallback.
    """

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        clean_query = query.strip()
        if not clean_query:
            return []

        terms = _extract_search_terms(clean_query)
        if not terms:
            return []

        try:
            with get_db_cursor() as cur:
                results = self._fts_or_search(cur, terms, top_k)
                if not results:
                    results = self._like_or_search(cur, terms, top_k)
                return results
        except Exception as e:
            logger.error("BM25 search error: %s", e, exc_info=True)
            return []

    @staticmethod
    def _fts_or_search(cur, terms: list[str], top_k: int) -> List[Dict[str, Any]]:
        tsvector_fallback = (
            "to_tsvector('french', "
            "COALESCE(p.title, '') || ' ' || "
            "COALESCE(p.brand, '') || ' ' || "
            "COALESCE(p.description, '')"
            ")"
        )
        tsvector_effective = f"COALESCE(p.search_vector, {tsvector_fallback})"

        where_clauses = []
        rank_exprs = []
        params = []

        for term in terms:
            tsq = "websearch_to_tsquery('french', %s)"
            where_clauses.append(
                f"(p.search_vector @@ {tsq} OR (p.search_vector IS NULL AND {tsvector_fallback} @@ {tsq}))"
            )
            rank_exprs.append(f"COALESCE(ts_rank({tsvector_effective}, {tsq}), 0)")
            params.extend([term, term, term])

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

        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        return [_product_row(row, row[10], "bm25") for row in rows]

    @staticmethod
    def _like_or_search(cur, terms: list[str], top_k: int) -> List[Dict[str, Any]]:
        like_clauses = []
        params = []
        for term in terms:
            pattern = f"%{term}%"
            like_clauses.append("(p.title ILIKE %s OR p.brand ILIKE %s OR p.description ILIKE %s)")
            params.extend([pattern, pattern, pattern])

        where_combined = " OR ".join(like_clauses)
        sql = f"""
            SELECT p.id, p.title, p.brand, p.price, p.final_price,
                   LEFT(p.description, 1000) AS description_preview,
                   p.rating_avg, p.stock,
                   c.name AS category_name,
                   s.name AS subcategory_name,
                   1.0 AS score
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN subcategories s ON s.id = p.subcategory_id
            WHERE ({where_combined})
              AND p.is_active = TRUE
              AND p.stock > 0
            LIMIT %s
        """
        params.append(top_k)
        cur.execute(sql, tuple(params))
        return [_product_row(row, 1.0, "bm25_fallback") for row in cur.fetchall()]


# ── 2. MOTEUR DE RECHERCHE SÉMANTIQUE (DENSE VECTOR / PGVECTOR) ───────────────
class DenseVectorRetriever:
    """
    Semantic search using multilingual sentence embeddings and pgvector.
    Employs cosine distance (<=> operator) with strict business filters.
    """

    def __init__(self, embedding_model: str = DEFAULT_MODEL, model_version: str = DEFAULT_MODEL_VERSION):
        self.model_name = embedding_model
        self.model_version = model_version
        self.model = None
        self._model_load_failed = False

    def _ensure_model(self) -> bool:
        if self.model is not None:
            return True
        if self._model_load_failed:
            return False

        allow_downloads = getattr(settings, "ML_ALLOW_MODEL_DOWNLOADS", True)
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name, local_files_only=not allow_downloads)
            return True
        except Exception as exc:
            self._model_load_failed = True
            logger.warning("Dense vector model unavailable; falling back to BM25-only retrieval: %s", exc)
            return False

    def _get_embedding(self, text: str) -> List[float]:
        if not self._ensure_model():
            return []
        return self.model.encode(text).tolist()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        clean_query = query.strip()
        if not clean_query:
            return []

        vector = self._get_embedding(clean_query)
        if not vector:
            return []

        try:
            with get_db_cursor() as cur:
                cur.execute(
                    """
                    SELECT p.id, p.title, p.brand, p.price, p.final_price,
                           LEFT(p.description, 1000) AS description_preview,
                           p.rating_avg, p.stock,
                           c.name AS category_name,
                           s.name AS subcategory_name,
                           1 - (pe.embedding_vector <=> %s::vector) AS similarity
                    FROM products p
                    JOIN product_embeddings pe ON p.id = pe.product_id
                    LEFT JOIN categories c ON c.id = p.category_id
                    LEFT JOIN subcategories s ON s.id = p.subcategory_id
                    WHERE p.is_active = TRUE
                      AND p.stock > 0
                      AND pe.model_name = %s
                      AND pe.model_version = %s
                    ORDER BY pe.embedding_vector <=> %s::vector
                    LIMIT %s
                    """,
                    (vector, self.model_name, self.model_version, vector, top_k),
                )
                rows = cur.fetchall()
                return [_product_row(row, row[10] or 0.0, "vector") for row in rows]
        except Exception as e:
            logger.error("Vector search error: %s", e, exc_info=True)
            return []


# ── 3. MOTEUR HYBRIDE RRF (RECIPROCAL RANK FUSION) ───────────────────────────
class HybridRetriever:
    """
    Hybrid retriever fusing BM25 (lexical) and Dense Vector (semantic) search
    using Weighted Reciprocal Rank Fusion (RRF).
    """

    def __init__(self):
        self.bm25 = BM25Retriever()
        self.vector = DenseVectorRetriever()

    def _apply_price_filter(self, results: List[Dict[str, Any]], constraint: Tuple[Optional[str], Optional[float]]) -> List[Dict[str, Any]]:
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
        words = _extract_search_terms(query)
        terms = set(words)
        entities: list[dict[str, Any]] = []

        catalog_entries = _get_raw_catalog_entities()
        for entity_type, name, product_count, normalized_name, name_terms in catalog_entries:
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

    def _finalize_results(
        self,
        results: List[Dict[str, Any]],
        clean_query: str,
        price_constraint: Tuple[Optional[str], Optional[float]],
    ) -> List[Dict[str, Any]]:
        """Apply price constraints and cheapest-first sort uniformly across all retrieval branches."""
        if price_constraint[0]:
            results = self._apply_price_filter(results, price_constraint)

        is_cheap_query = bool(_CHEAP_RE.search(clean_query))
        if is_cheap_query and results:
            results = sorted(
                results,
                key=lambda x: float(x.get("final_price") or x.get("price") or 0),
            )
            logger.info("Cheap intent detected — results re-sorted by price ascending")

        return results

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        clean_query = query.strip()
        if not clean_query:
            return []

        price_constraint = _extract_price_constraint(clean_query)
        search_query = _remove_price_tokens(clean_query) or clean_query
        entities = self._find_catalog_entities(search_query)

        fetch_k = top_k * 2
        bm25_results = []
        vector_results = []

        try:
            bm25_results = self._filter_relevant(self.bm25.search(search_query, top_k=fetch_k))
        except Exception as e:
            logger.warning("BM25 retrieval failed: %s", e)

        try:
            vector_results = self._filter_relevant(self.vector.search(search_query, top_k=fetch_k))
        except Exception as e:
            logger.warning("Vector retrieval failed: %s", e)

        if not bm25_results and not vector_results:
            return []

        if not bm25_results:
            strict_thresh = 0.48 if not entities else _MIN_VECTOR_SCORE
            valid_vec = [r for r in vector_results if float(r.get("score") or 0) >= strict_thresh]
            if not valid_vec:
                return []
            return self._finalize_results(valid_vec[:top_k], clean_query, price_constraint)

        if not vector_results:
            return self._finalize_results(bm25_results[:top_k], clean_query, price_constraint)

        # ── Weighted RRF (Adaptive Channel Weights) ─────────────────────────
        w_bm25 = 1.0
        w_dense = 1.0

        has_alphanumeric_or_code = bool(re.search(r"\b[a-zA-Z]+\d+|\d+[a-zA-Z]+\b", search_query))
        has_catalog_brand = any(e.get("type") == "brand" for e in entities)

        if has_alphanumeric_or_code or has_catalog_brand:
            w_bm25 = 1.2
            w_dense = 0.9
        elif len(search_query.split()) >= 4:
            w_dense = 1.2
            w_bm25 = 0.9

        rrf_scores: Dict[int, float] = {}
        product_data: Dict[int, Dict[str, Any]] = {}

        for rank, result in enumerate(vector_results):
            pid = result["product_id"]
            rrf_scores[pid] = rrf_scores.get(pid, 0) + w_dense / (RRF_K + rank + 1)
            product_data[pid] = result

        for rank, result in enumerate(bm25_results):
            pid = result["product_id"]
            rrf_scores[pid] = rrf_scores.get(pid, 0) + w_bm25 / (RRF_K + rank + 1)
            if pid not in product_data:
                product_data[pid] = result

        # Semantic query refinement
        is_top_query = bool(re.search(r"\b(top|meilleur|meilleurs|best|haut\s+de\s+gamme)\b", search_query, re.IGNORECASE))
        is_pc_query = bool(re.search(r"\b(pc|pcs|ordinateur|ordinateurs|laptop|laptops)\b", search_query, re.IGNORECASE))
        is_screen_query = bool(re.search(r"\b(ecran|ecrans|écran|écrans|moniteur|moniteurs|screen|display)\b", search_query, re.IGNORECASE))

        for pid in rrf_scores:
            p_item = product_data[pid]
            score_adj = rrf_scores[pid]
            if is_top_query:
                r_avg = float(p_item.get("rating_avg") or 0.0)
                if r_avg >= 4.0:
                    score_adj *= (1.0 + r_avg / 10.0)
            if is_pc_query and not is_screen_query:
                subcat = str(p_item.get("subcategory") or "").lower()
                if "monitor" in subcat:
                    score_adj *= 0.35
            rrf_scores[pid] = score_adj

        sorted_pids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        results = []
        for pid in sorted_pids[:top_k]:
            item = product_data[pid].copy()
            item["score"] = round(rrf_scores[pid], 4)
            item["source"] = "hybrid"
            results.append(item)

        return self._finalize_results(results, clean_query, price_constraint)
