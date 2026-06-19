"""Web search tool — delegates to WebSearchService for structured results."""
from typing import Dict, Any

import structlog

from app.config import get_settings
from app.services.web_search_service import WebSearchService

log = structlog.get_logger("web_search")
_settings = get_settings()


async def web_search(args: Dict[str, Any]) -> str:
    """Execute web search and return formatted, cited results."""
    query = str(args.get("query", "")).strip()
    if not query:
        return "No query provided."

    if not _settings.ENABLE_WEB_SEARCH:
        return "Web search is disabled. Set ENABLE_WEB_SEARCH=true to enable."

    try:
        service = WebSearchService()
        provider = args.get("provider")
        formatted = await service.search_formatted(query) if not provider else (
            "\n".join(
                f"{i}. **[{r.title}]({r.url})** (confidence: {r.score:.2f})\n   {r.snippet}"
                for i, r in enumerate(await service.search(query, provider=provider), 1)
            ) or f"No results found for: {query}"
        )
        log.info("web_search.success", query=query, provider=provider or _settings.WEB_SEARCH_PROVIDER)
        return formatted
    except Exception as e:
        log.error("web_search.error", query=query, error=str(e))
        return f"Search failed: {str(e)}"
