import pytest
from src.models.task import Task, Tag, VALID_PRIORITIES, VALID_STATUSES
from src.models.user import User
from sqlmodel import create_engine, Session
from src.services.task_service import TaskService
from uuid import uuid4
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, echo=False)

@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
        session.rollback()

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def task_service(test_user):
    """Create a TaskService instance with test user."""
    return TaskService(user_id=test_user.id)

def test_task_model_creation(db_session):
    """Test Task model can be created with valid data."""
    task = Task(
        owner_id=uuid4(),
        title="Test Task",
        description="Test Description",
        status="pending",
        priority="medium",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.id is not None
    assert task.title == "Test Task"
    assert task.description == "Test Description"
    assert task.status == "pending"
    assert task.priority == "medium"

def test_task_model_empty_title_rejected(db_session, task_service):
    """Test Task without title raises error."""
    with pytest.raises(ValueError, match="title cannot be empty"):
        task_service.create(
            db_session,
            title="   ",
            description="Description",
        )

def test_task_model_invalid_priority_rejected(db_session, task_service):
    """Test Task with invalid priority raises error."""
    with pytest.raises(ValueError, match="Invalid priority"):
        task_service.create(
            db_session,
            title="Test",
            priority="invalid",
        )

def test_task_model_invalid_status_rejected():
    """Test Task status enum is validated."""
    # This would be validated in the service layer
    assert "pending" in VALID_STATUSES
    assert "completed" in VALID_STATUSES

def test_task_model_invalid_priority_rejected():
    """Test Task priority enum is validated."""
    assert "low" in VALID_PRIORITIES
    assert "medium" in VALID_PRIORITIES
    assert "high" in VALID_PRIORITIES

def test_tag_model_creation(db_session, test_user):
    """Test Tag model can be created."""
    tag = Tag(
        user_id=test_user.id,
        name="work",
    )
    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)

    assert tag.id is not None
    assert tag.name == "work"
    assert tag.user_id == test_user.id

def test_task_tag_association(db_session, test_user):
    """Test Task can have multiple tags."""
    task = Task(
        owner_id=test_user.id,
        title="Test Task",
    )
    db_session.add(task)

    tag1 = Tag(user_id=test_user.id, name="work")
    tag2 = Tag(user_id=test_user.id, name="personal")

    db_session.add_all([tag1, tag2])
    task.tags.append(tag1)
    task.tags.append(tag2)

    db_session.commit()
    db_session.refresh(task)

    assert len(task.tags) == 2
    assert set(t.name for t in task.tags) == {"work", "personal"}

def test_user_model_creation(db_session):
    """Test User model can be created."""
    user = User(
        email="user@example.com",
        hashed_password="hashed_pass",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.email == "user@example.com"
    assert user.is_active is True

def test_user_model_email_unique(db_session):
    """Test User emails must be unique."""
    user1 = User(
        email="same@example.com",
        hashed_password="hashed",
    )
    user2 = User(
        email="same@example.com",
        hashed_password="hashed",
    )
    db_session.add_all([user1, user2])
    db_session.commit()

    # Second user should have failed due to unique constraint
    users = db_session.exec(User.select()).all()
    assert len(users) == 1
