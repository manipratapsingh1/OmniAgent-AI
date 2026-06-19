
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv("omniagent-ai/backend/.env")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "omniagent-ai" / "backend"))

from app.rag.ingest import ingest_file
from app.db.session import Session, engine

async def test_ingest_standalone():
    print("Testing Ingest Standalone...")
    content = b"OmniAgent is the best AI OS."
    filename = "test_standalone.txt"
    user_id = 1
    doc_id = 999 # dummy
    
    try:
        print("Calling ingest_file...")
        n_chunks, n_vectors, vector_ids, chunk_texts = await ingest_file(
            user_id, doc_id, filename, content
        )
        print(f"Result: {n_chunks} chunks, {n_vectors} vectors")
    except Exception as e:
        print(f"Error during ingestion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ingest_standalone())
