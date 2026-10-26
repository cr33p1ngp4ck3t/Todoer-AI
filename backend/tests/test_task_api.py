"""Task HTTP contracts, including input validation and ownership."""

from datetime import datetime

import pytest
from src.api.auth import create_access_token
from src.models.user import User


@pytest.fixture
def headers(test_user):
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


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
