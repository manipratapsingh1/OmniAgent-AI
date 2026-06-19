from sqlmodel import Session, select, and_, delete
import structlog
from app.models.document import Document, DocumentChunk
from app.repositories.base import BaseRepo

log = structlog.get_logger("document_repo")


class DocumentRepo(BaseRepo[Document]):
    def __init__(self, session: Session):
        super().__init__(Document, session)

    def for_user(self, user_id: int):
        return self.session.exec(select(Document).where(Document.user_id == user_id)).all()

    def search_for_user(self, user_id: int, query: str):
        """Search documents by filename for a specific user"""
        return self.session.exec(
            select(Document).where(
                and_(
                    Document.user_id == user_id,
                    Document.filename.ilike(f"%{query}%")
                )
            )
        ).all()

    def get_by_status(self, user_id: int, status: str):
        """Get documents by status for a specific user"""
        return self.session.exec(
            select(Document).where(
                and_(
                    Document.user_id == user_id,
                    Document.status == status
                )
            )
        ).all()

    def delete(self, doc_id: int) -> bool:
        """Delete a document, all chunks, and vectors from Chroma"""
        doc = self.session.get(Document, doc_id)
        if not doc:
            log.warning("document.delete.not_found", doc_id=doc_id)
            return False
        
        try:
            # CRITICAL: Remove vectors from Chroma vector store
            # Otherwise deleted documents will still be searchable
            from app.rag.retriever import get_vector_store
            
            try:
                store = get_vector_store()
                if store.collection:
                    # Generate all vector IDs for this document
                    # Vector IDs are formatted as "{doc_id}-{chunk_index}"
                    ids_to_delete = [f"{doc_id}-{i}" for i in range(doc.chunk_count or 0)]
                    
                    if ids_to_delete:
                        # Delete from Chroma
                        store.collection.delete(ids=ids_to_delete)
                        log.info(
                            "document.vectors_deleted",
                            doc_id=doc_id,
                            vectors_deleted=len(ids_to_delete),
                        )
            except Exception as e:
                log.warning(
                    "document.vector_deletion_failed",
                    doc_id=doc_id,
                    error=str(e),
                )
                # Continue with database deletion even if vector deletion fails
        
            # Delete all associated chunks from database
            chunks = self.session.exec(select(DocumentChunk).where(DocumentChunk.document_id == doc_id)).all()
            for chunk in chunks:
                self.session.delete(chunk)
            
            # Delete referencing StudyMaterial records (which lack CASCADE)
            from app.models.knowledge import StudyMaterial
            materials = self.session.exec(select(StudyMaterial).where(StudyMaterial.document_id == doc_id)).all()
            for material in materials:
                self.session.delete(material)
            
            # Delete the document
            self.session.delete(doc)
            self.session.commit()
            
            log.info(
                "document.deleted",
                doc_id=doc_id,
                filename=doc.filename,
                chunks_deleted=len(chunks),
            )
            return True
            
        except Exception as e:
            log.exception(
                "document.deletion_failed",
                doc_id=doc_id,
                error=str(e),
            )
            self.session.rollback()
            return False

    def add_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        self.session.add(chunk)
        self.session.commit()
        self.session.refresh(chunk)
        return chunk