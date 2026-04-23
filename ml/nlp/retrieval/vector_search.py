from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import sys
import os

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

from core.db import get_db_cursor

class DenseVectorRetriever:
    """
    Implements semantic search using sentence embeddings and cosine similarity.
    Queries the PostgreSQL pgvector database.
    """
    def __init__(self, embedding_model='all-MiniLM-L6-v2'):
        print(f"Loading SentenceTransformer: {embedding_model}...")
        self.model = SentenceTransformer(embedding_model)
        
    def _get_embedding(self, text: str) -> List[float]:
        """Convert text query to dense vector."""
        return self.model.encode(text).tolist()
        
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a semantic search in pgvector.
        """
        vector = self._get_embedding(query)
        results = []
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.title, 1 - (pe.embedding_vector <=> %s::vector) AS similarity 
                    FROM products p 
                    JOIN product_embeddings pe ON p.id = pe.product_id 
                    ORDER BY pe.embedding_vector <=> %s::vector 
                    LIMIT %s
                """, (vector, vector, top_k))
                
                for row in cur.fetchall():
                    results.append({
                        "product_id": row[0],
                        "name": row[1],
                        "similarity": float(row[2]) if row[2] else 0.0
                    })
        except Exception as e:
            print(f"Vector search error: {e}")
            
        return results
