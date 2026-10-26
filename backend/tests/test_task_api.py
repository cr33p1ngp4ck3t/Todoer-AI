"""Task HTTP contracts, including input validation and ownership."""

from datetime import datetime

import pytest
from src.api.auth import create_access_token
from src.models.user import User


@pytest.fixture
def headers(test_user):
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_task_crud(client, headers):
    created = client.post(
        "/tasks",
        headers=headers,
        json={"title": "Buy milk", "priority": "high", "tags": [" Shopping "]},
    )
    assert created.status_code == 201
    task = created.json()
    assert task["title"] == "Buy milk"
    assert task["tags"] == ["shopping"]
    task_id = task["id"]

    assert client.get(f"/tasks/{task_id}", headers=headers).json()["id"] == task_id
    assert (
        client.get(
            "/tasks?search=milk&status=pending&priority=high", headers=headers
        ).json()[0]["id"]
        == task_id
    )
    updated = client.patch(
        f"/tasks/{task_id}", headers=headers, json={"status": "completed", "tags": []}
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"
    assert updated.json()["tags"] == []
    assert client.delete(f"/tasks/{task_id}", headers=headers).status_code == 204
    assert client.get(f"/tasks/{task_id}", headers=headers).status_code == 404


@pytest.mark.parametrize(
    "payload",
    [{"title": "   "}, {"title": "Task", "priority": "invalid"}],
)
def test_create_validation(client, headers, payload):
    response = client.post("/tasks", headers=headers, json=payload)
    assert response.status_code in (400, 422)
    assert client.get("/tasks", headers=headers).json() == []


@pytest.mark.parametrize(
    "payload",
    [{"title": "   "}, {"priority": "invalid"}, {"status": "invalid"}],
)
def test_update_validation(client, headers, payload):
    created = client.post("/tasks", headers=headers, json={"title": "Original"}).json()
    response = client.patch(f"/tasks/{created['id']}", headers=headers, json=payload)
    assert response.status_code in (400, 422)
    unchanged = client.get(f"/tasks/{created['id']}", headers=headers).json()
    assert unchanged["title"] == "Original"
    assert unchanged["priority"] == "medium"
    assert unchanged["status"] == "pending"


def test_task_ownership(client, headers, db_session):
    task_id = client.post("/tasks", headers=headers, json={"title": "Private"}).json()[
        "id"
    ]
    other = User(username="other", email="other@example.com", hashed_password="hash")
    db_session.add(other)
    db_session.commit()
    token = create_access_token({"sub": str(other.id)})
    other_headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/tasks", headers=other_headers).json() == []
    assert client.get(f"/tasks/{task_id}", headers=other_headers).status_code == 404
    assert (
        client.patch(
            f"/tasks/{task_id}", headers=other_headers, json={"title": "Hacked"}
        ).status_code
        == 404
    )
    assert client.delete(f"/tasks/{task_id}", headers=other_headers).status_code == 404
    assert client.get(f"/tasks/{task_id}", headers=headers).json()["title"] == "Private"


@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize(
    "due_date,expected",
    [
        ("2026-11-01T09:30", "2026-11-01T09:30:00+00:00"),
        ("2026-11-01T09:30:00Z", "2026-11-01T09:30:00+00:00"),
        ("2026-11-01T09:30:00+05:00", "2026-11-01T04:30:00+00:00"),
    ],
)
def test_due_date_accepts_existing_clients(
    client, headers, operation, due_date, expected
):
    if operation == "create":
        response = client.post(
            "/tasks", headers=headers, json={"title": "Deadline", "due_date": due_date}
        )
        assert response.status_code == 201
    else:
        task_id = client.post(
            "/tasks", headers=headers, json={"title": "Deadline"}
        ).json()["id"]
        response = client.patch(
            f"/tasks/{task_id}", headers=headers, json={"due_date": due_date}
        )
        assert response.status_code == 200

    task = response.json()
    persisted = client.get(f"/tasks/{task['id']}", headers=headers).json()
    assert datetime.fromisoformat(task["due_date"]) == datetime.fromisoformat(expected)
    assert datetime.fromisoformat(persisted["due_date"]) == datetime.fromisoformat(
        expected
    )
