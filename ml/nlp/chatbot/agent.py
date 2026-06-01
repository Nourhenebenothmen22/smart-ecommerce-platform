"""
DB-grounded chatbot response formatter.

The chatbot may use retrieval models to find context, but the final answer is
constructed only from retrieved database rows. No product facts are generated
from model memory.
"""
import logging
import re
from typing import Any, Dict, List

try:
    from ml.core.config import settings
except ImportError:  # pragma: no cover - supports running from inside ml/
    from core.config import settings

logger = logging.getLogger(__name__)

_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|rules|prompts)",
    r"(oublie|ignore)\s+(toutes?\s+)?(les\s+)?(instructions|regles|r[eè]gles|consignes)",
    r"you\s+are\s+now\s+(?:a|an)",
    r"tu\s+es\s+maintenant",
    r"system\s*prompt",
    r"jailbreak",
    r"DAN\s+mode",
    r"let'?s\s+play\s+a\s+game",
    r"mots\s+de\s+passe",
    r"code\s+source",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


class RAGChatbotAgent:
    """
    Formats answers from retrieved product context only.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = None
        logger.warning("OpenAI client disabled; chatbot operates in DB-only mode.")
        self.system_prompt = (
            "Assistant e-commerce DB-only. Answer only from retrieved product context. "
            "If no context is present, return no result found."
        )

    def _detect_prompt_injection(self, text: str) -> bool:
        return bool(_INJECTION_RE.search(text))

    def _build_context_string(self, retrieved_context: List[Dict[str, Any]]) -> str:
        if not retrieved_context:
            return "(Aucun produit trouve dans le catalogue pour cette recherche.)"

        context_lines = []
        for i, item in enumerate(retrieved_context[:5], 1):
            name = item.get("name", "Produit")
            brand = item.get("brand", "N/A")
            price = item.get("price", "N/A")
            final_price = item.get("final_price", price)
            rating = item.get("rating_avg", "N/A")
            stock = item.get("stock", 0)
            description = item.get("description", "")
            price_display = f"{final_price} EUR"
            if price not in (None, "N/A", final_price):
                price_display = f"{final_price} EUR (au lieu de {price} EUR)"
            context_lines.append(
                f"{i}. {name}\n"
                f"   Marque: {brand} | Prix: {price_display} | Note: {rating}/5 | Stock: {stock}\n"
                f"   Description: {description[:500]}"
            )
        return "\n".join(context_lines)

    def build_user_message(self, user_query: str, retrieved_context: List[Dict[str, Any]]) -> str:
        return (
            f"Question du client:\n{user_query}\n\n"
            f"Produits recuperes depuis la base:\n{self._build_context_string(retrieved_context)}"
        )

    def generate_response(self, user_query: str, retrieved_context: List[Dict[str, Any]]) -> str:
        logger.info("Generating DB-only response for query '%s' with %s context items", user_query, len(retrieved_context))

        if self._detect_prompt_injection(user_query):
            logger.warning("Prompt injection attempt detected: '%s...'", user_query[:100])
            return (
                "Je suis votre assistant e-commerce. Je peux uniquement aider avec les "
                "produits disponibles dans la base."
            )

        if not retrieved_context:
            return (
                "Je n'ai pas trouve de produits correspondant a votre recherche dans la base. "
                "Pourriez-vous reformuler votre demande ou preciser la categorie souhaitee ?"
            )

        lines = ["D'apres les produits disponibles dans la base, voici ce que j'ai trouve :"]
        for index, item in enumerate(retrieved_context[:5], 1):
            name = item.get("name", "Produit")
            brand = item.get("brand") or "Marque non precisee"
            price = item.get("price")
            final_price = item.get("final_price", price)
            rating = item.get("rating_avg")
            stock = item.get("stock", 0)
            source = item.get("source")
            matched_entity = item.get("matched_entity")

            price_text = f"{final_price} EUR"
            if price not in (None, final_price):
                price_text = f"{final_price} EUR au lieu de {price} EUR"

            details = [
                f"{index}. {name}",
                f"marque: {brand}",
                f"prix: {price_text}",
                f"stock: {stock}",
            ]
            if rating is not None:
                details.append(f"note: {rating}/5")
            if matched_entity:
                details.append(f"correspondance: {matched_entity}")
            if source:
                details.append(f"source: {source}")
            lines.append(" - ".join(details))

        return "\n".join(lines)
