"""Tests for chat models (Conversation and Message)."""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlmodel import Session, select
from src.models.user import User
from src.models.conversation import Conversation
from src.models.message import Message
from src.lib.database import engine


@pytest.fixture
def db_session():
    """Create a test database session."""
    session = Session(engine)
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user for chat tests."""
    user = User(
        username=f"chattest_{uuid4().hex[:8]}",
        email=f"chattest_{uuid4().hex[:8]}@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user
    # Cleanup
    db_session.delete(user)
    db_session.commit()


def test_create_conversation(db_session, test_user):
    """Test creating a conversation."""
    conversation = Conversation(
        user_id=test_user.id,
        title="Test conversation about tasks"
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)

    assert conversation.id is not None
    assert conversation.user_id == test_user.id
    assert conversation.title == "Test conversation about tasks"
    assert conversation.created_at is not None
    assert conversation.updated_at is not None

    # Cleanup
    db_session.delete(conversation)
    db_session.commit()


def test_create_message(db_session, test_user):
    """Test creating messages in a conversation."""
    # Create conversation
    conversation = Conversation(
        user_id=test_user.id,
        title="Test chat"
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)

    # Create user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content="Add a task to buy groceries"
    )
    db_session.add(user_message)
    db_session.commit()
    db_session.refresh(user_message)

    assert user_message.id is not None
    assert user_message.conversation_id == conversation.id
    assert user_message.role == "user"
    assert user_message.content == "Add a task to buy groceries"
    assert user_message.tool_calls is None
    assert user_message.created_at is not None

    # Create assistant message with tool call
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content="I've created a task 'Buy groceries' with high priority.",
        tool_calls='[{"tool": "add_task", "args": {"title": "Buy groceries", "priority": "high"}}]'
    )
    db_session.add(assistant_message)
    db_session.commit()
    db_session.refresh(assistant_message)

    assert assistant_message.id is not None
    assert assistant_message.role == "assistant"
    assert assistant_message.tool_calls is not None

    # Cleanup
    db_session.delete(user_message)
    db_session.delete(assistant_message)
    db_session.delete(conversation)
    db_session.commit()


def test_conversation_user_relationship(db_session, test_user):
    """Test relationship between conversation and user."""
    conversation = Conversation(
        user_id=test_user.id,
        title="Test relationship"
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)

    # Test forward relationship (conversation -> user)
    assert conversation.user is not None
    assert conversation.user.id == test_user.id

    # Test backward relationship (user -> conversations)
    db_session.refresh(test_user)
    user_conversations = test_user.conversations
    assert len(user_conversations) > 0
    assert any(c.id == conversation.id for c in user_conversations)

    # Cleanup
    db_session.delete(conversation)
    db_session.commit()


def test_conversation_message_relationship(db_session, test_user):
    """Test relationship between conversation and messages."""
    conversation = Conversation(
        user_id=test_user.id,
        title="Test messages"
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)

    # Add multiple messages
    message1 = Message(
        conversation_id=conversation.id,
        role="user",
        content="First message"
    )
    message2 = Message(
        conversation_id=conversation.id,
        role="assistant",
        content="Response to first message"
    )
    db_session.add(message1)
    db_session.add(message2)
    db_session.commit()

    # Test forward relationship (message -> conversation)
    db_session.refresh(message1)
    assert message1.conversation is not None
    assert message1.conversation.id == conversation.id

    # Test backward relationship (conversation -> messages)
    db_session.refresh(conversation)
    messages = conversation.messages
    assert len(messages) == 2
    assert messages[0].role in ["user", "assistant"]
    assert messages[1].role in ["user", "assistant"]

    # Cleanup
    db_session.delete(message1)
    db_session.delete(message2)
    db_session.delete(conversation)
    db_session.commit()


def test_cascade_delete_messages(db_session, test_user):
    """Test that deleting a conversation also deletes its messages."""
    # Create conversation with messages
    conversation = Conversation(
        user_id=test_user.id,
        title="Test cascade delete"
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)

    message1 = Message(
        conversation_id=conversation.id,
        role="user",
        content="Test message 1"
    )
    message2 = Message(
        conversation_id=conversation.id,
        role="assistant",
        content="Test message 2"
    )
    db_session.add(message1)
    db_session.add(message2)
    db_session.commit()

    message1_id = message1.id
    message2_id = message2.id
    conversation_id = conversation.id

    # Delete conversation
    db_session.delete(conversation)
    db_session.commit()

    # Verify conversation is deleted
    deleted_conversation = db_session.get(Conversation, conversation_id)
    assert deleted_conversation is None

    # Verify messages are also deleted (cascade)
    deleted_message1 = db_session.get(Message, message1_id)
    deleted_message2 = db_session.get(Message, message2_id)
    assert deleted_message1 is None
    assert deleted_message2 is None


def test_cascade_delete_conversations(db_session):
    """Test that deleting a user also deletes their conversations."""
    # Create user
    user = User(
        username=f"cascade_test_{uuid4().hex[:8]}",
        email=f"cascade_test_{uuid4().hex[:8]}@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create conversation with message
    conversation = Conversation(
        user_id=user.id,
        title="Test cascade"
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)

    message = Message(
        conversation_id=conversation.id,
        role="user",
        content="Test message"
    )
    db_session.add(message)
    db_session.commit()

    user_id = user.id
    conversation_id = conversation.id
    message_id = message.id

    # Delete user
    db_session.delete(user)
    db_session.commit()

    # Verify user is deleted
    deleted_user = db_session.get(User, user_id)
    assert deleted_user is None

    # Verify conversation is also deleted (cascade)
    deleted_conversation = db_session.get(Conversation, conversation_id)
    assert deleted_conversation is None

    # Verify message is also deleted (cascade through conversation)
    deleted_message = db_session.get(Message, message_id)
    assert deleted_message is None
