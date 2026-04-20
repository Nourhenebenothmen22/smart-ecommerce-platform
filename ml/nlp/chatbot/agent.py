import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class RAGChatbotAgent:
    """
    Main agent for Retrieval-Augmented Generation.
    Takes a user query, retrieves context from algorithms, and formats prompt for LLMs.
    """
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        # Can store conversation history here or in Redis

    def generate_response(self, user_query: str, retrieved_context: List[Dict[str, Any]]) -> str:
        """
        Creates a prompt containing the retrieved context and user query.
        For now, this returns a mock response until the actual LLM is hooked up.
        """
        logger.info(f"Generating response for query: {user_query}")
        
        # In a real implementation:
        # prompt = self._build_prompt(user_query, retrieved_context)
        # response = self.llm_client.chat(prompt)
        # return response
        
        context_preview = [item.get('name', 'Unknown Product') for item in retrieved_context[:3]]
        
        return f"Je comprends que vous cherchez : '{user_query}'. " \
               f"Basé sur nos données, voici quelques éléments pertinents : {', '.join(context_preview)}."
