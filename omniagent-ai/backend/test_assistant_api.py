#!/usr/bin/env python3
"""Test script for AI Assistant API."""
import asyncio
import httpx
import json

async def login():
    """Login and get access token."""
    print("\n=== Logging In ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123"
            },
            timeout=10.0
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            print(response.text)
            raise Exception("Failed to login")
        
        data = response.json()
        token = data["access_token"]
        print(f"✓ Login successful: {token[:20]}...")
        return token

async def test_chat_non_streaming(token):
    """Test non-streaming chat endpoint."""
    print("\n=== Testing Non-Streaming Chat ===")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/assistant/chat",
                json={"message": "Hello, what is 2+2?"},
                headers=headers,
                timeout=30.0
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

async def test_chat_streaming(token):
    """Test streaming chat endpoint."""
    print("\n=== Testing Streaming Chat ===")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "POST",
                "http://localhost:8000/api/v1/assistant/chat",
                json={"message": "Tell me a short joke", "stream": True},
                headers=headers,
                timeout=30.0
            ) as response:
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print("Streaming chunks:")
                    full_response = ""
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            chunk_text = data['data']['text']
                            print(f"  {chunk_text!r}", end="", flush=True)
                            full_response += chunk_text
                    print("\n")
                    print(f"Full response: {full_response}")
                else:
                    print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

async def main():
    print("🚀 AI Assistant API Tests")
    try:
        token = await login()
        await test_chat_non_streaming(token)
        await test_chat_streaming(token)
        print("\n✓ Tests completed")
    except Exception as e:
        print(f"\n✗ Tests failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

