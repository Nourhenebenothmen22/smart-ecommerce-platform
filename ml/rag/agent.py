"""
ml/rag/agent.py — DarStore DB-Grounded RAG Response Generator.

Formats customer answers strictly from retrieved database catalog rows.
Ensures 100% faithfulness (anti-hallucination) by deriving prices, stock,
and category data directly from verified PostgreSQL records.
"""

import logging
import re
from typing import Any, Dict, List, Optional

try:
    from ml.core.config import settings
except ImportError:  # pragma: no cover
    from core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

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

_GREETING_PATTERNS = [
    r"^(?:bonjour|salut|hello|hi|hey|coucou|bonsoir|salam|ahla|aslema|yo)"
    r"(?:\s+(?:a\s+tous|tout\s+le\s+monde|darstore|l'equipe|there|bot))?[!.,?\s]*$",
]
_THANKS_PATTERNS = [
    r"^(?:merci|merci\s+beaucoup|thanks|thank\s+you|thx|c'est\s+(?:gentil|parfait|bon|super)|super\s+merci)[!.,?\s]*$",
]
_REFUSAL_PATTERNS = [
    r"^(?:rien|je\s+ne\s+(?:demande|veux|cherche)\s+rien|rien\s+du\s+tout|pas\s+besoin|laisse\s+tomber|non\s+merci|nothing)[!.,?\s]*$",
]
_FAREWELL_PATTERNS = [
    r"^(?:au\s+revoir|bye(?:\s+bye)?|a\s+bientot|à\s+bientôt|bonne\s+(?:journ[eé]e|soir[eé]e|nuit))[!.,?\s]*$",
]
_HELP_OR_IDENTITY_PATTERNS = [
    r"^(?:qui\s+(?:es-tu|es\s+tu|etes-vous|êtes-vous)|tu\s+es\s+qui|c'est\s+quoi\s+darstore|"
    r"que\s+peux-tu\s+faire|qui\s+est\s+tu|aide(?:\s+moi)?|help)[!.,?\s]*$",
]

_GREETING_RE = re.compile("|".join(_GREETING_PATTERNS), re.IGNORECASE)
_THANKS_RE = re.compile("|".join(_THANKS_PATTERNS), re.IGNORECASE)
_REFUSAL_RE = re.compile("|".join(_REFUSAL_PATTERNS), re.IGNORECASE)
_FAREWELL_RE = re.compile("|".join(_FAREWELL_PATTERNS), re.IGNORECASE)
_HELP_RE = re.compile("|".join(_HELP_OR_IDENTITY_PATTERNS), re.IGNORECASE)

# Unrelated topics outside the e-commerce catalog
_UNRELATED_PATTERNS = [
    # Recipes & cooking
    r"\b(recette|recettes|cuisiner|comment\s+faire\s+(?:une?|des?)\s+(?:omelette|g[aâ]teau|tarte|pizza|salade|soupe|p[aâ]tes|cr[eê]pes?)|"
    r"ingr[eé]dients?\s+pour|recipe|recipes|how\s+to\s+(?:make|cook)\s+(?:an?|the)?\s*(?:omelet|cake|pizza|soup))\b",
    # Weather
    r"\b(m[eé]t[eé]o|temp[eé]rature|quel\s+temps\s+fait-il|va-t-il\s+pleuvoir|weather|forecast|temperature\s+today)\b",
    # Politics & elections
    r"\b(pr[eé]sident\s+de\s+la|ministre|gouvernement|politique|parti\s+politique|[eé]lections?|president\s+of|prime\s+minister|who\s+is\s+the\s+president)\b",
    # Math & encyclopedic trivia
    r"\b(capitale\s+de|qui\s+a\s+invent[eé]|qui\s+a\s+d[eé]couvert|distance\s+(?:terre|lune|soleil)|th[eé]or[eè]me|combien\s+font\s+\d+|capital\s+of|who\s+discovered|how\s+far\s+is)\b",
    # Vehicles & automobiles (not in DarStore catalog)
    r"\b(tesla(?:\s+model\s+[3sxy])?|voiture|automobile|v[eé]hicule|[eé]lectrique\s+car|renault\s+clio|peugeot\s+\d+|bmw\s+s[eé]rie|mercedes\s+classe)\b",
    # Real estate
    r"\b(appartement\s+[aà]\s+(?:louer|vendre)|maison\s+[aà]\s+vendre|immobilier|villa\s+[aà]|real\s+estate|apartment\s+for\s+rent)\b",
    # Travel & flights
    r"\b(billet\s+d'avion|vol\s+pour|r[eé]servation\s+h[oô]tel|flight\s+tickets?|book\s+a\s+hotel)\b",
    # Medical consultations
    r"\b(ordonnance\s+m[eé]dicale|sympt[oô]mes?\s+de\s+la|diagnostic\s+m[eé]dical|traitement\s+pour\s+soigner)\b",
]
_UNRELATED_RE = re.compile("|".join(_UNRELATED_PATTERNS), re.IGNORECASE)

# Comparison patterns
_COMPARISON_PATTERNS = [
    r"\b(compare|comparer|comparatif|comparaison|diff[eé]rence\s+entre|versus|\bvs\b|lequel\s+choisir\s+entre|which\s+(?:one\s+is\s+)?better)\b"
]
_COMPARISON_RE = re.compile("|".join(_COMPARISON_PATTERNS), re.IGNORECASE)


def _detect_language(query: str) -> str:
    """Detect if the user query is primarily English or French."""
    q = (query or "").lower()
    en_signals = {
        "the", "is", "for", "with", "best", "cheap", "cheapest", "looking",
        "want", "price", "show", "give", "available", "compare", "which",
        "shoes", "phone", "laptop", "what", "how", "can", "help", "under",
        "stock", "one", "first", "second", "most", "recommend", "recommendation",
    }
    fr_signals = {
        "je", "cherche", "veux", "pour", "avec", "meilleur", "moins", "cher",
        "prix", "montre", "donne", "disponible", "quel", "quelle", "est",
        "dans", "des", "les", "une", "bonjour", "salut", "merci", "qui",
        "premier", "deuxième", "dernier", "offre", "promo", "conseil",
    }
    words = set(re.findall(r"\b\w+\b", q))
    en_score = len(words.intersection(en_signals))
    fr_score = len(words.intersection(fr_signals))
    if en_score > fr_score:
        return "en"
    return "fr"


def _detect_query_intent(query: str) -> Dict[str, bool]:
    q = (query or "").lower()
    return {
        "is_top": bool(re.search(r"\b(top|meilleur|meilleurs|best|haut\s+de\s+gamme|leader|plus\s+populaire)\b", q)),
        "is_advice": bool(re.search(r"\b(conseil|conseils|consigne|consignes|guide|recommandation|recommander|aide|choisir|que\s+prendre|avis)\b", q)),
        "is_cheap": bool(re.search(
            r"\b(pas\s+cher|moins\s+cher|economique|économique|petit\s+prix|promo|solde|budget|sous|"
            r"prix\s+min(?:imum|imal)?|le\s+moins\s+co[uû]teux|plus?\s+(?:abordable|accessible)|"
            r"budget\s+serr[eé]|cheapest|lowest\s+price)\b", q)),
        "is_pc": bool(re.search(r"\b(pc|pcs|ordinateur|ordinateurs|laptop|laptops|bureau)\b", q)),
        "is_phone": bool(re.search(r"\b(smartphone|smartphones|telephone|téléphone|mobile|iphone|galaxy)\b", q)),
    }


def _price_text(item: Dict[str, Any], lang: str = "fr") -> str:
    price = item.get("price")
    final_price = item.get("final_price", price)
    if final_price is None:
        return "Non indiqué" if lang == "fr" else "Not specified"
    if price not in (None, final_price):
        try:
            diff = round(float(price) - float(final_price), 2)
            if diff > 0:
                pct = int(round((diff / float(price)) * 100))
                if lang == "en":
                    return f"{final_price} EUR (originally {price} EUR, -{pct}% off, save {diff} EUR)"
                return f"{final_price} EUR au lieu de {price} EUR (Remise -{pct}%, économie de {diff} EUR)"
        except (ValueError, TypeError):
            pass
        return f"{final_price} EUR (au lieu de {price} EUR)" if lang == "fr" else f"{final_price} EUR (was {price} EUR)"
    return f"{final_price} EUR"


def _availability_text(item: Dict[str, Any], lang: str = "fr") -> str:
    stock = item.get("stock")
    if stock is None:
        return "Disponibilité non indiquée" if lang == "fr" else "Availability not specified"
    try:
        stock_value = int(stock)
    except (TypeError, ValueError):
        return "Disponibilité non indiquée" if lang == "fr" else "Availability not specified"
    if stock_value > 50:
        return f"Disponible en stock ({stock_value} unités)" if lang == "fr" else f"In stock ({stock_value} units)"
    elif stock_value > 0:
        return f"Plus que {stock_value} unités restantes" if lang == "fr" else f"Only {stock_value} units left"
    return "Hors stock" if lang == "fr" else "Out of stock"


def _rating_text(item: Dict[str, Any], lang: str = "fr") -> str:
    rating = item.get("rating_avg")
    if rating is not None:
        try:
            r_val = float(rating)
            if r_val > 0:
                return f"⭐ {r_val:.1f} / 5"
        except (ValueError, TypeError):
            pass
    return "Non encore noté" if lang == "fr" else "Not rated yet"


def _category_text(item: Dict[str, Any]) -> str:
    category = item.get("category") or ""
    subcategory = item.get("subcategory") or ""
    if category and subcategory and category != subcategory:
        return f"{category} / {subcategory}"
    return category or subcategory or "Non indiquée"


# English-to-French feature translation for product descriptions
_FEATURE_FR: dict[str, str] = {
    "battery life": "autonomie de la batterie",
    "battery": "batterie",
    "camera quality": "qualité photo et vidéo",
    "camera": "qualité d'appareil photo",
    "display clarity": "clarté de l'écran",
    "display quality": "qualité d'affichage",
    "display refresh rate": "fréquence de rafraîchissement",
    "display": "qualité d'affichage",
    "reading consistency": "cohérence de lecture",
    "alert features": "fonctionnalités d'alerte",
    "data export quality": "qualité d'export des données",
    "ai features": "fonctionnalités IA",
    "ai": "intelligence artificielle embarquée",
    "storage capacity": "capacité de stockage",
    "storage": "espace de stockage",
    "build quality": "qualité de fabrication",
    "fingerprint sensor": "capteur d'empreinte digitale",
    "face recognition": "reconnaissance faciale",
    "biometric": "biométrique",
    "audio quality": "qualité audio",
    "sound quality": "qualité sonore",
    "noise cancellation": "réduction de bruit active",
    "noise cancelling": "réduction de bruit active",
    "water resistance": "résistance à l'eau",
    "waterproof": "étanchéité",
    "durability": "durabilité",
    "performance": "performances",
    "processing power": "puissance de traitement",
    "graphics": "qualité graphique",
    "gpu": "carte graphique",
    "cpu": "processeur",
    "processor": "processeur",
    "ram": "mémoire vive (RAM)",
    "memory": "mémoire",
    "connectivity": "connectivité",
    "5g": "5G",
    "wifi": "Wi-Fi",
    "bluetooth": "Bluetooth",
    "charging speed": "vitesse de recharge",
    "fast charging": "charge rapide",
    "wireless charging": "charge sans fil",
    "portability": "portabilité",
    "weight": "légèreté",
    "size": "format compact",
    "keyboard": "clavier",
    "trackpad": "pavé tactile",
    "screen size": "taille d'écran",
    "resolution": "résolution",
    "color accuracy": "fidélité des couleurs",
    "refresh rate": "taux de rafraîchissement",
    "stylus": "stylet",
    "touch screen": "écran tactile",
    "foldable": "format pliable",
}


def _translate_feature(phrase: str, lang: str = "fr") -> str:
    """Translate an English product feature phrase to French or clean it in English."""
    lower = phrase.lower().strip()
    if lang == "en":
        return lower
    if lower in _FEATURE_FR:
        return _FEATURE_FR[lower]
    best_key = ""
    for key in _FEATURE_FR:
        if key in lower and len(key) > len(best_key):
            best_key = key
    if best_key:
        translated = re.sub(re.escape(best_key), _FEATURE_FR[best_key], lower, flags=re.IGNORECASE)
        return translated.strip()
    return phrase.strip()


def _clean_feature_phrase(desc: str, lang: str = "fr") -> str:
    """Extract and format features cleanly from raw catalog descriptions without truncating words."""
    if not desc:
        return ""
    m1 = re.search(r"strongly value\s+([^.]+)", desc, re.IGNORECASE)
    m2 = re.search(r"sets a new standard for\s+([^.]+)", desc, re.IGNORECASE)
    f1 = _translate_feature(m1.group(1).strip(), lang=lang) if m1 else ""
    f2 = _translate_feature(m2.group(1).strip(), lang=lang) if m2 else ""

    if lang == "en":
        if f1 and f2:
            return f"designed for users who value {f1} with key strengths in {f2}"
        if f1:
            return f"recommended for users prioritizing {f1}"
        if f2:
            return f"distinguished by high performance in {f2}"
    else:
        if f1 and f2:
            return f"conçu pour exceller en {f1} avec des atouts majeurs sur {f2}"
        if f1:
            return f"recommandé pour les utilisateurs privilégiant {f1}"
        if f2:
            return f"se distingue par un haut niveau de satisfaction sur {f2}"

    first_sentence = desc.split(".")[0].strip()
    if len(first_sentence) > 20:
        return first_sentence
    return desc[:140].strip()


def _product_badge(item: Dict[str, Any], rank: int, query_intent: Dict[str, bool]) -> str:
    price = float(item.get("price") or 0)
    final_price = float(item.get("final_price") or price or 0)
    rating = float(item.get("rating_avg") or 0)

    if rank == 1 and (query_intent.get("is_top") or rating >= 4.3):
        return " 🏆 [Top Choix Recommandé]"
    if price > 0 and final_price < price and (price - final_price) >= 15:
        pct = int(round(((price - final_price) / price) * 100))
        return f" 🏷️ [-{pct}% Promo]"
    if query_intent.get("is_cheap") and rank == 1:
        return " ⚡ [Meilleur Prix]"
    return ""


def _why_text(item: Dict[str, Any], query_intent: Optional[Dict[str, bool]] = None, lang: str = "fr") -> str:
    parts = []
    matched_entity = item.get("matched_entity")
    source = item.get("source")
    description = str(item.get("description") or "").strip()
    intent = query_intent or {}

    feature_phrase = _clean_feature_phrase(description, lang=lang)
    if feature_phrase:
        intro = "sa description indique: " if lang == "fr" else "description indicates: "
        parts.append(f"{intro}{feature_phrase}")
    elif description:
        intro = "sa description indique: " if lang == "fr" else "description indicates: "
        parts.append(f"{intro}{description[:160].strip()}")

    if matched_entity:
        parts.append(f"il correspond à la recherche autour de {matched_entity}" if lang == "fr" else f"matches search for {matched_entity}")
    if source in {"catalog_price_desc", "catalog_price_asc"} or intent.get("is_cheap"):
        parts.append("il correspond à une sélection avantageuse sur le prix" if lang == "fr" else "selected as a budget-friendly option")
    if source == "session_context":
        parts.append("il provient du contexte de votre conversation précédente" if lang == "fr" else "sourced from your previous conversation context")
    if not parts:
        parts.append("il fait partie des produits les plus adaptés du catalogue DarStore" if lang == "fr" else "ranks among the best matching products in DarStore")
    return "; ".join(parts) + "."


# ---------------------------------------------------------------------------
# Agent Class
# ---------------------------------------------------------------------------

class RAGChatbotAgent:
    """
    Formats DarStore answers strictly from retrieved product context only.
    Guarantees deterministic, hallucination-free catalog recommendations
    with semantic classification and contextual personalization.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", "")
        self.client = None
        self.system_prompt = (
            "Assistant e-commerce DarStore DB-only. Answer only from retrieved product context. "
            "If no relevant context is present, return the DarStore no-result message."
        )

    def _detect_prompt_injection(self, text: str) -> bool:
        """Detect prompt injection or jailbreak attempts via pattern matching."""
        return bool(_INJECTION_RE.search(text))

    def detect_conversational_intent(
        self,
        text: str,
        user_profile: Optional[Dict[str, Any]] = None,
        lang: str = "fr",
    ) -> Optional[str]:
        """
        Detect non-catalog conversational intents (greetings, thanks, refusals, goodbyes).
        Returns an appropriate response if matched, or None for product searches.
        """
        cleaned = (text or "").strip()
        if not cleaned:
            return None

        first_name = (user_profile.get("first_name") or "").strip() if user_profile else ""
        hello_name = f" {first_name}" if first_name else ""

        if _GREETING_RE.match(cleaned):
            if lang == "en":
                return (
                    f"Hello{hello_name}! I am the DarStore assistant. How can I help you today?\n\n"
                    "You can search for smartphones, laptops, clothing, or ask for recommendations based on your budget."
                )
            return (
                f"Bonjour{hello_name} ! Je suis l'assistant virtuel DarStore. Comment puis-je vous aider aujourd'hui ?\n\n"
                "Vous pouvez rechercher des smartphones, des ordinateurs, des vêtements, ou me demander conseil selon votre budget."
            )

        if _THANKS_RE.match(cleaned):
            if lang == "en":
                return "You're very welcome! Feel free to ask if you need anything else on DarStore."
            return "Avec grand plaisir ! N'hésitez pas si vous avez d'autres questions ou si vous recherchez un autre produit sur DarStore."

        if _REFUSAL_RE.match(cleaned):
            if lang == "en":
                return "Understood! I remain at your disposal whenever you wish to browse DarStore products."
            return "C'est bien noté ! Je reste à votre entière disposition si vous changez d'avis ou souhaitez découvrir des articles sur DarStore."

        if _FAREWELL_RE.match(cleaned):
            if lang == "en":
                return "Goodbye and thank you for visiting DarStore! Have a wonderful day."
            return "Au revoir et merci de votre visite sur DarStore ! Excellente journée et à bientôt."

        if _HELP_RE.match(cleaned):
            if lang == "en":
                return (
                    "I am DarStore's virtual shopping assistant. I can help you:\n"
                    "- Find the right products (smartphones, audio, computers, fashion...)\n"
                    "- Compare prices and technical specifications\n"
                    "- Check real-time stock availability."
                )
            return (
                "Je suis l'assistant intelligent de DarStore. Je peux vous aider à :\n"
                "- Trouver les produits les plus adaptés à vos besoins (smartphones, audio, informatique, mode...)\n"
                "- Comparer les prix et les caractéristiques techniques\n"
                "- Vérifier la disponibilité en stock en temps réel."
            )

        return None

    def detect_unrelated_intent(self, text: str, lang: str = "fr") -> Optional[str]:
        """
        Detect requests unrelated to the retail catalog (recipes, weather, politics, cars/Tesla, etc.).
        Returns a polite natural boundary message, or None if the query is in-domain.
        """
        cleaned = (text or "").strip()
        if not cleaned:
            return None
        if _UNRELATED_RE.search(cleaned):
            if lang == "en":
                return "Sorry, I can only help with products available in the DarStore catalog."
            return "Désolé, je peux uniquement vous renseigner sur les produits disponibles dans le catalogue DarStore."
        return None

    def detect_comparison_intent(self, text: str) -> bool:
        """Detect whether the user wants to compare products or brands."""
        return bool(_COMPARISON_RE.search(text or ""))

    def detect_follow_up_intent(self, text: str) -> Optional[str]:
        """
        Detect follow-up sub-intents (cheapest, ordinal, highest-rated, stock).
        Returns the sub-intent name or None.
        """
        q = (text or "").lower()
        if re.search(r"\b(moins\s+cher|cheapest|lowest\s+price|prix\s+min(?:imum|imal)?|plus\s+abordable|[eé]conomique)\b", q):
            return "cheapest"
        if re.search(r"\b(plus\s+cher|most\s+expensive|highest\s+price)\b", q):
            return "most_expensive"
        if re.search(r"\b(premier|premi[eè]re|first|1er)\b", q):
            return "first"
        if re.search(r"\b(deuxi[eè]me|second|second[e]|2[eè]me)\b", q):
            return "second"
        if re.search(r"\b(troisi[eè]me|third|3[eè]me)\b", q):
            return "third"
        if re.search(r"\b(dernier|derni[eè]re|last)\b", q):
            return "last"
        if re.search(r"\b(mieux\s+not[eé]|meilleure?\s+note|best\s+rated|highest\s+rating)\b", q):
            return "best_rated"
        if re.search(r"\b(stock|disponible|disponibilit[eé]|available|combien\s+reste)\b", q):
            return "stock"
        return None

    def generate_follow_up_response(
        self,
        query: str,
        previous_context: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None,
        lang: str = "fr",
    ) -> Optional[str]:
        """
        Answer follow-up questions directly from previously retrieved products
        WITHOUT repeating the full list.
        """
        if not previous_context:
            return None

        subintent = self.detect_follow_up_intent(query)
        if not subintent:
            return None

        if subintent == "cheapest":
            item = min(previous_context, key=lambda x: float(x.get("final_price") or x.get("price") or 0))
            name = item.get("name", "Produit")
            brand = item.get("brand") or ""
            brand_str = f" ({brand})" if brand else ""
            price_val = item.get("final_price") or item.get("price")
            rating = _rating_text(item, lang=lang)
            avail = _availability_text(item, lang=lang)
            feature = _clean_feature_phrase(item.get("description", ""), lang=lang)

            if lang == "en":
                msg = f"The most affordable model among the selected products is the **{name}{brand_str}** at **{price_val} EUR** ({rating}, {avail})."
                if feature:
                    msg += f" Its key highlight: {feature}."
                return msg
            msg = f"Le modèle le plus abordable parmi votre sélection est le **{name}{brand_str}** à **{price_val} EUR** (note : {rating}, {avail})."
            if feature:
                msg += f" Sa description indique : {feature}."
            return msg

        if subintent == "most_expensive":
            item = max(previous_context, key=lambda x: float(x.get("final_price") or x.get("price") or 0))
            name = item.get("name", "Produit")
            brand = item.get("brand") or ""
            brand_str = f" ({brand})" if brand else ""
            price_val = item.get("final_price") or item.get("price")
            rating = _rating_text(item, lang=lang)
            avail = _availability_text(item, lang=lang)
            feature = _clean_feature_phrase(item.get("description", ""), lang=lang)

            if lang == "en":
                msg = f"The highest-end reference in your selection is the **{name}{brand_str}** at **{price_val} EUR** ({rating}, {avail})."
                if feature:
                    msg += f" Highlight: {feature}."
                return msg
            msg = f"La référence la plus haut de gamme parmi votre sélection est le **{name}{brand_str}** à **{price_val} EUR** (note : {rating}, {avail})."
            if feature:
                msg += f" Sa description indique : {feature}."
            return msg

        if subintent in {"first", "second", "third", "last"}:
            idx = 0
            ordinal_label_fr = "premier"
            ordinal_label_en = "first"
            if subintent == "second" and len(previous_context) >= 2:
                idx = 1
                ordinal_label_fr = "deuxième"
                ordinal_label_en = "second"
            elif subintent == "third" and len(previous_context) >= 3:
                idx = 2
                ordinal_label_fr = "troisième"
                ordinal_label_en = "third"
            elif subintent == "last":
                idx = -1
                ordinal_label_fr = "dernier"
                ordinal_label_en = "last"

            item = previous_context[idx]
            name = item.get("name", "Produit")
            brand = item.get("brand") or ""
            brand_str = f" ({brand})" if brand else ""
            price_str = _price_text(item, lang=lang)
            rating_str = _rating_text(item, lang=lang)
            avail_str = _availability_text(item, lang=lang)
            feature = _clean_feature_phrase(item.get("description", ""), lang=lang)

            if lang == "en":
                msg = f"The {ordinal_label_en} product from your selection is the **{name}{brand_str}** at **{price_str}** ({rating_str}, {avail_str})."
                if feature:
                    msg += f" Key feature: {feature}."
                return msg
            msg = f"Le {ordinal_label_fr} produit de votre sélection est le **{name}{brand_str}** à **{price_str}** (note : {rating_str}, {avail_str})."
            if feature:
                msg += f" Sa description indique : {feature}."
            return msg

        if subintent == "best_rated":
            item = max(previous_context, key=lambda x: float(x.get("rating_avg") or 0))
            name = item.get("name", "Produit")
            brand = item.get("brand") or ""
            brand_str = f" ({brand})" if brand else ""
            price_val = item.get("final_price") or item.get("price")
            rating_str = _rating_text(item, lang=lang)
            feature = _clean_feature_phrase(item.get("description", ""), lang=lang)

            if lang == "en":
                return f"The best-rated product in your selection is the **{name}{brand_str}** with a rating of **{rating_str}** ({price_val} EUR, in stock). Feature: {feature}."
            return f"Le produit le mieux noté parmi votre sélection est le **{name}{brand_str}** avec une évaluation de **{rating_str}** ({price_val} EUR, en stock). Atout : {feature}."

        if subintent == "stock":
            in_stock_items = [p for p in previous_context if int(p.get("stock") or 0) > 0]
            if lang == "en":
                return f"{len(in_stock_items)} out of {len(previous_context)} products from your previous search are currently available in stock."
            return f"{len(in_stock_items)} sur les {len(previous_context)} produits de votre sélection précédente sont actuellement disponibles en stock."

        return None

    def generate_comparison_response(
        self,
        user_query: str,
        retrieved_context: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None,
        lang: str = "fr",
    ) -> str:
        """Generate a concise, direct comparison between the retrieved products."""
        items = retrieved_context[:3]
        if not items:
            return self.generate_no_result_response(user_query, lang=lang)

        if lang == "en":
            lines = ["Here is a concise comparison of the matching references:"]
            for idx, item in enumerate(items, 1):
                name = item.get("name", "Product")
                brand = item.get("brand") or ""
                brand_str = f" ({brand})" if brand else ""
                lines.append(
                    f"\n{idx}. **{name}{brand_str}**\n"
                    f"   - Price: {_price_text(item, lang='en')}\n"
                    f"   - Rating: {_rating_text(item, lang='en')}\n"
                    f"   - Key feature: {_clean_feature_phrase(item.get('description', ''), lang='en')}"
                )
            cheapest = min(items, key=lambda x: float(x.get("final_price") or x.get("price") or 0))
            best = max(items, key=lambda x: float(x.get("rating_avg") or 0))
            lines.append(
                f"\n**Takeaway:** For the best price, the **{cheapest.get('name')}** is the most accessible choice. "
                f"For top user satisfaction, the **{best.get('name')}** is the highest rated."
            )
            return "\n".join(lines)

        lines = ["Voici une comparaison directe des références sélectionnées :"]
        for idx, item in enumerate(items, 1):
            name = item.get("name", "Produit")
            brand = item.get("brand") or ""
            brand_str = f" ({brand})" if brand else ""
            lines.append(
                f"\n{idx}. **{name}{brand_str}**\n"
                f"   - Prix : {_price_text(item, lang='fr')}\n"
                f"   - Évaluation : {_rating_text(item, lang='fr')}\n"
                f"   - Atout principal : {_clean_feature_phrase(item.get('description', ''), lang='fr')}"
            )
        cheapest = min(items, key=lambda x: float(x.get("final_price") or x.get("price") or 0))
        best = max(items, key=lambda x: float(x.get("rating_avg") or 0))
        lines.append(
            f"\n**En résumé :** Pour un budget maîtrisé, le **{cheapest.get('name')}** est le plus avantageux. "
            f"Pour la meilleure satisfaction générale, le **{best.get('name')}** est le mieux noté."
        )
        return "\n".join(lines)

    def generate_no_result_response(self, user_query: str, lang: str = "fr") -> str:
        """Clear message when no matching catalog products exist."""
        if lang == "en":
            return (
                "I could not find any products matching your request in the current catalog.\n"
                "You can try rephrasing your search or browsing another category on DarStore."
            )
        return (
            "Je n'ai pas trouvé de produit correspondant à votre demande dans le catalogue actuel.\n"
            "Vous pouvez reformuler votre recherche ou consulter une autre catégorie disponible sur DarStore."
        )

    def build_user_message(self, user_query: str, retrieved_context: List[Dict[str, Any]]) -> str:
        """Format a concise summary of user query and context items for logging."""
        if not retrieved_context:
            return f"Question: {user_query} | (Aucun produit)"
        items = [f"{item.get('name', 'Produit')} (#{item.get('product_id', '?')})" for item in retrieved_context[:5]]
        return f"Question: {user_query} | Context ({len(retrieved_context)}): {', '.join(items)}"

    def generate_response(
        self,
        user_query: str,
        retrieved_context: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None,
        lang: Optional[str] = None,
    ) -> str:
        """
        Generate structured, DB-grounded response formatted in clean Markdown.
        Faithful to database catalog rows without hallucination or rigid boilerplate.
        """
        detected_lang = lang or _detect_language(user_query)
        logger.info("Generating DarStore response for query '%s' (%s) with %s context items", user_query, detected_lang, len(retrieved_context))

        if self._detect_prompt_injection(user_query):
            return self.generate_no_result_response(user_query, lang=detected_lang)

        chit_chat = self.detect_conversational_intent(user_query, user_profile=user_profile, lang=detected_lang)
        if chit_chat:
            return chit_chat

        unrelated = self.detect_unrelated_intent(user_query, lang=detected_lang)
        if unrelated:
            return unrelated

        if not retrieved_context:
            return self.generate_no_result_response(user_query, lang=detected_lang)

        intent = _detect_query_intent(user_query)
        first_name = (user_profile.get("first_name") or "").strip() if user_profile else ""
        segment = (user_profile.get("segment") or "").strip() if user_profile else ""

        # Personalized or contextual intro
        if detected_lang == "en":
            if first_name and segment == "VIP Customers":
                intro = f"Pleasure to advise you, **{first_name}**! As a **VIP** customer, here is our selection:"
            elif first_name:
                intro = f"Hello **{first_name}**! Here are the recommended references matching your search:"
            elif intent.get("is_cheap"):
                intro = "Here are the most affordable options currently in stock in the DarStore catalog:"
            elif intent.get("is_top"):
                intro = "Here are our top-rated references available in the DarStore catalog:"
            else:
                intro = "Here are the products available in the DarStore catalog matching your search:"
        else:
            if first_name and segment == "VIP Customers":
                if intent.get("is_cheap"):
                    intro = f"Ravi de vous conseiller, **{first_name}** ! En tant que client **VIP**, voici nos meilleures offres et remises exclusives :"
                elif intent.get("is_top"):
                    intro = f"Ravi de vous conseiller, **{first_name}** ! En tant que client **VIP**, voici notre sélection haut de gamme la plus prestigieuse :"
                else:
                    intro = f"Ravi de vous conseiller, **{first_name}** ! En tant que client **VIP**, découvrez notre sélection personnalisée :"
            elif first_name and segment == "Loyal Buyers":
                intro = f"Ravi de vous retrouver, **{first_name}** ! Voici notre sélection personnalisée selon vos préférences :"
            elif first_name:
                if intent.get("is_cheap"):
                    intro = f"Bonjour **{first_name}** ! Voici les meilleures opportunités tarifaires adaptées à votre budget :"
                elif intent.get("is_top"):
                    intro = f"Bonjour **{first_name}** ! Voici notre sélection des modèles les plus réputés et les mieux notés :"
                else:
                    intro = f"Bonjour **{first_name}** ! Voici les références recommandées selon votre recherche :"
            else:
                if intent.get("is_top"):
                    intro = "D'après les produits disponibles dans le catalogue DarStore, voici notre sélection des **modèles les plus réputés et les mieux notés** :"
                elif intent.get("is_cheap"):
                    intro = "D'après les produits disponibles dans le catalogue DarStore, voici les **meilleures opportunités tarifaires** actuellement en stock :"
                else:
                    intro = "D'après les produits disponibles dans le catalogue DarStore, voici les produits les plus adaptés à votre demande :"

        lines = [intro]

        for index, item in enumerate(retrieved_context[:5], 1):
            name = item.get("name", "Produit")
            brand = item.get("brand")
            display_name = f"{name} ({brand})" if brand else name
            badge = _product_badge(item, index, intent)
            rating_str = _rating_text(item, lang=detected_lang)

            if detected_lang == "en":
                item_lines = [
                    "",
                    f"{index}. {display_name}{badge}",
                    f"   - Category: {_category_text(item)}",
                    f"   - Price: {_price_text(item, lang='en')}",
                    f"   - Rating: {rating_str}",
                    f"   - Availability: {_availability_text(item, lang='en')}",
                    f"   - Why this fits: {_why_text(item, intent, lang='en')}",
                ]
            else:
                item_lines = [
                    "",
                    f"{index}. {display_name}{badge}",
                    f"   - Catégorie : {_category_text(item)}",
                    f"   - Prix : {_price_text(item, lang='fr')}",
                    f"   - Évaluation : {rating_str}",
                    f"   - Disponibilité : {_availability_text(item, lang='fr')}",
                    f"   - Pourquoi ce produit est adapté : {_why_text(item, intent, lang='fr')}",
                ]
            lines.extend(item_lines)

        return "\n".join(lines)
