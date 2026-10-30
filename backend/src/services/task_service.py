import calendar
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import case, or_
from sqlmodel import Session, select
from src.models.project import Project, ProjectMember, TaskImport
from src.models.task import Tag, Task, utcnow
from src.services.project_service import ProjectService

logger = logging.getLogger("todo-api")

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"pending", "completed"}
VALID_RECURRENCES = {"daily", "weekly", "monthly"}
VALID_SORTS = {"created_at", "created_at_asc", "priority", "due_date"}


def validate_task_values(
    title, description, priority, due_date, tags, recurrence, recurrence_timezone
):
    if not title.strip():
        raise ValueError("title cannot be empty")
    if len(title.strip()) > 255:
        raise ValueError("title cannot exceed 255 characters")
    if description is not None and len(description) > 1000:
        raise ValueError("description cannot exceed 1000 characters")
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Invalid priority: {priority}")
    if len(tags or []) > 50 or any(
        not tag.strip() or len(tag.strip()) > 50 for tag in tags or []
    ):
        raise ValueError("Use at most 50 nonempty tags of up to 50 characters")
    if recurrence is not None and recurrence not in VALID_RECURRENCES:
        raise ValueError("Invalid recurrence")
    if recurrence is not None and due_date is None:
        raise ValueError("Recurring tasks require a due date")
    try:
        ZoneInfo(recurrence_timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("Invalid recurrence timezone") from exc


def normalize_date(value):
    if value is None:
        return None
    # Existing clients sent offset-free dates; preserve their UTC interpretation.
    return (
        value.replace(tzinfo=timezone.utc)
        if value.utcoffset() is None
        else value.astimezone(timezone.utc)
    )


class TaskService:
    """Task operations shared by HTTP and MCP callers, including project access."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    def get_all(
        self,
        session: Session,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        sort_by: str = "created_at",
        project_id: UUID | None = None,
    ) -> List[Task]:
        if project_id is not None:
            ProjectService(self.user_id).require_access(project_id, session)
            query = select(Task).where(Task.project_id == project_id)
        else:
            query = select(Task).where(
                Task.owner_id == self.user_id, Task.project_id.is_(None)
            )
        if search:
            query = query.where(
                or_(
                    Task.title.ilike(f"%{search}%"),
                    Task.description.ilike(f"%{search}%"),
                )
            )
        if status in VALID_STATUSES:
            query = query.where(Task.status == status)
        if priority in VALID_PRIORITIES:
            query = query.where(Task.priority == priority)
        if sort_by == "priority":
            query = query.order_by(
                case(
                    (Task.priority == "high", 0),
                    (Task.priority == "medium", 1),
                    else_=2,
                ),
                Task.created_at.desc(),
            )
        elif sort_by == "created_at_asc":
            query = query.order_by(Task.created_at, Task.id)
        elif sort_by == "due_date":
            query = query.order_by(
                Task.due_date.is_(None), Task.due_date, Task.created_at.desc()
            )
        else:
            query = query.order_by(Task.created_at.desc())
        return list(session.exec(query).all())

    def get_by_id(
        self, task_id: UUID, session: Session, write: bool = False
    ) -> Optional[Task]:
        task = session.get(Task, task_id)
        if task is None:
            return None
        if task.project_id is not None:
            service = ProjectService(self.user_id)
            if service.role(task.project_id, session) is None:
                return None
            service.require_access(task.project_id, session, write=write)
        elif task.owner_id != self.user_id:
            return None
        return task

    def _validate_assignment(self, session, project_id, assignee_id):
        if assignee_id is None:
            return
        if project_id is None:
            if assignee_id != self.user_id:
                raise ValueError("Personal tasks can only be assigned to their owner")
            return
        project = session.get(Project, project_id)
        if project.owner_id == assignee_id:
            return
        member = session.exec(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == assignee_id,
                ProjectMember.accepted == True,  # noqa: E712
            )
        ).first()
        if member is None:
            raise ValueError("Assignee must be an accepted project member")

    def _new_task(
        self,
        session,
        title,
        description=None,
        priority="medium",
        due_date=None,
        tags=None,
        project_id=None,
        assignee_id=None,
        recurrence=None,
        recurrence_timezone="UTC",
    ):
        validate_task_values(
            title,
            description,
            priority,
            due_date,
            tags,
            recurrence,
            recurrence_timezone,
        )
        if project_id is not None:
            ProjectService(self.user_id).require_access(project_id, session, write=True)
        self._validate_assignment(session, project_id, assignee_id)
        due_date = normalize_date(due_date)
        task = Task(
            owner_id=self.user_id,
            title=title.strip(),
            description=description.strip() if description else None,
            priority=priority,
            due_date=due_date,
            project_id=project_id,
            assignee_id=assignee_id,
            recurrence=recurrence,
            recurrence_timezone=recurrence_timezone,
            recurrence_day=(
                due_date.astimezone(ZoneInfo(recurrence_timezone)).day
                if recurrence and due_date
                else None
            ),
        )
        task.tags = [
            Tag(name=name)
            for name in dict.fromkeys(tag.lower().strip() for tag in tags or [])
        ]
        return task

    def create(
        self,
        session: Session,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        project_id: UUID | None = None,
        assignee_id: UUID | None = None,
        recurrence: str | None = None,
        recurrence_timezone: str = "UTC",
    ) -> Task:
        task = self._new_task(
            session,
            title,
            description,
            priority,
            due_date,
            tags,
            project_id,
            assignee_id,
            recurrence,
            recurrence_timezone,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        logger.info("Created task %s", task.id)
        return task

    def update(
        self,
        task_id: UUID,
        session: Session,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        recurrence: str | None = None,
        recurrence_timezone: str | None = None,
        assignee_id: UUID | None = None,
        clear_fields: set[str] | None = None,
    ) -> Optional[Task]:
        task = self.get_by_id(task_id, session, write=True)
        if task is None:
            return None
        # Serialize recurring completions on PostgreSQL; the unique predecessor is a second guard.
        task = session.exec(
            select(Task)
            .where(Task.id == task_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).one()
        cleared = clear_fields or set()
        next_title = task.title if title is None else title
        next_description = (
            None
            if "description" in cleared
            else task.description if description is None else description
        )
        next_priority = task.priority if priority is None else priority
        next_due = (
            None
            if "due_date" in cleared
            else (
                normalize_date(task.due_date)
                if due_date is None
                else normalize_date(due_date)
            )
        )
        next_recurrence = (
            None
            if "recurrence" in cleared
            else task.recurrence if recurrence is None else recurrence
        )
        next_timezone = (
            task.recurrence_timezone
            if recurrence_timezone is None
            else recurrence_timezone
        )
        next_assignee = (
            None
            if "assignee_id" in cleared
            else task.assignee_id if assignee_id is None else assignee_id
        )
        validate_task_values(
            next_title,
            next_description,
            next_priority,
            next_due,
            tags,
            next_recurrence,
            next_timezone,
        )
        if status is not None and status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        self._validate_assignment(session, task.project_id, next_assignee)
        first_completion = (
            status == "completed"
            and task.status != "completed"
            and next_recurrence
            and not task.recurrence_spawned
        )
        schedule_changed = (
            (due_date is not None and next_due != normalize_date(task.due_date))
            or (recurrence is not None and next_recurrence != task.recurrence)
            or (
                recurrence_timezone is not None
                and next_timezone != task.recurrence_timezone
            )
        )
        task.title, task.description = next_title.strip(), (
            next_description.strip() if next_description else None
        )
        task.priority, task.due_date = next_priority, next_due
        if schedule_changed:
            task.recurrence_day = (
                next_due.astimezone(ZoneInfo(next_timezone)).day if next_due else None
            )
        task.recurrence, task.recurrence_timezone, task.assignee_id = (
            next_recurrence,
            next_timezone,
            next_assignee,
        )
        if status is not None:
            task.status = status
        if tags is not None:
            task.tags = [
                Tag(name=name)
                for name in dict.fromkeys(tag.lower().strip() for tag in tags)
            ]
        if first_completion:
            local_date = next_due.astimezone(ZoneInfo(next_timezone))
            if next_recurrence == "monthly":
                year = local_date.year + (local_date.month == 12)
                month = local_date.month % 12 + 1
                local_date = local_date.replace(
                    year=year,
                    month=month,
                    day=min(
                        task.recurrence_day or local_date.day,
                        calendar.monthrange(year, month)[1],
                    ),
                )
            else:
                local_date += timedelta(days=1 if next_recurrence == "daily" else 7)
            successor = Task(
                owner_id=task.owner_id,
                title=task.title,
                description=task.description,
                priority=task.priority,
                due_date=local_date.astimezone(timezone.utc),
                recurrence=next_recurrence,
                recurrence_timezone=next_timezone,
                recurrence_day=task.recurrence_day,
                project_id=task.project_id,
                assignee_id=task.assignee_id,
                predecessor_id=task.id,
            )
            successor.tags = [Tag(name=tag.name) for tag in task.tags]
            session.add(successor)
            task.recurrence_spawned = True
        task.updated_at = utcnow()
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    def delete(self, task_id: UUID, session: Session) -> bool:
        task = self.get_by_id(task_id, session, write=True)
        if task is None:
            return False
        session.delete(task)
        session.commit()
        return True

    def import_tasks(self, session: Session, entries) -> dict:
        candidates = []
        seen = set()
        skipped = 0
        for entry in entries:
            values = entry.model_dump(
                exclude={"id", "status", "recurrence_day", "recurrence_spawned"}
            )
            task = self._new_task(session, **values)
            task.recurrence_day = entry.recurrence_day or task.recurrence_day
            if (
                entry.id in seen
                or session.get(TaskImport, (self.user_id, entry.id)) is not None
            ):
                skipped += 1
                continue
            existing = session.get(Task, entry.id)
            if (
                existing is not None
                and existing.owner_id == self.user_id
                and existing.project_id is None
            ):
                skipped += 1
                continue
            seen.add(entry.id)
            task.status = entry.status
            task.recurrence_spawned = (
                entry.recurrence_spawned or entry.status == "completed"
            )
            candidates.append((entry.id, task))
        for source_id, task in candidates:
            session.add(task)
            session.add(TaskImport(user_id=self.user_id, source_id=source_id))
        try:
            session.commit()
        except Exception:
            session.rollback()
            raise
        return {"imported": len(candidates), "skipped": skipped}
