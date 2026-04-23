"""
Hybrid Retriever — Reciprocal Rank Fusion (RRF) of BM25 + Vector search.

Combines the strengths of both retrievers:
- BM25: Exact keyword matching (good for product names, brands, model numbers)
- Vector: Semantic understanding (good for intent, synonyms, descriptions)

Uses RRF formula: score(d) = Σ 1 / (k + rank(d))
"""
import logging
from typing import List, Dict, Any
import sys
import os

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

from nlp.retrieval.bm25_search import BM25Retriever
from nlp.retrieval.vector_search import DenseVectorRetriever

logger = logging.getLogger(__name__)

# RRF constant — standard value from the original paper (Cormack et al., 2009)
RRF_K = 60


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

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Execute both BM25 and Vector search, then fuse results using RRF.
        Each retriever fetches top_k * 2 results for better fusion quality.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        # Fetch from both retrievers (extra results for better fusion)
        fetch_k = top_k * 2

        bm25_results = []
        vector_results = []

        # BM25 search — may return empty if no lexical match, that's OK
        try:
            bm25_results = self.bm25.search(clean_query, top_k=fetch_k)
            logger.info(f"BM25 returned {len(bm25_results)} results for '{clean_query}'")
        except Exception as e:
            logger.warning(f"BM25 search failed, continuing with vector only: {e}")

        # Vector search — primary retriever
        try:
            vector_results = self.vector.search(clean_query, top_k=fetch_k)
            logger.info(f"Vector returned {len(vector_results)} results for '{clean_query}'")
        except Exception as e:
            logger.warning(f"Vector search failed, continuing with BM25 only: {e}")

        # If both failed, return empty
        if not bm25_results and not vector_results:
            logger.warning(f"Both retrievers returned 0 results for '{clean_query}'")
            return []

        # If only one retriever has results, return its results directly
        if not bm25_results:
            return vector_results[:top_k]
        if not vector_results:
            return bm25_results[:top_k]

        # --- Reciprocal Rank Fusion ---
        rrf_scores: Dict[int, float] = {}
        product_data: Dict[int, Dict[str, Any]] = {}

        # Score Vector results first (often has richer metadata or more reliable fields)
        for rank, result in enumerate(vector_results):
            pid = result["product_id"]
            rrf_scores[pid] = rrf_scores.get(pid, 0) + 1 / (RRF_K + rank + 1)
            product_data[pid] = result

        # Score BM25 results (add to score, but don't overwrite Vector metadata if already present)
        for rank, result in enumerate(bm25_results):
            pid = result["product_id"]
            rrf_scores[pid] = rrf_scores.get(pid, 0) + 1 / (RRF_K + rank + 1)
            if pid not in product_data:
                product_data[pid] = result

        # Sort by fused RRF score
        sorted_pids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # Build final results
        results = []
        for pid in sorted_pids[:top_k]:
            item = product_data[pid].copy()
            item["score"] = round(rrf_scores[pid], 4)
            item["source"] = "hybrid"
            results.append(item)

        logger.info(f"Hybrid RRF returned {len(results)} merged results (from {len(bm25_results)} BM25 + {len(vector_results)} vector)")
        return results
