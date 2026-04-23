"""
similarity_eval.py — Real evaluation of BM25 vs Dense Vector vs Hybrid search.

Runs actual queries against the database and measures precision, latency,
and result quality. Results can be inserted into nlp_similarity_metrics.
"""
import time
import sys
import os
import json
import logging

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Test queries with expected relevant product categories/keywords
TEST_QUERIES = [
    {
        "query": "téléphone portable avec bonne batterie",
        "expected_keywords": ["phone", "smartphone", "mobile", "téléphone", "batterie"],
        "type": "semantic"
    },
    {
        "query": "iphone 12 pro max",
        "expected_keywords": ["iphone", "apple"],
        "type": "exact"
    },
    {
        "query": "chaussures de course homme légères",
        "expected_keywords": ["chaussure", "course", "running", "sport"],
        "type": "semantic"
    },
    {
        "query": "Samsung Galaxy S21",
        "expected_keywords": ["samsung", "galaxy"],
        "type": "exact"
    },
    {
        "query": "cadeau tech pas cher",
        "expected_keywords": ["tech", "électronique"],
        "type": "intent"
    },
    {
        "query": "écouteurs bluetooth sans fil",
        "expected_keywords": ["écouteur", "bluetooth", "audio", "casque"],
        "type": "semantic"
    }
]


def compute_keyword_precision(results: list, expected_keywords: list) -> float:
    """
    Compute a simple keyword-based precision metric.
    Checks how many results contain at least one expected keyword in title/brand/description.
    """
    if not results:
        return 0.0

    hits = 0
    for r in results:
        text = f"{r.get('name', '')} {r.get('brand', '')} {r.get('description', '')}".lower()
        if any(kw.lower() in text for kw in expected_keywords):
            hits += 1

    return hits / len(results)


def evaluate_retriever(retriever_class, retriever_name: str, queries: list, top_k: int = 5):
    """Run evaluation on a single retriever."""
    results_summary = []

    for q in queries:
        query = q["query"]
        expected = q["expected_keywords"]

        start = time.time()
        try:
            results = retriever_class.search(query, top_k=top_k)
        except Exception as e:
            logger.error(f"  {retriever_name} failed on '{query}': {e}")
            results = []
        latency = (time.time() - start) * 1000

        precision = compute_keyword_precision(results, expected)

        results_summary.append({
            "query": query,
            "algorithm": retriever_name,
            "num_results": len(results),
            "precision_at_k": round(precision, 4),
            "latency_ms": round(latency, 2),
            "top_result": results[0].get("name", "N/A") if results else "N/A"
        })

        logger.info(
            f"  [{retriever_name}] '{query[:40]}...' → "
            f"{len(results)} results | P@{top_k}={precision:.2f} | {latency:.1f}ms"
        )

    return results_summary


def save_to_db(results: list, experiment_name: str):
    """Save evaluation results to nlp_similarity_metrics table."""
    try:
        from core.db import get_db_cursor
        with get_db_cursor(commit=True) as cur:
            for r in results:
                cur.execute("""
                    INSERT INTO nlp_similarity_metrics
                    (experiment_name, dataset_size, algorithm_name, precision_at_k, avg_latency_ms, hyperparameters)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    experiment_name,
                    len(TEST_QUERIES),
                    r["algorithm"],
                    r["precision_at_k"],
                    r["latency_ms"],
                    json.dumps({"query": r["query"], "top_result": r["top_result"]})
                ))
        logger.info(f"Results saved to nlp_similarity_metrics ({len(results)} rows)")
    except Exception as e:
        logger.warning(f"Could not save to DB (non-fatal): {e}")


def run_experiment(experiment_name: str = "Hybrid_Evaluation_v2"):
    """Run a full comparative evaluation of all retrievers."""
    print(f"\n{'='*60}")
    print(f"  Similarity Evaluation: {experiment_name}")
    print(f"{'='*60}\n")

    all_results = []

    # 1. BM25
    print("--- BM25 (Full-Text Search) ---")
    try:
        from nlp.retrieval.bm25_search import BM25Retriever
        bm25 = BM25Retriever()
        bm25_results = evaluate_retriever(bm25, "BM25", TEST_QUERIES)
        all_results.extend(bm25_results)
    except Exception as e:
        print(f"  BM25 unavailable: {e}")

    # 2. Dense Vector
    print("\n--- Dense Vector (Semantic Search) ---")
    try:
        from nlp.retrieval.vector_search import DenseVectorRetriever
        vector = DenseVectorRetriever()
        vector_results = evaluate_retriever(vector, "Dense_Cosine", TEST_QUERIES)
        all_results.extend(vector_results)
    except Exception as e:
        print(f"  Vector search unavailable: {e}")

    # 3. Hybrid RRF
    print("\n--- Hybrid RRF (BM25 + Vector) ---")
    try:
        from nlp.retrieval.hybrid_search import HybridRetriever
        hybrid = HybridRetriever()
        hybrid_results = evaluate_retriever(hybrid, "Hybrid_RRF", TEST_QUERIES)
        all_results.extend(hybrid_results)
    except Exception as e:
        print(f"  Hybrid search unavailable: {e}")

    # Summary
    print(f"\n{'='*60}")
    print("  Summary")
    print(f"{'='*60}")

    for algo in ["BM25", "Dense_Cosine", "Hybrid_RRF"]:
        algo_results = [r for r in all_results if r["algorithm"] == algo]
        if algo_results:
            avg_precision = sum(r["precision_at_k"] for r in algo_results) / len(algo_results)
            avg_latency = sum(r["latency_ms"] for r in algo_results) / len(algo_results)
            print(f"  {algo:15s} | Avg P@5: {avg_precision:.2f} | Avg Latency: {avg_latency:.1f}ms")

    # Save to DB
    if all_results:
        save_to_db(all_results, experiment_name)

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    run_experiment()
