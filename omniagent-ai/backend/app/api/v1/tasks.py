from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List
from pydantic import BaseModel

from app.deps import db_session, current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskOut
from app.services.task_service import TaskService

router = APIRouter()


class BulkDeleteRequest(BaseModel):
    task_ids: List[int] = []


class TaskStatsResponse(BaseModel):
    total: int
    completed: int
    in_progress: int
    pending: int
    failed: int
    completion_rate: float


def _to_task_out(task) -> TaskOut:
    """
    Safe converter for SQLModel/Pydantic task objects.
    """
    try:
        return TaskOut.model_validate(task)
    except Exception:
        return TaskOut(**task.model_dump())


@router.post("/", response_model=TaskOut)
def create(
    data: TaskCreate,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    task = TaskService(db).create(user.id, data)
    return _to_task_out(task)


@router.get("/", response_model=List[TaskOut])
def list_tasks(
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    tasks = TaskService(db).list(user.id)
    return [_to_task_out(t) for t in tasks]


@router.get("/stats", response_model=TaskStatsResponse)
def get_stats(
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    tasks = TaskService(db).list(user.id)

    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "done")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    pending = sum(1 for t in tasks if t.status == "pending")
    failed = sum(1 for t in tasks if t.status == "failed")

    completion_rate = (completed / total * 100) if total > 0 else 0.0

    return TaskStatsResponse(
        total=total,
        completed=completed,
        in_progress=in_progress,
        pending=pending,
        failed=failed,
        completion_rate=completion_rate,
    )


@router.get("/filter/by-tag", response_model=List[TaskOut])
def filter_by_tag(
    tag: str = Query(..., min_length=1, max_length=50),
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    tasks = TaskService(db).filter_by_tag(user.id, tag)
    return [_to_task_out(t) for t in tasks]


@router.get("/filter/by-priority", response_model=List[TaskOut])
def filter_by_priority(
    priority: int = Query(..., ge=1, le=5),
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    tasks = TaskService(db).filter_by_priority(user.id, priority)
    return [_to_task_out(t) for t in tasks]


@router.patch("/{task_id}/status", response_model=TaskOut)
def update_status(
    task_id: int,
    status: str,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    try:
        task = TaskService(db).update_status(user.id, task_id, status)
        return _to_task_out(task)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    try:
        TaskService(db).delete(user.id, task_id)
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bulk/delete")
def bulk_delete_tasks(
    req: BulkDeleteRequest,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
):
    if len(req.task_ids) > 100:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete more than 100 tasks at once",
        )

    service = TaskService(db)
    deleted = 0
    failed = 0

    for task_id in req.task_ids:
        try:
            service.delete(user.id, task_id)
            deleted += 1
        except ValueError:
            failed += 1

    return {"deleted": deleted, "failed": failed, "total": len(req.task_ids)}