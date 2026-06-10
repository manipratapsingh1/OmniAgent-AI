from sqlmodel import SQLModel

# Import all models so SQLModel.metadata is populated
from app.models.user import User  # noqa
from app.models.conversation import Conversation  # noqa
from app.models.message import Message  # noqa
from app.models.document import Document, DocumentChunk  # noqa
from app.models.task import Task  # noqa
from app.models.agent_run import AgentRun  # noqa
from app.models.tool_call import ToolCall  # noqa
from app.models.feedback import Feedback  # noqa
from app.models.audit_log import AuditLog  # noqa
from app.models.api_key import APIKey  # noqa
from app.models.response import Response  # noqa
from app.models.memory import MemoryEntry  # noqa
from app.models.background_job import BackgroundJob  # noqa
from app.models.notification import Notification  # noqa
from app.models.document_tags import DocumentTag, DocumentCategory  # noqa
from app.models.document_versions import DocumentSummary  # noqa
from app.models.sharing_and_faq import ConversationShare, FrequentlyAskedQuestion, QueryTemplate  # noqa
from app.models.tool_log import ToolLog  # noqa

metadata = SQLModel.metadata