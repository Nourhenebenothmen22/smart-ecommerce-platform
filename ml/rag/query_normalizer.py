"""
ml/rag/query_normalizer.py — Query Normalization & Expansion for DarStore RAG.

Provides lightweight, rule-based query pre-processing before retrieval:
  1. Unicode normalization & lowercase
  2. Typo correction via static replacement map (no model needed)
  3. Abbreviation expansion (pc → ordinateur portable, etc.)
  4. Synonym expansion (inject canonical terms alongside the original)
  5. Multi-turn context injection (prepend prev-turn category/product signals)

All operations are pure-Python (no network, no GPU), executed synchronously
in < 1 ms per query.
"""

import re
import unicodedata
from typing import Optional

# ---------------------------------------------------------------------------
# 1. Abbreviation & informal term normalization map
# ---------------------------------------------------------------------------
_ABBREVIATIONS: dict[str, str] = {
    r"\bpcs?\b": "ordinateur portable",
    r"\bloc\b": "ordinateur portable",
    r"\blptps?\b": "laptop",
    r"\bsmartphn\b": "smartphone",
    r"\bsmphne\b": "smartphone",
    r"\bgsm\b": "téléphone mobile",
    r"\btv\b": "télévision",
    r"\btabs?\b": "tablette",
    r"\becouteurs\b": "écouteurs",
    r"\baudio\b": "casque audio",
    r"\bclaviers?\b": "clavier",
    r"\bsouris\b": "souris",
    r"\bcam\b": "caméra",
    r"\bapn\b": "appareil photo",
}

# Pre-compile all abbreviation patterns for speed
_ABBR_COMPILED = [
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in _ABBREVIATIONS.items()
]

# ---------------------------------------------------------------------------
# 2. Common typo / misspelling corrections (French + Arabic transliteration)
# ---------------------------------------------------------------------------
_TYPO_MAP: dict[str, str] = {
    "smarthphone": "smartphone",
    "smartphon": "smartphone",
    "samartphone": "smartphone",
    "tlephone": "téléphone",
    "telephon": "téléphone",
    "ordinatuer": "ordinateur",
    "orrdinateur": "ordinateur",
    "latpop": "laptop",
    "lapot": "laptop",
    "laptp": "laptop",
    "ecouteur": "écouteur",
    "ecouteurs": "écouteurs",
    "casqe": "casque",
    "casqu": "casque",
    "iphone": "iPhone",
    "mackbook": "MacBook",
    "macbok": "MacBook",
    "galaxi": "Galaxy",
    "galxy": "Galaxy",
    "samsong": "Samsung",
    "smsung": "Samsung",
    "consolle": "console",
    "consolee": "console",
    "consloe": "console",
    "promo": "promotion",
    "promos": "promotions",
    "soldes": "soldes",
    "moin cher": "moins cher",
    "moin chere": "moins cher",
    "prixminimum": "prix minimum",
    "prixmin": "prix minimum",
    "buget": "budget",
    "bugdet": "budget",
}

_TYPO_COMPILED = [
    (re.compile(rf"\b{re.escape(wrong)}\b", re.IGNORECASE), correct)
    for wrong, correct in _TYPO_MAP.items()
]

# ---------------------------------------------------------------------------
# 3. Price-intent keyword normalization
#    Ensures "prix minimum", "le moins cher", "pas cher" all map consistently
# ---------------------------------------------------------------------------
_CHEAP_NORMALIZE_PATTERNS = [
    # "prix minimum", "prix min", "le moins coûteux", etc.
    (re.compile(r"\bprix\s+min(?:imum|imal)?\b", re.IGNORECASE), "moins cher"),
    (re.compile(r"\ble?\s+moins\s+co[uû]teux\b", re.IGNORECASE), "moins cher"),
    (re.compile(r"\bplus?\s+(?:abordable|accessible)\b", re.IGNORECASE), "moins cher"),
    (re.compile(r"\b(?:en\s+dessous\s+de|sous)\s+(\d+)\b", re.IGNORECASE), r"moins de \1 EUR"),
    (re.compile(r"\b(?:economique|économique)\b", re.IGNORECASE), "pas cher"),
]

# ---------------------------------------------------------------------------
# 4. Category synonym expansion
#    Injects canonical category term after user's informal expression so that
#    both BM25 and the dense encoder pick up the right context.
# ---------------------------------------------------------------------------
_SYNONYM_EXPANSIONS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(?:tel|tél|teleph)\b", re.IGNORECASE), "téléphone smartphone"),
    (re.compile(r"\b(?:ordi|bécane)\b", re.IGNORECASE), "ordinateur laptop"),
    (re.compile(r"\b(?:play.?station|ps[45])\b", re.IGNORECASE), "console PlayStation"),
    (re.compile(r"\b(?:xbox)\b", re.IGNORECASE), "console Xbox"),
    (re.compile(r"\b(?:airpods?|earbuds?)\b", re.IGNORECASE), "écouteurs sans fil"),
    (re.compile(r"\b(?:frigo|réfrigérateur|frigidaire)\b", re.IGNORECASE), "réfrigérateur électroménager"),
    (re.compile(r"\b(?:lave.?linge)\b", re.IGNORECASE), "machine à laver électroménager"),
]


def _unicode_normalize(text: str) -> str:
    """Normalize unicode: NFKC decomposition then strip extra spaces."""
    normalized = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_query(
    query: str,
    session_category_hint: Optional[str] = None,
    session_product_hint: Optional[str] = None,
) -> str:
    """
    Normalize and enrich a raw user query before passing it to retrieval.

    Args:
        query: Raw user input (possibly with typos, abbreviations, arabic slang).
        session_category_hint: Most recent product category seen in this session
            (e.g., "Electronics / Smartphones"). If provided, injected into the
            query when a follow-up is detected.
        session_product_hint: Most recent product name seen in this session.

    Returns:
        Cleaned, normalized, and possibly enriched query string.
    """
    if not query or not query.strip():
        return query

    q = _unicode_normalize(query)

    # Step 1 — Typo correction (exact word boundaries)
    for pattern, correct in _TYPO_COMPILED:
        q = pattern.sub(correct, q)

    # Step 2 — Abbreviation expansion
    for pattern, replacement in _ABBR_COMPILED:
        q = pattern.sub(replacement, q)

    # Step 3 — Price-intent normalization
    for pattern, replacement in _CHEAP_NORMALIZE_PATTERNS:
        q = pattern.sub(replacement, q)

    # Step 4 — Synonym expansion (append canonical terms without replacing)
    for pattern, canonical in _SYNONYM_EXPANSIONS:
        if pattern.search(q):
            # Only append if the canonical term is not already present
            if canonical.split()[0].lower() not in q.lower():
                q = q.rstrip() + f" {canonical}"

    # Step 5 — Multi-turn session context injection
    #   If the query looks like a follow-up (short + no category mention) and we
    #   have a session category hint, prepend it to improve retrieval recall.
    is_short = len(q.split()) <= 6
    has_no_category = not re.search(
        r"\b(smartphone|ordinateur|laptop|casque|tablette|console|télévision|montre|vêtement)\b",
        q,
        re.IGNORECASE,
    )
    if is_short and has_no_category and session_category_hint:
        # Extract the leaf category from "Electronics / Smartphones" → "Smartphones"
        leaf = session_category_hint.split("/")[-1].strip()
        q = f"{leaf} {q}"

    # Clean up any double spaces introduced by substitutions
    q = re.sub(r"\s+", " ", q).strip()

    return q
