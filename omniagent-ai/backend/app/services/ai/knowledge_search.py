"""
Knowledge Base Search Service

Searches admin-uploaded knowledge base documents using semantic search.
Returns relevant chunks with metadata for hybrid AI responses.
"""

from typing import List, Dict, Any, Optional
import structlog
from sqlmodel import Session, select

from app.models.document import Document, DocumentChunk
from app.rag.retriever import retrieve

log = structlog.get_logger("knowledge_search")


class KnowledgeSearchService:
    """Search admin-uploaded knowledge base documents only."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_knowledge_base_doc_ids(self) -> List[int]:
        """Get all admin-uploaded knowledge base document IDs."""
        try:
            docs = self.db.exec(
                select(Document).where(
                    Document.is_knowledge_base == True,
                    Document.status == "indexed",
                    Document.embedding_status == "embedded",
                )
            ).all()
            
            doc_ids = [doc.id for doc in docs]
            log.info("knowledge_search.docs_found", count=len(doc_ids))
            return doc_ids
        except Exception as e:
            log.error("knowledge_search.get_docs_failed", error=str(e))
            return []
    
    async def search_knowledge_base(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base for relevant chunks.

        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum relevance score (0-1)

        Returns:
            List of relevant chunks with metadata
        """
        log.info("knowledge_search.start", query_len=len(query), k=k)

        try:
            # Get admin knowledge base documents
            doc_ids = self._get_knowledge_base_doc_ids()

            if not doc_ids:
                log.warning("knowledge_search.no_docs_found")
                return []

            # Search knowledge base using RAG retriever over knowledge base docs
            results = await retrieve(
                user_id=None,
                query=query,
                k=k,
                filters={"is_knowledge_base": True},
                db=self.db,
            )

            if not results:
                log.info("knowledge_search.no_results", query=query)
                return []

            kb_results = [
                result for result in results if result.get("document_id") in doc_ids
            ]

            log.info(
                "knowledge_search.complete",
                query=query,
                total_results=len(results),
                kb_results=len(kb_results),
                k=k,
            )

            return kb_results

        except Exception as e:
            log.error("knowledge_search.error", error=str(e), query=query)
            return []
    
    def get_knowledge_base_summary(self) -> Dict[str, Any]:
        """Get summary of knowledge base documents."""
        try:
            docs = self.db.exec(
                select(Document).where(
                    Document.is_knowledge_base == True
                )
            ).all()
            
            total_size = sum(doc.size_bytes for doc in docs)
            total_chunks = sum(doc.chunk_count for doc in docs)
            indexed_count = sum(1 for doc in docs if doc.status == "indexed")
            
            return {
                "total_documents": len(docs),
                "indexed_documents": indexed_count,
                "failed_documents": len(docs) - indexed_count,
                "total_size_bytes": total_size,
                "total_chunks": total_chunks,
                "documents": [
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "status": doc.status,
                        "chunk_count": doc.chunk_count,
                        "size_bytes": doc.size_bytes,
                        "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
                    }
                    for doc in docs
                ]
            }
        except Exception as e:
            log.error("knowledge_search.summary_failed", error=str(e))
            return {}
