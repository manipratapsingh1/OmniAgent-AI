"""Web search tool with support for multiple providers.
Supports DuckDuckGo (default, no API key), Tavily AI, or custom SearxNG instance."""
import httpx
from typing import Dict, Any, List, Optional
from app.config import get_settings
import structlog

log = structlog.get_logger("web_search")

_settings = get_settings()


async def web_search(args: Dict[str, Any]) -> str:
    """Execute web search and return formatted results."""
    query = str(args.get("query", "")).strip()
    if not query:
        return "No query provided."
    
    try:
        # Determine which provider to use
        provider = getattr(_settings, "WEB_SEARCH_PROVIDER", "duckduckgo").lower()
        
        if provider == "tavily":
            return await _search_tavily(query)
        elif provider == "searxng":
            return await _search_searxng(query)
        else:
            # Default to DuckDuckGo
            return await _search_duckduckgo(query)
    
    except Exception as e:
        log.error("web_search.error", query=query, error=str(e))
        return f"Search failed: {str(e)}"


async def _search_duckduckgo(query: str) -> str:
    """Search using DuckDuckGo library (free, no key required)."""
    try:
        from duckduckgo_search import DDGS
        
        results = []
        with DDGS() as ddgs:
            # Get web results
            ddgs_results = ddgs.text(query, max_results=5)
            for r in ddgs_results:
                results.append({
                    "title": r.get("title", "Result"),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", ""),
                })
        
        if not results:
            return f"No results found for: {query}"
        
        # Format results
        formatted = f"**Web Search Results for: {query}**\n\n"
        for i, result in enumerate(results, 1):
            formatted += f"{i}. **[{result.get('title', 'Result')}]({result.get('url')})**\n"
            formatted += f"   {result.get('snippet', '')}\n\n"
        
        log.info("web_search.duckduckgo.success", query=query, result_count=len(results))
        return formatted.strip()
    
    except Exception as e:
        log.error("web_search.duckduckgo.error", query=query, error=str(e))
        return f"DuckDuckGo search failed: {str(e)}"


async def _search_tavily(query: str) -> str:
    """Search using Tavily AI API (requires TAVILY_API_KEY env var)."""
    api_key = getattr(_settings, "TAVILY_API_KEY", None)
    if not api_key:
        return "Tavily API key not configured."
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "api_key": api_key,
                "query": query,
                "max_results": 5,
                "include_domains": [],
                "exclude_domains": [],
            }
            
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if not results:
                return f"No results found for: {query}"
            
            # Format results
            formatted = f"**Search Results for: {query}**\n\n"
            for i, result in enumerate(results, 1):
                formatted += f"{i}. **{result.get('title', 'Result')}**\n"
                formatted += f"   {result.get('content', '')}\n"
                formatted += f"   Link: {result.get('url', '')}\n\n"
            
            log.info("web_search.tavily.success", query=query, result_count=len(results))
            return formatted.strip()
    
    except Exception as e:
        log.error("web_search.tavily.error", query=query, error=str(e))
        raise


async def _search_searxng(query: str) -> str:
    """Search using SearxNG instance (self-hosted, requires SEARXNG_BASE_URL env var)."""
    base_url = getattr(_settings, "SEARXNG_BASE_URL", None)
    if not base_url:
        return "SearxNG base URL not configured."
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "q": query,
                "format": "json",
                "pageno": 1,
            }
            
            response = await client.get(f"{base_url.rstrip('/')}/search", params=params)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if not results:
                return f"No results found for: {query}"
            
            # Format results
            formatted = f"**Search Results for: {query}**\n\n"
            for i, result in enumerate(results[:5], 1):
                formatted += f"{i}. **{result.get('title', 'Result')}**\n"
                formatted += f"   {result.get('content', '')}\n"
                formatted += f"   Link: {result.get('url', '')}\n\n"
            
            log.info("web_search.searxng.success", query=query, result_count=len(results))
            return formatted.strip()
    
    except Exception as e:
        log.error("web_search.searxng.error", query=query, error=str(e))
        raise