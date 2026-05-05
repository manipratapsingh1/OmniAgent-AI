# backend/app/agents/state.py
"""
Agent State Management with Memory Integration
"""
from typing import Annotated, List, TypedDict, Optional, Any
import operator
from pydantic import BaseModel
from datetime import datetime


class StepResult(BaseModel):
    step: str
    output: str
    score: float  # 0.0 - 1.0 quality gate
    feedback: str
    timestamp: Optional[datetime] = None


class AgentState(TypedDict):
    """State object passed through all agent nodes"""
    objective: str
    plan: List[str]
    step_results: Annotated[List[StepResult], operator.add]  # Append-only audit trail
    current_step_idx: int
    status: str
    memory_context: Optional[str]  # Retrieved from long-term memory
    conversation_id: Optional[str]
    user_id: Optional[str]
    meta_data: Optional[dict]