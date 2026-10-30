"""Conversation management API endpoints."""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, func, select
from src.api.auth import get_current_user
from src.lib.database import get_session
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.user import User

logger = logging.getLogger("todo-api")
router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class ConversationResponse(BaseModel):
    """Conversation response model."""

    id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class MessageResponse(BaseModel):
    """Message response model."""

    id: UUID
    role: str
    content: str
    tool_calls: Optional[str] = None
    created_at: datetime


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""

    title: Optional[str] = None


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all conversations for the current user.

    Args:
        current_user: Authenticated user from JWT
        session: Database session
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip

    Returns:
        List of conversation summaries with message counts
    """
    # Get conversations with message counts
    conv_query = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )

    conversations = session.exec(conv_query).all()

    # Build response with message counts
    results = []
    for conv in conversations:
        # Count messages
        count_query = select(func.count(Message.id)).where(
            Message.conversation_id == conv.id
        )
        message_count = session.exec(count_query).one()

        results.append(
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=message_count,
            )
        )

    return results


@router.get("/{conversation_id}", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
):
    """Get all messages in a conversation.

    Args:
        conversation_id: UUID of the conversation
        current_user: Authenticated user from JWT
        session: Database session
        limit: Maximum number of messages to return

    Returns:
        List of messages in chronological order
    """
    # Verify conversation belongs to user
    conv_query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    )
    conversation = session.exec(conv_query).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Get messages
    messages_query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )

    messages = session.exec(messages_query).all()

    return [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            tool_calls=msg.tool_calls,
            created_at=msg.created_at,
        )
        for msg in messages
    ]


@router.post(
    "", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a new conversation.

    Args:
        request: Request with optional title
        current_user: Authenticated user from JWT
        session: Database session

    Returns:
        The created conversation
    """
    conversation = Conversation(
        user_id=current_user.id,
        title=request.title,
    )

    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    logger.info(f"Created conversation {conversation.id} for user {current_user.id}")

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=0,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete a conversation and all its messages.

    Args:
        conversation_id: UUID of the conversation to delete
        current_user: Authenticated user from JWT
        session: Database session
    """
    # Verify conversation belongs to user
    conv_query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    )
    conversation = session.exec(conv_query).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Delete conversation (messages are cascade-deleted)
    session.delete(conversation)
    session.commit()

    logger.info(f"Deleted conversation {conversation_id} for user {current_user.id}")
