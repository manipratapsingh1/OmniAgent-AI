#!/usr/bin/env python3
"""
Check the actual password hash in the database
"""
import sys
sys.path.insert(0, '/c/Users/manip/OneDrive/Desktop/omniagent-ai-ar/omniagent-ai/backend')

from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.core.security import verify_password, hash_password

session = get_session()

print("=" * 60)
print("DATABASE PASSWORD CHECK")
print("=" * 60)

# Get the user
user = session.exec(select(User).where(User.email == "mani1@gmail.com")).first()
if user:
    print(f"\n✓ User found: {user.email}")
    print(f"  - ID: {user.id}")
    print(f"  - Hashed Password: {user.hashed_password[:50]}...")
    print(f"  - Password length: {len(user.hashed_password)}")
    
    # Test with different passwords
    test_passwords = [
        "Test@1234",
        "test@1234",
        "Password123",
        "password123",
        "Mani@1234",
        "omniagent"
    ]
    
    print(f"\n Testing password verification:")
    for pwd in test_passwords:
        try:
            result = verify_password(pwd, user.hashed_password)
            status = "✓ MATCH" if result else "✗ NO MATCH"
            print(f"  - {pwd}: {status}")
        except Exception as e:
            print(f"  - {pwd}: ERROR - {e}")
    
    # Try to hash a test password and see what it looks like
    print(f"\n Sample hash (for Test@1234): {hash_password('Test@1234')[:50]}...")
    
else:
    print(f"✗ User not found!")
