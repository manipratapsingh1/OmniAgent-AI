
import asyncio
import os
import sys
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Load .env
load_dotenv("omniagent-ai/backend/.env")

BASE_URL = "http://localhost:8000/api/v1"
TEST_FILES_DIR = Path("test_files")
TEST_FILES_DIR.mkdir(exist_ok=True)

def create_test_files():
    print("Creating test files...")
    # TXT
    (TEST_FILES_DIR / "test.txt").write_text("OmniAgent is a next-generation AI Operating System.")
    
    # CSV
    (TEST_FILES_DIR / "test.csv").write_text("name,feature\nOmniAgent,RAG\nOmniAgent,Multi-Agent")
    
    # DOCX
    try:
        from docx import Document
        doc = Document()
        doc.add_paragraph("OmniAgent supports document intelligence.")
        doc.save(TEST_FILES_DIR / "test.docx")
    except ImportError:
        print("python-docx not installed, skipping DOCX creation")

    # XLSX
    try:
        import pandas as pd
        df = pd.DataFrame({"Project": ["OmniAgent"], "Status": ["Production-Ready"]})
        df.to_excel(TEST_FILES_DIR / "test.xlsx", index=False)
    except ImportError:
        print("pandas/openpyxl not installed, skipping XLSX creation")

    # Image (Blank with text)
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (200, 60), color = (73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((10,10), "OmniAgent OCR Test", fill=(255,255,0))
        img.save(TEST_FILES_DIR / "test.png")
    except ImportError:
        print("Pillow not installed, skipping PNG creation")

async def test_upload_pipeline(file_path: Path, token: str):
    print(f"\nTesting pipeline for: {file_path.name}")
    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Upload
        print("  - Uploading...")
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            resp = await client.post(f"{BASE_URL}/documents/upload", files=files, headers=headers)
        
        if resp.status_code != 200:
            print(f"  FAILURE: Upload failed: {resp.status_code} {resp.text}")
            return False
        
        doc_id = resp.json().get("id")
        print(f"  SUCCESS: Uploaded (ID: {doc_id})")
        
        # 2. Wait for processing (Polling)
        print("  - Processing (waiting for indexing)...")
        for _ in range(60): # Increase to 120 seconds
            resp = await client.get(f"{BASE_URL}/documents/{doc_id}", headers=headers)
            status = resp.json().get("status")
            if status == "indexed":
                print("  SUCCESS: Indexed")
                break
            if status == "failed":
                print(f"  FAILURE: Indexing failed: {resp.json().get('error_message')}")
                return False
            await asyncio.sleep(2)
        else:
            print("  FAILURE: Indexing timed out")
            return False
        
        # 3. Retrieval & QA
        print("  - Testing Retrieval & QA...")
        query = "What is this document about?"
        chat_req = {
            "message": query,
            "use_rag": True,
            "conversation_id": None,
            "model": "llama3.2"
        }
        resp = await client.post(f"{BASE_URL}/chat/", json=chat_req, headers=headers)
        
        if resp.status_code != 200:
            print(f"  FAILURE: Chat failed: {resp.status_code} {resp.text}")
            return False
        
        answer = resp.json().get("content")
        sources = resp.json().get("sources", [])
        
        if sources:
            print(f"  SUCCESS: Answer: {answer[:100]}...")
            print(f"  SUCCESS: Sources cited: {len(sources)}")
            return True
        else:
            print(f"  FAILURE: No sources cited. Retrieval might have failed.")
            return False

async def get_token():
    async with httpx.AsyncClient() as client:
        # Assuming admin@example.com / admin123 exists from init_db
        resp = await client.post(f"{BASE_URL}/auth/login", json={"email": "admin@example.com", "password": "admin123"})
        if resp.status_code == 200:
            return resp.json().get("access_token")
        else:
            print(f"Login failed: {resp.status_code} {resp.text}")
        return None

async def main():
    create_test_files()
    token = await get_token()
    if not token:
        print("Could not get auth token. Ensure backend is running and db is initialized.")
        return

    results = []
    for f in TEST_FILES_DIR.glob("*"):
        res = await test_upload_pipeline(f, token)
        results.append((f.name, res))
    
    print("\n" + "="*30)
    print("PHASE 2 VALIDATION SUMMARY")
    print("="*30)
    for name, res in results:
        print(f"{name:20}: {'PASS' if res else 'FAIL'}")

if __name__ == "__main__":
    asyncio.run(main())
