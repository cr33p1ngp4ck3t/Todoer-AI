from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
from src.models.task import Task
from src.models.user import User
from src.services.mcp_server import MCPToolHandler


@pytest.fixture
def handler(test_user, db_session):
    return MCPToolHandler(test_user.id, db_session)


@pytest.mark.parametrize("tool", ["update_task", "complete_task", "delete_task"])
def test_malformed_task_id_returns_error(handler, tool):
    result = handler.execute_tool(tool, {"task_id": "not-a-uuid"})
    assert result["success"] is False
    assert "UUID" in result["error"]


@pytest.mark.parametrize("tool,args", [("search_tasks", {}), ("suggest_breakdown", {})])
def test_missing_required_arguments(handler, tool, args):
    result = handler.execute_tool(tool, args)
    assert result["success"] is False and result["error"]


def test_completing_missing_task_returns_error(handler):
    result = handler.execute_tool("complete_task", {"task_id": str(uuid4())})
    assert result["success"] is False
    assert "not found or access denied" in result["error"]


@pytest.mark.parametrize("tool", ["update_task", "complete_task", "delete_task"])
def test_foreign_task_is_not_mutated(handler, db_session, tool):
    owner = User(
        username="foreign", email="foreign@example.com", hashed_password="unused"
    )
    db_session.add(owner)
    db_session.commit()
    task = Task(owner_id=owner.id, title="Private")
    db_session.add(task)
    db_session.commit()
    result = handler.execute_tool(tool, {"task_id": str(task.id), "title": "Changed"})
    assert result["success"] is False
    db_session.refresh(task)
    assert task.title == "Private" and task.status == "pending"


def test_database_failure_is_reported(handler, monkeypatch):
    def fail(**kwargs):
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(handler.task_service, "get_all", fail)
    result = handler.execute_tool("list_tasks", {})
    assert result == {"success": False, "error": "database unavailable"}
