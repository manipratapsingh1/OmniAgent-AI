import asyncio
import structlog
from typing import List, Optional
from sqlmodel import Session, select
from app.models.knowledge import KnowledgeRelationship, StudyMaterial
from app.llm.ollama_client import ollama
from app.config import get_settings

log = structlog.get_logger("knowledge_service")
settings = get_settings()

class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db

    def add_relationship(self, user_id: int, source: str, relation: str, target: str, source_type: str = "doc", target_type: str = "topic"):
        """Add a semantic link in the knowledge graph."""
        rel = KnowledgeRelationship(
            user_id=user_id,
            source_id=source,
            source_type=source_type,
            relation=relation,
            target_id=target,
            target_type=target_type
        )
        self.db.add(rel)
        self.db.commit()
        log.info("knowledge.graph.relation_added", source=source, relation=relation, target=target)
        return rel

    async def generate_study_material(self, user_id: int, document_id: int, text: str):
        """AI Second Brain: Extract flashcards and quizzes from document text."""
        prompt = f"""Analyze the following text and generate:
1. 3 Flashcards (Question/Answer)
2. 2 Quiz questions (Multiple choice)
3. 2 Action items or key takeaways.

Format as JSON:
{{
  "flashcards": [{{ "q": "...", "a": "..." }}],
  "quizzes": [{{ "q": "...", "options": ["...", "..."], "a": "..." }}],
  "actions": ["...", "..."]
}}

Text: {text[:4000]}"""

        try:
            resp = await ollama.generate(
                prompt=prompt,
                model=settings.OLLAMA_FAST_MODEL,
                system="You are an educational assistant. Return ONLY valid JSON."
            )
            
            # Basic JSON extraction (naive)
            import json
            import re
            json_match = re.search(r'\{.*\}', resp, re.DOTALL)
            if not json_match:
                return []
            
            data = json.loads(json_match.group())
            materials = []
            
            # Store Flashcards
            for fc in data.get("flashcards", []):
                materials.append(StudyMaterial(user_id=user_id, document_id=document_id, material_type="flashcard", content=fc))
            
            # Store Quizzes
            for q in data.get("quizzes", []):
                materials.append(StudyMaterial(user_id=user_id, document_id=document_id, material_type="quiz", content=q))
                
            # Store Actions
            for a in data.get("actions", []):
                materials.append(StudyMaterial(user_id=user_id, document_id=document_id, material_type="action_item", content={"task": a}))
            
            for m in materials:
                self.db.add(m)
            self.db.commit()
            
            log.info("knowledge.brain.materials_generated", doc_id=document_id, count=len(materials))
            return materials
            
        except Exception as e:
            log.error("knowledge.brain.generation_failed", error=str(e))
            return []

    async def run_workflow(self, user_id: int, document_id: int, text: str):
        """Stage 11: Workflow Automation (Summarize -> Notes -> Quiz)."""
        log.info("workflow.start", doc_id=document_id)
        
        # 1. Generate Summary (already exists in background jobs, but let's formalize)
        # 2. Generate Study Materials (Second Brain)
        await self.generate_study_material(user_id, document_id, text)
        
        # 3. Add to Knowledge Graph
        # Extract topics first
        topic_prompt = f"Extract 3 main topics from this text as a comma-separated list: {text[:1000]}"
        topics_resp = await ollama.generate(prompt=topic_prompt, model=settings.OLLAMA_FAST_MODEL)
        topics = [t.strip() for t in topics_resp.split(",")]
        
        for topic in topics:
            self.add_relationship(user_id, f"doc:{document_id}", "discusses", topic, "document", "topic")
            
        log.info("workflow.completed", doc_id=document_id)
