#!/usr/bin/env python3
"""
List all users in the database
"""
import sys
sys.path.insert(0, '/c/Users/manip/OneDrive/Desktop/omniagent-ai-ar/omniagent-ai/backend')

from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User

session = get_session()

print("=" * 60)
print("ALL USERS IN DATABASE")
print("=" * 60)

users = session.exec(select(User)).all()
for i, user in enumerate(users, 1):
    print(f"\n{i}. {user.email}")
    print(f"   - ID: {user.id}")
    print(f"   - Full Name: {user.full_name}")
    print(f"   - Is Admin: {user.is_admin}")
    print(f"   - Is Active: {user.is_active}")
    print(f"   - Hash: {user.hashed_password[:40]}...")

print(f"\nTotal users: {len(users)}")
