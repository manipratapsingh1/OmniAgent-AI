# backend/app/agents/nodes.py
"""
Multi-Agent Intelligence: Planner → Executor → Verifier
"""
from typing import Any, Dict
from .state import AgentState, StepResult

from langchain.prompts import PromptTemplate
import json
from langchain_community.chat_models import ChatOllama

llm = ChatOllama(
    model="llama3",
    temperature=0.7
)

# ============= PLANNER AGENT =============
def planner(state: AgentState) -> AgentState:
    """
    Planner Agent: Breaks down complex problems into steps
    """
    plan_prompt = PromptTemplate(
        template="""You are a strategic planner. Analyze this objective and break it into clear, sequential steps.
        
Objective: {objective}

Previous Results: {previous_results}

Create a JSON array of steps (max 5-7 steps). Each step should be:
- Clear and actionable
- Dependent on previous steps if needed
- Measurable

Return ONLY valid JSON in this format:
{{"steps": ["step 1", "step 2", ...]}}""",
        input_variables=["objective", "previous_results"]
    )
    
    previous_results = json.dumps([r.dict() for r in state.get("step_results", [])])
    
    response = llm.invoke(plan_prompt.format(
        objective=state["objective"],
        previous_results=previous_results
    ))
    
    try:
        plan_data = json.loads(response.content)
        plan = plan_data.get("steps", [])
    except json.JSONDecodeError:
        plan = [state["objective"]]
    
    state["plan"] = plan
    state["current_step_idx"] = 0
    state["status"] = "planning_complete"
    
    return state


# ============= EXECUTOR AGENT =============
def executor(state: AgentState) -> AgentState:
    """
    Executor Agent: Executes the current step in the plan
    """
    if not state.get("plan"):
        state["plan"] = [state["objective"]]
    
    current_step_idx = state.get("current_step_idx", 0)
    
    if current_step_idx >= len(state["plan"]):
        state["status"] = "execution_complete"
        return state
    
    current_step = state["plan"][current_step_idx]
    
    executor_prompt = PromptTemplate(
        template="""Execute this specific step thoroughly and provide a detailed output.

Step: {step}
Objective Context: {objective}
Previous Steps Results: {previous_results}

Provide a comprehensive solution/output for this step.""",
        input_variables=["step", "objective", "previous_results"]
    )
    
    previous_results = json.dumps([r.dict() for r in state.get("step_results", [])])
    
    response = llm.invoke(executor_prompt.format(
        step=current_step,
        objective=state["objective"],
        previous_results=previous_results
    ))
    
    output = response.content
    
    step_result = StepResult(
        step=current_step,
        output=output,
        score=0.8,  # Default, will be verified
        feedback=""
    )
    
    # Append to audit trail
    if "step_results" not in state:
        state["step_results"] = []
    state["step_results"].append(step_result)
    state["current_step_idx"] = current_step_idx + 1
    state["status"] = "executing"
    
    return state


# ============= VERIFIER AGENT =============
def verifier(state: AgentState) -> AgentState:
    """
    Verifier Agent: Checks output quality (0.0-1.0 score)
    Triggers retry if score < 0.85
    """
    if not state.get("step_results"):
        state["status"] = "verification_failed"
        return state
    
    last_result = state["step_results"][-1]
    
    verify_prompt = PromptTemplate(
        template="""Rate the quality of this step's output on a scale of 0.0 to 1.0.
Consider: completeness, accuracy, relevance, and actionability.

Step: {step}
Output: {output}
Objective: {objective}

Respond in JSON format:
{{"score": 0.85, "feedback": "explanation here"}}""",
        input_variables=["step", "output", "objective"]
    )
    
    response = llm.invoke(verify_prompt.format(
        step=last_result.step,
        output=last_result.output,
        objective=state["objective"]
    ))
    
    try:
        verify_data = json.loads(response.content)
        score = verify_data.get("score", 0.7)
        feedback = verify_data.get("feedback", "")
    except json.JSONDecodeError:
        score = 0.7
        feedback = "Verification incomplete"
    
    # Update last result with verification
    state["step_results"][-1].score = score
    state["step_results"][-1].feedback = feedback
    state["status"] = f"verified (score: {score})"
    
    return state
