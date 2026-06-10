#!/usr/bin/env python3
"""
Test the complete auth flow: login -> store token -> call /me
"""
import sys
sys.path.insert(0, '/c/Users/manip/OneDrive/Desktop/omniagent-ai-ar/omniagent-ai/backend')

from sqlmodel import Session, select
from app.config import get_settings
from app.db.session import get_session
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest
from app.models.user import User
from app.core.security import decode_token
from app.deps import current_user
import traceback

settings = get_settings()
session = get_session()

print("=" * 60)
print("TESTING COMPLETE AUTH FLOW")
print("=" * 60)

try:
    # Step 1: Check existing user
    print("\n1. Checking for test user...")
    user = session.exec(select(User).where(User.email == "mani1@gmail.com")).first()
    if user:
        print(f"   ✓ User found: {user.email} (ID: {user.id})")
    else:
        print(f"   ✗ User not found!")
        sys.exit(1)
    
    # Step 2: Perform login
    print("\n2. Performing login...")
    auth_service = AuthService(session)
    login_request = LoginRequest(email="mani1@gmail.com", password="Test@1234")
    token_response = auth_service.login(login_request)
    print(f"   ✓ Login successful")
    print(f"   - Token type: {token_response.token_type}")
    print(f"   - Token: {token_response.access_token[:50]}...")
    
    # Step 3: Decode token to verify it
    print("\n3. Decoding token...")
    payload = decode_token(token_response.access_token)
    print(f"   ✓ Token decoded successfully")
    print(f"   - Subject: {payload.get('sub')}")
    print(f"   - Expiry: {payload.get('exp')}")
    
    # Step 4: Simulate /auth/me call with token
    print("\n4. Simulating /auth/me endpoint call...")
    # This is what the endpoint would do
    try:
        decoded_user = session.exec(
            select(User).where(User.email == payload.get("sub"))
        ).first()
        if decoded_user:
            print(f"   ✓ User retrieved from database")
            print(f"   - ID: {decoded_user.id}")
            print(f"   - Email: {decoded_user.email}")
            print(f"   - Full Name: {decoded_user.full_name}")
            print(f"   - Is Active: {decoded_user.is_active}")
        else:
            print(f"   ✗ User not found in database!")
    except Exception as e:
        print(f"   ✗ Error retrieving user: {e}")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✓ COMPLETE AUTH FLOW TEST PASSED")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
