"""
Query rewriting and expansion for improved RAG retrieval.
Generates alternative query formulations to improve recall.
"""
from __future__ import annotations

import re
from typing import List

import structlog

log = structlog.get_logger("query_rewriter")

# Stop words to remove for keyword extraction
_STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "what", "which", "who", "whom", "this", "that", "these", "those",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "my", "your", "his", "its", "our", "their", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "about", "into", "through", "during",
    "before", "after", "above", "below", "between", "and", "or", "but",
    "not", "no", "how", "when", "where", "why", "please", "tell", "explain",
}


def extract_keywords(query: str, max_keywords: int = 8) -> List[str]:
    """Extract meaningful keywords from a query."""
    tokens = re.findall(r"\b[a-zA-Z0-9]{2,}\b", query.lower())
    keywords = [t for t in tokens if t not in _STOP_WORDS]
    return keywords[:max_keywords]


def rewrite_query(query: str) -> List[str]:
    """
    Generate query variants for multi-query retrieval.
    Returns original query plus up to 3 rewritten variants.
    """
    query = query.strip()
    if not query:
        return []

    variants = [query]
    keywords = extract_keywords(query)

    if len(keywords) >= 2:
        # Keyword-only variant (improves BM25 recall)
        kw_query = " ".join(keywords)
        if kw_query != query.lower():
            variants.append(kw_query)

    # Question simplification: strip question words
    simplified = re.sub(
        r"^(what|how|why|when|where|who|which|can|could|would|should|is|are|do|does)\s+",
        "",
        query,
        flags=re.I,
    ).strip(" ?.")
    if simplified and simplified != query and len(simplified) > 5:
        variants.append(simplified)

    # Definition-style variant for "what is X" queries
    what_match = re.match(r"what\s+(?:is|are)\s+(.+?)\??$", query, re.I)
    if what_match:
        subject = what_match.group(1).strip()
        variants.append(f"{subject} definition explanation")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for v in variants:
        key = v.lower()
        if key not in seen:
            seen.add(key)
            unique.append(v)

    log.debug("query_rewriter.rewritten", original=query, variants=len(unique))
    return unique[:4]


def expand_query_with_synonyms(query: str) -> str:
    """
    Lightweight query expansion using common synonym mappings.
    Used as a single expanded query string for hybrid search.
    """
    expansions = {
        "ai": "artificial intelligence machine learning",
        "ml": "machine learning",
        "db": "database",
        "api": "application programming interface",
        "rag": "retrieval augmented generation",
        "llm": "large language model",
    }
    lower = query.lower()
    extra_terms = []
    for abbr, expansion in expansions.items():
        if re.search(rf"\b{re.escape(abbr)}\b", lower):
            extra_terms.append(expansion)

    if extra_terms:
        return f"{query} {' '.join(extra_terms)}"
    return query
