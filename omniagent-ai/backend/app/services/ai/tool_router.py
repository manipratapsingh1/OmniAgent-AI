from typing import Any, Callable, Dict, Optional


class ToolRouter:
    """Simple tool registry and safe executor."""

    def __init__(self):
        self.tools: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]):
        self.tools[name] = fn

    def execute(self, name: str, *args, **kwargs) -> Dict[str, Any]:
        if name not in self.tools:
            return {"ok": False, "error": "tool_not_found"}
        # For safety, external checks should be applied here
        try:
            result = self.tools[name](*args, **kwargs)
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}
