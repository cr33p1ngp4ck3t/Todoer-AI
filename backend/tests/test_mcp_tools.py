"""Tests for MCP tool handlers."""
import pytest
from uuid import uuid4, UUID
from sqlmodel import Session, select
from src.models.user import User
from src.models.task import Task, Tag
from src.services.mcp_server import MCPToolHandler, get_mcp_tools
from src.lib.database import engine


@pytest.fixture
def db_session():
    """Create a test database session."""
    session = Session(engine)
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user for MCP tests."""
    user = User(
        username=f"mcptest_{uuid4().hex[:8]}",
        email=f"mcptest_{uuid4().hex[:8]}@example.com",
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


@pytest.fixture
def mcp_handler(db_session, test_user):
    """Create an MCP tool handler for testing."""
    return MCPToolHandler(user_id=test_user.id, session=db_session)


def test_get_mcp_tools():
    """Test that MCP tools are properly defined."""
    tools = get_mcp_tools()
    assert len(tools) == 7

    tool_names = [tool["function"]["name"] for tool in tools]
    expected_tools = [
        "add_task",
        "list_tasks",
        "update_task",
        "complete_task",
        "delete_task",
        "search_tasks",
        "suggest_breakdown",
    ]

    for expected in expected_tools:
        assert expected in tool_names


def test_add_task_tool(mcp_handler, db_session):
    """Test add_task tool."""
    result = mcp_handler.execute_tool(
        "add_task",
        {
            "title": "Buy groceries",
            "description": "Milk, eggs, bread",
            "priority": "high",
            "tags": ["shopping", "urgent"],
        }
    )

    assert result["success"] is True
    data = result["data"]
    assert data["title"] == "Buy groceries"
    assert data["description"] == "Milk, eggs, bread"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    assert set(data["tags"]) == {"shopping", "urgent"}
    assert "task_id" in data

    # Verify task was created in database
    task_id = UUID(data["task_id"])
    task = db_session.get(Task, task_id)
    assert task is not None
    assert task.title == "Buy groceries"

    # Cleanup
    db_session.delete(task)
    db_session.commit()


def test_add_task_minimal(mcp_handler, db_session):
    """Test add_task with only required fields."""
    result = mcp_handler.execute_tool(
        "add_task",
        {"title": "Simple task"}
    )

    assert result["success"] is True
    data = result["data"]
    assert data["title"] == "Simple task"
    assert data["description"] is None
    assert data["priority"] == "medium"  # Default
    assert data["tags"] == []

    # Cleanup
    task_id = UUID(data["task_id"])
    task = db_session.get(Task, task_id)
    db_session.delete(task)
    db_session.commit()


def test_list_tasks_tool(mcp_handler, db_session, test_user):
    """Test list_tasks tool."""
    # Create test tasks
    task1 = Task(
        owner_id=test_user.id,
        title="Task 1",
        description="First task",
        priority="high",
        status="pending",
    )
    task2 = Task(
        owner_id=test_user.id,
        title="Task 2",
        description="Second task",
        priority="low",
        status="completed",
    )
    db_session.add(task1)
    db_session.add(task2)
    db_session.commit()

    # Test list all tasks
    result = mcp_handler.execute_tool("list_tasks", {"status": "all"})
    assert result["success"] is True
    data = result["data"]
    assert data["count"] >= 2
    assert len(data["tasks"]) >= 2

    # Test filter by status
    result = mcp_handler.execute_tool("list_tasks", {"status": "pending"})
    assert result["success"] is True
    data = result["data"]
    pending_tasks = [t for t in data["tasks"] if t["status"] == "pending"]
    assert len(pending_tasks) >= 1

    # Test filter by priority
    result = mcp_handler.execute_tool("list_tasks", {"priority": "high"})
    assert result["success"] is True
    data = result["data"]
    high_tasks = [t for t in data["tasks"] if t["priority"] == "high"]
    assert len(high_tasks) >= 1

    # Cleanup
    db_session.delete(task1)
    db_session.delete(task2)
    db_session.commit()


def test_update_task_tool(mcp_handler, db_session, test_user):
    """Test update_task tool."""
    # Create a task
    task = Task(
        owner_id=test_user.id,
        title="Original title",
        description="Original description",
        priority="low",
        status="pending",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Update the task
    result = mcp_handler.execute_tool(
        "update_task",
        {
            "task_id": str(task.id),
            "title": "Updated title",
            "priority": "high",
            "tags": ["updated", "test"],
        }
    )

    assert result["success"] is True
    data = result["data"]
    assert data["title"] == "Updated title"
    assert data["priority"] == "high"
    assert set(data["tags"]) == {"updated", "test"}

    # Verify update in database
    db_session.refresh(task)
    assert task.title == "Updated title"
    assert task.priority == "high"

    # Cleanup
    db_session.delete(task)
    db_session.commit()


def test_update_nonexistent_task(mcp_handler):
    """Test updating a task that doesn't exist."""
    fake_id = str(uuid4())
    result = mcp_handler.execute_tool(
        "update_task",
        {
            "task_id": fake_id,
            "title": "This should fail",
        }
    )

    assert result["success"] is False
    assert "not found" in result["error"].lower()


def test_complete_task_tool(mcp_handler, db_session, test_user):
    """Test complete_task tool."""
    # Create a pending task
    task = Task(
        owner_id=test_user.id,
        title="Task to complete",
        status="pending",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Complete the task
    result = mcp_handler.execute_tool(
        "complete_task",
        {"task_id": str(task.id)}
    )

    assert result["success"] is True
    data = result["data"]
    assert data["status"] == "completed"

    # Verify in database
    db_session.refresh(task)
    assert task.status == "completed"

    # Cleanup
    db_session.delete(task)
    db_session.commit()


def test_delete_task_tool(mcp_handler, db_session, test_user):
    """Test delete_task tool."""
    # Create a task
    task = Task(
        owner_id=test_user.id,
        title="Task to delete",
        status="pending",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    task_id = task.id

    # Delete the task
    result = mcp_handler.execute_tool(
        "delete_task",
        {"task_id": str(task_id)}
    )

    assert result["success"] is True
    data = result["data"]
    assert data["status"] == "deleted"

    # Verify deletion in database
    deleted_task = db_session.get(Task, task_id)
    assert deleted_task is None


def test_delete_nonexistent_task(mcp_handler):
    """Test deleting a task that doesn't exist."""
    fake_id = str(uuid4())
    result = mcp_handler.execute_tool(
        "delete_task",
        {"task_id": fake_id}
    )

    assert result["success"] is False
    assert "not found" in result["error"].lower()


def test_search_tasks_tool(mcp_handler, db_session, test_user):
    """Test search_tasks tool."""
    # Create tasks with searchable content
    task1 = Task(
        owner_id=test_user.id,
        title="Shopping for groceries",
        description="Buy milk and eggs",
        status="pending",
    )
    task2 = Task(
        owner_id=test_user.id,
        title="Work meeting",
        description="Discuss project timeline",
        status="pending",
    )
    db_session.add(task1)
    db_session.add(task2)
    db_session.commit()

    # Search for "shopping"
    result = mcp_handler.execute_tool(
        "search_tasks",
        {"query": "shopping"}
    )

    assert result["success"] is True
    data = result["data"]
    assert data["count"] >= 1
    shopping_tasks = [t for t in data["tasks"] if "shopping" in t["title"].lower()]
    assert len(shopping_tasks) >= 1

    # Search for "milk"
    result = mcp_handler.execute_tool(
        "search_tasks",
        {"query": "milk"}
    )

    assert result["success"] is True
    data = result["data"]
    milk_tasks = [t for t in data["tasks"] if "milk" in (t["description"] or "").lower()]
    assert len(milk_tasks) >= 1

    # Cleanup
    db_session.delete(task1)
    db_session.delete(task2)
    db_session.commit()


def test_suggest_breakdown_tool(mcp_handler):
    """Test suggest_breakdown tool."""
    result = mcp_handler.execute_tool(
        "suggest_breakdown",
        {"task_description": "Plan team event for 50 people"}
    )

    assert result["success"] is True
    data = result["data"]
    assert "suggestions" in data
    assert len(data["suggestions"]) >= 3

    # Verify suggestion structure
    for suggestion in data["suggestions"]:
        assert "title" in suggestion
        assert "priority" in suggestion
        assert "tags" in suggestion


def test_user_isolation(db_session):
    """Test that users can only access their own tasks."""
    # Create two users
    user1 = User(
        username=f"isolation1_{uuid4().hex[:8]}",
        email=f"isolation1_{uuid4().hex[:8]}@example.com",
        hashed_password="pass123",
        is_active=True,
    )
    user2 = User(
        username=f"isolation2_{uuid4().hex[:8]}",
        email=f"isolation2_{uuid4().hex[:8]}@example.com",
        hashed_password="pass123",
        is_active=True,
    )
    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)

    # User 1 creates a task
    handler1 = MCPToolHandler(user_id=user1.id, session=db_session)
    result = handler1.execute_tool("add_task", {"title": "User 1's task"})
    task_id = result["data"]["task_id"]

    # User 2 tries to update User 1's task
    handler2 = MCPToolHandler(user_id=user2.id, session=db_session)
    result = handler2.execute_tool(
        "update_task",
        {"task_id": task_id, "title": "Hacked!"}
    )

    # Should fail due to user isolation
    assert result["success"] is False

    # User 2 tries to delete User 1's task
    result = handler2.execute_tool("delete_task", {"task_id": task_id})
    assert result["success"] is False

    # Verify task is still owned by User 1
    task = db_session.get(Task, UUID(task_id))
    assert task is not None
    assert task.owner_id == user1.id
    assert task.title == "User 1's task"

    # Cleanup
    db_session.delete(task)
    db_session.delete(user1)
    db_session.delete(user2)
    db_session.commit()


def test_invalid_tool_name(mcp_handler):
    """Test executing an invalid tool name."""
    with pytest.raises(ValueError, match="Unknown tool"):
        mcp_handler.execute_tool("invalid_tool", {})


def test_tool_error_handling(mcp_handler):
    """Test that tool errors are caught and returned properly."""
    # Try to complete a task with invalid UUID format
    result = mcp_handler.execute_tool(
        "complete_task",
        {"task_id": "not-a-valid-uuid"}
    )

    assert result["success"] is False
    assert "error" in result
