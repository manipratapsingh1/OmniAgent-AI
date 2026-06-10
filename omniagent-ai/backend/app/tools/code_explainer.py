from typing import Dict, Any
from app.llm.ollama_client import ollama


async def code_explainer(args: Dict[str, Any]) -> str:
    code = str(args.get("code", "")).strip()
    if not code:
        return "No code provided."
    sys = "Explain the following code clearly and concisely. Note potential bugs."
    return await ollama.generate(prompt=code, system=sys)