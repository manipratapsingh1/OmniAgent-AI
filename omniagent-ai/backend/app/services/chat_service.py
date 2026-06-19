import json
import structlog
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.agent_run import AgentRun
from app.repositories.conversation_repo import ConversationRepo
from app.schemas.chat import ChatRequest, ChatResponse, Citation, AgentTrace
from app.agents.graph import GRAPH
from app.agents.state import AgentState
from app.memory.short_term import append as mem_append

log = structlog.get_logger("chat")


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ConversationRepo(db)

    def _ensure_conversation(self, user_id: int, conv_id: Optional[int], model: Optional[str]) -> Conversation:
        if conv_id and conv_id > 0:
            conv = self.repo.get(conv_id)
            if not conv or conv.user_id != user_id:
                log.warning("chat.conversation_access_denied", user_id=user_id, conv_id=conv_id)
                raise ValueError("Conversation not found")
            return conv
        conv = Conversation(user_id=user_id, model=model or "llama3.2")
        saved_conv = self.repo.add(conv)
        log.info("chat.conversation_created", user_id=user_id, conv_id=saved_conv.id)
        return saved_conv

    async def chat(self, user_id: int, req: ChatRequest) -> ChatResponse:
        conv = self._ensure_conversation(user_id, req.conversation_id, req.model)
        log.info("chat.start", user_id=user_id, conv_id=conv.id, message_len=len(req.message))

        user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)
        await mem_append(conv.id, "user", req.message)

        state = AgentState(
            user_id=user_id, conversation_id=conv.id, query=req.message,
            model=req.model or conv.model, use_rag=req.use_rag,
        )
        result = await GRAPH.ainvoke(state)
        # langgraph may return dict-like; coerce back
        final_state = AgentState.model_validate(result) if not isinstance(result, AgentState) else result

        answer = final_state.final or final_state.tool_result or "I couldn't generate a response."
        sources = [
            Citation(document_id=c["document_id"], chunk_index=c["chunk_index"], snippet=c["text"][:240])
            for c in final_state.context if c.get("document_id") is not None
        ]

        assistant_msg = Message(
            conversation_id=conv.id, role="assistant", content=answer, agent="graph",
            sources=json.dumps([s.model_dump() for s in sources]),
        )
        self.db.add(assistant_msg)

        for t in final_state.trace:
            self.db.add(AgentRun(
                conversation_id=conv.id, agent=t.agent, input=t.input[:4000],
                output=t.output[:4000], latency_ms=t.latency_ms,
            ))

        conv.updated_at = datetime.now(timezone.utc)
        if conv.title == "New Conversation":
            conv.title = (req.message[:48] + ("…" if len(req.message) > 48 else ""))
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(assistant_msg)

        await mem_append(conv.id, "assistant", answer)

        log.info("chat.complete", user_id=user_id, conv_id=conv.id, sources_count=len(sources))

        return ChatResponse(
            conversation_id=conv.id,
            message_id=assistant_msg.id,
            content=answer,
            sources=sources,
            trace=[AgentTrace(**t.model_dump()) for t in final_state.trace],
        )