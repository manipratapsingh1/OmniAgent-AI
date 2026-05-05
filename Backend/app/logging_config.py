"""
Comprehensive logging system for OmniAgent AI
"""
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Optional, Any
import os
from pathlib import Path
import structlog

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "endpoint"):
            log_obj["endpoint"] = record.endpoint
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "duration"):
            log_obj["duration_ms"] = record.duration
        if hasattr(record, "status_code"):
            log_obj["status_code"] = record.status_code
            
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (JSON format)
    file_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "omniai.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # API logs handler
    api_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "api.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    api_handler.setLevel("INFO")
    api_handler.setFormatter(file_formatter)
    
    api_logger = logging.getLogger("api")
    api_logger.addHandler(api_handler)
    
    # Error logs handler
    error_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "errors.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel("ERROR")
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)


# Create loggers
logger = logging.getLogger(__name__)
api_logger = logging.getLogger("api")
agent_logger = logging.getLogger("agent")
rag_logger = logging.getLogger("rag")
db_logger = logging.getLogger("database")


class Logger:
    """Wrapper class for structured logging"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info level"""
        self._log(logging.INFO, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error level"""
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical level"""
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)
    
    def _log(self, level: int, message: str, exc_info: bool = False, **kwargs):
        """Internal log method"""
        # Create log record with extra fields
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            None,
            0,
            message,
            (),
            exc_info
        )
        
        # Add custom fields
        for key, value in kwargs.items():
            setattr(record, key, value)
        
        self.logger.handle(record)


# Specific loggers
class APILogger(Logger):
    """Logger for API requests/responses"""
    
    def log_request(self, user_id: Optional[str], endpoint: str, method: str, **kwargs):
        """Log API request"""
        self.info(f"API Request: {method} {endpoint}", user_id=user_id, endpoint=endpoint, **kwargs)
    
    def log_response(self, endpoint: str, status_code: int, duration_ms: float, **kwargs):
        """Log API response"""
        self.info(f"API Response: {status_code}", endpoint=endpoint, status_code=status_code, duration=duration_ms, **kwargs)
    
    def log_error(self, endpoint: str, status_code: int, error_msg: str, **kwargs):
        """Log API error"""
        self.error(f"API Error: {status_code} - {error_msg}", endpoint=endpoint, status_code=status_code, **kwargs)


class AgentLogger(Logger):
    """Logger for agent operations"""
    
    def log_planning(self, user_id: str, query: str, steps: int):
        """Log agent planning"""
        self.info(f"Agent Planning: {steps} steps", user_id=user_id, query=query[:100], steps=steps)
    
    def log_execution(self, user_id: str, step: int, tool: str):
        """Log agent execution"""
        self.info(f"Agent Execution: Step {step}", user_id=user_id, step=step, tool=tool)
    
    def log_verification(self, user_id: str, score: float, passed: bool):
        """Log agent verification"""
        level = "PASS" if passed else "RETRY"
        self.info(f"Agent Verification: {level} (score: {score})", user_id=user_id, score=score)


class RAGLogger(Logger):
    """Logger for RAG operations"""
    
    def log_upload(self, user_id: str, filename: str, chunks: int):
        """Log document upload"""
        self.info(f"RAG Upload: {filename}", user_id=user_id, filename=filename, chunks=chunks)
    
    def log_retrieval(self, user_id: str, query: str, results: int, latency_ms: float):
        """Log RAG retrieval"""
        self.info(f"RAG Retrieval: {results} results", user_id=user_id, query=query[:100], results=results, latency_ms=latency_ms)


# Initialize logging on import
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

# Export logger instances
__all__ = [
    "logger",
    "api_logger",
    "agent_logger",
    "rag_logger",
    "db_logger",
    "Logger",
    "APILogger",
    "AgentLogger",
    "RAGLogger",
    "setup_logging"
]
