from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import or_
from sqlmodel import Session, select
from src.models.task import Task, Tag
from src.models.user import User
import logging

logger = logging.getLogger("todo-api")

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"pending", "completed"}

class TaskService:
    """Business logic for task operations with user isolation."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    def get_all(
        self,
        session: Session,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        sort_by: str = "created_at",
    ) -> List[Task]:
        """Get all tasks for current user with optional filters."""
        query = select(Task).where(Task.owner_id == self.user_id)

        # Apply search filter (title OR description)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term)
                )
            )

        if status and status in VALID_STATUSES:
            query = query.where(Task.status == status)

        if priority and priority in VALID_PRIORITIES:
            query = query.where(Task.priority == priority)

        # Apply sorting
        if sort_by == "priority":
            # Sort by priority (high to low), then by created_at descending
            # Using case expression for proper priority ordering
            from sqlalchemy import case
            priority_case = case(
                (Task.priority == "high", 0),
                (Task.priority == "medium", 1),
                (Task.priority == "low", 2),
                else_=3
            )
            query = query.order_by(priority_case, Task.created_at.desc())
        else:
            query = query.order_by(Task.created_at.desc())

        result = session.exec(query).all()

        logger.info(f"Retrieved {len(result)} tasks for user {self.user_id}")
        return result

    def get_by_id(self, task_id: UUID, session: Session) -> Optional[Task]:
        """Get a single task by ID (user-scoped)."""
        return session.get(Task, task_id)

    def create(
        self,
        session: Session,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        tags: Optional[List[str]] = None,
    ) -> Task:
        """Create a new task for current user."""
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}")

        task = Task(
            owner_id=self.user_id,
            title=title.strip(),
            description=description.strip() if description else None,
            priority=priority,
            status="pending",
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Add tags if provided
        if tags:
            for tag_name in tags:
                tag = Tag(task_id=task.id, name=tag_name.lower().strip())
                session.add(tag)

            session.commit()

        logger.info(f"Created task {task.id} for user {self.user_id}")
        return task

    def update(
        self,
        task_id: UUID,
        session: Session,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Task]:
        """Update an existing task (user-scoped, last-write-wins)."""
        task = self.get_by_id(task_id, session)
        if not task or task.owner_id != self.user_id:
            return None

        if title is not None:
            task.title = title.strip()
        if description is not None:
            task.description = description.strip() if description else None
        if status is not None and status in VALID_STATUSES:
            task.status = status
        if priority is not None and priority in VALID_PRIORITIES:
            task.priority = priority

        task.updated_at = datetime.utcnow()

        # Update tags if provided
        if tags is not None:
            # Remove old tags
            old_tags = session.exec(select(Tag).where(Tag.task_id == task.id)).all()
            for tag in old_tags:
                session.delete(tag)

            # Add new tags
            for tag_name in tags:
                tag = Tag(task_id=task.id, name=tag_name.lower().strip())
                session.add(tag)

        session.commit()
        session.refresh(task)
        logger.info(f"Updated task {task_id} for user {self.user_id}")
        return task

    def delete(self, task_id: UUID, session: Session) -> bool:
        """Delete a task permanently (user-scoped)."""
        task = self.get_by_id(task_id, session)
        if not task or task.owner_id != self.user_id:
            return False

        session.delete(task)
        session.commit()
        logger.info(f"Deleted task {task_id} for user {self.user_id}")
        return True
