#!/usr/bin/env python3
"""Comprehensive diagnostics for Chat + Document integration issues"""

import sys
import asyncio
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import structlog
from sqlmodel import Session, select
from app.db.session import get_session, test_db_connection
from app.config import get_settings
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.rag.retriever import retrieve, query_vectors
from app.rag.embeddings import embed_texts

settings = get_settings()
log = structlog.get_logger()

print("\n" + "=" * 70)
print("CHAT + DOCUMENT INTEGRATION DIAGNOSTIC")
print("=" * 70 + "\n")

# 1. Check Database Connection
print("1. DATABASE CONNECTION")
print("-" * 70)
try:
    if test_db_connection():
        print("✓ Database connection: OK")
        db = get_session()
        print("✓ Session created: OK")
    else:
        print("✗ Database connection failed")
        sys.exit(1)
except Exception as e:
    print(f"✗ Database error: {e}")
    sys.exit(1)

# 2. Check Users
print("\n2. USERS IN DATABASE")
print("-" * 70)
try:
    users = db.exec(select(User)).all()
    if users:
        print(f"✓ Found {len(users)} users:")
        for u in users[:3]:
            print(f"  - ID {u.id}: {u.email}")
        if len(users) > 3:
            print(f"  ... and {len(users) - 3} more")
    else:
        print("✗ No users found in database")
        print("  💡 Create a user first before uploading documents")
except Exception as e:
    print(f"✗ Error fetching users: {e}")

# 3. Check Documents
print("\n3. DOCUMENTS IN DATABASE")
print("-" * 70)
try:
    docs = db.exec(select(Document).order_by(Document.created_at.desc())).all()
    if docs:
        print(f"✓ Found {len(docs)} documents:")
        for doc in docs[:3]:
            print(f"\n  Document ID {doc.id}:")
            print(f"    - Filename: {doc.filename}")
            print(f"    - User ID: {doc.user_id}")
            print(f"    - Status: {doc.status}")
            print(f"    - Embedding Status: {doc.embedding_status}")
            print(f"    - Chunk Count: {doc.chunk_count}")
            print(f"    - Size: {doc.size_bytes} bytes")
            if doc.error_message:
                print(f"    - Error: {doc.error_message}")
            
            # Check chunks
            chunks = db.exec(
                select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            ).all()
            print(f"    - Chunks in DB: {len(chunks)}")
            if chunks:
                print(f"      First chunk vector_id: {chunks[0].vector_id}")
    else:
        print("✗ No documents found in database")
        print("  💡 Upload a document first")
except Exception as e:
    print(f"✗ Error fetching documents: {e}")

# 4. Check Chroma Connection
print("\n4. CHROMA (VECTOR DATABASE) CONNECTION")
print("-" * 70)
try:
    print(f"Config: {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
    from app.rag.retriever import vector_store
    
    # Try to get the vector store (this will trigger connection attempt)
    store = vector_store._get_store()
    
    if store._initialized and store.collection:
        count = store.collection.count()
        print(f"✓ Chroma connection: OK")
        print(f"✓ Collection 'omniagent' exists with {count} vectors")
    else:
        print(f"✗ Chroma not initialized")
        print(f"  💡 Make sure Chroma server is running on {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
except Exception as e:
    print(f"✗ Chroma connection failed: {e}")
    print(f"  💡 Start Chroma: docker run -p 8000:8000 chromadb/chroma")

# 5. Check Embeddings Service (Ollama)
print("\n5. EMBEDDINGS SERVICE (OLLAMA) CONNECTION")
print("-" * 70)
try:
    from app.llm.ollama_client import ollama
    
    # Try to generate an embedding for a test query
    test_embedding = asyncio.run(embed_texts(["test"]))
    if test_embedding and len(test_embedding) > 0:
        print(f"✓ Ollama connection: OK")
        print(f"  Embedding dimension: {len(test_embedding[0])}")
    else:
        print(f"✗ Ollama returned empty embeddings")
except Exception as e:
    print(f"✗ Ollama connection failed: {e}")
    print(f"  💡 Make sure Ollama is running (default: http://localhost:11434)")

# 6. Test Full Retrieval Pipeline
print("\n6. FULL RETRIEVAL PIPELINE TEST")
print("-" * 70)
try:
    if docs:
        first_doc = docs[0]
        user_id = first_doc.user_id
        
        print(f"Using document: {first_doc.filename} (User ID: {user_id})")
        
        # Try retrieval
        test_query = "test"
        results = asyncio.run(retrieve(user_id=user_id, query=test_query, k=4))
        
        if results:
            print(f"✓ Retrieval successful: found {len(results)} chunks")
            for i, result in enumerate(results[:2]):
                print(f"  Result {i+1}: {result['text'][:100]}...")
        else:
            print(f"✗ Retrieval returned no results")
            print(f"  💡 Check that:")
            print(f"     - Documents are indexed in Chroma")
            print(f"     - Chunks are in DocumentChunk table")
            print(f"     - Metadata includes user_id: {user_id}")
    else:
        print("⊘ Cannot test retrieval - no documents in database")
except Exception as e:
    print(f"✗ Retrieval pipeline failed: {e}")
    import traceback
    traceback.print_exc()

# 7. Check Chat Service
print("\n7. CHAT SERVICE TEST")
print("-" * 70)
try:
    from app.services.chat_service import ChatService
    from app.schemas.chat import ChatRequest
    
    if docs and users:
        service = ChatService(db)
        user_id = users[0].id
        
        # Try to create a chat request
        req = ChatRequest(
            message="What is in the documents?",
            use_rag=True,
            model="llama3.2"
        )
        
        print(f"✓ Chat service initialized for user {user_id}")
        print(f"  Message: '{req.message}'")
        print(f"  Use RAG: {req.use_rag}")
        print(f"  Model: {req.model}")
        print("\n  💡 Chat service is ready - test via API endpoint")
    else:
        print("⊘ Cannot test chat service - need users and documents")
except Exception as e:
    print(f"✗ Chat service initialization failed: {e}")
    import traceback
    traceback.print_exc()

# 8. Summary and Recommendations
print("\n" + "=" * 70)
print("DIAGNOSTIC SUMMARY & NEXT STEPS")
print("=" * 70 + "\n")

issues = []

# Check database
try:
    if not test_db_connection():
        issues.append("❌ Database not responding")
except:
    issues.append("❌ Database connection issue")

# Check documents
try:
    doc_count = db.exec(select(Document)).first()
    if not doc_count:
        issues.append("⚠️  No documents uploaded - upload one to test")
except:
    issues.append("❌ Cannot read documents")

# Check Chroma
try:
    from app.rag.retriever import vector_store
    store = vector_store._get_store()
    if not store._initialized:
        issues.append("❌ Chroma not running - start it first")
except:
    issues.append("❌ Chroma connection issue")

# Check Ollama
try:
    test_vec = asyncio.run(embed_texts(["test"]))
    if not test_vec:
        issues.append("❌ Ollama embedding failed")
except:
    issues.append("❌ Ollama not running or not responding")

if not issues:
    print("✅ ALL SYSTEMS OPERATIONAL")
    print("\nIf chat is still not working:")
    print("  1. Check browser console for errors (F12)")
    print("  2. Check backend logs for exceptions")
    print("  3. Try uploading a new document")
    print("  4. Refresh the browser and try chatting")
else:
    print("⚠️  ISSUES FOUND:\n")
    for issue in issues:
        print(f"  {issue}")
    print("\n🔧 FIXES REQUIRED:")
    if "Chroma" in str(issues):
        print("  • Start Chroma: docker run -p 8000:8000 chromadb/chroma")
    if "Ollama" in str(issues):
        print("  • Start Ollama: ollama serve")
    if "Database" in str(issues):
        print("  • Check DATABASE_URL in .env")
        print("  • Ensure PostgreSQL is running")

print("\n" + "=" * 70 + "\n")

db.close()
