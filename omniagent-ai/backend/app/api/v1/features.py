"""API endpoints for enhanced Knowledge Platform features."""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import List, Optional
import structlog
import json

from app.deps import db_session, current_user, require_admin
from app.models.user import User
from app.models.message import Message
from app.services.feedback_service import ResponseFeedbackService
from app.services.export_service import ExportService
from app.services.tagging_service import TaggingService
from app.services.sharing_faq_service import SharingAndFAQService
from app.services.summarization_service import DocumentSummarizationService
from app.services.analytics_service import AnalyticsService

router = APIRouter()
log = structlog.get_logger("features_api")


# ==================== FEEDBACK ENDPOINTS ====================

class FeatureFeedbackRequest(BaseModel):
    response_id: int
    helpful: Optional[bool] = None
    rating_scale: Optional[int] = None


@router.post("/feedback/submit")
async def submit_feedback(
    req: FeatureFeedbackRequest,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Submit feedback on an AI response."""
    try:
        service = ResponseFeedbackService(db)
        success = service.add_feedback(
            req.response_id,
            user.id,
            helpful=req.helpful,
            rating=req.rating_scale,
        )
        if not success:
            raise HTTPException(status_code=404, detail="Response not found")
        return {"status": "feedback recorded"}
    except HTTPException:
        raise
    except Exception as e:
        log.error("feedback.submit_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/feedback/summary")
async def get_feedback_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """Get feedback summary (admin only)."""
    try:
        service = ResponseFeedbackService(db)
        return await service.get_feedback_summary(days=days)
    except Exception as e:
        log.error("feedback.summary_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/feedback/impact")
async def get_feedback_impact(
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """Get document feedback impact analysis (admin only)."""
    try:
        service = ResponseFeedbackService(db)
        return await service.get_document_feedback_impact()
    except Exception as e:
        log.error("feedback.impact_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ==================== EXPORT ENDPOINTS ====================

@router.get("/export/conversation/{conversation_id}")
async def export_conversation(
    conversation_id: int,
    format: str = Query("markdown", pattern="^(markdown|json|csv)$"),
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Export a conversation in specified format."""
    try:
        messages = db.exec(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        ).all()

        if not messages:
            raise HTTPException(status_code=404, detail="Conversation not found or has no messages")

        parsed_messages = []
        for msg in messages:
            sources = []
            if msg.sources:
                try:
                    sources = json.loads(msg.sources)
                except Exception:
                    sources = []

            parsed_messages.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "sources": sources,
            })

        if format == "markdown":
            content = ExportService.export_conversation_to_markdown(parsed_messages)
            return {
                "format": "markdown",
                "content": content,
                "filename": f"conversation_{conversation_id}.md"
            }
        elif format == "json":
            content = ExportService.export_conversation_to_json(parsed_messages)
            return {
                "format": "json",
                "content": content,
                "filename": f"conversation_{conversation_id}.json"
            }
        elif format == "csv":
            content = ExportService.export_conversation_to_csv(parsed_messages)
            return {
                "format": "csv",
                "content": content,
                "filename": f"conversation_{conversation_id}.csv"
            }
    except HTTPException:
        raise
    except Exception as e:
        log.error("export.failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ==================== TAGGING ENDPOINTS ====================

@router.post("/document/{document_id}/tags")
async def add_document_tags(
    document_id: int,
    tags: List[str],
    category: Optional[str] = None,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """Add tags to a document (admin only)."""
    try:
        service = TaggingService(db)
        return await service.add_tags(document_id, tags, category)
    except Exception as e:
        log.error("tagging.add_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/document/{document_id}/tags")
async def get_document_tags(
    document_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Get tags for a document."""
    try:
        service = TaggingService(db)
        tags = await service.get_document_tags(document_id)
        return {"document_id": document_id, "tags": tags}
    except Exception as e:
        log.error("tagging.get_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/document/{document_id}/tags/{tag}")
async def remove_document_tag(
    document_id: int,
    tag: str,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """Remove a tag from a document (admin only)."""
    try:
        service = TaggingService(db)
        return await service.remove_tag(document_id, tag)
    except Exception as e:
        log.error("tagging.remove_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tags/search")
async def search_by_tag(
    tag: str,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Search documents by tag."""
    try:
        service = TaggingService(db)
        document_ids = await service.search_by_tag(tag)
        return {"tag": tag, "document_ids": document_ids, "count": len(document_ids)}
    except Exception as e:
        log.error("tagging.search_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/categories")
async def create_category(
    name: str,
    description: Optional[str] = None,
    color: Optional[str] = None,
    icon: Optional[str] = None,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """Create a document category (admin only)."""
    try:
        service = TaggingService(db)
        return await service.create_category(name, description, color, icon)
    except Exception as e:
        log.error("category.create_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories")
async def get_categories(
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Get all document categories."""
    try:
        service = TaggingService(db)
        categories = await service.get_all_categories()
        return {"categories": categories, "count": len(categories)}
    except Exception as e:
        log.error("category.get_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ==================== SHARING ENDPOINTS ====================

@router.post("/conversation/{conversation_id}/share")
async def create_conversation_share(
    conversation_id: int,
    shared_with_user_id: Optional[int] = None,
    expires_in_hours: Optional[int] = None,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Create a shareable link for a conversation."""
    try:
        service = SharingAndFAQService(db)
        return await service.create_share(
            conversation_id,
            user.id,
            shared_with_user_id,
            expires_in_hours,
        )
    except Exception as e:
        log.error("sharing.create_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/shared/{share_token}")
async def access_shared_conversation(
    share_token: str,
    db: Session = Depends(db_session),
):
    """Access a shared conversation (no auth required)."""
    try:
        service = SharingAndFAQService(db)
        result = await service.access_shared_conversation(share_token)
        if not result:
            raise HTTPException(status_code=404, detail="Share not found or expired")
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error("sharing.access_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ==================== FAQ ENDPOINTS ====================

@router.post("/document/{document_id}/faq")
async def add_faq(
    document_id: int,
    question: str,
    answer: str,
    relevance_score: float = 0.8,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """Add FAQ entry to a document (admin only)."""
    try:
        service = SharingAndFAQService(db)
        return await service.add_faq(document_id, question, answer, relevance_score)
    except Exception as e:
        log.error("faq.add_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/document/{document_id}/faqs")
async def get_document_faqs(
    document_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Get FAQs for a document."""
    try:
        service = SharingAndFAQService(db)
        faqs = await service.get_document_faqs(document_id)
        return {"document_id": document_id, "faqs": faqs, "count": len(faqs)}
    except Exception as e:
        log.error("faq.get_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ==================== QUERY TEMPLATES ENDPOINTS ====================

@router.post("/templates")
async def create_template(
    title: str,
    template: str,
    category: str,
    icon: Optional[str] = None,
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """Create a query template (admin only)."""
    try:
        service = SharingAndFAQService(db)
        return await service.create_query_template(title, template, category, icon)
    except Exception as e:
        log.error("template.create_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates")
async def get_templates(
    category: Optional[str] = None,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Get query templates, optionally filtered by category."""
    try:
        service = SharingAndFAQService(db)
        
        if category:
            templates = await service.get_templates_by_category(category)
            return {"category": category, "templates": templates, "count": len(templates)}
        
        # Return empty if no category specified
        return {"templates": [], "count": 0}
    except Exception as e:
        log.error("template.get_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ==================== SUMMARIZATION ENDPOINTS ====================

@router.post("/document/{document_id}/summarize")
async def summarize_document(
    document_id: int,
    document_text: str,
    model: str = "llama3.2",
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """Generate summary for a document (admin only)."""
    try:
        service = DocumentSummarizationService(db)
        return await service.generate_summary(document_id, document_text, model)
    except Exception as e:
        log.error("summarization.failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/document/{document_id}/summary")
async def get_document_summary(
    document_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    """Get stored summary for a document."""
    try:
        service = DocumentSummarizationService(db)
        summary = await service.get_summary(document_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        log.error("summarization.get_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/analytics/knowledge-base")
async def get_knowledge_base_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """Get knowledge base analytics (admin only)."""
    try:
        service = AnalyticsService(db)
        
        # Get KB documents for extended analytics
        from app.models.document import Document
        from sqlmodel import select
        
        kb_docs = db.exec(
            select(Document).where(Document.is_knowledge_base == True)
        ).all()
        
        return {
            "period_days": days,
            "documents": {
                "total": len(kb_docs),
                "indexed": sum(1 for d in kb_docs if d.status == "indexed"),
                "failed": sum(1 for d in kb_docs if d.status == "failed"),
                "pending": sum(1 for d in kb_docs if d.status == "pending"),
                "total_chunks": sum(d.chunk_count for d in kb_docs),
                "total_size_gb": round(sum(d.size_bytes for d in kb_docs) / (1024**3), 2),
            },
            "top_documents": [
                {
                    "filename": d.filename,
                    "chunks": d.chunk_count,
                    "size_mb": round(d.size_bytes / (1024**2), 2),
                    "status": d.status,
                }
                for d in sorted(kb_docs, key=lambda d: d.chunk_count, reverse=True)[:5]
            ],
        }
    except Exception as e:
        log.error("analytics.failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/usage")
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """Get platform usage analytics (admin only)."""
    try:
        service = AnalyticsService(db)
        overview = service.overview()
        
        return {
            "period_days": days,
            "statistics": overview,
        }
    except Exception as e:
        log.error("analytics.usage_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/tag-usage")
async def get_tag_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(db_session),
    user: User = Depends(require_admin),
):
    """Get document tag analytics (admin only)."""
    try:
        service = AnalyticsService(db)
        return {
            "period_days": days,
            "tag_usage": service.get_tag_usage_analytics(days=days),
        }
    except Exception as e:
        log.error("analytics.tag_usage_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
