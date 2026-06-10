import structlog
from sqlmodel import Session
from app.models.task import Task
from app.repositories.task_repo import TaskRepo
from app.schemas.task import TaskCreate

log = structlog.get_logger("tasks")


class TaskService:
    def __init__(self, db: Session):
        self.repo = TaskRepo(db)

    def create(self, user_id: int, data: TaskCreate) -> Task:
        tags = ",".join(data.tags) if data.tags else None
        t = Task(
            user_id=user_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            tags=tags
        )
        t = self.repo.add(t)
        log.info("task.created", user_id=user_id, task_id=t.id, priority=t.priority)
        return t

    def list(self, user_id: int):
        tasks = self.repo.for_user(user_id)
        log.info("task.list", user_id=user_id, count=len(tasks))
        return tasks

    def update_status(self, user_id: int, task_id: int, status: str) -> Task:
        t = self.repo.get(task_id)
        if not t or t.user_id != user_id:
            log.warning("task.update_status.access_denied", user_id=user_id, task_id=task_id)
            raise ValueError("Task not found")
        t.status = status
        t = self.repo.add(t)
        log.info("task.status_updated", task_id=task_id, status=status)
        return t

    def delete(self, user_id: int, task_id: int) -> bool:
        t = self.repo.get(task_id)
        if not t or t.user_id != user_id:
            log.warning("task.delete.access_denied", user_id=user_id, task_id=task_id)
            raise ValueError("Task not found")
        log.info("task.deleted", user_id=user_id, task_id=task_id)
        return self.repo.delete(task_id)

    def filter_by_tag(self, user_id: int, tag: str):
        """Get tasks by tag"""
        tasks = self.repo.for_user(user_id)
        return [t for t in tasks if t.tags and tag in t.tags.split(",")]

    def filter_by_priority(self, user_id: int, priority: int):
        """Get tasks by priority"""
        tasks = self.repo.for_user(user_id)
        return [t for t in tasks if t.priority == priority]