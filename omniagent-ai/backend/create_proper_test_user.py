#!/usr/bin/env python3
"""
Create a test user with proper email
"""
import sys
sys.path.insert(0, '/c/Users/manip/OneDrive/Desktop/omniagent-ai-ar/omniagent-ai/backend')

from app.db.session import get_session
from app.models.user import User
from app.core.security import hash_password
from app.repositories.user_repo import UserRepo

session = get_session()
repo = UserRepo(session)

test_email = "testuser@example.com"
existing = repo.by_email(test_email)

if existing:
    print(f"User {test_email} already exists (ID: {existing.id})")
else:
    test_password = "TestPassword123"
    new_user = User(
        email=test_email,
        hashed_password=hash_password(test_password),
        full_name="Test User",
        is_admin=False,
        is_active=True
    )
    repo.add(new_user)
    print(f"✓ Created user: {test_email}")
    print(f"  Password: {test_password}")
