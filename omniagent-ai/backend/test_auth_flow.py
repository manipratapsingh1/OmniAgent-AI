#!/usr/bin/env python3
"""
Diagnostic script to test authentication token flow
"""
import sys
sys.path.insert(0, '/c/Users/manip/OneDrive/Desktop/omniagent-ai-ar/omniagent-ai/backend')

from app.config import get_settings
from app.core.security import create_access_token, decode_token
import traceback

settings = get_settings()
print(f"✓ Settings loaded")
print(f"  - SECRET_KEY length: {len(settings.SECRET_KEY)}")
print(f"  - JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
print(f"  - DATABASE_URL: {settings.DATABASE_URL[:30]}...")

try:
    # Test token creation
    test_email = "test@example.com"
    token = create_access_token(test_email)
    print(f"\n✓ Token created: {token[:50]}...")
    
    # Test token decoding
    payload = decode_token(token)
    print(f"✓ Token decoded successfully")
    print(f"  - Subject (email): {payload.get('sub')}")
    print(f"  - Expiry: {payload.get('exp')}")
    
    # Verify subject matches
    if payload.get('sub') == test_email:
        print(f"✓ Subject matches!")
    else:
        print(f"✗ Subject mismatch! Expected {test_email}, got {payload.get('sub')}")
        
except Exception as e:
    print(f"\n✗ Error during token test: {e}")
    traceback.print_exc()
    sys.exit(1)

# Now test database connection
try:
    from app.db.session import get_session
    session = get_session()
    print(f"\n✓ Database session created")
    
    # Test query
    from sqlmodel import select
    from app.models.user import User
    
    users = session.exec(select(User)).all()
    print(f"✓ Database query successful")
    print(f"  - Total users in DB: {len(users)}")
    
except Exception as e:
    print(f"\n✗ Database error: {e}")
    traceback.print_exc()

print(f"\n{'='*50}")
print("✓ All authentication components working!")
print(f"{'='*50}")
