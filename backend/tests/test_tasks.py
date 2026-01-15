import pytest
import pytest_asyncio
from httpx import AsyncClient, Response
from src.models.task import Task, VALID_PRIORITIES, VALID_STATUSES
from src.models.user import User
from src.services.task_service import TaskService
from sqlmodel import Session, create_engine, select
from uuid import uuid4
import asyncio
from datetime import datetime

DATABASE_URL = "sqlite:///./test_tasks.db"
engine = create_engine(DATABASE_URL, echo=False)

@pytest.fixture
async def db_session():
    """Create a fresh database session for each test."""
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    async with Session(engine) as session:
        yield session
        session.rollback()
    session.close()
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    from src.api.auth import get_password_hash
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
async def task_service(test_user, db_session):
    """Create TaskService instance with test user."""
    return TaskService(user_id=test_user.id)

@pytest.mark.asyncio
async def test_list_all_tasks(task_service, db_session):
    """Test listing all tasks for a user."""
    # Create test tasks
    task1 = Task(
        owner_id=task_service.user_id,
        title="Task 1",
        status="pending",
        priority="medium",
    )
    task2 = Task(
        owner_id=task_service.user_id,
        title="Task 2",
        status="completed",
        priority="high",
    )
    db_session.add_all([task1, task2])
    db_session.commit()

    # Get tasks
    tasks = task_service.get_all(session=db_session)

    assert len(tasks) == 2
    assert any(t.title == "Task 1" for t in tasks)
    assert any(t.title == "Task 2" for t in tasks)

@pytest.mark.asyncio
async def test_list_with_filters(task_service, db_session):
    """Test filtering tasks by status and priority."""
    # Create test tasks
    for priority in ["low", "medium", "high"]:
        for status in ["pending", "completed"]:
            db_session.add(Task(
                owner_id=task_service.user_id,
                title=f"{priority} {status}",
                status=status,
                priority=priority,
            ))
    db_session.commit()

    # Filter by status
    pending_tasks = task_service.get_all(
        session=db_session,
        status="pending",
    )
    assert len(pending_tasks) == 3

    # Filter by priority
    high_tasks = task_service.get_all(
        session=db_session,
        priority="high",
    )
    assert len(high_tasks) == 2

@pytest.mark.asyncio
async def test_list_with_search(task_service, db_session):
    """Test searching tasks by text."""
    db_session.add(Task(
        owner_id=task_service.user_id,
        title="Buy groceries",
        description="Milk, bread, eggs",
        status="pending",
    ))
    db_session.commit()

    # Search for "milk"
    results = task_service.get_all(
        session=db_session,
        search="milk",
    )
    assert len(results) == 1
    assert "groceries".lower() in results[0].title.lower()

@pytest.mark.asyncio
async def test_list_with_sort_by_priority(task_service, db_session):
    """Test sorting tasks by priority."""
    db_session.add_all([
        Task(owner_id=task_service.user_id, title="Low task", priority="low"),
        Task(owner_id=task_service.user_id, title="High task", priority="high"),
        Task(owner_id=task_service.user_id, title="Medium task", priority="medium"),
    ])
    db_session.commit()

    tasks = task_service.get_all(
        session=db_session,
        sort_by="priority",
    )
    assert len(tasks) == 3
    assert tasks[0].priority == "high"
    assert tasks[1].priority == "medium"
    assert tasks[2].priority == "low"

@pytest.mark.asyncio
async def test_get_by_id(task_service, db_session):
    """Test getting a task by ID."""
    task = Task(
        owner_id=task_service.user_id,
        title="Test task",
        status="pending",
        priority="medium",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    result = task_service.get_by_id(task.id, session=db_session)

    assert result is not None
    assert result.id == task.id
    assert result.title == "Test task"

@pytest.mark.asyncio
async def test_get_by_id_not_found(task_service, db_session):
    """Test getting a non-existent task returns None."""
    result = task_service.get_by_id(uuid4(), session=db_session)
    assert result is None

@pytest.mark.asyncio
async def test_create_task(task_service, db_session):
    """Test creating a new task."""
    task = task_service.create(
        session=db_session,
        title="New Task",
        description="Description",
        priority="high",
        tags=["work", "urgent"],
    )

    assert task.id is not None
    assert task.title == "New Task"
    assert task.description == "Description"
    assert task.priority == "high"
    assert task.status == "pending"

    # Verify tags were created
    assert len(task.tags) == 2
    tag_names = {tag.name for tag in task.tags}
    assert "work" in tag_names
    assert "urgent" in tag_names

@pytest.mark.asyncio
async def test_create_task_with_invalid_priority_raises(task_service, db_session):
    """Test creating task with invalid priority raises ValueError."""
    with pytest.raises(ValueError, match="Invalid priority"):
        task_service.create(
            session=db_session,
            title="Test",
            priority="invalid",
        )

@pytest.mark.asyncio
async def test_create_task_with_empty_title_raises(task_service, db_session):
    """Test creating task without title raises error."""
    with pytest.raises(ValueError, match="title cannot be empty"):
        task_service.create(
            session=db_session,
            title="   ",
        )

@pytest.mark.asyncio
async def test_create_task_user_isolation(task_service, db_session):
    """Test tasks are isolated to the creating user."""
    from src.models.user import User

    # Create another user
    other_user = User(
        email="other@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    # Create task for other user
    other_task = Task(
        owner_id=other_user.id,
        title="Other user's task",
    )

    # Try to get it with task_service scoped to test_user
    tasks = task_service.get_all(session=db_session)

    # Should not see other user's tasks
    assert len(tasks) == 0

@pytest.mark.asyncio
async def test_update_task(task_service, db_session):
    """Test updating a task."""
    task = task_service.create(
        session=db_session,
        title="Original",
        priority="low",
    )

    updated = task_service.update(
        task_id=task.id,
        session=db_session,
        title="Updated",
        priority="high",
        status="completed",
        tags=["new-tag"],
    )

    assert updated.title == "Updated"
    assert updated.priority == "high"
    assert updated.status == "completed"
    assert len(updated.tags) == 1
    assert updated.tags[0].name == "new-tag"

@pytest.mark.asyncio
async def test_update_task_with_invalid_priority(task_service, db_session):
    """Test updating task with invalid priority raises ValueError."""
    task = task_service.create(session=db_session, title="Test")

    with pytest.raises(ValueError, match="Invalid priority"):
        task_service.update(
            task_id=task.id,
            session=db_session,
            priority="invalid",
        )

@pytest.mark.asyncio
async def test_update_nonexistent_task(task_service, db_session):
    """Test updating a non-existent task returns None."""
    result = task_service.update(
        task_id=uuid4(),
        session=db_session,
        title="Updated",
    )
    assert result is None

@pytest.mark.asyncio
async def test_delete_task(task_service, db_session):
    """Test deleting a task."""
    task = task_service.create(session=db_session, title="To Delete")
    task_id = task.id

    success = task_service.delete(task_id, session=db_session)

    assert success is True

    # Verify task is deleted from DB
    result = task_service.get_by_id(task_id, session=db_session)
    assert result is None

@pytest.mark.asyncio
async def test_delete_nonexistent_task(task_service, db_session):
    """Test deleting a non-existent task returns False."""
    success = task_service.delete(uuid4(), session=db_session)
    assert success is False

@pytest.mark.asyncio
async def test_concurrent_updates_last_write_wins(task_service, db_session):
    """Test that concurrent updates result in last-write-wins."""
    task = task_service.create(
        session=db_session,
        title="Concurrent Test",
    )

    task_id = task.id

    # Simulate concurrent updates
    async def update_1():
        await asyncio.sleep(0.01)  # Ensure update_2 starts first
        task_service.update(
            task_id=task_id,
            session=db_session,
            title="First Update",
        )

    async def update_2():
        task_service.update(
            task_id=task_id,
            session=db_session,
            title="Second Update",  # This should win
        )

    await asyncio.gather(update_1(), update_2())

    # Final state should be "Second Update"
    result = task_service.get_by_id(task_id, session=db_session)
    assert result.title == "Second Update"

@pytest.mark.asyncio
async def test_delete_other_user_task_returns_false(task_service, db_session):
    """Test that user cannot delete another user's task."""
    from src.models.user import User

    other_user = User(
        email="other@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    other_task = Task(
        owner_id=other_user.id,
        title="Other's task",
    )
    db_session.add(other_task)
    db_session.commit()

    # Try to delete other user's task
    success = task_service.delete(other_task.id, session=db_session)
    assert success is False
