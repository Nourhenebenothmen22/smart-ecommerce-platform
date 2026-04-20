from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os

# Add the 'ml' directory to the path so we can import 'nlp' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nlp.chatbot.agent import RAGChatbotAgent
from nlp.retrieval.vector_search import DenseVectorRetriever
from nlp.retrieval.bm25_search import BM25Retriever

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

@app.post("/chat")
def chat(request: ChatRequest):
    # 1. Retrieve Context from Database
    # (Mock implementation will trigger from our scaffold classes)
    context = retriever.search(request.query, top_k=3)
    
    # 2. RAG Generation
    response = agent.generate_response(request.query, context)
    
    # 3. Log interaction to SQL table `chatbot_interactions`
    # ... (Would happen here using psycopg2/SQLAlchemy) ...
    
    return {
        "query": request.query,
        "response": response,
        "context_used": context,
        "algorithm": "Dense_Cosine"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
