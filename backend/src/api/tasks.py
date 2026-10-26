from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session
from src.api.auth import get_current_user
from src.lib.database import get_session
from src.models.user import User
from src.services.task_service import VALID_PRIORITIES, VALID_STATUSES, TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


# Schemas
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None


class TaskResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    current_user: Optional[User] = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """List all tasks for current user with optional filters."""
    if current_user is None:
        return []
    service = TaskService(user_id=current_user.id)

    # Validate filters
    if status and status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if priority and priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")
    if sort_by not in ["created_at", "priority"]:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by: {sort_by}")

    tasks = service.get_all(
        session=session,
        search=search,
        status=status,
        priority=priority,
        sort_by=sort_by,
    )
    return [
        TaskResponse(
            id=t.id,
            owner_id=t.owner_id,
            title=t.title,
            description=t.description,
            status=t.status,
            priority=t.priority,
            due_date=t.due_date.isoformat() if t.due_date else None,
            tags=[tag.name for tag in t.tags] if t.tags else [],
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat(),
        )
        for t in tasks
    ]


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    current_user: Optional[User] = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a new task for current user."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    service = TaskService(user_id=current_user.id)
    try:
        created = service.create(
            session=session,
            title=task.title,
            description=task.description,
            priority=task.priority,
            due_date=task.due_date,
            tags=task.tags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskResponse(
        id=created.id,
        owner_id=created.owner_id,
        title=created.title,
        description=created.description,
        status=created.status,
        priority=created.priority,
        due_date=created.due_date.isoformat() if created.due_date else None,
        tags=[tag.name for tag in created.tags] if created.tags else [],
        created_at=created.created_at.isoformat(),
        updated_at=created.updated_at.isoformat(),
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: Optional[User] = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get a single task by ID."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    service = TaskService(user_id=current_user.id)
    task = service.get_by_id(task_id, session=session)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(
        id=task.id,
        owner_id=task.owner_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        tags=[tag.name for tag in task.tags] if task.tags else [],
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    current_user: Optional[User] = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Update an existing task (last write wins, user-scoped)."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    service = TaskService(user_id=current_user.id)
    try:
        updated = service.update(
            task_id=task_id,
            session=session,
            title=task_update.title,
            description=task_update.description,
            status=task_update.status,
            priority=task_update.priority,
            due_date=task_update.due_date,
            tags=task_update.tags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(
        id=updated.id,
        owner_id=updated.owner_id,
        title=updated.title,
        description=updated.description,
        status=updated.status,
        priority=updated.priority,
        due_date=updated.due_date.isoformat() if updated.due_date else None,
        tags=[tag.name for tag in updated.tags] if updated.tags else [],
        created_at=updated.created_at.isoformat(),
        updated_at=updated.updated_at.isoformat(),
    )


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    current_user: Optional[User] = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Permanently delete a task."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    service = TaskService(user_id=current_user.id)
    success = service.delete(task_id, session=session)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
