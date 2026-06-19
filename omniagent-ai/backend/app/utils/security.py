"""
Security utilities for input validation, sanitization, and attack prevention.
Covers OWASP Top 10 vectors relevant to AI platforms.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Tuple
from urllib.parse import urlparse

# Dangerous filename patterns
_PATH_TRAVERSAL = re.compile(r"(\.\.[\\/]|^[\\/]|[\x00-\x1f])")
_DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".ps1", ".dll", ".so",
    ".php", ".jsp", ".asp", ".aspx", ".py", ".rb", ".pl", ".js",
}

# Prompt injection patterns (common attack vectors)
_INJECTION_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
        r"disregard\s+(your\s+)?(instructions?|system\s+prompt|rules?)",
        r"you\s+are\s+now\s+(?:a\s+)?(?:DAN|evil|unrestricted|jailbroken)",
        r"forget\s+(everything|all)\s+(you\s+)?(know|learned|were\s+told)",
        r"reveal\s+(your\s+)?(system\s+prompt|instructions?|api\s+key|secret)",
        r"<\s*script\b",
        r"javascript\s*:",
        r"on\w+\s*=",
    ]
]

# Private/reserved IP ranges for SSRF prevention
_PRIVATE_HOSTS = re.compile(
    r"^(localhost|127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|0\.|::1|\[::1\])",
    re.I,
)

ALLOWED_UPLOAD_EXTENSIONS = {
    ".md", ".txt", ".pdf", ".markdown", ".docx", ".pptx",
    ".html", ".htm", ".csv", ".xlsx", ".png", ".jpg", ".jpeg", ".webp",
}


def sanitize_email(email: str) -> str:
    """Sanitize email input."""
    return email.strip().lower()


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input with length limit."""
    if not value:
        return ""
    sanitized = value.strip()
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def sanitize_filename(filename: str) -> Tuple[bool, str, str]:
    """
    Sanitize uploaded filename against path traversal and dangerous extensions.
    Returns: (is_valid, sanitized_name, error_message)
    """
    if not filename or not filename.strip():
        return False, "", "Filename cannot be empty"

    # Strip directory components
    name = PurePosixPath(filename.replace("\\", "/")).name
    name = name.strip()

    if _PATH_TRAVERSAL.search(filename):
        return False, "", "Invalid filename: path traversal detected"

    if len(name) > 255:
        return False, "", "Filename too long (max 255 characters)"

    ext = PurePosixPath(name).suffix.lower()
    if ext in _DANGEROUS_EXTENSIONS:
        return False, "", f"File extension '{ext}' is not allowed"

    if ext and ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return False, "", f"File extension '{ext}' is not supported"

    # Remove null bytes and control characters
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    if not name:
        return False, "", "Invalid filename after sanitization"

    return True, name, ""


def validate_file_size(size_bytes: int, max_mb: int = 10) -> Tuple[bool, str]:
    """Validate uploaded file size."""
    max_bytes = max_mb * 1024 * 1024
    if size_bytes <= 0:
        return False, "File is empty"
    if size_bytes > max_bytes:
        return False, f"File too large. Max size is {max_mb}MB"
    return True, ""


def is_valid_password(password: str) -> Tuple[bool, str]:
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    return True, ""


def is_valid_title(title: str) -> Tuple[bool, str]:
    """Validate title/name input."""
    if not title or not title.strip():
        return False, "Title cannot be empty"
    if len(title) > 512:
        return False, "Title is too long (max 512 characters)"
    return True, ""


def is_safe_url(url: str, allow_localhost: bool = False) -> Tuple[bool, str]:
    """
    Validate URL for SSRF prevention.
    Returns: (is_safe, error_message)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False, "Invalid URL format"

    if parsed.scheme not in ("http", "https"):
        return False, f"URL scheme '{parsed.scheme}' not allowed"

    host = parsed.hostname or ""
    if not host:
        return False, "URL has no hostname"

    if not allow_localhost and _PRIVATE_HOSTS.match(host):
        return False, "URL points to a private/reserved address"

    return True, ""


def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Detect common prompt injection patterns.
    Returns: (is_suspicious, matched_pattern_description)
    """
    if not text:
        return False, ""

    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, f"Suspicious pattern detected: {match.group()[:50]}"

    return False, ""


def sanitize_user_message(text: str, max_length: int = 32000) -> str:
    """Sanitize user chat message — strip control chars, enforce length."""
    if not text:
        return ""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned.strip()
