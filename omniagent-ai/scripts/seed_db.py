"""Create an admin user for first-run convenience."""
from app.db.session import get_session
from app.repositories.user_repo import UserRepo
from app.models.user import User
from app.core.security import hash_password


def main():
    with get_session() as db:
        repo = UserRepo(db)
        if not repo.by_email("admin@omniagent.ai"):
            u = User(email="admin@omniagent.ai", hashed_password=hash_password("admin12345"),
                    full_name="Admin", is_admin=True)
            repo.add(u)
            print("Created admin@omniagent.ai / admin12345")
        else:
            print("Admin already exists.")


if __name__ == "__main__":
    main()