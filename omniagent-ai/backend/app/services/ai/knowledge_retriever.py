from typing import List, Dict, Any, Optional
from app.config import get_settings


class KnowledgeRetriever:
    """Wrapper for RAG retrieval. Uses existing app.rag.retriever when available."""

    def __init__(self):
        self.settings = get_settings()

    def retrieve(self, user_id: int, query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        try:
            from app.rag.retriever import retrieve as rag_retrieve
            # rag_retrieve is async in some places; call sync-safe wrapper if needed
            import asyncio
            return asyncio.get_event_loop().run_until_complete(rag_retrieve(user_id=user_id, query=query, k=k, filters=filters))
        except Exception:
            return []
