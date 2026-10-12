"""
ml/rag — Unified, Modular RAG Package for DarStore E-Commerce.

Public API:
- HybridRetriever, DenseVectorRetriever, BM25Retriever (Recherche Hybride BM25 + Vector + RRF)
- RAGChatbotAgent (Générateur déterministe DB-grounded & guardrails)
- generate_product_embeddings, format_embedding_text (Ingestion & Embeddings)
- run_rag_benchmark, RAGBenchmarkCase, RetrievalMetrics (Évaluation IR & RAGAS)
"""

from .retrieval import HybridRetriever, DenseVectorRetriever, BM25Retriever
from .agent import RAGChatbotAgent
from .embeddings import generate_product_embeddings, format_embedding_text
from .evaluation import run_rag_benchmark, RAGBenchmarkCase, RetrievalMetrics

__all__ = [
    "HybridRetriever",
    "DenseVectorRetriever",
    "BM25Retriever",
    "RAGChatbotAgent",
    "generate_product_embeddings",
    "format_embedding_text",
    "run_rag_benchmark",
    "RAGBenchmarkCase",
    "RetrievalMetrics",
]
