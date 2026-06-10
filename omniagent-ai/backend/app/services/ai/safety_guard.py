from typing import Dict, Any


class SafetyGuard:
    """Basic safety checks and prompt-injection protection."""

    def __init__(self):
        pass

    def check_tool_call(self, tool_name: str, user_role: str) -> Dict[str, Any]:
        # Example: restrict admin-only tools
        if tool_name.startswith("admin_") and user_role != "admin":
            return {"ok": False, "error": "unauthorized"}
        return {"ok": True}

    def sanitize_prompt(self, prompt: str) -> str:
        # Simple sanitation placeholder
        return prompt
