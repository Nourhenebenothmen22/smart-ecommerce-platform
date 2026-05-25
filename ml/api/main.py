"""
FastAPI application for the e-commerce ML Intelligence service.

Provides:
- /health: Health check
- /chat: RAG chatbot endpoint using Hybrid search (BM25 + Vector + RRF)
- /price/predict: Product price prediction endpoint

Includes input validation, session tracking, and full interaction logging.
"""
import logging
import uuid
import json
import sys
import os
from collections import defaultdict, deque
from time import monotonic

from fastapi import FastAPI, BackgroundTasks, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator, model_validator

# Ensure both project root and the 'ml' directory are importable.
_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJECT_ROOT = os.path.dirname(_ML_ROOT)
for _path in (_PROJECT_ROOT, _ML_ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from nlp.chatbot.agent import RAGChatbotAgent
from nlp.retrieval.hybrid_search import HybridRetriever
from price_prediction.prediction import predict_price
from core.db import get_db_cursor
from core.config import settings

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# App
app = FastAPI(
    title="eCommerce ML Intelligence API",
    description="RAG Chatbot API with Hybrid Search (BM25 + Dense Vector + RRF Fusion).",
    version="2.0.0"
)

# Initialize engines. Hybrid retriever uses both BM25 + Vector internally.
retriever = HybridRetriever()
agent = RAGChatbotAgent()
_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


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


class PricePredictionRequest(BaseModel):
    product_id: int | None = Field(default=None, gt=0, description="Existing product id to load from PostgreSQL.")
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    brand: str | None = Field(default=None, max_length=120)
    category_id: int | None = Field(default=None, ge=0)
    subcategory_id: int | None = Field(default=None, ge=0)
    category_name: str | None = Field(default=None, max_length=120)
    subcategory_name: str | None = Field(default=None, max_length=120)
    discount_percent: float | None = Field(default=None, ge=0, le=100)
    rating_avg: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    tags: list[str] | None = Field(default=None, max_length=50)
    is_active: bool | None = None

    @field_validator("title", "description", "brand", "category_name", "subcategory_name")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = value.strip()
        return clean or None

    @field_validator("tags")
    @classmethod
    def strip_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        clean = [item.strip() for item in value if item and item.strip()]
        return clean or None

    @model_validator(mode="after")
    def require_product_id_or_features(self):
        payload = self.model_dump(exclude_none=True)
        if not payload:
            raise ValueError("Provide product_id or product feature fields for price prediction.")
        return self


# Endpoints

@app.get("/health")
def health_check():
    return {"status": "online", "message": "ML Intelligence Service is running.", "version": "2.0.0"}


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
    context = retriever.search(request.query, top_k=5)
    algorithm = "Hybrid_RRF"

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
