from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User

# Valid priority and status values
VALID_PRIORITIES = ["low", "medium", "high"]
VALID_STATUSES = ["pending", "completed"]


def utcnow():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Task(SQLModel, table=True):
    __tablename__: str = "task"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="user.id")
    title: str = Field(index=True, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="pending", index=True)  # pending, completed
    priority: str = Field(default="medium")  # low, medium, high
    due_date: Optional[datetime] = Field(default=None, index=True)  # optional deadline
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow)

    owner: "User" = Relationship(back_populates="tasks")
    tags: List["Tag"] = Relationship(
        back_populates="task", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Tag(SQLModel, table=True):
    __tablename__: str = "tag"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="task.id")
    name: str = Field(max_length=50)
    created_at: datetime = Field(default_factory=utcnow)

    task: Task = Relationship(back_populates="tags")
