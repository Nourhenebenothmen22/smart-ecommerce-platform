from typing import List, Dict, Any

class BM25Retriever:
    """
    Implements a BM25 algorithm (lexical search).
    Could use PostgreSQL Full Text Search (tsvector), Elasticsearch, or a local Python index.
    """
    def __init__(self):
        # Initialize index or DB connection
        pass
        
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for top_k products matching exactly the keywords.
        """
        # Mock behavior
        return [
            {"product_id": 1, "name": f"Mock Product matching '{query}'", "score": 2.5}
        ]
