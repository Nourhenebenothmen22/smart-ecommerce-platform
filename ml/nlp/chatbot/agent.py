"""
DarStore DB-grounded chatbot response formatter.

Retrieval can use BM25, embeddings, and RRF, but final responses are built only
from retrieved database rows. No product facts are generated from model memory.
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


def _price_text(item: Dict[str, Any]) -> str:
    price = item.get("price")
    final_price = item.get("final_price", price)
    if final_price is None:
        return "Non indique"
    if price not in (None, final_price):
        return f"{final_price} EUR au lieu de {price} EUR"
    return f"{final_price} EUR"


def _availability_text(item: Dict[str, Any]) -> str:
    stock = item.get("stock")
    if stock is None:
        return "Disponibilite non indiquee"
    try:
        stock_value = int(stock)
    except (TypeError, ValueError):
        return "Disponibilite non indiquee"
    if stock_value > 0:
        return f"Disponible en stock ({stock_value})"
    return "Hors stock"


def _category_text(item: Dict[str, Any]) -> str:
    category = item.get("category") or ""
    subcategory = item.get("subcategory") or ""
    if category and subcategory and category != subcategory:
        return f"{category} / {subcategory}"
    return category or subcategory or "Non indiquee"


def _why_text(item: Dict[str, Any]) -> str:
    parts = []
    matched_entity = item.get("matched_entity")
    source = item.get("source")
    description = str(item.get("description") or "").strip()

    if matched_entity:
        parts.append(f"il correspond a la recherche autour de {matched_entity}")
    if source in {"catalog_price_desc", "catalog_price_asc"}:
        parts.append("il correspond a une demande basee sur le prix")
    if source == "session_context":
        parts.append("il provient du contexte de votre conversation precedente")
    if description:
        parts.append(f"sa description indique: {description[:180]}")
    if not parts:
        parts.append("il fait partie des produits les plus pertinents recuperes depuis le catalogue")
    return "; ".join(parts) + "."


class RAGChatbotAgent:
    """
    Formats DarStore answers from retrieved product context only.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = None
        logger.warning("OpenAI client disabled; chatbot operates in DB-only mode.")
        self.system_prompt = (
            "Assistant e-commerce DarStore DB-only. Answer only from retrieved product context. "
            "If no relevant context is present, return the DarStore no-result message."
        )

    def _detect_prompt_injection(self, text: str) -> bool:
        return bool(_INJECTION_RE.search(text))

    def _build_context_string(self, retrieved_context: List[Dict[str, Any]]) -> str:
        if not retrieved_context:
            return "(Aucun produit trouve dans le catalogue actuel.)"

        context_lines = []
        for i, item in enumerate(retrieved_context[:5], 1):
            name = item.get("name", "Produit")
            brand = item.get("brand", "N/A")
            description = str(item.get("description") or "")
            context_lines.append(
                f"{i}. {name}\n"
                f"   Marque: {brand} | Categorie: {_category_text(item)} | "
                f"Prix: {_price_text(item)} | Disponibilite: {_availability_text(item)}\n"
                f"   Description: {description[:500]}"
            )
        return "\n".join(context_lines)

    def build_user_message(self, user_query: str, retrieved_context: List[Dict[str, Any]]) -> str:
        return (
            f"Question du client:\n{user_query}\n\n"
            f"Produits recuperes depuis la base DarStore:\n{self._build_context_string(retrieved_context)}"
        )

    def generate_response(self, user_query: str, retrieved_context: List[Dict[str, Any]]) -> str:
        logger.info("Generating DarStore DB-only response for query '%s' with %s context items", user_query, len(retrieved_context))

        if self._detect_prompt_injection(user_query) or not retrieved_context:
            return (
                "Je n'ai pas trouve de produit correspondant a votre demande dans le catalogue actuel.\n"
                "Vous pouvez reformuler votre recherche ou consulter une autre categorie disponible sur DarStore."
            )

        lines = [
            "D'apres les produits disponibles dans le catalogue DarStore, voici les produits les plus adaptes a votre demande :"
        ]
        for index, item in enumerate(retrieved_context[:5], 1):
            name = item.get("name", "Produit")
            brand = item.get("brand")
            display_name = f"{name} ({brand})" if brand else name
            lines.extend([
                "",
                f"{index}. {display_name}",
                f"   - Categorie : {_category_text(item)}",
                f"   - Prix : {_price_text(item)}",
                f"   - Disponibilite : {_availability_text(item)}",
                f"   - Pourquoi ce produit est adapte : {_why_text(item)}",
            ])

        lines.extend([
            "",
            "Vous pouvez choisir le produit selon votre budget et sa disponibilite.",
        ])
        return "\n".join(lines)
