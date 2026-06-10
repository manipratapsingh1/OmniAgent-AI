#!/usr/bin/env python3
"""Test Chroma connection and diagnose Vector DB issues"""

import httpx
import json
from app.config import get_settings

settings = get_settings()

print(f"\n{'='*60}")
print("CHROMA CONNECTION DIAGNOSTIC")
print(f"{'='*60}\n")

print(f"Config:")
print(f"  CHROMA_HOST: {settings.CHROMA_HOST}")
print(f"  CHROMA_PORT: {settings.CHROMA_PORT}")
print(f"  Base URL: http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}\n")

# Test 1: Basic connectivity
print("TEST 1: Basic connectivity")
try:
    with httpx.Client(timeout=5) as client:
        response = client.get(f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/")
        print(f"  ✓ Connected (status: {response.status_code})")
except Exception as e:
    print(f"  ✗ Connection failed: {e}")
    print(f"  💡 Check if Chroma is running on port {settings.CHROMA_PORT}")

# Test 2: API v2 endpoint
print("\nTEST 2: API /api/v2 endpoint")
try:
    with httpx.Client(timeout=5) as client:
        response = client.get(f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v2/tenants/default_tenant")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✓ API responding correctly")
            print(f"  Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"  ⚠ Unexpected status code (expected 200)")
            print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"  ✗ API endpoint failed: {e}")

# Test 3: List collections
print("\nTEST 3: List collections")
try:
    with httpx.Client(timeout=5) as client:
        response = client.get(f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v1/collections")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            collections = response.json()
            print(f"  ✓ Found {len(collections) if isinstance(collections, list) else 'N/A'} collections")
            print(f"  Collections: {json.dumps(collections, indent=2)}")
        else:
            print(f"  ⚠ Unexpected status code: {response.status_code}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 4: Try Python client
print("\nTEST 4: Python Chroma client")
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    
    client = chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    
    # Try to get collections
    collections = client.list_collections()
    print(f"  ✓ Python client connected")
    print(f"  Collections: {len(collections)}")
    for coll in collections:
        print(f"    - {coll.name} ({coll.count()} vectors)")
    
    # Check omniagent collection
    try:
        coll = client.get_or_create_collection("omniagent")
        print(f"\n  ✓ omniagent collection exists/created")
        print(f"    Vectors: {coll.count()}")
    except Exception as e:
        print(f"  ✗ Could not access omniagent collection: {e}")
        
except Exception as e:
    print(f"  ✗ Python client failed: {e}")

print(f"\n{'='*60}\n")
