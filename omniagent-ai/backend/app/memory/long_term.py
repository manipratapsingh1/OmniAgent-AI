from typing import List
from app.rag.retriever import retrieve, vector_store
from app.rag.embeddings import embed_texts
import structlog
import uuid

log = structlog.get_logger("long_term_memory")


async def remember(user_id: int, text: str) -> None:
    """Write long-term memory to persistent vector store (Chroma).
    Stores memories with metadata for later retrieval via semantic search."""
    try:
        if not text or not text.strip():
            log.warning("long_term_memory.empty_text", user_id=user_id)
            return
        
        # Generate embedding for the memory
        embeddings = await embed_texts([text])
        if not embeddings or not embeddings[0]:
            log.warning("long_term_memory.embedding_failed", user_id=user_id, text_length=len(text))
            return
        
        # Generate unique ID for this memory entry
        memory_id = str(uuid.uuid4())
        
        # Store in vector database with user metadata for filtering
        metadata = {
            "user_id": user_id,
            "memory_type": "long_term",
            "is_memory": True,
        }
        
        vector_store.add(
            ids=[memory_id],
            embeddings=embeddings,
            documents=[text],
            metadatas=[metadata],
        )
        
        log.info(
            "long_term_memory.stored",
            user_id=user_id,
            memory_id=memory_id,
            text_length=len(text),
        )
    
    except Exception as e:
        log.error(
            "long_term_memory.write_error",
            user_id=user_id,
            error=str(e),
            error_type=type(e).__name__,
        )


async def recall(user_id: int, query: str, k: int = 3) -> List[str]:
    """Retrieve long-term memories via semantic search.
    Queries the vector store and filters by user_id."""
    try:
        chunks = await retrieve(user_id=user_id, query=query, k=k)
        return [c["text"] for c in chunks]
    except Exception as e:
        log.error(
            "long_term_memory.recall_error",
            user_id=user_id,
            query=query,
            error=str(e),
        )
        return []