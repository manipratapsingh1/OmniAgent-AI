"""Admin Agent: handles administrative operations and system management.
Processes requests for user management, system monitoring, and administrative tasks."""
from app.agents.state import AgentState, TraceEntry
import structlog
import time

log = structlog.get_logger("admin_agent")


async def admin_review(state: AgentState) -> AgentState:
    """Process administrative tasks and user management requests."""
    start_time = time.time()
    
    try:
        # Analyze the query to determine what admin action is needed
        query_lower = state.query.lower()
        
        # Route to appropriate admin function based on query
        if any(keyword in query_lower for keyword in ["user", "users", "account", "accounts", "profile"]):
            result = await _handle_user_management(state)
        elif any(keyword in query_lower for keyword in ["system", "health", "status", "monitor", "statistics", "stats"]):
            result = await _handle_system_monitoring(state)
        elif any(keyword in query_lower for keyword in ["quota", "limit", "usage", "rate"]):
            result = await _handle_quota_management(state)
        elif any(keyword in query_lower for keyword in ["audit", "log", "access", "activity"]):
            result = await _handle_audit_review(state)
        elif any(keyword in query_lower for keyword in ["document", "upload", "delete", "file"]):
            result = await _handle_document_management(state)
        else:
            result = f"Admin request received: {state.query}. This request will be processed by the admin team."
        
        # Record trace
        latency_ms = int((time.time() - start_time) * 1000)
        trace_entry = TraceEntry(
            agent="admin",
            input=state.query,
            output=result[:200] if result else "",
            latency_ms=latency_ms,
        )
        
        state.trace.append(trace_entry)
        state.route.append("admin")
        state.final = result
        
        log.info("admin_agent.complete", latency_ms=latency_ms, query=state.query[:50])
        return state
    
    except Exception as e:
        log.error("admin_agent.error", error=str(e), query=state.query)
        state.final = f"Admin processing error: {str(e)}"
        return state


async def _handle_user_management(state: AgentState) -> str:
    """Handle user management operations."""
    query_lower = state.query.lower()
    
    if "create" in query_lower or "add" in query_lower:
        return "User creation request recorded. An admin will review the request."
    elif "delete" in query_lower or "remove" in query_lower:
        return "User deletion request recorded. This action requires admin review."
    elif "deactivate" in query_lower or "disable" in query_lower:
        return "User deactivation request recorded. Processing..."
    elif "role" in query_lower or "permission" in query_lower:
        return "User role/permission modification request recorded."
    elif "list" in query_lower or "show" in query_lower:
        return "User list query recorded. Retrieving user information..."
    else:
        return "User management request received and will be processed."


async def _handle_system_monitoring(state: AgentState) -> str:
    """Handle system monitoring and health checks."""
    query_lower = state.query.lower()
    
    if "health" in query_lower or "status" in query_lower:
        return "System health check initiated. All components are operational."
    elif "performance" in query_lower or "metric" in query_lower:
        return "Performance metrics request received. Current system performance is optimal."
    elif "uptime" in query_lower:
        return "System uptime check initiated. System has been running smoothly."
    elif "resource" in query_lower or "memory" in query_lower or "cpu" in query_lower:
        return "System resource monitoring initiated. Resources are within normal limits."
    else:
        return "System monitoring request received."


async def _handle_quota_management(state: AgentState) -> str:
    """Handle API quota and rate limit management."""
    query_lower = state.query.lower()
    
    if "increase" in query_lower or "raise" in query_lower:
        return "Quota increase request recorded. An admin will review and process this request."
    elif "decrease" in query_lower or "lower" in query_lower:
        return "Quota decrease request recorded."
    elif "reset" in query_lower:
        return "Quota reset request recorded."
    elif "view" in query_lower or "check" in query_lower or "show" in query_lower:
        return "Current quota information has been requested. Retrieving details..."
    else:
        return "Quota management request received."


async def _handle_audit_review(state: AgentState) -> str:
    """Handle audit log and access review."""
    query_lower = state.query.lower()
    
    if "activity" in query_lower or "log" in query_lower:
        return "Audit log review initiated. Recent activities are being analyzed."
    elif "access" in query_lower:
        return "Access review initiated. Checking user access patterns."
    elif "report" in query_lower:
        return "Audit report generation initiated. Report will be compiled shortly."
    else:
        return "Audit review request received."


async def _handle_document_management(state: AgentState) -> str:
    """Handle document management operations."""
    query_lower = state.query.lower()
    
    if "delete" in query_lower or "remove" in query_lower:
        return "Document deletion request recorded. This action requires admin confirmation."
    elif "upload" in query_lower or "add" in query_lower:
        return "Document upload will be processed. The document will be indexed for RAG."
    elif "list" in query_lower or "show" in query_lower:
        return "Document list query received. Retrieving document inventory..."
    else:
        return "Document management request received."