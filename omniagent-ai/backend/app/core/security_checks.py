import re
import html
from typing import Any

# SQL injection patterns (e.g. UNION SELECT, OR 1=1, DROP TABLE)
SQL_INJECTION_PATTERN = re.compile(
    r"(union\s+all\s+select|select\s+.*\s+from|drop\s+table|delete\s+from|insert\s+into|update\s+.*\s+set|or\s+\d+\s*=\s*\d+)",
    re.IGNORECASE
)

# Command injection patterns (characters like ; || && ` $() or key shell/exec utilities)
COMMAND_INJECTION_PATTERN = re.compile(
    r"(;|\|\||&&|`|\$\(|\b(rm|cat|bash|sh|powershell|cmd|wget|curl)\b)",
    re.IGNORECASE
)

# Prompt injection patterns (override instructions)
PROMPT_INJECTION_PATTERN = re.compile(
    r"(ignore\s+all\s+(previous)?\s+instructions|system\s+override|you\s+are\s+now\b|disregard\s+above)",
    re.IGNORECASE
)


def sanitize_xss(text: str) -> str:
    """Escape HTML tags to prevent XSS attacks"""
    if not isinstance(text, str):
        return text
    return html.escape(text)


def has_sql_injection(text: str) -> bool:
    """Check for obvious SQL injection attempts"""
    if not isinstance(text, str):
        return False
    return bool(SQL_INJECTION_PATTERN.search(text))


def has_command_injection(text: str) -> bool:
    """Check for obvious command injection attempts"""
    if not isinstance(text, str):
        return False
    return bool(COMMAND_INJECTION_PATTERN.search(text))


def has_prompt_injection(text: str) -> bool:
    """Check for potential prompt injection attempts"""
    if not isinstance(text, str):
        return False
    return bool(PROMPT_INJECTION_PATTERN.search(text))


def is_safe_path(path: str) -> bool:
    """Check if path is safe from traversal attacks"""
    if not isinstance(path, str):
        return False
    normalized = path.replace("\\", "/")
    # Block parent directory traversal
    if ".." in normalized:
        return False
    # Absolute paths are blocked for safety where relative pathing is expected
    if normalized.startswith("/") or re.match(r"^[a-zA-Z]:", normalized):
        return False
    return True


def validate_input_safety(text: str) -> tuple[bool, str | None]:
    """Validate text against injection attacks. Returns (is_safe, error_msg)"""
    if not isinstance(text, str):
        return True, None
    if has_sql_injection(text):
        return False, "Potential SQL injection pattern detected"
    if has_command_injection(text):
        return False, "Potential command/system injection pattern detected"
    if has_prompt_injection(text):
        return False, "Potential prompt injection pattern detected"
    return True, None


def is_safe_url(url: str) -> bool:
    """Validate URL to prevent SSRF attacks against internal network/localhost"""
    import socket
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        
        host = parsed.hostname
        if not host:
            return False
            
        host_lower = host.lower()
        if host_lower in ('localhost', 'localhost.localdomain'):
            return False
            
        try:
            addr_info = socket.getaddrinfo(host, None)
        except socket.gaierror:
            return False
            
        for family, _, _, _, sockaddr in addr_info:
            ip = sockaddr[0]
            if ":" not in ip:
                if ip.startswith("127."):
                    return False
                if ip.startswith("10."):
                    return False
                if ip.startswith("192.168."):
                    return False
                if ip.startswith("172."):
                    parts = ip.split(".")
                    if len(parts) >= 2 and 16 <= int(parts[1]) <= 31:
                        return False
                if ip.startswith("169.254."):
                    return False
                if ip.startswith("0.") or ip.startswith("255.") or ip.startswith("224."):
                    return False
            else:
                if ip == "::1" or ip == "0:0:0:0:0:0:0:1":
                    return False
                if ip.lower().startswith("fe80"):
                    return False
                if ip.lower().startswith("fc") or ip.lower().startswith("fd"):
                    return False
        return True
    except Exception:
        return False


def validate_mime_type(content: bytes, declared_mime: str, filename: str) -> bool:
    """Validate that the file content headers match the expected/declared MIME type or file extension"""
    if not content:
        return True
        
    ext = filename.split('.')[-1].lower()
    mime = declared_mime.lower()
    
    if ext == 'pdf' or 'pdf' in mime:
        return content.startswith(b'%PDF-')
        
    if ext in ('docx', 'xlsx', 'pptx') or 'officedocument' in mime or 'zip' in mime:
        return content.startswith(b'PK\x03\x04')
        
    if ext == 'png' or 'png' in mime:
        return content.startswith(b'\x89PNG\r\n\x1a\n')
    if ext in ('jpg', 'jpeg') or 'jpeg' in mime:
        return content.startswith(b'\xff\xd8')
        
    if ext == 'json' or 'json' in mime:
        try:
            import json
            json.loads(content.decode('utf-8'))
            return True
        except Exception:
            return False
            
    if ext in ('csv', 'txt', 'md', 'log') or 'text/' in mime or 'csv' in mime:
        return b'\x00' not in content[:8192]
        
    return True
