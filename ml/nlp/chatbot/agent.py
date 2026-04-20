import logging
from typing import Dict, Any, List
import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

class RAGChatbotAgent:
    """
    Main agent for Retrieval-Augmented Generation.
    Takes a user query, retrieves context from algorithms, and formats prompt for LLMs.
    """
    def __init__(self, api_key: str = None):
        from dotenv import load_dotenv
        import os
        # Point specifically to project root .env
        dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../.env'))
        load_dotenv(dotenv_path) # Load variables from .env if present
        
        # We allow injecting API Key, fallback to env variable. 
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        ) if OpenAI and self.api_key else None
        
        # Le System Prompt est CRUCIAL pour bloquer l'overfitting hors-domaine
        self.system_prompt = (
            "Tu es 'L'Assistant Intelligent', un conseiller de vente expert pour notre plateforme e-commerce. "
            "Ton rôle est d'accompagner les utilisateurs dans leurs achats en te basant EXCLUSIVEMENT "
            "sur le contexte produit fourni.\n"
            "Règles strictes :\n"
            "1. Si on te pose une question hors du domaine e-commerce (ex: recettes de cuisine, réparation de voiture), "
            "REFUSE POLIMENT de répondre et réoriente l'utilisateur vers nos produits.\n"
            "2. Si la question est trop vague (ex: 'Quel est le meilleur produit ?'), demande de préciser "
            "la catégorie ou l'usage souhaité (ex: électronique, vêtements de sport).\n"
            "3. Reste concis, aimable, et vendeur.\n"
            "4. Ne dis jamais que tu es une IA."
        )

    def generate_response(self, user_query: str, retrieved_context: List[Dict[str, Any]]) -> str:
        """
        Creates a prompt containing the retrieved context and user query, and queries the LLM.
        """
        logger.info(f"Generating response for query: {user_query}")
        
        # 1. Préparation du Contexte (Limité aux 3 meilleurs résultats)
        context_preview = []
        for item in retrieved_context[:3]:
            # Extrait les champs utiles selon la structure de nos dictionnaires
            name = item.get('name', 'Produit Inconnu')
            sim = item.get('similarity', 'N/A')
            context_preview.append(f"- {name} (Score: {sim})")
            
        context_str = "\n".join(context_preview)
        
        # 2. Construction du Message Utilisateur Augmenté (RAG)
        user_message = (
            f"Voici la question du client : '{user_query}'\n\n"
            f"Voici les produits extraits de notre catalogue qui correspondent pertinemment :\n{context_str}\n\n"
            f"Réponds au client en utilisant ces informations. S'il n'y a pas de contexte, dis-le poliment."
        )

        # 3. Validation de sécurité (Client non configuré / Pas de clé)
        if not self.client:
            logger.warning("Mock Response Triggered: Missing OpenAI Client or API Key.")
            return (
                f"(Mode DÉMO - API Key Manquante)\n"
                f"Je comprends que vous cherchez : '{user_query}'.\n"
                f"Basé sur nos données : {', '.join([item.get('name', 'N/A') for item in retrieved_context[:2]])}."
            )

        # 4. Inférence LLM
        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini", # Compatible OpenRouter
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3, # Faible temp pour éviter les hallucinations sur les refs produits
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur lors de l'appel LLM: {e}")
            return "Je suis désolé, je rencontre des difficultés techniques pour accéder au catalogue."
