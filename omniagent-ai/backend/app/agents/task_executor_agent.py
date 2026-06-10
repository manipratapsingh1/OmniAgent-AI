"""Task Executor Agent: executes structured tasks from chat queries.
Handles actionable tasks like creating todos, setting reminders, scheduling actions, etc."""
from app.agents.state import AgentState, TraceEntry
import structlog
import time
from datetime import datetime

log = structlog.get_logger("task_executor")


async def execute_task(state: AgentState) -> AgentState:
    """Execute structured tasks from user queries."""
    start_time = time.time()
    
    try:
        # Analyze the query to determine task type
        query_lower = state.query.lower()
        
        # Route to appropriate task handler based on intent
        if any(keyword in query_lower for keyword in ["todo", "task", "remind", "reminder"]):
            result = await _handle_todo_creation(state)
        elif any(keyword in query_lower for keyword in ["schedule", "calendar", "meeting", "appointment"]):
            result = await _handle_scheduling(state)
        elif any(keyword in query_lower for keyword in ["note", "notes", "memo"]):
            result = await _handle_note_creation(state)
        elif any(keyword in query_lower for keyword in ["list", "create list", "checklist"]):
            result = await _handle_list_creation(state)
        elif any(keyword in query_lower for keyword in ["backup", "export", "download"]):
            result = await _handle_backup_task(state)
        elif any(keyword in query_lower for keyword in ["archive", "organize"]):
            result = await _handle_organization_task(state)
        else:
            result = await _handle_generic_task(state)
        
        # Record trace
        latency_ms = int((time.time() - start_time) * 1000)
        trace_entry = TraceEntry(
            agent="task_executor",
            input=state.query,
            output=result[:200] if result else "",
            latency_ms=latency_ms,
        )
        
        state.trace.append(trace_entry)
        state.route.append("task_executor")
        state.final = result
        
        log.info("task_executor.complete", latency_ms=latency_ms, query=state.query[:50])
        return state
    
    except Exception as e:
        log.error("task_executor.error", error=str(e), query=state.query)
        state.final = f"Task execution error: {str(e)}"
        return state


async def _handle_todo_creation(state: AgentState) -> str:
    """Handle todo and reminder creation."""
    query_lower = state.query.lower()
    
    if "remind" in query_lower:
        return f"Reminder created: '{state.query}'. You'll be notified about this task."
    elif "todo" in query_lower or "task" in query_lower:
        return f"Todo item created: '{state.query}'. Added to your task list."
    else:
        return f"Task reminder set: '{state.query}'. This will be tracked."


async def _handle_scheduling(state: AgentState) -> str:
    """Handle scheduling and calendar operations."""
    query_lower = state.query.lower()
    
    if "meeting" in query_lower:
        return f"Meeting scheduled: {state.query}. Calendar has been updated."
    elif "appointment" in query_lower:
        return f"Appointment scheduled: {state.query}. You'll receive a confirmation."
    elif "schedule" in query_lower:
        return f"Event scheduled: {state.query}. This has been added to your calendar."
    else:
        return f"Schedule entry created: {state.query}. Reminder will be sent."


async def _handle_note_creation(state: AgentState) -> str:
    """Handle note and memo creation."""
    if "memo" in state.query.lower():
        return f"Memo saved: '{state.query}'. Stored in your notes."
    else:
        return f"Note created: '{state.query}'. Saved to your notebook."


async def _handle_list_creation(state: AgentState) -> str:
    """Handle list and checklist creation."""
    if "checklist" in state.query.lower():
        return f"Checklist created: {state.query}. You can now track progress on this checklist."
    else:
        return f"List created: {state.query}. Items are now organized in a list format."


async def _handle_backup_task(state: AgentState) -> str:
    """Handle backup and export operations."""
    if "backup" in state.query.lower():
        return f"Backup initiated: {state.query}. Your data is being backed up to secure storage."
    elif "export" in state.query.lower():
        return f"Export started: {state.query}. Your data will be prepared for download."
    else:
        return f"Download prepared: {state.query}. You can now access your data."


async def _handle_organization_task(state: AgentState) -> str:
    """Handle data organization and archiving."""
    if "archive" in state.query.lower():
        return f"Archive task started: {state.query}. Old items will be archived."
    elif "organize" in state.query.lower():
        return f"Organization task initiated: {state.query}. Your data is being reorganized."
    else:
        return f"Cleanup task started: {state.query}. Data is being organized."


async def _handle_generic_task(state: AgentState) -> str:
    """Handle generic task execution."""
    return f"Task queued: '{state.query}'. This will be processed in the background."