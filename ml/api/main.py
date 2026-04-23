from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import sys
import os
import json

# ── Ensure the 'ml' directory is in sys.path ──────────────
_ML_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

from nlp.chatbot.agent import RAGChatbotAgent
from nlp.retrieval.vector_search import DenseVectorRetriever
from nlp.retrieval.bm25_search import BM25Retriever
from core.db import get_db_cursor

app = FastAPI(
    title="eCommerce ML Intelligence API",
    description="Minimal API for health checks and RAG NLP Chatbot tasks.",
    version="1.0.0"
)

# Initialize engines
retriever = DenseVectorRetriever() # We default to Semantic Search
agent = RAGChatbotAgent()

class ChatRequest(BaseModel):
    query: str
    user_id: int | None = None

@app.get("/health")
def health_check():
    return {"status": "online", "message": "ML Intelligence Service is running."}

def log_interaction(req_query, resp_text, context_data, req_user_id, prompt_text):
    try:
        with get_db_cursor(commit=True) as cur:
            insert_query = """
            INSERT INTO chatbot_interactions 
            (user_id, session_id, user_query, retrieval_algorithm, retrieved_context, llm_prompt, llm_response, llm_model_used) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(insert_query, (
                req_user_id,
                "session_auto_1",
                req_query,
                "Dense_Cosine",
                json.dumps(context_data),
                prompt_text,
                resp_text,
                "openai/gpt-4o-mini"
            ))
    except Exception as e:
        print(f"Error logging to db: {e}")

@app.post("/chat")
def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    # 1. Retrieve Context from Database
    context = retriever.search(request.query, top_k=3)
    
    # 2. RAG Generation
    response = agent.generate_response(request.query, context)
    
    # 3. Log interaction safely in background
    background_tasks.add_task(log_interaction, request.query, response, context, request.user_id, agent.system_prompt)
    
    return {
        "query": request.query,
        "response": response,
        "context_used": context,
        "algorithm": "Dense_Cosine"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
