import structlog
import asyncio
from datetime import datetime, timezone
from typing import Optional, Callable
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.repositories.document_repo import DocumentRepo
from app.rag.ingest import ingest_file
from app.services.knowledge_service import KnowledgeService
from app.services.audit_service import AuditService

log = structlog.get_logger("documents")


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DocumentRepo(db)

    async def upload(
        self,
        user_id: int,
        filename: str,
        mime_type: str,
        raw: bytes,
        is_knowledge_base: bool = False,
        job_id: Optional[int] = None,
    ) -> Document:
        doc = Document(
            user_id=user_id,
            filename=filename,
            mime_type=mime_type or "application/octet-stream",
            size_bytes=len(raw),
            status="pending",
            embedding_status="pending",
            error_message=None,
            is_knowledge_base=is_knowledge_base,
        )

        try:
            # Save first so doc.id is available for ingestion and logs
            doc = self.repo.add(doc)
            self.db.flush()
            self.db.commit()
            self.db.refresh(doc)

            log.info(
                "document.upload.start",
                user_id=user_id,
                doc_id=doc.id,
                filename=filename,
                size_bytes=len(raw),
                mime_type=mime_type,
            )

            # Prepare optional progress callback to update background job status
            progress_callback: Optional[Callable[[int, str], None]] = None
            if job_id:
                try:
                    from app.services.background_job_service import BackgroundJobService

                    def _progress(pct: int, message: str = ""):
                        try:
                            BackgroundJobService(self.db).update_status(job_id, "processing", progress=int(pct), result=message)
                        except Exception:
                            pass

                    progress_callback = _progress
                except Exception:
                    progress_callback = None

            # Ingest into RAG pipeline and get chunks, vectors, and IDs
            n_chunks, n_vectors, vector_ids, chunk_texts = await ingest_file(
                user_id,
                doc.id,
                filename,
                raw,
                is_knowledge_base=is_knowledge_base,
                progress_callback=progress_callback,
            )

            log.info(
                "document.rag.ingested",
                doc_id=doc.id,
                chunks_created=n_chunks,
                vectors_created=n_vectors,
                success=n_chunks > 0,
            )

            # Store chunk metadata in database with vector IDs
            if n_chunks > 0 and vector_ids and chunk_texts:
                chunks_stored = 0
                chunks_failed = 0
                for i, (vector_id, chunk_text) in enumerate(zip(vector_ids, chunk_texts)):
                    try:
                        chunk = DocumentChunk(
                            document_id=doc.id,
                            chunk_index=i,
                            text=chunk_text[:2000],  # Store first 2000 chars for display
                            vector_id=vector_id,
                        )
                        self.db.add(chunk)
                        chunks_stored += 1
                    except Exception as e:
                        chunks_failed += 1
                        log.warning(
                            "chunk.store.failed",
                            doc_id=doc.id,
                            chunk_index=i,
                            error=str(e),
                        )

                self.db.commit()
                
                log.info(
                    "document.chunks.stored",
                    doc_id=doc.id,
                    chunks_stored=chunks_stored,
                    chunks_failed=chunks_failed,
                )

            # Verify retrieval works for at least one chunk before marking as indexed
            retrieval_ok = False
            if n_chunks > 0:
                try:
                    from app.rag.retriever import retrieve
                    test_results = await retrieve(user_id=user_id, query=chunk_texts[0][:100], k=1, db=self.db)
                    if test_results:
                        retrieval_ok = True
                    else:
                        log.warning("document.retrieval_test_failed", doc_id=doc.id)
                except Exception as e:
                    log.warning("document.retrieval_test_error", doc_id=doc.id, error=str(e))

            # Update status based on successful ingestion and retrieval verification
            doc.status = "indexed" if (n_chunks > 0 and retrieval_ok) else "failed"
            doc.embedding_status = "embedded" if n_chunks > 0 else "failed"
            doc.chunk_count = n_chunks
            doc.last_indexed_at = datetime.now(timezone.utc)
            doc.vector_ids_prefix = f"{doc.id}-"
            
            # Set error message if ingestion failed
            if n_chunks == 0:
                doc.error_message = "No text extracted from file or embedding failed"
            elif not retrieval_ok:
                doc.error_message = "Embeddings created but retrieval verification failed"
            else:
                log.info(
                    "document.indexed.success",
                    doc_id=doc.id,
                    filename=filename,
                    chunks=n_chunks,
                    vectors=n_vectors,
                )
            
            self.db.add(doc)
            self.db.commit()
            self.db.refresh(doc)

            AuditService(self.db).log(action="upload_document", entity="document", user_id=user_id, entity_id=str(doc.id), meta={"filename": filename})

            log.info(
                "document.upload.complete",
                doc_id=doc.id,
                status=doc.status,
                embedding_status=doc.embedding_status,
            )

            # Stage 8 & 11: AI Second Brain & Workflow Automation
            if doc.status == "indexed" and chunk_texts:
                full_text = " ".join(chunk_texts[:10]) # Use first 10 chunks for summary/materials to avoid too much context
                asyncio.create_task(KnowledgeService(self.db).run_workflow(user_id, doc.id, full_text))

            return doc

        except Exception as e:
            self.db.rollback()

            # Try to mark the document as failed with error message
            try:
                doc.status = "failed"
                doc.embedding_status = "failed"
                doc.error_message = str(e)[:500]  # Store first 500 chars of error
                self.db.add(doc)
                self.db.commit()
                self.db.refresh(doc)
            except Exception as rollback_error:
                log.warning(
                    "document.status_update.failed",
                    doc_id=doc.id if hasattr(doc, 'id') else None,
                    error=str(rollback_error),
                )
                self.db.rollback()

            log.exception(
                "document.upload.failed",
                user_id=user_id,
                filename=filename,
                doc_id=doc.id if hasattr(doc, 'id') else None,
                error=str(e),
            )
            raise

    def list_for_user(self, user_id: int):
        docs = self.repo.for_user(user_id)
        log.info("document.list", user_id=user_id, count=len(docs))
        return docs

    def delete(self, user_id: int, doc_id: int) -> bool:
        doc = self.repo.get(doc_id)
        if not doc or doc.user_id != user_id:
            log.warning("document.delete.access_denied", user_id=user_id, doc_id=doc_id)
            raise ValueError("Document not found or access denied")

        log.info("document.delete", user_id=user_id, doc_id=doc_id, filename=doc.filename)
        return self.repo.delete(doc_id)