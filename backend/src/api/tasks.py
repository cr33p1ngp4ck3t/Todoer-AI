from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session
from src.api.auth import get_current_user
from src.lib.database import get_session
from src.models.task import Task
from src.models.user import User
from src.services.task_service import (
    VALID_PRIORITIES,
    VALID_SORTS,
    VALID_STATUSES,
    TaskService,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    priority: str = "medium"
    due_date: datetime | None = None
    tags: list[str] | None = Field(default=None, max_length=50)
    project_id: UUID | None = None
    assignee_id: UUID | None = None
    recurrence: str | None = None
    recurrence_timezone: str = "UTC"


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    status: str | None = None
    priority: str | None = None
    due_date: datetime | None = None
    tags: list[str] | None = Field(default=None, max_length=50)
    assignee_id: UUID | None = None
    recurrence: str | None = None
    recurrence_timezone: str | None = None


class TaskResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    description: str | None
    status: str
    priority: str
    due_date: str | None
    tags: list[str]
    project_id: UUID | None
    assignee_id: UUID | None
    recurrence: str | None
    recurrence_timezone: str
    created_at: str
    updated_at: str


def task_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        owner_id=task.owner_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        tags=[tag.name for tag in task.tags],
        project_id=task.project_id,
        assignee_id=task.assignee_id,
        recurrence=task.recurrence,
        recurrence_timezone=task.recurrence_timezone,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


class BackupTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    status: Literal["pending", "completed"] = "pending"
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: datetime | None = None
    tags: list[str] = Field(default_factory=list, max_length=50)
    recurrence: Literal["daily", "weekly", "monthly"] | None = None
    recurrence_timezone: str = "UTC"
    recurrence_day: int | None = Field(default=None, ge=1, le=31)
    recurrence_spawned: bool = False


class TaskBackup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1]
    tasks: list[BackupTask] = Field(max_length=1000)


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    search: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    sort_by: str = "created_at",
    project_id: UUID | None = None,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if status and status not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status: {status}")
    if priority and priority not in VALID_PRIORITIES:
        raise HTTPException(400, f"Invalid priority: {priority}")
    if sort_by not in VALID_SORTS:
        raise HTTPException(400, f"Invalid sort_by: {sort_by}")
    return [
        task_response(task)
        for task in TaskService(user.id).get_all(
            session, search, status, priority, sort_by, project_id
        )
    ]


@router.get("/export", response_model=TaskBackup)
def export_tasks(
    user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    tasks = TaskService(user.id).get_all(session)
    # shortcut: backups support 1000 tasks; use streamed batches for larger workspaces.
    if len(tasks) > 1000:
        raise HTTPException(400, "Export supports up to 1000 personal tasks")
    return {
        "version": 1,
        "tasks": [
            BackupTask(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                due_date=task.due_date,
                tags=[tag.name for tag in task.tags],
                recurrence=task.recurrence,
                recurrence_timezone=task.recurrence_timezone,
                recurrence_day=task.recurrence_day,
                recurrence_spawned=task.recurrence_spawned,
            )
            for task in tasks
        ],
    }


@router.post("/import")
def import_tasks(
    payload: TaskBackup,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        return TaskService(user.id).import_tasks(session, payload.tasks)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    payload: TaskCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        return task_response(
            TaskService(user.id).create(session, **payload.model_dump())
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    task = TaskService(user.id).get_by_id(task_id, session)
    if task is None:
        raise HTTPException(404, "Task not found")
    return task_response(task)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    values = payload.model_dump(exclude_unset=True)
    clear_fields = {key for key, value in values.items() if value is None}
    if clear_fields - {"description", "due_date", "recurrence", "assignee_id", "tags"}:
        raise HTTPException(400, "Title, priority, status and timezone cannot be null")
    try:
        updated = TaskService(user.id).update(
            task_id, session, **values, clear_fields=clear_fields
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if updated is None:
        raise HTTPException(404, "Task not found")
    return task_response(updated)


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not TaskService(user.id).delete(task_id, session):
        raise HTTPException(404, "Task not found")
