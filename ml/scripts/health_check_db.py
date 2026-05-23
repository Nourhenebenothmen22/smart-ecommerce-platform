"""
Database health check for the backend/ML shared PostgreSQL schema.
"""

import json
import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

try:
    from ml.core.config import settings
except ImportError:  # pragma: no cover - supports running from ml/
    from core.config import settings

TABLES_TO_CHECK = (
    "users",
    "products",
    "reviews",
    "orders",
    "user_features",
    "product_embeddings",
    "chatbot_interactions",
    "nlp_similarity_metrics",
)


def get_connection():
    return psycopg2.connect(**settings.db_config_dict)


def _count_table(cur, table_name: str):
    if table_name not in TABLES_TO_CHECK:
        raise ValueError(f"Unexpected table name: {table_name}")
    cur.execute(f"SELECT COUNT(*) AS count FROM {table_name};")
    return cur.fetchone()["count"]


def run_deep_audit():
    audit_results = {
        "tables": {},
        "nlp_embeddings": {},
        "chatbot_interactions": {},
        "data_consistency": {},
    }

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for table in TABLES_TO_CHECK:
                    try:
                        audit_results["tables"][table] = _count_table(cur, table)
                    except psycopg2.errors.UndefinedTable:
                        conn.rollback()
                        audit_results["tables"][table] = "missing"

                cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
                audit_results["nlp_embeddings"]["pgvector_installed"] = bool(cur.fetchone())

                if audit_results["tables"].get("product_embeddings") != "missing":
                    cur.execute(
                        """
                        SELECT COUNT(*) AS count
                        FROM products p
                        LEFT JOIN product_embeddings pe
                          ON p.id = pe.product_id
                         AND pe.model_name = %s
                         AND pe.model_version = %s
                        WHERE p.is_active = TRUE
                          AND pe.product_id IS NULL;
                        """,
                        (settings.EMBEDDING_MODEL_NAME, settings.EMBEDDING_MODEL_VERSION),
                    )
                    audit_results["nlp_embeddings"]["active_products_missing_current_embedding"] = cur.fetchone()["count"]
                    audit_results["nlp_embeddings"]["embedding_model"] = settings.EMBEDDING_MODEL_NAME
                    audit_results["nlp_embeddings"]["embedding_version"] = settings.EMBEDDING_MODEL_VERSION

                if audit_results["tables"].get("chatbot_interactions") != "missing":
                    count_chatbot = audit_results["tables"].get("chatbot_interactions", 0)
                    audit_results["chatbot_interactions"]["total"] = count_chatbot
                    if count_chatbot:
                        cur.execute(
                            """
                            SELECT COUNT(*) AS count
                            FROM chatbot_interactions
                            WHERE llm_response IS NULL OR llm_response = '';
                            """
                        )
                        audit_results["chatbot_interactions"]["empty_llm_responses"] = cur.fetchone()["count"]

                cur.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM reviews r
                    LEFT JOIN products p ON p.id = r.product_id
                    WHERE p.id IS NULL;
                    """
                )
                audit_results["data_consistency"]["orphaned_reviews"] = cur.fetchone()["count"]

        print(json.dumps(audit_results, indent=2))
        max_missing = os.getenv("ML_HEALTH_MAX_MISSING_EMBEDDINGS")
        missing_embeddings = audit_results["nlp_embeddings"].get("active_products_missing_current_embedding")
        if max_missing is not None and isinstance(missing_embeddings, int) and missing_embeddings > int(max_missing):
            raise SystemExit(
                f"Current embedding coverage failed: {missing_embeddings} missing active product embeddings "
                f"(allowed: {max_missing})"
            )
    except Exception as exc:
        print(f"Database health check failed: {exc}")
        raise


if __name__ == "__main__":
    run_deep_audit()
