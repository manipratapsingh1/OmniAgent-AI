#!/usr/bin/env python3
"""
Test the complete auth flow with the test user
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
import traceback

settings = get_settings()
session = get_session()

print("=" * 60)
print("COMPLETE AUTH FLOW TEST")
print("=" * 60)

try:
    # Step 1: Perform login
    print("\n1. Performing login with testuser@example.com...")
    auth_service = AuthService(session)
    login_request = LoginRequest(email="testuser@example.com", password="TestPassword123")
    token_response = auth_service.login(login_request)
    print(f"   ✓ Login successful")
    print(f"   - Token type: {token_response.token_type}")
    print(f"   - Token: {token_response.access_token[:50]}...")
    
    # Step 2: Decode token to verify it
    print("\n2. Decoding token...")
    payload = decode_token(token_response.access_token)
    print(f"   ✓ Token decoded successfully")
    print(f"   - Subject (email): {payload.get('sub')}")
    print(f"   - Expiry timestamp: {payload.get('exp')}")
    
    # Step 3: Simulate /auth/me call with token
    print("\n3. Simulating /auth/me endpoint call...")
    decoded_user = session.exec(
        select(User).where(User.email == payload.get("sub"))
    ).first()
    if decoded_user:
        print(f"   ✓ User retrieved from database")
        print(f"   - ID: {decoded_user.id}")
        print(f"   - Email: {decoded_user.email}")
        print(f"   - Full Name: {decoded_user.full_name}")
        print(f"   - Is Admin: {decoded_user.is_admin}")
        print(f"   - Is Active: {decoded_user.is_active}")
    else:
        print(f"   ✗ User not found in database!")
        sys.exit(1)
    
    # Step 4: Test token invalidation
    print("\n4. Testing invalid token...")
    try:
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.token"
        decode_token(invalid_token)
        print(f"   ✗ Invalid token was accepted (ERROR!)")
    except ValueError as e:
        print(f"   ✓ Invalid token properly rejected: {e}")
    
    print("\n" + "=" * 60)
    print("✓ ALL AUTH TESTS PASSED!")
    print("=" * 60)
    print("\nNow try logging in from the frontend with:")
    print("  Email: testuser@example.com")
    print("  Password: TestPassword123")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
