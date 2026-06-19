"""
Advanced Tools API Endpoints
Code Interpreter, Calculator, File Analyzer, Visualization, Export/Share
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
import json
import structlog

from app.deps import db_session, current_user
from app.models.user import User
from app.tools.advanced_tools import (
    code_interpreter,
    calculator,
    file_analyzer,
    visualizer,
)

router = APIRouter()
log = structlog.get_logger("tools_api")


# ============= SCHEMAS =============

class CodeExecutionRequest(BaseModel):
    """Code execution request"""
    code: str = Field(..., description="Python code to execute")
    variables: Optional[Dict[str, Any]] = None


class CalculatorRequest(BaseModel):
    """Calculator request"""
    expression: str = Field(..., description="Mathematical expression")


class FileAnalysisRequest(BaseModel):
    """File analysis request"""
    filename: str
    content: str


class ChartGenerationRequest(BaseModel):
    """Chart generation request"""
    data: List[Dict[str, Any]]
    chart_type: str = Field("line", description="Chart type: line, bar, pie, etc.")


class ConversationExportRequest(BaseModel):
    """Export conversation request"""
    format: str = Field("markdown", description="Format: markdown, json, pdf")


class ConversationShareRequest(BaseModel):
    """Share conversation request"""
    share_with_email: Optional[str] = None
    public: bool = False


# ============= RESPONSES =============

class ToolResponse(BaseModel):
    """Standard tool response"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ============= CODE INTERPRETER ENDPOINTS =============

@router.post("/execute-code", response_model=ToolResponse)
async def execute_code(
    req: CodeExecutionRequest,
    user: User = Depends(current_user),
):
    """Execute Python code in sandboxed environment"""
    log.info("execute_code.start", user_id=user.id, code_len=len(req.code))

    result = code_interpreter.execute(req.code, req.variables or {})

    return ToolResponse(
        success=result['success'],
        result=result.get('result') or result.get('output'),
        error=result.get('error'),
        metadata={'code': (result.get('code') or '')[:100]}
    )


# ============= CALCULATOR ENDPOINTS =============

@router.post("/calculate", response_model=ToolResponse)
async def calculate(
    req: CalculatorRequest,
    user: User = Depends(current_user),
):
    """Evaluate mathematical expression"""
    log.info("calculate.start", user_id=user.id, expr=req.expression)

    result = calculator.evaluate(req.expression)

    return ToolResponse(
        success=result['success'],
        result=result.get('result'),
        error=result.get('error'),
        metadata=result
    )


# ============= FILE ANALYZER ENDPOINTS =============

@router.post("/analyze-file", response_model=ToolResponse)
async def analyze_file(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
):
    """Analyze uploaded file"""
    try:
        content = await file.read()

        log.info("analyze_file.start", user_id=user.id, filename=file.filename)

        analysis = file_analyzer.analyze(file.filename or "file", content)

        return ToolResponse(
            success=True,
            result=analysis,
            metadata={'filename': file.filename}
        )

    except Exception as e:
        log.exception("analyze_file.failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"File analysis failed: {str(e)}")


@router.post("/analyze-file-text", response_model=ToolResponse)
async def analyze_file_text(
    req: FileAnalysisRequest,
    user: User = Depends(current_user),
):
    """Analyze file content (text-based)"""
    log.info("analyze_file_text.start", user_id=user.id, filename=req.filename)

    analysis = file_analyzer.analyze(req.filename, req.content.encode('utf-8'), text_content=req.content)

    return ToolResponse(
        success=True,
        result=analysis,
        metadata={'filename': req.filename}
    )


# ============= DATA VISUALIZATION ENDPOINTS =============

@router.post("/generate-chart", response_model=ToolResponse)
async def generate_chart(
    req: ChartGenerationRequest,
    user: User = Depends(current_user),
):
    """Generate chart configuration from data"""
    log.info("generate_chart.start", user_id=user.id, chart_type=req.chart_type)

    result = visualizer.generate_chart_data(req.data, req.chart_type)

    return ToolResponse(
        success=result['success'],
        result=result,
        error=result.get('error'),
        metadata={'chart_type': req.chart_type}
    )


@router.post("/generate-chart-from-csv", response_model=ToolResponse)
async def generate_chart_from_csv(
    rows: Optional[List[List]] = None,
    user: User = Depends(current_user),
):
    """Generate chart from CSV rows"""
    try:
        if not rows:
            raise HTTPException(status_code=400, detail="No data provided")

        log.info("generate_chart_from_csv.start", user_id=user.id, rows=len(rows))

        result = visualizer.generate_from_csv(rows)

        return ToolResponse(
            success=result['success'],
            result=result,
            error=result.get('error')
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= EXPORT & SHARE ENDPOINTS =============

@router.post("/export-conversation")
async def export_conversation(
    conv_id: int,
    format: str = "markdown",
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
):
    """Export conversation in various formats"""
    try:
        from app.repositories.conversation_repo import ConversationRepo
        from app.models.conversation import Conversation
        from app.models.message import Message

        repo = ConversationRepo(db)
        conv = repo.get(conv_id)

        if not conv or conv.user_id != user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get all messages
        messages = db.exec(
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.created_at)  # type: ignore
        ).all()

        if format == "markdown":
            # Export as markdown
            content = f"# Conversation: {conv.title or 'Untitled'}\n\n"
            content += f"*Created: {conv.created_at}*\n\n"

            for msg in messages:
                role = "**User:**" if msg.role == "user" else "**Assistant:**"
                content += f"{role} {msg.content}\n\n"

            return {
                "success": True,
                "format": "markdown",
                "content": content,
                "filename": f"{conv.title or 'conversation'}.md"
            }

        elif format == "json":
            # Export as JSON
            data = {
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in messages
                ]
            }

            return {
                "success": True,
                "format": "json",
                "content": json.dumps(data, indent=2),
                "filename": f"{conv.title or 'conversation'}.json"
            }

        elif format == "pdf":
            # PDF export (simplified - return data for frontend to generate)
            content = f"Conversation: {conv.title or 'Untitled'}\n"
            content += f"Created: {conv.created_at}\n\n"

            for msg in messages:
                role = "User:" if msg.role == "user" else "Assistant:"
                content += f"{role} {msg.content}\n\n"

            return {
                "success": True,
                "format": "pdf",
                "content": content,
                "filename": f"{conv.title or 'conversation'}.pdf",
                "note": "Use a PDF library to generate from content"
            }

        else:
            raise HTTPException(status_code=400, detail="Unsupported format")

    except Exception as e:
        log.exception("export_conversation.failed", error=str(e))
        raise HTTPException(status_code=500, detail="Export failed")


@router.post("/share-conversation")
async def share_conversation(
    conv_id: int,
    req: ConversationShareRequest,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
):
    """Share conversation with others or make public"""
    try:
        from app.repositories.conversation_repo import ConversationRepo
        from app.models.conversation import Conversation
        from app.models.sharing_and_faq import ConversationShare

        repo = ConversationRepo(db)
        conv = repo.get(conv_id)

        if not conv or conv.user_id != user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Update conversation
        conv.is_shared = True
        db.add(conv)

        # Find existing share or create new
        share = db.exec(
            select(ConversationShare).where(ConversationShare.conversation_id == conv_id)
        ).first()

        if not share:
            import secrets
            share_token = secrets.token_urlsafe(32)
            share = ConversationShare(
                conversation_id=conv_id,
                shared_by_user_id=user.id,
                share_token=share_token,
            )
            db.add(share)
        else:
            share_token = share.share_token

        db.commit()

        from app.config import get_settings
        share_url = f"{get_settings().FRONTEND_URL}/share/{share_token}"

        log.info("conversation.shared", user_id=user.id, conv_id=conv_id)

        return {
            "success": True,
            "share_token": share_token,
            "share_url": share_url,
            "public": req.public
        }

    except Exception as e:
        log.exception("share_conversation.failed", error=str(e))
        raise HTTPException(status_code=500, detail="Share failed")


@router.get("/shared-conversation/{share_token}")
async def get_shared_conversation(
    share_token: str,
    db: Session = Depends(db_session),
):
    """View a shared conversation"""
    try:
        from sqlmodel import select
        from app.models.conversation import Conversation
        from app.models.message import Message
        from app.models.sharing_and_faq import ConversationShare

        # Find the share record
        share = db.exec(
            select(ConversationShare).where(
                ConversationShare.share_token == share_token
            )
        ).first()

        if not share:
            raise HTTPException(status_code=404, detail="Shared conversation not found")

        # Get conversation
        conv = db.get(Conversation, share.conversation_id)
        if not conv or not conv.is_shared:
            raise HTTPException(status_code=404, detail="Shared conversation not found")

        # Get messages
        messages = db.exec(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at)  # type: ignore
        ).all()

        return {
            "title": conv.title,
            "created_at": conv.created_at,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at
                }
                for msg in messages
            ]
        }

    except Exception as e:
        log.exception("get_shared_conversation.failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve shared conversation")


# ============= UTILITY ENDPOINTS =============

@router.get("/tools/available")
async def get_available_tools(user: User = Depends(current_user)):
    """Get list of available tools"""
    return {
        "tools": [
            {
                "name": "Code Interpreter",
                "endpoint": "/tools/execute-code",
                "description": "Execute Python code in sandboxed environment",
                "capabilities": ["math", "json", "data processing"]
            },
            {
                "name": "Calculator",
                "endpoint": "/tools/calculate",
                "description": "Evaluate mathematical expressions",
                "capabilities": ["arithmetic", "trigonometry", "logarithms"]
            },
            {
                "name": "File Analyzer",
                "endpoint": "/tools/analyze-file",
                "description": "Analyze uploaded files (TXT, JSON, CSV, etc.)",
                "capabilities": ["text analysis", "json validation", "csv parsing"]
            },
            {
                "name": "Data Visualizer",
                "endpoint": "/tools/generate-chart",
                "description": "Generate charts and visualizations",
                "capabilities": ["line charts", "bar charts", "pie charts"]
            },
            {
                "name": "Export/Share",
                "endpoint": "/tools/export-conversation",
                "description": "Export and share conversations",
                "capabilities": ["markdown", "json", "pdf export", "public sharing"]
            }
        ]
    }
