"""
Citation extraction utilities for parsing [doc:X#Y] patterns from AI responses.
Enables accurate tracking of which documents were actually used in responses.
"""

import re
import structlog
from typing import List, Dict, Set, Any, Tuple

log = structlog.get_logger("citations")


def extract_citations_from_response(response: str) -> List[Dict[str, Any]]:
    """
    Extract citation references from model response text.
    
    Matches patterns like: [doc:123#5], [doc:456#2], etc.
    Returns list of dicts with document_id and chunk_index.
    
    Args:
        response: The AI model's text response
        
    Returns:
        List of dicts: [{"document_id": 123, "chunk_index": 5}, ...]
    """
    if not response or not isinstance(response, str):
        return []
    
    try:
        # Match [doc:DIGITS#DIGITS] pattern
        pattern = r'\[doc:(\d+)#(\d+)\]'
        matches = re.findall(pattern, response)
        
        citations = []
        seen = set()  # Track unique citations to avoid duplicates
        
        for doc_id_str, chunk_idx_str in matches:
            try:
                doc_id = int(doc_id_str)
                chunk_idx = int(chunk_idx_str)
                key = (doc_id, chunk_idx)
                
                if key not in seen:
                    citations.append({
                        "document_id": doc_id,
                        "chunk_index": chunk_idx,
                    })
                    seen.add(key)
            except (ValueError, TypeError) as e:
                log.debug("citation.parse_error", doc_id=doc_id_str, chunk_idx=chunk_idx_str, error=str(e))
                continue
        
        log.debug("citations.extracted", count=len(citations), response_len=len(response))
        return citations
        
    except Exception as e:
        log.exception("citations.extraction_failed", error=str(e))
        return []


def filter_sources_by_citations(
    all_sources: List[Dict[str, Any]], 
    cited_indices: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Filter sources to only include those that were actually cited in the response.
    
    Args:
        all_sources: All retrieved sources [{"document_id": X, "chunk_index": Y, ...}, ...]
        cited_indices: Citations extracted from response [{"document_id": X, "chunk_index": Y}, ...]
        
    Returns:
        Filtered list of sources that were cited, in order of appearance in response
    """
    if not cited_indices:
        return []
    
    if not all_sources:
        return []
    
    try:
        # Create lookup for all sources
        source_map = {}
        for source in all_sources:
            doc_id = source.get("document_id")
            chunk_idx = source.get("chunk_index")
            if doc_id is not None and chunk_idx is not None:
                source_map[(doc_id, chunk_idx)] = source
        
        # Filter to only cited sources, maintaining citation order
        cited_sources = []
        for citation in cited_indices:
            key = (citation.get("document_id"), citation.get("chunk_index"))
            if key in source_map:
                cited_sources.append(source_map[key])
        
        log.debug(
            "sources.filtered",
            total_retrieved=len(all_sources),
            total_cited=len(cited_indices),
            actual_cited=len(cited_sources),
        )
        return cited_sources
        
    except Exception as e:
        log.exception("sources.filtering_failed", error=str(e))
        return []


def get_citations_with_fallback(
    response: str,
    all_sources: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Extract citations from response with graceful fallback.
    
    If citations are found and match retrieved sources, return those.
    Otherwise return empty list (don't show unverified sources).
    
    Args:
        response: AI model's text response
        all_sources: All retrieved document chunks
        
    Returns:
        Tuple of (cited_sources, was_cited)
        where was_cited indicates whether model explicitly cited sources
    """
    if not response:
        return [], False
    
    # Try to extract citations from response
    citations = extract_citations_from_response(response)
    
    if citations:
        # Filter to only those that actually exist in retrieved sources
        filtered = filter_sources_by_citations(all_sources, citations)
        
        if filtered:
            log.info(
                "citations.found",
                extracted_count=len(citations),
                verified_count=len(filtered),
            )
            return filtered, True
        else:
            # Citations found but don't match retrieved sources - likely hallucination
            log.warning(
                "citations.unverified",
                extracted_count=len(citations),
                retrieved_count=len(all_sources),
            )
            if all_sources:
                return [all_sources[0]], False
            return [], False
    else:
        # No citations found in response - fallback to returning the top matching retrieved source
        if all_sources:
            log.info("citations.fallback_to_top_source", total_sources=len(all_sources))
            return [all_sources[0]], False
        log.debug("citations.not_found", response_len=len(response))
        return [], False


def validate_citation_accuracy(
    response: str,
    cited_sources: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate citation accuracy and provide debugging info.
    
    Args:
        response: AI model's response text
        cited_sources: Sources that were included in response
        
    Returns:
        Dict with validation metrics:
        {
            "citations_in_text": N,
            "verified_sources": N,
            "all_sources_cited": bool,
            "has_unverified_citations": bool,
            "accuracy_score": 0.0-1.0
        }
    """
    try:
        citations = extract_citations_from_response(response)
        num_citations_in_text = len(citations)
        num_verified = len(cited_sources)
        
        # Score: 1.0 if all citations verified, 0.0 if none
        accuracy_score = num_verified / num_citations_in_text if num_citations_in_text > 0 else 0.0
        
        return {
            "citations_in_text": num_citations_in_text,
            "verified_sources": num_verified,
            "accuracy_score": accuracy_score,
            "has_unverified_citations": num_citations_in_text > num_verified,
        }
    except Exception as e:
        log.exception("citations.validation_failed", error=str(e))
        return {
            "citations_in_text": 0,
            "verified_sources": 0,
            "accuracy_score": 0.0,
            "has_unverified_citations": False,
        }
