"""
Security utilities for input validation and sanitization
"""
from typing import Tuple


def sanitize_email(email: str) -> str:
    """Sanitize email input"""
    return email.strip().lower()


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input"""
    if not value:
        return ""
    # Remove leading/trailing whitespace
    sanitized = value.strip()
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def is_valid_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    # Could add more requirements: uppercase, lowercase, numbers, symbols, etc.
    return True, ""


def is_valid_title(title: str) -> Tuple[bool, str]:
    """Validate title/name input"""
    if not title or not title.strip():
        return False, "Title cannot be empty"
    if len(title) > 512:
        return False, "Title is too long (max 512 characters)"
    return True, ""
