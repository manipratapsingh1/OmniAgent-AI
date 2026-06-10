"""Document summarization service."""

from typing import Dict, Any, Optional, List
import structlog
import json
from sqlmodel import Session, select

from app.models.document_versions import DocumentSummary
from app.services.ai.provider import get_provider

log = structlog.get_logger("summarization_service")


class DocumentSummarizationService:
    """Generate and manage document summaries."""
    
    def __init__(self, db: Session, provider: str = "ollama"):
        self.db = db
        self.llm = get_provider(provider)
    
    async def generate_summary(
        self,
        document_id: int,
        document_text: str,
        model: str = "llama3.2",
    ) -> Dict[str, Any]:
        """Generate a summary for a document."""
        try:
            # Create prompt for summarization
            prompt = f"""Please provide a concise summary of this document and extract 3-5 key points.

Document:
{document_text[:5000]}  # Limit to first 5000 chars for efficiency

Provide response in JSON format:
{{
  "summary": "Brief 2-3 sentence summary",
  "key_points": ["point 1", "point 2", "point 3"]
}}
"""
            
            system_prompt = "You are an expert document analyst. Summarize documents concisely and extract key points."
            
            # Generate summary using LLM
            response = await self.llm.generate(
                prompt=prompt,
                system=system_prompt,
                model=model
            )
            
            # Parse response
            summary_data = self._parse_summary_response(response)
            
            # Store in database
            doc_summary = DocumentSummary(
                document_id=document_id,
                summary=summary_data.get("summary", ""),
                key_points=json.dumps(summary_data.get("key_points", [])),
            )
            
            self.db.add(doc_summary)
            self.db.commit()
            self.db.refresh(doc_summary)
            
            log.info("summarization.generated", document_id=document_id)
            
            return {
                "document_id": document_id,
                "summary": summary_data.get("summary"),
                "key_points": summary_data.get("key_points", []),
                "status": "generated",
            }
        except Exception as e:
            log.error("summarization.failed", error=str(e))
            raise
    
    @staticmethod
    def _parse_summary_response(response: str) -> Dict[str, Any]:
        """Parse LLM response to extract summary and key points."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback: extract text manually
        lines = response.split('\n')
        summary = '\n'.join(lines[:2]) if lines else ""
        key_points = [
            line.strip().lstrip('- ').lstrip('* ')
            for line in lines[3:] if line.strip()
        ][:5]
        
        return {
            "summary": summary,
            "key_points": key_points,
        }
    
    async def get_summary(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get stored summary for a document."""
        try:
            summary = self.db.exec(
                select(DocumentSummary).where(DocumentSummary.document_id == document_id)
            ).first()
            
            if not summary:
                return None
            
            return {
                "document_id": summary.document_id,
                "summary": summary.summary,
                "key_points": json.loads(summary.key_points),
                "generated_at": summary.generated_at.isoformat(),
            }
        except Exception as e:
            log.error("summarization.get_failed", error=str(e))
            return None
