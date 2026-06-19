"""
Structured web search service with multi-provider support, reranking, and citations.

Providers: DuckDuckGo, Tavily, Brave Search, SerpAPI, SearxNG
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
import structlog

from app.config import get_settings
from app.rag.hybrid_search import bm25_score

log = structlog.get_logger("web_search_service")
_settings = get_settings()


class SearchResult:
    """Structured search result with citation metadata."""

    def __init__(
        self,
        title: str,
        snippet: str,
        url: str,
        source: str = "web",
        score: float = 0.0,
    ):
        self.title = title
        self.snippet = snippet
        self.url = url
        self.source = source
        self.score = score
        self.retrieved_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "source": self.source,
            "score": round(self.score, 3),
            "confidence_score": round(min(self.score, 1.0), 3),
            "retrieved_at": self.retrieved_at,
        }

    def to_citation(self, index: int) -> str:
        return f"[web:{index}] {self.title} — {self.url}"


def rerank_results(results: List[SearchResult], query: str) -> List[SearchResult]:
    """Rerank search results using BM25 over title + snippet."""
    for r in results:
        combined = f"{r.title} {r.snippet}"
        r.score = bm25_score(query, combined)
    results.sort(key=lambda x: x.score, reverse=True)
    return results


def validate_url(url: str) -> bool:
    """Basic URL validation to filter malformed results."""
    if not url:
        return False
    return bool(re.match(r"^https?://[^\s/$.?#].[^\s]*$", url, re.I))


class WebSearchService:
    """Multi-provider web search with routing, reranking, and structured citations."""

    def __init__(self):
        self.provider = _settings.WEB_SEARCH_PROVIDER.lower()
        self.max_results = _settings.WEB_SEARCH_MAX_RESULTS

    async def search(self, query: str, provider: Optional[str] = None) -> List[SearchResult]:
        if not query.strip():
            return []

        prov = (provider or self.provider).lower()
        fetchers = {
            "duckduckgo": self._search_duckduckgo,
            "tavily": self._search_tavily,
            "brave": self._search_brave,
            "serpapi": self._search_serpapi,
            "searxng": self._search_searxng,
        }
        fetcher = fetchers.get(prov, self._search_duckduckgo)

        try:
            results = await fetcher(query)
        except Exception as e:
            log.warning("web_search.primary_failed", provider=prov, error=str(e))
            # Fallback chain
            for fallback in ["duckduckgo", "tavily", "brave"]:
                if fallback != prov and fallback in fetchers:
                    try:
                        results = await fetchers[fallback](query)
                        log.info("web_search.fallback_success", provider=fallback)
                        break
                    except Exception:
                        continue
            else:
                return []

        valid = [r for r in results if validate_url(r.url)]
        return rerank_results(valid, query)[: self.max_results]

    async def search_formatted(self, query: str) -> str:
        results = await self.search(query)
        if not results:
            return f"No web results found for: {query}"

        lines = [f"**Web Search Results** (retrieved {results[0].retrieved_at})\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **[{r.title}]({r.url})** (confidence: {r.score:.2f})")
            lines.append(f"   {r.snippet}\n")
        return "\n".join(lines)

    async def _search_duckduckgo(self, query: str) -> List[SearchResult]:
        import asyncio
        
        def _sync_ddg():
            from duckduckgo_search import DDGS
            results = []
            try:
                with DDGS() as ddgs:
                    res_list = list(ddgs.text(query, max_results=self.max_results))
                    for r in res_list:
                        results.append(SearchResult(
                            title=r.get("title", "Result"),
                            snippet=r.get("body", ""),
                            url=r.get("href", ""),
                            source="duckduckgo",
                        ))
            except Exception as ddg_err:
                log.warning("web_search.ddg_sync_failed", error=str(ddg_err))
            return results

        return await asyncio.to_thread(_sync_ddg)

    async def _search_tavily(self, query: str) -> List[SearchResult]:
        api_key = _settings.TAVILY_API_KEY
        if not api_key:
            raise ValueError("TAVILY_API_KEY not configured")
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query, "max_results": self.max_results},
            )
            r.raise_for_status()
            return [
                SearchResult(
                    title=item.get("title", ""),
                    snippet=item.get("content", ""),
                    url=item.get("url", ""),
                    source="tavily",
                    score=item.get("score", 0.0),
                )
                for item in r.json().get("results", [])
            ]

    async def _search_brave(self, query: str) -> List[SearchResult]:
        api_key = _settings.BRAVE_API_KEY
        if not api_key:
            raise ValueError("BRAVE_API_KEY not configured")
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"Accept": "application/json", "X-Subscription-Token": api_key},
                params={"q": query, "count": self.max_results},
            )
            r.raise_for_status()
            web_results = r.json().get("web", {}).get("results", [])
            return [
                SearchResult(
                    title=item.get("title", ""),
                    snippet=item.get("description", ""),
                    url=item.get("url", ""),
                    source="brave",
                )
                for item in web_results
            ]

    async def _search_serpapi(self, query: str) -> List[SearchResult]:
        api_key = _settings.SERPAPI_KEY
        if not api_key:
            raise ValueError("SERPAPI_KEY not configured")
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                "https://serpapi.com/search",
                params={"q": query, "api_key": api_key, "num": self.max_results, "engine": "google"},
            )
            r.raise_for_status()
            organic = r.json().get("organic_results", [])
            return [
                SearchResult(
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    url=item.get("link", ""),
                    source="serpapi",
                )
                for item in organic
            ]

    async def _search_searxng(self, query: str) -> List[SearchResult]:
        base_url = _settings.SEARXNG_BASE_URL
        if not base_url:
            raise ValueError("SEARXNG_BASE_URL not configured")
        
        from app.core.security_checks import is_safe_url
        if not is_safe_url(base_url):
            raise ValueError("SEARXNG_BASE_URL points to an unsafe or restricted address (SSRF protection)")

        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{base_url.rstrip('/')}/search",
                params={"q": query, "format": "json"},
            )
            r.raise_for_status()
            return [
                SearchResult(
                    title=item.get("title", ""),
                    snippet=item.get("content", ""),
                    url=item.get("url", ""),
                    source="searxng",
                )
                for item in r.json().get("results", [])[: self.max_results]
            ]
