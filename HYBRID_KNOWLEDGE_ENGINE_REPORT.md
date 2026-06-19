# OmniAgent Hybrid Knowledge Engine Report

This report outlines the functionality, priority routing logic, and improvements made to the Hybrid Knowledge Engine.

## Priority Routing Hierarchy

The engine intelligently routes queries across knowledge sources in the following strict priority order:

1. **Uploaded Documents**: Scoped to the current user's documents (unless requesting admin shared knowledge).
2. **Internal Knowledge Base**: Global shared documents uploaded by administrator (`is_knowledge_base = True`).
3. **Conversation Memory**: Short-term recent messages in the thread and long-term learned preferences/facts.
4. **Knowledge Graph**: Semantic entity-relation links stored in graph memory.
5. **Web Search**: Fallback duckduckgo queries (if enabled) executed when document confidence is low.
6. **OpenAI / Gemini / Claude / Ollama**: General foundation models selected dynamically using the Model Router.

## Classification and Routing Rules

The engine classifies each query into one of six distinct cases based on document match confidence:

| Case | Condition | Behavior | LLM Prompt Instructions |
|---|---|---|---|
| **Case 1: Full Document Match** | Match confidence is `high` or `medium` (score >= 0.35) | Rely primary on document evidence | Answer strictly from document context; cite chunks; enforce no hallucinations. |
| **Case 2: Partial Document Match** | Match confidence is `low` (score >= 0.15) | Combine document evidence with AI explanation | Separate answer into `## Document Evidence` and `## Additional AI Explanation` sections. |
| **Case 3: No Document Match** | Chunks empty or confidence is `none` (score < 0.15) | Fall back to general AI knowledge base | If user query explicitly mentions documents/files, state they weren't found. Otherwise, provide direct AI answer directly without warning. |
| **Case 4: Multi-Document Match** | Relevant chunks span multiple documents | Compare and synthesize evidence | Synthesize findings; resolve any conflicts; cite all sources. |
| **Case 5: Documents Only Mode** | Explicit keyword triggers (e.g. "answer only from my documents") | Enforce document exclusivity | Use ONLY provided document context. If not found, output exactly *"Information not found in uploaded documents"*. |
| **Case 6: AI Only Mode** | Explicit keyword triggers (e.g. "ignore my documents") | Bypass retrieval entirely | Query selected LLM directly without retrieving or injecting vector context. |

## Key Improvements
1. **Confidence Score Calibration**: Fixed a bug where low-relevance chunks received a score boost of `0.1` due to position bias, preventing the engine from ever returning `none` confidence. Cap irrelevant chunk scores to `0.05` to enforce proper `NO_DOCUMENT` fallback routing.
2. **General Query Warnings Removed**: Suppressed document-missing warnings for queries that do not reference documents, leading to a much smoother ChatGPT/Claude-like user experience.
3. **Knowledge Base Global Search**: Fixed the SQL and vector scoping query filters to allow shared knowledge base documents to be retrieved by non-admin users.
