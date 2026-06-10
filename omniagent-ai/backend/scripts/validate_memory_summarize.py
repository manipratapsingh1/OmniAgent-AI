"""Quick validator for POST /api/v1/memory/summarize

Creates a test user, conversation and messages, patches AI/embed/vector-store
to avoid external calls, invokes the endpoint, and prints results.
"""
import os
import asyncio
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./validate_memory.db")

from app.main import app
from app.db.session import get_session
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.memory import MemoryEntry


class DummyVectorStore:
    def __init__(self):
        self.added = []

    def add(self, ids, embeddings, documents, metadatas):
        print("DummyVectorStore.add called", ids, len(embeddings[0]) if embeddings else 0)
        self.added.append({"ids": ids, "embeddings": embeddings, "documents": documents, "metadatas": metadatas})


async def _async_return(val):
    return val


def run():
    # Patch AIService.generate and embeddings + vector_store
    from app.services.ai.service import AIService
    from app.rag import embeddings as rag_embeddings
    from app.rag import retriever as rag_retriever

    async def fake_generate(self, *args, **kwargs):
        return "Test summary of the conversation: user prefers compact answers and scheduling preferences."

    async def fake_embed_texts(texts):
        # return a simple low-dim embedding
        return [[0.1, 0.2, 0.3] for _ in texts]

    AIService.generate = fake_generate
    rag_embeddings.embed_texts = fake_embed_texts
    dummy_store = DummyVectorStore()
    rag_retriever.vector_store = dummy_store

    # Use TestClient to ensure app startup (init_db) runs
    with TestClient(app) as client:
        # Create test data using DB session
        session = get_session()
        try:
            user = User(email="validate@example.com", hashed_password="x")
            session.add(user)
            session.commit()
            session.refresh(user)

            conv = Conversation(user_id=user.id, title="Validation Conv")
            session.add(conv)
            session.commit()
            session.refresh(conv)

            msgs = [
                Message(conversation_id=conv.id, role="user", content="I like concise answers."),
                Message(conversation_id=conv.id, role="assistant", content="Noted. I will keep replies short."),
                Message(conversation_id=conv.id, role="user", content="Also prefer meetings in the morning."),
            ]
            for m in msgs:
                session.add(m)
            session.commit()

            # Override current_user dependency to return our test user
            from app.deps import current_user as current_user_dep
            app.dependency_overrides[current_user_dep] = lambda: user

            # Call summarize endpoint
            resp = client.post("/api/v1/memory/summarize", json={"conversation_id": conv.id, "memory_type": "long_term"})
            print("Response status:", resp.status_code)
            print(resp.json())

            # Check DB for MemoryEntry
            # Use ORM query
            mems = session.query(MemoryEntry).filter(MemoryEntry.user_id == user.id).all()
            print("Memory entries in DB:", len(mems))
            for e in mems:
                print(e.id, e.memory_type, (e.content or '')[:120])

            # Check vector store dummy
            print("Vector store added count:", len(dummy_store.added))
        finally:
            session.close()


if __name__ == "__main__":
    run()
