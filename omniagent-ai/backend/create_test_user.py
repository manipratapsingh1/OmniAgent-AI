#!/usr/bin/env python3
"""
Create a test user with known credentials
"""
import sys
sys.path.insert(0, '/c/Users/manip/OneDrive/Desktop/omniagent-ai-ar/omniagent-ai/backend')

from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.core.security import hash_password
from app.repositories.user_repo import UserRepo

session = get_session()
repo = UserRepo(session)

print("=" * 60)
print("CREATE TEST USER")
print("=" * 60)

# Check if test user exists
test_email = "test@omniagent.local"
existing_user = repo.by_email(test_email)

if existing_user:
    print(f"\n✗ User {test_email} already exists (ID: {existing_user.id})")
    print(f"  You can use:")
    print(f"  - Email: {test_email}")
    print(f"  - Password: TestPassword123")
else:
    # Create new test user
    test_password = "TestPassword123"
    new_user = User(
        email=test_email,
        hashed_password=hash_password(test_password),
        full_name="Test User",
        is_admin=False,
        is_active=True
    )
    repo.add(new_user)
    print(f"\n✓ Test user created!")
    print(f"  - Email: {test_email}")
    print(f"  - Password: {test_password}")
    print(f"  - ID: {new_user.id}")

print("\n" + "=" * 60)
