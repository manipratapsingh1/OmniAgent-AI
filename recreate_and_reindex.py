import asyncio
import os
import sys
from pathlib import Path
import structlog

# Load .env
from dotenv import load_dotenv
load_dotenv("omniagent-ai/backend/.env")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "omniagent-ai" / "backend"))

from app.db.session import get_session
from app.models.document import Document, DocumentChunk
from app.rag.embeddings import embed_texts
from app.rag.retriever import get_vector_store

log = structlog.get_logger("recreate_and_reindex")

async def run_reindexing():
    print("=" * 80)
    print("RECREATING CHROMA COLLECTIONS AND RE-INDEXING ALL SQL CHUNKS")
    print("=" * 80)
    
    # 1. Reset/Create collections in Cosine Space
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from app.config import get_settings
    
    settings = get_settings()
    print(f"Connecting to Chroma at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}...")
    
    client = chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    
    # Delete existing collections if they exist
    for coll_name in ["omniagent", "semantic_cache"]:
        try:
            client.delete_collection(coll_name)
            print(f"✓ Deleted existing collection: '{coll_name}'")
        except Exception as e:
            print(f"- Collection '{coll_name}' did not exist or could not be deleted: {e}")
            
    # Recreate collections with Cosine Similarity metadata
    print("Creating collections with Cosine Similarity space metadata...")
    collection = client.create_collection(
        "omniagent",
        metadata={"hnsw:space": "cosine"}
    )
    cache_collection = client.create_collection(
        "semantic_cache",
        metadata={"hnsw:space": "cosine"}
    )
    print("✓ Created 'omniagent' and 'semantic_cache' collections in Cosine similarity space.")
    
    # 2. Query all indexed documents and their chunks from SQL database
    db = get_session()
    try:
        from sqlmodel import select
        documents = db.exec(select(Document).where(Document.status == "indexed")).all()
        print(f"Found {len(documents)} indexed documents in SQL database.")
        
        total_reindexed_chunks = 0
        
        for doc in documents:
            print(f"\nProcessing Document ID={doc.id}, Name='{doc.filename}', UserID={doc.user_id}...")
            chunks = db.exec(select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index)).all()
            
            if not chunks:
                print(f"  ⚠ No chunks found in database for document {doc.id}. Skipping.")
                continue
                
            print(f"  - Found {len(chunks)} chunks to embed and index.")
            
            chunk_texts = [c.text for c in chunks]
            
            # Embed all chunks
            print("  - Generating embeddings (Ollama)...")
            try:
                embeddings = await embed_texts(chunk_texts)
            except Exception as e:
                print(f"  ✗ Failed to generate embeddings for document {doc.id}: {e}")
                continue
                
            if not embeddings or len(embeddings) != len(chunks):
                print(f"  ✗ Embeddings count mismatch for document {doc.id}!")
                continue
                
            # Prepare data for Chroma insertion
            ids = [f"{doc.id}-{c.chunk_index}" for c in chunks]
            metadatas = [
                {
                    "user_id": int(doc.user_id),
                    "document_id": int(doc.id),
                    "chunk_index": int(c.chunk_index),
                    "is_knowledge_base": bool(doc.is_knowledge_base),
                    "filename": str(doc.filename),
                }
                for c in chunks
            ]
            
            # Add to Chroma
            print("  - Storing vectors in Chroma 'omniagent' collection...")
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunk_texts,
                metadatas=metadatas
            )
            print(f"  ✓ Reindexed {len(chunks)} chunks successfully.")
            total_reindexed_chunks += len(chunks)
            
        print("\n" + "=" * 80)
        print(f"SUCCESS: Reindexing completed! Total Chunks Re-indexed: {total_reindexed_chunks}")
        print("=" * 80 + "\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_reindexing())
