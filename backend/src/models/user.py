from datetime import datetime, timezone
from typing import TYPE_CHECKING, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .task import Task
    from .conversation import Conversation

def utcnow():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utcnow)

    tasks: List["Task"] = Relationship(back_populates="owner", cascade_delete=True)
    conversations: List["Conversation"] = Relationship(back_populates="user", cascade_delete=True)
