import time
import asyncio

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, select, col
from typing import List, Optional, Dict, Any, cast

from app.deps import db_session, current_user, require_admin
from app.models.user import User
from app.models.document import DocumentChunk
from app.schemas.document import DocumentOut
from app.schemas.chat import ChatResponse, Citation
from app.services.document_service import DocumentService
from app.services.background_job_service import BackgroundJobService
from app.workers.queue import default_queue
from app.llm.ollama_client import ollama
from app.llm.prompts import RESEARCH_SYSTEM
from app.rag.retriever import retrieve, get_optimized_retriever
from app.repositories.document_repo import DocumentRepo
from app import metrics as app_metrics
from app.utils.security import sanitize_filename

router = APIRouter()
ALLOWED = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/x-markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/octet-stream",
    "text/html",
}

def _allowed_file(filename: str, content_type: str) -> bool:
    lower_name = filename.lower()
    # Explicitly block executables and scripting files for reliability and security hardening
    blocked_exts = (".exe", ".bat", ".sh", ".cmd", ".msi", ".vbs", ".scr", ".js", ".vbe", ".jse", ".wsf", ".wsh")
    if lower_name.endswith(blocked_exts):
        return False
    allowed_ext = (".md", ".txt", ".pdf", ".markdown", ".docx", ".pptx", ".html", ".htm", ".csv", ".xlsx", ".png", ".jpg", ".jpeg", ".webp")
    return lower_name.endswith(allowed_ext) or content_type in ALLOWED


class DocumentQARequest(BaseModel):
    question: str
    document_id: Optional[int] = None
    k: int = 5


class DocumentChunkOut(BaseModel):
    id: int
    chunk_index: int
    text: str
    vector_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentPreviewResponse(BaseModel):
    document: DocumentOut
    chunks: List[DocumentChunkOut]

    model_config = ConfigDict(from_attributes=True)


@router.get("/{doc_id}/preview", response_model=DocumentPreviewResponse)
def preview_document(
    doc_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    if user.id is None:
        raise HTTPException(status_code=401, detail="User ID not found")

    doc = DocumentRepo(db).get(doc_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = db.exec(
        select(DocumentChunk)
        .where(col(DocumentChunk.document_id) == doc_id)
        .order_by(col(DocumentChunk.chunk_index))
        .limit(8)
    ).all()

    return DocumentPreviewResponse(
        document=DocumentOut(**doc.model_dump()),
        chunks=chunks
    )


@router.post("/cache/clear")
def clear_retriever_cache(
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
):
    """Clear the optimized retriever cache (if available)."""
    optimized = get_optimized_retriever()
    if not optimized:
        return {"cleared": False, "reason": "optimized retriever not active"}

    optimized.clear_cache()
    return {"cleared": True}


@router.get("/cache/stats")
def retriever_cache_stats(
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
):
    """Get basic cache stats for the optimized retriever."""
    optimized = get_optimized_retriever()
    if not optimized:
        return {"active": False, "stats": {}}

    return {"active": True, "stats": optimized.get_cache_stats()}


@router.post("/upload", response_model=DocumentOut)
async def upload(file: UploadFile = File(...), db: Session = Depends(db_session), user: User = Depends(current_user)):
    """Upload document"""
    try:
        if user.id is None:
            raise HTTPException(status_code=401, detail="User ID not found")
        user_id = cast(int, user.id)

        filename_raw = cast(str, file.filename or "")
        valid_name, safe_filename, name_error = sanitize_filename(filename_raw)
        if not valid_name:
            raise HTTPException(status_code=400, detail=name_error)

        filename = safe_filename.lower()
        if not _allowed_file(filename, file.content_type or ""):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Allowed: PDF, TXT, MD, DOCX, PPTX, HTML, CSV, XLSX, Images",
            )

        raw = await file.read()
        
        # Check file size
        max_size_bytes = 10 * 1024 * 1024
        if len(raw) > max_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size is 10MB, but got {len(raw) / 1024 / 1024:.1f}MB"
            )
        
        # Check if file is empty
        if len(raw) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Log upload attempt
        import structlog
        log = structlog.get_logger("document_api")
        log.info(
            "document.upload.attempt",
            user_id=user_id,
            filename=filename,
            file_size_kb=len(raw) / 1024
        )
        
        doc = await DocumentService(db).upload(
            user_id,
            filename_raw,
            file.content_type or "application/octet-stream",
            raw,
        )
        return DocumentOut(**doc.model_dump())
    
    except HTTPException:
        raise
    except Exception as e:
        import structlog
        log = structlog.get_logger("document_api")
        log.exception("document.upload.failed", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)[:100]}"
        )


@router.post("/knowledge-base/upload", response_model=DocumentOut)
async def upload_knowledge_base(
    file: UploadFile = File(...),
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """
    Upload a document to the knowledge base.
    Only administrators can upload knowledge base documents.
    These documents will be used to answer all users' questions.
    """
    try:
        if user.id is None:
            raise HTTPException(status_code=401, detail="User ID not found")
        user_id = cast(int, user.id)

        import structlog
        log = structlog.get_logger("document_api")
        
        filename_raw = cast(str, file.filename or "")
        filename = filename_raw.lower()
        if not _allowed_file(filename, file.content_type or ""):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Allowed: PDF, TXT, MD, DOCX, PPTX, HTML, CSV, XLSX, Images",
            )

        raw = await file.read()
        
        # Check file size
        max_size_bytes = 10 * 1024 * 1024
        if len(raw) > max_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size is 10MB, but got {len(raw) / 1024 / 1024:.1f}MB"
            )
        
        # Check if file is empty
        if len(raw) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        log.info(
            "document.knowledge_base_upload.attempt",
            admin_id=user_id,
            filename=filename,
            file_size_kb=len(raw) / 1024
        )
        
        # Upload the document as knowledge base content
        doc = await DocumentService(db).upload(
            user_id,
            filename_raw,
            file.content_type or "application/octet-stream",
            raw,
            is_knowledge_base=True,
        )

        return DocumentOut(**doc.model_dump())
    
    except HTTPException:
        raise
    except Exception as e:
        import structlog
        log = structlog.get_logger("document_api")
        log.exception("document.knowledge_base_upload.failed", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge base upload failed: {str(e)[:100]}"
        )


@router.get("/knowledge-base/info", response_model=Dict[str, Any])
async def get_knowledge_base_info(
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Get information about the knowledge base."""
    from app.services.ai.knowledge_search import KnowledgeSearchService
    service = KnowledgeSearchService(db)
    return service.get_knowledge_base_summary()


@router.get("/knowledge-base/list", response_model=List[DocumentOut])
def list_knowledge_base_docs(
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """List all knowledge base documents."""
    from app.models.document import Document
    docs = db.exec(
        select(Document).where(col(Document.is_knowledge_base) == True)
    ).all()
    return [DocumentOut(**d.model_dump()) for d in docs]


@router.get("/", response_model=List[DocumentOut])
def list_docs(db: Session = Depends(db_session), user: User = Depends(current_user)):
    if user.id is None:
        raise HTTPException(status_code=401, detail="User ID not found")
    user_id = cast(int, user.id)
    docs = DocumentService(db).list_for_user(user_id)
    return [DocumentOut(**d.model_dump()) for d in docs]


@router.get("/search", response_model=List[DocumentOut])
def search_docs(
    q: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Search documents by filename"""
    if user.id is None:
        raise HTTPException(status_code=401, detail="User ID not found")
    user_id = cast(int, user.id)
    from app.repositories.document_repo import DocumentRepo
    docs = DocumentRepo(db).search_for_user(user_id, q)
    return [DocumentOut(**d.model_dump()) for d in docs]


@router.get("/rag-search", response_model=List[dict])
async def rag_search_docs(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    k: int = Query(5, ge=1, le=100, description="Number of results"),
    skip: int = Query(0, ge=0, description="Result offset for pagination"),
    status: Optional[str] = Query(None, description="Optional document status filter"),
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """
    Search document contents using semantic/RAG-based search.
    Returns matching chunks with their document info.
    """
    try:
        if user.id is None:
            raise HTTPException(status_code=401, detail="User ID not found")
        user_id = cast(int, user.id)
        from app.rag.retriever import retrieve
        
        # Build filters for retriever (document-level filters can be passed)
        retriever_filters = None
        if status:
            # ensure we only return chunks from documents with given status
            retriever_filters = {"status": status}

        results = await retrieve(
            user_id=user_id,
            query=q,
            k=max(k + skip, k),
            filters=retriever_filters,
            db=db,
        )
        
        # Enhance results with document metadata
        enhanced_results = []
        for result in results:
            doc_id = result.get("document_id")
            if doc_id:
                from app.repositories.document_repo import DocumentRepo
                doc = DocumentRepo(db).get(doc_id)
                if doc and doc.user_id == user_id:
                    enhanced_results.append({
                        "chunk_text": result.get("text", ""),
                        "chunk_index": result.get("chunk_index", 0),
                        "document_id": doc_id,
                        "filename": doc.filename,
                        "similarity_score": result.get("distance", 0),
                    })
        # If no semantic results found, fall back to a simple DB text search over chunks
        if not enhanced_results:
            try:
                from app.models.document import DocumentChunk, Document
                from sqlmodel import select, and_

                q_like = f"%{q}%"
                rows = db.exec(
                    select(DocumentChunk, Document)
                    .where(
                        and_(
                            col(Document.id) == col(DocumentChunk.document_id),
                            col(Document.user_id) == user_id,
                            col(DocumentChunk.text).ilike(q_like),
                        )
                    )
                    .limit(k)
                ).all()

                fallback = []
                for chunk, doc in rows:
                    fallback.append({
                        "chunk_text": chunk.text,
                        "chunk_index": chunk.chunk_index,
                        "document_id": doc.id,
                        "filename": doc.filename,
                        "similarity_score": 0.25,
                    })

                return fallback
            except Exception:
                # If DB fallback fails, just return empty list
                return []

        # Apply pagination (skip/limit)
        paged = enhanced_results[skip:skip + k]
        return paged
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/filter", response_model=List[DocumentOut])
def filter_docs(
    status: str = Query("indexed", description="Filter by status: indexed, failed, pending"),
    db: Session = Depends(db_session),
    user: User = Depends(current_user)
):
    """Filter documents by status"""
    if user.id is None:
        raise HTTPException(status_code=401, detail="User ID not found")
    user_id = cast(int, user.id)
    from app.repositories.document_repo import DocumentRepo
    docs = DocumentRepo(db).get_by_status(user_id, status)
    return [DocumentOut(**d.model_dump()) for d in docs]


@router.delete("/{doc_id}")
def delete_doc(doc_id: int, db: Session = Depends(db_session), user: User = Depends(current_user)):
    """Delete document - users can delete their own documents"""
    try:
        if user.id is None:
            raise HTTPException(status_code=401, detail="User ID not found")
        user_id = cast(int, user.id)
        DocumentService(db).delete(user_id, doc_id)
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(db_session), user: User = Depends(current_user)):
    """Get document by ID"""
    if user.id is None:
        raise HTTPException(status_code=401, detail="User ID not found")
    from app.repositories.document_repo import DocumentRepo
    doc = DocumentRepo(db).get(doc_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut(**doc.model_dump())


@router.post("/upload_job")
async def upload_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Upload a document and enqueue background ingestion job."""
    try:
        if user.id is None:
            raise HTTPException(status_code=401, detail="User ID not found")
        user_id = cast(int, user.id)

        filename_raw = cast(str, file.filename or "")
        valid_name, safe_filename, name_error = sanitize_filename(filename_raw)
        if not valid_name:
            raise HTTPException(status_code=400, detail=name_error)

        filename = safe_filename.lower()
        if not _allowed_file(filename, file.content_type or ""):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Allowed: PDF, TXT, MD, DOCX, PPTX, HTML, CSV, XLSX",
            )

        raw = await file.read()
        max_size_bytes = 10 * 1024 * 1024
        if len(raw) > max_size_bytes:
            raise HTTPException(status_code=413, detail=f"File too large. Max size is 10MB")
        if len(raw) == 0:
            raise HTTPException(status_code=400, detail="File is empty")

        job = BackgroundJobService(db).create_job(user_id, "ingest_document")

        # Check for active RQ workers on the queue
        use_rq = False
        try:
            from rq import Worker
            from app.workers.queue import redis_conn
            workers = Worker.all(connection=redis_conn)
            active_workers = [w for w in workers if "omniagent" in w.queue_names()]
            if active_workers:
                use_rq = True
        except Exception:
            use_rq = False

        if use_rq:
            # Enqueue to RQ
            try:
                rq_job = default_queue.enqueue(
                    "app.workers.jobs.ingest_document",
                    user_id,
                    filename_raw,
                    file.content_type or "application/octet-stream",
                    raw,
                    cast(int, job.id),
                )
                if rq_job and hasattr(rq_job, "id"):
                    job.task_id = getattr(rq_job, "id")
                    db.add(job)
                    db.commit()
                    db.refresh(job)
            except Exception as e:
                BackgroundJobService(db).update_status(job.id, "failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Failed to enqueue ingestion job: {str(e)}")
        else:
            # Fallback to local background tasks
            from app.workers.jobs import ingest_document
            background_tasks.add_task(
                ingest_document,
                user_id,
                filename_raw,
                file.content_type or "application/octet-stream",
                raw,
                cast(int, job.id),
            )
            job.task_id = f"local-task-{job.id}"
            db.add(job)
            db.commit()
            db.refresh(job)

        return {"job_id": job.id, "task_id": job.task_id, "status": job.status}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload job failed: {str(e)}")


@router.post("/qa", response_model=ChatResponse)
async def document_qa(
    request: DocumentQARequest,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Ask questions against indexed documents."""
    try:
        if user.id is None:
            raise HTTPException(status_code=401, detail="User ID not found")
        user_id = cast(int, user.id)

        if request.document_id:
            doc = DocumentRepo(db).get(request.document_id)
            if not doc or doc.user_id != user_id:
                raise HTTPException(status_code=404, detail="Document not found")

        app_metrics.CHAT_REQUESTS.labels(endpoint="document_qa").inc()
        start_time = time.time()

        filters = {"document_id": request.document_id} if request.document_id else None
        ctx = await retrieve(
            user_id=user_id,
            query=request.question,
            k=request.k,
            filters=filters,
            db=db,
        )

        if not ctx:
            return ChatResponse(
                conversation_id=0,
                message_id=0,
                content="I could not find a relevant answer in your indexed documents.",
                sources=[],
                trace=[],
            )

        context_text = "\n\n".join([f"[doc:{c.get('document_id')}#{c.get('chunk_index')}] {(c.get('text') or '')[:500]}" for c in ctx if c is not None])
        prompt = (
            f"You are a document assistant. Use only the information below to answer the question. "
            f"If the documents do not contain the answer, say 'I don't know'.\n\n"
            f"Question: {request.question}\n\n"
            f"Context:\n{context_text}\n\n"
            f"Answer concisely and cite document chunks when possible."
        )

        answer = await ollama.generate(
            prompt=prompt,
            model="phi3:mini",
            system=RESEARCH_SYSTEM,
        )

        app_metrics.CHAT_LATENCY.labels(endpoint="document_qa").observe(time.time() - start_time)

        sources = [
            Citation(
                document_id=int(c.get("document_id") or 0),
                chunk_index=int(c.get("chunk_index") or 0),
                snippet=(c.get("text") or "")[:240],
            )
            for c in ctx
            if c is not None and c.get("document_id") is not None
        ]

        return ChatResponse(
            conversation_id=0,
            message_id=0,
            content=answer,
            sources=sources,
            trace=[],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document QA failed: {str(e)}")


@router.post("/upload_and_qa", response_model=ChatResponse)
async def upload_and_qa(
    question: str = Query(..., min_length=1, max_length=1000, description="Question about the uploaded document"),
    file: UploadFile = File(...),
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Upload a document, index it, then run a quick RAG Q&A and return an answer."""
    # Reuse existing upload flow to index the document
    try:
        if user.id is None:
            raise HTTPException(status_code=401, detail="User ID not found")
        user_id = cast(int, user.id)

        filename_raw = cast(str, file.filename or "unknown")

        # Perform upload (this will index into vector DB)
        doc = await DocumentService(db).upload(user_id, filename_raw, file.content_type or "application/octet-stream", await file.read())

        # Wait a short moment to ensure vector DB has the new vectors (ingest is synchronous here)
        await asyncio.sleep(0.2)

        # Retrieve top-k chunks for the question from this user's docs
        ctx = await retrieve(
            user_id=user_id,
            query=question,
            k=6,
            db=db,
        )

        context_text = ""
        if ctx:
            context_text = "\n\n".join([f"[doc:{c.get('document_id')}#{c.get('chunk_index')}] {(c.get('text') or '')[:500]}" for c in ctx if c is not None])
        else:
            context_text = "(no relevant documents found)"

        prompt = f"User question: {question}\n\nDocument context:\n{context_text}\n\nProvide a concise, direct answer based on the documents above. If the documents do not contain the answer, say so clearly."

        answer = await ollama.generate(prompt=prompt, model="phi3:mini", system=RESEARCH_SYSTEM)

        sources = [
            Citation(document_id=int(c.get("document_id") or 0), chunk_index=int(c.get("chunk_index") or 0), snippet=(c.get("text") or "")[:240])
            for c in ctx if c is not None and c.get("document_id") is not None
        ]

        return ChatResponse(conversation_id=0, message_id=0, content=answer, sources=sources, trace=[])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload and Q&A failed: {str(e)}")