from typing import List, Dict, Tuple
from sqlmodel import Session, select
from app.models.document import DocumentChunk
import structlog

log = structlog.get_logger("citations")


class CitationService:
    def __init__(self, db: Session):
        self.db = db

    def get_chunk_sources(self, chunk_ids: List[int]) -> Dict[int, dict]:
        """Get source document info for chunks"""
        chunks = self.db.exec(
            select(DocumentChunk)
            .where(DocumentChunk.id.in_(chunk_ids))
        ).all()
        
        from app.models.document import Document
        
        sources = {}
        for chunk in chunks:
            doc = self.db.exec(
                select(Document).where(Document.id == chunk.document_id)
            ).first()
            
            if doc:
                sources[chunk.id] = {
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "chunk_index": chunk.chunk_index,
                    "created_at": doc.created_at.isoformat()
                }
        
        return sources

    def format_citations(self, chunk_ids: List[int]) -> List[dict]:
        """Format citations for display"""
        sources = self.get_chunk_sources(chunk_ids)
        
        citations = []
        seen_docs = set()
        
        for chunk_id, source in sources.items():
            doc_id = source["document_id"]
            
            if doc_id not in seen_docs:
                citations.append({
                    "document": source["filename"],
                    "document_id": doc_id,
                    "chunks": [source["chunk_index"]]
                })
                seen_docs.add(doc_id)
            else:
                # Add chunk to existing citation
                for citation in citations:
                    if citation["document_id"] == doc_id:
                        citation["chunks"].append(source["chunk_index"])
                        break
        
        log.info("citations.formatted", count=len(citations))
        return citations

    def add_citation_to_response(
        self,
        response_content: str,
        retrieved_chunks: List[int],
        sources: List[str] = None
    ) -> Tuple[str, List[dict]]:
        """Add citations to response content"""
        citations = self.format_citations(retrieved_chunks)
        
        if citations:
            citation_text = "\n\n**Sources:**\n"
            for citation in citations:
                citation_text += f"- {citation['document']} (chunks {citation['chunks']})\n"
            
            response_content += citation_text
        
        return response_content, citations
