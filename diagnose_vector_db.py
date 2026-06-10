#!/usr/bin/env python3
"""Simple test to check if documents are in the database and if Chroma can be accessed"""

import sys
sys.path.insert(0, r'C:\Users\manip\OneDrive\Desktop\omniagent-ai-ar\omniagent-ai\backend')

from app.config import get_settings

settings = get_settings()

print("\n" + "="*70)
print("OMNIAGENT VECTOR DB DIAGNOSTIC")
print("="*70 + "\n")

print("1. CONFIGURATION CHECK")
print(f"   - CHROMA_HOST: {settings.CHROMA_HOST}")
print(f"   - CHROMA_PORT: {settings.CHROMA_PORT}")
print(f"   - DATABASE_URL: {settings.DATABASE_URL[:50]}..." if settings.DATABASE_URL else "   - DATABASE_URL: NOT SET")

# Check database for documents
print("\n2. DATABASE DOCUMENTS CHECK")
try:
    from sqlmodel import Session, create_engine, select
    from app.models.document import Document
    
    engine = create_engine(settings.DATABASE_URL, echo=False)
    with Session(engine) as session:
        docs = session.exec(select(Document)).all()
        print(f"   ✓ Connected to database")
        print(f"   - Total documents: {len(docs)}")
        
        if docs:
            print(f"\n   Documents:")
            for doc in docs[:5]:  # Show first 5
                print(f"      ID: {doc.id}, Name: {doc.filename}")
                print(f"         Status: {doc.status}, Embedding: {doc.embedding_status}")
                print(f"         Chunks: {doc.chunk_count}, Error: {doc.error_message or 'None'}")
        
        if len(docs) > 5:
            print(f"      ... and {len(docs) - 5} more")
            
except Exception as e:
    print(f"   ✗ Database error: {e}")
    import traceback
    traceback.print_exc()

# Check Chroma
print("\n3. CHROMA CONNECTION CHECK")
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    
    print(f"   Connecting to http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}...")
    client = chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    
    print(f"   ✓ Connected to Chroma")
    
    # List collections
    collections = client.list_collections()
    print(f"   - Collections: {len(collections)}")
    for coll in collections:
        print(f"      • {coll.name}: {coll.count()} vectors")
    
    # Check for omniagent collection
    if any(c.name == "omniagent" for c in collections):
        print(f"\n   ✓ 'omniagent' collection exists")
        coll = client.get_or_create_collection("omniagent")
        print(f"     Vector count: {coll.count()}")
    else:
        print(f"\n   ⚠ 'omniagent' collection NOT FOUND")
        print(f"     This is the issue! Vectors have not been stored.")
        
except ConnectionError as e:
    print(f"   ✗ CONNECTION REFUSED")
    print(f"     Error: {e}")
    print(f"     💡 Chroma server is not running or not reachable at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("DIAGNOSIS SUMMARY")
print("="*70)
print("""
If Chroma is not reachable:
  1. Chroma server is not running (see ERROR above)
  2. Need to start: chroma run --host 127.0.0.1 --port 8001
  
If omniagent collection doesn't exist:
  1. Documents were marked indexed but vectors not stored in Chroma
  2. Need to re-upload documents after Chroma is running
  3. Or check the ingestion logs for errors
  
If both are OK:
  1. Check if user_id filter is matching correctly
  2. Run a test query to debug retrieval
""")
print("="*70 + "\n")
