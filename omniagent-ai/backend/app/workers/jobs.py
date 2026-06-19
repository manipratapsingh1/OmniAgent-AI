"""Defines background jobs. Wire to actual ingestion/summarization flows as needed."""
def reindex_user(user_id: int) -> str:
    # Placeholder: real implementation would walk user's documents and refresh embeddings.
    return f"reindex queued for user {user_id}"


def ingest_document(user_id: int, filename: str, content_type: str, raw_bytes: bytes, job_id: int = None) -> dict:
    """Background worker entrypoint to ingest a single uploaded document.

    This is designed to be called by RQ workers. It creates its own DB session
    and uses the DocumentService.upload wrapper to perform ingestion.
    """
    try:
        # Lazy import to avoid heavy dependencies at module import time
        from app.db.session import get_session
        from app.services.document_service import DocumentService
        from app.services.background_job_service import BackgroundJobService
        import asyncio

        db = get_session()
        db.expire_on_commit = False

        # Mark job as processing if job_id provided
        if job_id:
            BackgroundJobService(db).update_status(job_id, "processing", progress=0)

        # DocumentService.upload is async — run it in an event loop
        # Pass job_id so upload can report progress to BackgroundJobService
        result_doc = asyncio.run(DocumentService(db).upload(user_id, filename, content_type, raw_bytes, job_id=job_id, await_workflow=True))

        # Mark job completed
        if job_id:
            BackgroundJobService(db).update_status(job_id, "completed", progress=100, result=str(result_doc.id))

        db.close()
        return {"status": "ok", "doc_id": getattr(result_doc, "id", None)}
    except Exception as e:
        try:
            # attempt to update job to failed
            from app.db.session import get_session
            from app.services.background_job_service import BackgroundJobService
            db = get_session()
            if job_id:
                BackgroundJobService(db).update_status(job_id, "failed", error=str(e))
            db.close()
        except Exception:
            pass
        return {"status": "error", "error": str(e)}