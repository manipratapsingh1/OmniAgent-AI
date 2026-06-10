#!/usr/bin/env python3
"""
Diagnostic script to test document upload and retrieval flow.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.config import get_settings
from app.db.session import get_session_sync
from app.models.document import Document, DocumentChunk
from app.rag.retriever import retrieve, vector_store
from app.repositories.document_repo import DocumentRepo


async def main():
    print("=" * 60)
    print("DOCUMENT RETRIEVAL DIAGNOSTIC")
    print("=" * 60)
    
    # Get settings
    settings = get_settings()
    print(f"\n✓ Settings loaded")
    print(f"  DATABASE_URL: {settings.DATABASE_URL[:50]}...")
    print(f"  CHROMA_HOST: {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
    
    # Connect to database
    try:
        db = get_session_sync()
        print(f"✓ Database connection: OK")
    except Exception as e:
        print(f"✗ Database connection FAILED: {e}")
        return
    
    # Check documents in database
    try:
        repo = DocumentRepo(db)
        all_docs = db.query(Document).all()
        print(f"\n✓ Documents in database: {len(all_docs)}")
        for doc in all_docs[:5]:
            print(f"  - {doc.id}: {doc.filename} (status={doc.status}, embedding_status={doc.embedding_status}, chunks={doc.chunk_count})")
    except Exception as e:
        print(f"✗ Failed to list documents: {e}")
        return
    
    if not all_docs:
        print("\n⚠️ NO DOCUMENTS FOUND IN DATABASE - Upload a document first!")
        return
    
    # Check chunks in database
    try:
        chunks = db.query(DocumentChunk).all()
        print(f"\n✓ DocumentChunks in database: {len(chunks)}")
        if chunks:
            print(f"  - First chunk: doc_id={chunks[0].document_id}, index={chunks[0].chunk_index}, vector_id={chunks[0].vector_id}")
    except Exception as e:
        print(f"✗ Failed to list chunks: {e}")
    
    # Check Chroma connection
    try:
        print(f"\n✓ Testing Chroma connection...")
        vs = vector_store._get_store()
        count = vs.collection.count()
        print(f"  - Vectors in Chroma: {count}")
    except Exception as e:
        print(f"✗ Chroma connection FAILED: {e}")
        print(f"  Make sure Chroma is running on {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
        return
    
    # Test retrieval
    try:
        print(f"\n✓ Testing retrieval with use_rag=True...")
        # Get first document's user_id
        if all_docs:
            user_id = all_docs[0].user_id
            print(f"  - Using user_id: {user_id}")
            
            # Try to retrieve
            results = await retrieve(user_id=user_id, query="document content", k=4)
            print(f"  - Retrieval results: {len(results)} chunks found")
            for r in results[:3]:
                print(f"    * doc_id={r.get('document_id')}, chunk={r.get('chunk_index')}, text={r.get('text')[:60]}...")
    except Exception as e:
        print(f"✗ Retrieval FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
