"""Message model for chat messages within conversations."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Text
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .conversation import Conversation


def utcnow():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Message(SQLModel, table=True):
    """Represents a single message in a conversation.

    Messages can be from either the user or the AI assistant.
    Tool calls are stored as JSON for traceability of AI actions.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversation.id", index=True)
    role: str = Field(index=True)  # "user" or "assistant"
    content: str = Field(sa_column=Column(Text))  # No length limit for long messages
    tool_calls: Optional[str] = Field(default=None)  # JSON array of tool invocations
    created_at: datetime = Field(default_factory=utcnow, index=True)

    # Relationships
    conversation: "Conversation" = Relationship(back_populates="messages")
