"""
FastAPI application for the e-commerce ML Intelligence service.

Provides:
- /health: Health check
- /chat: RAG chatbot endpoint using Hybrid search (BM25 + Vector + RRF)

Includes input validation, session tracking, and full interaction logging.
"""
import logging
import uuid
import json
import sys
import os

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field

# ── Ensure the 'ml' directory is in sys.path ──────────────
_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

from nlp.chatbot.agent import RAGChatbotAgent
from nlp.retrieval.hybrid_search import HybridRetriever
from core.db import get_db_cursor

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────
app = FastAPI(
    title="eCommerce ML Intelligence API",
    description="RAG Chatbot API with Hybrid Search (BM25 + Dense Vector + RRF Fusion).",
    version="2.0.0"
)

# Initialize engines — Hybrid retriever uses both BM25 + Vector internally
retriever = HybridRetriever()
agent = RAGChatbotAgent()


# ── Request/Response Models ───────────────────────────────

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
        description="Optional authenticated user ID for personalization."
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for multi-turn conversation tracking. Auto-generated if not provided."
    )


# ── Endpoints ─────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "online", "message": "ML Intelligence Service is running.", "version": "2.0.0"}


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
def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    RAG Chatbot endpoint.
    1. Hybrid retrieval (BM25 + Vector with RRF fusion)
    2. LLM generation with enriched context
    3. Background logging for traceability
    """
    # Generate or reuse session ID
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(f"[{session_id}] Chat request: '{request.query[:80]}...' (user_id={request.user_id})")

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
        request.user_id,
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


if __name__ == "__main__":
    import uvicorn
    import webbrowser
    from threading import Timer

    # Use 127.0.0.1 which is more reliable than 0.0.0.0 for local access on Windows
    url = "http://127.0.0.1:8000/docs"

    def open_browser():
        webbrowser.open(url)

    # Launch browser after a short delay
    Timer(1.5, open_browser).start()
    
    # Passing the app object directly is more robust when running from different CWDs
    uvicorn.run(app, host="127.0.0.1", port=8000)
