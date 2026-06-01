"""
FastAPI application for the e-commerce ML Intelligence service.

Provides:
- /health: Health check
- /chat: RAG chatbot endpoint using Hybrid search (BM25 + Vector + RRF)
- /price/predict: Product price prediction endpoint

Includes input validation, session tracking, and full interaction logging.
"""
import logging
import re
import uuid
import json
import sys
import os
from collections import defaultdict, deque
from time import monotonic

from fastapi import FastAPI, BackgroundTasks, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# Ensure both project root and the 'ml' directory are importable.
_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJECT_ROOT = os.path.dirname(_ML_ROOT)
for _path in (_PROJECT_ROOT, _ML_ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from nlp.chatbot.agent import RAGChatbotAgent
from nlp.retrieval.hybrid_search import HybridRetriever
from price_prediction.prediction import predict_price
try:
    from ml.api.schemas import PricePredictionRequest
except ImportError:  # pragma: no cover - supports running from inside ml/
    from api.schemas import PricePredictionRequest
from core.db import get_db_cursor
from core.config import settings

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
_FOLLOW_UP_RE = re.compile(
    r"\b(celui|celle|ceux|this|that|it|them|same|meme|même|similar|similaire|"
    r"moins\s+cher|plus\s+cher|cheapest|most\s+expensive|available|disponible)\b",
    re.IGNORECASE,
)

# App
app = FastAPI(
    title="eCommerce ML Intelligence API",
    description="RAG Chatbot API with Hybrid Search (BM25 + Dense Vector + RRF Fusion).",
    version="2.0.0"
)

# CORS - allow only configured origins in production, localhost in development
_cors_origins_str = os.getenv("ML_CORS_ORIGINS", "")
if _cors_origins_str:
    _cors_origins = [o.strip() for o in _cors_origins_str.split(",") if o.strip()]
else:
    _cors_origins = ["http://backend:5000", "http://127.0.0.1:5000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-ML-Service-Token", "X-ML-User-Id"],
)

# Initialize engines. Hybrid retriever uses both BM25 + Vector internally.
retriever = HybridRetriever()
agent = RAGChatbotAgent()
_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_SESSION_CONTEXT_CACHE: dict[str, list[int]] = {}


# Request/Response Models

class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User search query. Must be 1-500 characters.",
        examples=["je cherche un iphone pas cher"]
    )
    user_id: int | None = Field(
        default=None,
        description="Deprecated. Ignored unless ALLOW_UNVERIFIED_CHAT_USER_ID=true."
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for multi-turn conversation tracking. Auto-generated if not provided."
    )

    @field_validator("query")
    @classmethod
    def strip_query_whitespace(cls, v: str) -> str:
        query = v.strip()
        if not query:
            raise ValueError("Query must not be empty or whitespace.")
        return query


# Endpoints

@app.get("/health")
def health_check():
    return {"status": "online", "message": "ML Intelligence Service is running.", "version": "2.0.0"}


@app.get("/ready")
def readiness_check():
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM products WHERE is_active = TRUE;")
            active_products = int(cur.fetchone()[0])
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            pgvector_installed = bool(cur.fetchone())
            cur.execute(
                """
                SELECT COUNT(*)
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
            missing_embeddings = int(cur.fetchone()[0])

        ready = active_products > 0 and pgvector_installed and missing_embeddings == 0
        payload = {
            "ready": ready,
            "active_products": active_products,
            "pgvector_installed": pgvector_installed,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "embedding_version": settings.EMBEDDING_MODEL_VERSION,
            "active_products_missing_current_embedding": missing_embeddings,
        }
        if not ready:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=payload)
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("ML readiness check failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"ready": False, "error": "Database or embedding readiness check failed."},
        ) from exc


def _client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(bucket: str, limit: int, window_seconds: float = 60.0) -> None:
    if limit <= 0:
        return
    now = monotonic()
    hits = _RATE_BUCKETS[bucket]
    while hits and now - hits[0] > window_seconds:
        hits.popleft()
    if len(hits) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="ML API rate limit exceeded.",
        )
    hits.append(now)


def _production_config_guard() -> None:
    errors = settings.production_config_errors()
    if errors:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML service production configuration is invalid.",
        )


def log_interaction(
    req_query: str,
    resp_text: str,
    context_data: list,
    req_user_id: int | None,
    full_prompt: str,
    session_id: str,
    algorithm: str
):
    """Log the complete chatbot interaction to the database for traceability."""
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO chatbot_interactions
                (user_id, session_id, user_query, retrieval_algorithm, retrieved_context, llm_prompt, llm_response, llm_model_used)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                req_user_id,
                session_id,
                req_query,
                algorithm,
                json.dumps(context_data, default=str),
                full_prompt,  # Now logs the FULL prompt (system + user message with context)
                resp_text,
                "openai/gpt-4o-mini"
            ))
            logger.info(f"Interaction logged for session {session_id}")
    except Exception as e:
        logger.error(f"Error logging interaction to DB: {e}", exc_info=True)


def _load_recent_context_product_ids(session_id: str, limit: int = 10) -> list[int]:
    product_ids: list[int] = list(_SESSION_CONTEXT_CACHE.get(session_id, []))
    try:
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT retrieved_context
                FROM chatbot_interactions
                WHERE session_id = %s
                  AND retrieved_context IS NOT NULL
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (session_id, limit),
            )
            for (context_value,) in cur.fetchall():
                items = context_value
                if isinstance(items, str):
                    items = json.loads(items)
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    product_id = item.get("product_id")
                    if isinstance(product_id, int) and product_id not in product_ids:
                        product_ids.append(product_id)
    except Exception as exc:
        logger.warning("Could not load previous chat context for session %s: %s", session_id, exc)
    return product_ids


def _remember_context(session_id: str, context: list[dict], limit: int = 20) -> None:
    cached = list(_SESSION_CONTEXT_CACHE.get(session_id, []))
    for item in context:
        product_id = item.get("product_id") if isinstance(item, dict) else None
        if isinstance(product_id, int):
            if product_id in cached:
                cached.remove(product_id)
            cached.insert(0, product_id)
    _SESSION_CONTEXT_CACHE[session_id] = cached[:limit]


def _load_products_by_ids(product_ids: list[int], top_k: int = 5) -> list[dict]:
    if not product_ids:
        return []
    order = {pid: idx for idx, pid in enumerate(product_ids)}
    try:
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.title, p.brand, p.price, p.final_price,
                       LEFT(p.description, 1000) AS description_preview,
                       p.rating_avg, p.stock
                FROM products p
                WHERE p.id = ANY(%s)
                  AND p.is_active = TRUE
                  AND p.stock > 0
                """,
                (product_ids,),
            )
            rows = sorted(cur.fetchall(), key=lambda row: order.get(row[0], 10_000))
            results = []
            for rank, row in enumerate(rows[:top_k], 1):
                results.append({
                    "product_id": row[0],
                    "name": row[1],
                    "brand": row[2],
                    "price": float(row[3]) if row[3] else 0.0,
                    "final_price": float(row[4]) if row[4] else 0.0,
                    "description": row[5] or "",
                    "rating_avg": float(row[6]) if row[6] else 0.0,
                    "stock": row[7] or 0,
                    "score": round(1 / rank, 4),
                    "source": "session_context",
                })
            return results
    except Exception as exc:
        logger.warning("Could not refresh session context products: %s", exc)
        return []


def _apply_follow_up_sort(query: str, context: list[dict]) -> list[dict]:
    if not context:
        return []
    if re.search(r"\b(moins\s+cher|cheapest|lowest)\b", query, re.IGNORECASE):
        return sorted(context, key=lambda item: float(item.get("final_price") or item.get("price") or 0))
    if re.search(r"\b(plus\s+cher|most\s+expensive|highest)\b", query, re.IGNORECASE):
        return sorted(context, key=lambda item: float(item.get("final_price") or item.get("price") or 0), reverse=True)
    return context


@app.post("/chat")
def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    x_ml_user_id: int | None = Header(default=None, alias="X-ML-User-Id"),
    x_ml_service_token: str | None = Header(default=None, alias="X-ML-Service-Token"),
):
    """
    RAG Chatbot endpoint.
    1. Hybrid retrieval (BM25 + Vector with RRF fusion)
    2. LLM generation with enriched context
    3. Background logging for traceability
    """
    # Generate or reuse session ID
    _production_config_guard()
    _check_rate_limit(f"chat:{_client_key(http_request)}", settings.ML_CHAT_RATE_LIMIT_PER_MINUTE)
    session_id = request.session_id or str(uuid.uuid4())
    effective_user_id = x_ml_user_id
    service_token_valid = settings.verify_ml_service_token(x_ml_service_token)
    if settings.ML_REQUIRE_SERVICE_TOKEN and not service_token_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ML service token",
        )
    if x_ml_user_id is not None and not service_token_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ML service token",
        )

    if effective_user_id is None and settings.ALLOW_UNVERIFIED_CHAT_USER_ID:
        effective_user_id = request.user_id

    if request.user_id and effective_user_id != request.user_id:
        logger.warning("[%s] Ignoring unverified body user_id for /chat.", session_id)

    logger.info(f"[{session_id}] Chat request: '{request.query[:80]}...' (user_id={effective_user_id})")

    # 1. Retrieve Context via Hybrid Search (BM25 + Vector + RRF)
    if agent._detect_prompt_injection(request.query):
        context = []
    else:
        previous_context: list[dict] = []
        if request.session_id and _FOLLOW_UP_RE.search(request.query):
            previous_context = _load_products_by_ids(_load_recent_context_product_ids(session_id), top_k=5)

        context = retriever.search(request.query, top_k=5)
        if previous_context and (not context or _FOLLOW_UP_RE.search(request.query)):
            context = _apply_follow_up_sort(request.query, previous_context)[:5]
    algorithm = "Hybrid_RRF"
    _remember_context(session_id, context)

    logger.info(f"[{session_id}] Retrieved {len(context)} products via {algorithm}")

    # 2. RAG Generation
    response = agent.generate_response(request.query, context)

    # 3. Build full prompt for logging (system prompt + user message with context)
    full_prompt = (
        f"[SYSTEM]\n{agent.system_prompt}\n\n"
        f"[USER MESSAGE]\n{agent.build_user_message(request.query, context)}"
    )

    # 4. Log interaction in background (non-blocking)
    background_tasks.add_task(
        log_interaction,
        request.query,
        response,
        context,
        effective_user_id,
        full_prompt,
        session_id,
        algorithm
    )

    return {
        "query": request.query,
        "response": response,
        "context_used": context,
        "algorithm": algorithm,
        "session_id": session_id
    }


@app.post("/price/predict")
def predict_product_price(
    request: PricePredictionRequest,
    http_request: Request,
    x_ml_service_token: str | None = Header(default=None, alias="X-ML-Service-Token"),
):
    """
    Predict product price from an existing product_id or explicit product features.
    Intended to be called by the trusted backend gateway.
    """
    _production_config_guard()
    _check_rate_limit(f"price:{_client_key(http_request)}", settings.ML_PRICE_RATE_LIMIT_PER_MINUTE)
    if not settings.verify_ml_service_token(x_ml_service_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ML service token",
        )

    try:
        return predict_price(request.model_dump(exclude_none=True))
    except FileNotFoundError as exc:
        logger.error("Price prediction model is not trained: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Price prediction model is not trained.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Price prediction failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Price prediction failed.",
        ) from exc


if __name__ == "__main__":
    import uvicorn
    
    # Passing the app object directly is more robust when running from different CWDs
    uvicorn.run(app, host="127.0.0.1", port=8000)
