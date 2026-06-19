"""
Context compression utilities for RAG pipelines.
Removes redundant and low-value context before LLM generation.
"""
from __future__ import annotations

from typing import Any, Dict, List


def compress_context(
    chunks: List[Dict[str, Any]],
    max_total_chars: int = 6000,
    max_chunks: int = 8,
) -> List[Dict[str, Any]]:
    """
    Compress retrieved chunks to fit within token budget.
    Keeps highest-scoring chunks and truncates long text.
    """
    if not chunks:
        return []

    sorted_chunks = sorted(chunks, key=lambda c: c.get("score", 0), reverse=True)
    selected: List[Dict[str, Any]] = []
    total_chars = 0

    for chunk in sorted_chunks[:max_chunks]:
        text = chunk.get("text") or ""
        remaining = max_total_chars - total_chars
        if remaining <= 0:
            break

        if len(text) > remaining:
            truncated = dict(chunk)
            truncated["text"] = text[:remaining] + "…"
            truncated["truncated"] = True
            selected.append(truncated)
            break

        selected.append(chunk)
        total_chars += len(text)

    return selected


def deduplicate_chunks(chunks: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
    """Remove near-duplicate chunks based on text overlap."""
    if len(chunks) <= 1:
        return chunks

    unique: List[Dict[str, Any]] = []
    seen_texts: List[str] = []

    for chunk in chunks:
        text = (chunk.get("text") or "").strip().lower()
        if not text:
            continue

        is_duplicate = False
        for seen in seen_texts:
            shorter = min(len(text), len(seen))
            if shorter == 0:
                continue
            # Simple overlap check: if one contains most of the other
            overlap = sum(1 for w in text.split()[:20] if w in seen.split()[:20])
            if overlap / max(len(text.split()[:20]), 1) > similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(chunk)
            seen_texts.append(text)

    return unique
