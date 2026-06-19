import asyncio
import os
import sys
from pathlib import Path

# Load .env
if "IS_E2E_TESTING" in os.environ:
    del os.environ["IS_E2E_TESTING"]
sys.path.insert(0, str(Path(__file__).parent / "omniagent-ai" / "backend"))

from app.db.session import get_session
from app.workers.jobs import ingest_document
from app.models.user import User

def reproduce():
    db = get_session()
    # Create or get user
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(email="test@example.com", username="testuser", hashed_password="pw")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    user_id = user.id
    
    # Create job
    from app.services.background_job_service import BackgroundJobService
    job = BackgroundJobService(db).create_job(user_id, "ingest_document")
    job_id = job.id
    db.close()
    
    print(f"Ingesting document for user {user_id} with job {job_id}...")
    res = ingest_document(user_id, "reproduce_test.txt", "text/plain", b"This is a reproduction test for document ingestion database errors.", job_id=job_id)
    print("Result:", res)
    if res.get("status") == "error":
        print("Traceback would be printed inside ingest_document, let's inspect the error:")

if __name__ == "__main__":
    try:
        reproduce()
    except Exception as e:
        import traceback
        traceback.print_exc()
