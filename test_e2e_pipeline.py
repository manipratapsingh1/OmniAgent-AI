"""
End-to-end test for upload-to-answer RAG pipeline.
Tests: document upload → embedding → vector storage → retrieval → chat
"""

import asyncio
import sys
import json
import os
from pathlib import Path

# Set E2E testing flag
os.environ["IS_E2E_TESTING"] = "true"

# Add backend to path
backend_path = Path(__file__).parent / "omniagent-ai" / "backend"
sys.path.insert(0, str(backend_path))

import structlog
from sqlmodel import create_engine, Session, SQLModel
from app.config import get_settings
from app.models.document import Document
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.document_service import DocumentService
from app.services.fast_chat_service import FastChatService
from app.schemas.chat import ChatRequest
from app.rag.retriever import retrieve

log = structlog.get_logger("e2e_test")

settings = get_settings()


async def test_e2e_pipeline():
    """Complete test of upload → embedding → retrieval → chat"""
    
    print("\n" + "=" * 80)
    print("END-TO-END RAG PIPELINE TEST")
    print("=" * 80 + "\n")
    
    # Setup database
    engine = create_engine(settings.DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as db:
        try:
            # Step 1: Create test user
            print("STEP 1: Creating test user...")
            user = db.query(User).filter(User.email == "test@example.com").first()
            if not user:
                user = User(
                    email="test@example.com",
                    hashed_password="test123",
                    username="testuser",
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            print(f"✓ User created: ID={user.id}, email={user.email}\n")
            
            # Clean up previous data for this test user to keep the test fast and clean
            print("Cleaning up previous data for test user...")
            from app.models.document import DocumentChunk
            from app.models.knowledge import StudyMaterial
            
            # Delete from SQL
            db.query(Message).filter(Message.conversation_id.in_(
                db.query(Conversation.id).filter(Conversation.user_id == user.id)
            )).delete(synchronize_session=False)
            db.query(Conversation).filter(Conversation.user_id == user.id).delete(synchronize_session=False)
            db.query(StudyMaterial).filter(StudyMaterial.user_id == user.id).delete(synchronize_session=False)
            db.query(DocumentChunk).filter(DocumentChunk.document_id.in_(
                db.query(Document.id).filter(Document.user_id == user.id)
            )).delete(synchronize_session=False)
            db.query(Document).filter(Document.user_id == user.id).delete(synchronize_session=False)
            db.commit()
            
            # Delete from Chroma
            try:
                from app.rag.retriever import vector_store
                store = vector_store._get_store()
                if store and store.collection:
                    store.collection.delete(where={"user_id": user.id})
                    print("✓ Cleaned up vector database for user ID")
            except Exception as e:
                print(f"Warning: could not clean vector database: {e}")
            print("Cleanup complete.\n")
            
            # Step 2: Upload a test document
            print("STEP 2: Uploading test document...")
            doc_service = DocumentService(db)
            
            # Create a test PDF-like content
            test_content = b"""# Test Document: Machine Learning Guide

## Introduction
Machine learning is a subset of artificial intelligence. It enables systems to learn and improve from experience without being explicitly programmed.

## Key Concepts
1. Supervised Learning: Learning with labeled data
2. Unsupervised Learning: Learning from unlabeled data
3. Reinforcement Learning: Learning through interactions

## Applications
Machine learning is used in:
- Computer Vision
- Natural Language Processing
- Recommendation Systems
- Fraud Detection
- Autonomous Vehicles

## Popular Algorithms
- Linear Regression
- Decision Trees
- Random Forests
- Neural Networks
- Support Vector Machines

## Future Trends
The future of machine learning includes:
- Explainable AI
- Edge Computing
- Federated Learning
- Quantum Machine Learning

Conclusion: Machine learning continues to evolve and transform industries."""

            doc = await doc_service.upload(
                user_id=user.id,
                filename="test_ml_guide.txt",
                mime_type="text/plain",
                raw=test_content,
            )
            
            print(f"✓ Document uploaded: ID={doc.id}, filename={doc.filename}")
            print(f"  Status: {doc.status}")
            print(f"  Chunks: {doc.chunk_count}")
            print(f"  Embeddings: {doc.embedding_status}\n")
            
            if doc.status != "indexed":
                print(f"✗ ERROR: Document not indexed! Status: {doc.status}")
                print(f"  Error message: {doc.error_message}")
                return False
            
            if doc.chunk_count == 0:
                print(f"✗ ERROR: No chunks created!")
                return False
            
            # Step 3: Verify embeddings
            print("STEP 3: Verifying embeddings...")
            if doc.embedding_status != "embedded":
                print(f"✗ ERROR: Embeddings not generated! Status: {doc.embedding_status}")
                return False
            
            print(f"✓ Embeddings generated: {doc.chunk_count} vectors\n")
            
            # Step 4: Test retrieval
            print("STEP 4: Testing document retrieval...")
            
            test_queries = [
                "What is machine learning?",
                "What are the applications of machine learning?",
                "Tell me about neural networks",
                "What is supervised learning?",
            ]
            
            for query in test_queries:
                results = await retrieve(user_id=user.id, query=query, k=3)
                print(f"\n  Query: '{query}'")
                print(f"  Results: {len(results)} chunks")
                
                if results:
                    for i, result in enumerate(results, 1):
                        print(f"    {i}. [doc:{result['document_id']}#{result['chunk_index']}] "
                              f"Score: {result['score']:.3f}")
                        print(f"       Text: {result['text'][:100]}...")
                else:
                    print(f"  ✗ No results for query!")
                    return False
            
            print("\n✓ Retrieval working!\n")
            
            # Step 5: Test chat with RAG
            print("STEP 5: Testing chat with document context...")
            
            # Create conversation
            conv = Conversation(user_id=user.id, model="phi3:mini")
            db.add(conv)
            db.commit()
            db.refresh(conv)
            print(f"✓ Conversation created: ID={conv.id}\n")
            
            # Send chat messages
            chat_queries = [
                "What is machine learning?",
                "List the applications mentioned",
            ]
            
            chat_service = FastChatService(db)
            
            for chat_query in chat_queries:
                print(f"\n  Sending: '{chat_query}'")
                
                req = ChatRequest(
                    conversation_id=conv.id,
                    message=chat_query,
                    use_rag=True,
                    model="phi3:mini",
                )
                
                response = await chat_service.chat(user.id, req)
                
                print(f"  Response: {response.content[:200]}...")
                print(f"  Sources: {len(response.sources)}")
                
                for src in response.sources:
                    print(f"    - [doc:{src.document_id}#{src.chunk_index}]")
                    print(f"      {src.snippet[:100]}...")
            
            print("\n✓ Chat with RAG working!\n")
            
            # Step 6: Verify database state
            print("STEP 6: Verifying database state...")
            
            messages = db.query(Message).filter(Message.conversation_id == conv.id).all()
            print(f"✓ Messages in conversation: {len(messages)}")
            
            for msg in messages:
                sources_list = []
                if msg.sources:
                    try:
                        sources_list = json.loads(msg.sources)
                    except:
                        pass
                print(f"  - {msg.role}: {msg.content[:50]}... (sources: {len(sources_list)})")
            
            print("\n" + "=" * 80)
            print("✓ ALL TESTS PASSED!")
            print("=" * 80 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n✗ TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(test_e2e_pipeline())
    sys.exit(0 if success else 1)
