from sqlmodel import Session, select

from app.models.task import Task
from app.repositories.base import BaseRepo


class TaskRepo(BaseRepo[Task]):
    def __init__(self, session: Session):
        super().__init__(Task, session)

    def for_user(self, user_id: int):
        """
        Return all tasks for one user, newest first.
        """
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
        )
        return self.session.exec(stmt).all()

    def get_by_id(self, task_id: int, user_id: int):
        """
        Get a task only if it belongs to the given user.
        """
        stmt = select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id,
        )
        return self.session.exec(stmt).first()

    def delete_by_id(self, task_id: int, user_id: int) -> bool:
        """
        Delete a task only if it belongs to the given user.
        """
        task = self.get_by_id(task_id, user_id)
        if not task:
            return False

        self.session.delete(task)
        self.session.commit()
        return True