from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class TraceEntry(BaseModel):
    agent: str
    input: str
    output: str
    latency_ms: int = 0


class AgentState(BaseModel):
    user_id: int
    conversation_id: int
    query: str
    model: Optional[str] = None
    use_rag: bool = True

    plan: Optional[str] = None
    context: List[Dict[str, Any]] = []  # list of {document_id, chunk_index, text}
    draft: Optional[str] = None
    final: Optional[str] = None
    tool_result: Optional[str] = None
    route: List[str] = []
    trace: List[TraceEntry] = []