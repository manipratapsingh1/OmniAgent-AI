"""Tagging and categorization service for documents."""

from typing import List, Dict, Any, Optional
import structlog
from sqlmodel import Session, select

from app.models.document_tags import DocumentTag, DocumentCategory

log = structlog.get_logger("tagging_service")


class TaggingService:
    """Manage document tags and categories."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def add_tags(
        self,
        document_id: int,
        tags: List[str],
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add tags to a document."""
        try:
            added_tags = []
            for tag in tags:
                doc_tag = DocumentTag(
                    document_id=document_id,
                    tag=tag.lower(),
                    category=category,
                )
                self.db.add(doc_tag)
                added_tags.append(tag)
            
            self.db.commit()
            log.info("tagging.added", document_id=document_id, tag_count=len(tags))
            
            return {
                "status": "success",
                "document_id": document_id,
                "tags_added": added_tags,
            }
        except Exception as e:
            log.error("tagging.add_failed", error=str(e))
            raise
    
    async def get_document_tags(self, document_id: int) -> List[str]:
        """Get all tags for a document."""
        try:
            tags = self.db.exec(
                select(DocumentTag).where(DocumentTag.document_id == document_id)
            ).all()
            
            return [t.tag for t in tags]
        except Exception as e:
            log.error("tagging.get_failed", error=str(e))
            return []
    
    async def search_by_tag(self, tag: str, document_ids: Optional[List[int]] = None) -> List[int]:
        """Find documents with a specific tag."""
        try:
            query = select(DocumentTag).where(DocumentTag.tag == tag.lower())
            
            if document_ids:
                query = query.where(DocumentTag.document_id.in_(document_ids))
            
            results = self.db.exec(query).all()
            
            return list(set([t.document_id for t in results]))
        except Exception as e:
            log.error("tagging.search_failed", error=str(e))
            return []
    
    async def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a document category."""
        try:
            category = DocumentCategory(
                name=name,
                description=description,
                color=color,
                icon=icon,
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
            
            log.info("tagging.category_created", name=name)
            
            return {
                "id": category.id,
                "name": category.name,
                "status": "created",
            }
        except Exception as e:
            log.error("tagging.category_failed", error=str(e))
            raise
    
    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all document categories."""
        try:
            categories = self.db.exec(select(DocumentCategory)).all()
            
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "color": c.color,
                    "icon": c.icon,
                }
                for c in categories
            ]
        except Exception as e:
            log.error("tagging.get_categories_failed", error=str(e))
            return []
    
    async def remove_tag(self, document_id: int, tag: str) -> Dict[str, Any]:
        """Remove a tag from a document."""
        try:
            tag_obj = self.db.exec(
                select(DocumentTag).where(
                    (DocumentTag.document_id == document_id) &
                    (DocumentTag.tag == tag.lower())
                )
            ).first()
            
            if tag_obj:
                self.db.delete(tag_obj)
                self.db.commit()
                log.info("tagging.removed", document_id=document_id, tag=tag)
            
            return {
                "status": "success",
                "message": "Tag removed" if tag_obj else "Tag not found",
            }
        except Exception as e:
            log.error("tagging.remove_failed", error=str(e))
            raise
