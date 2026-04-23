from typing import List, Dict, Any
import sys
import os
import re

_ML_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)

from core.db import get_db_cursor

class BM25Retriever:
    """
    Implements a BM25 or FTS algorithm using PostgreSQL native text search.
    """
    def __init__(self):
        pass
        
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        results = []
        
        # Clean query for pg_trgm and to_tsquery
        words = [w for w in re.split(r'\s+', query.strip()) if w]
        if not words:
            return results
            
        ts_query_str = " | ".join(words)
        
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT id, title, ts_rank(to_tsvector('french', title || ' ' || description), to_tsquery('french', %s)) AS score 
                    FROM products
                    WHERE to_tsvector('french', title || ' ' || description) @@ to_tsquery('french', %s)
                    ORDER BY score DESC
                    LIMIT %s
                """, (ts_query_str, ts_query_str, top_k))
                
                for row in cur.fetchall():
                    results.append({
                        "product_id": row[0],
                        "name": row[1],
                        "score": float(row[2]) if row[2] else 0.0
                    })
        except Exception as e:
            print(f"BM25 search error: {e}")
            
        return results
