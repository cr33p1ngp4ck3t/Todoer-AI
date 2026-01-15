"""Conversation model for chat history."""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .message import Message


def utcnow():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Conversation(SQLModel, table=True):
    """Represents a chat conversation between user and AI assistant.

    Each conversation contains multiple messages and belongs to a user.
    The title is auto-generated from the first message for easy identification.
    """
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    title: Optional[str] = Field(default=None, max_length=255)  # Auto-generated from first message
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation", cascade_delete=True)
