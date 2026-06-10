from typing import Awaitable, Callable, Dict, Any, List
from app.tools.calculator import calculator
from app.tools.web_search import web_search
from app.tools.code_explainer import code_explainer
from app.tools.file_summarizer import file_summarizer
from app.tools.notes import notes_tool

ToolFn = Callable[[Dict[str, Any]], Awaitable[str]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolFn] = {}

    def register(self, name: str, fn: ToolFn) -> None:
        self._tools[name] = fn

    def names(self) -> List[str]:
        return list(self._tools.keys())

    async def run(self, name: str, args: Dict[str, Any]) -> str:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return await self._tools[name](args)


registry = ToolRegistry()
registry.register("calculator", calculator)
registry.register("web_search", web_search)
registry.register("code_explainer", code_explainer)
registry.register("file_summarizer", file_summarizer)
registry.register("notes", notes_tool)