from typing import Dict, Any
from app.llm.ollama_client import ollama


async def file_summarizer(args: Dict[str, Any]) -> str:
    text = str(args.get("text", "")).strip()
    if not text:
        return "No text provided."
    sys = "Summarize the document in 8 bullet points, then a 2-sentence TL;DR."
    return await ollama.generate(prompt=text[:12000], system=sys)