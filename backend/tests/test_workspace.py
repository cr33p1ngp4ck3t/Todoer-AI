"""Workspace regression contracts: schedules, projects, backups and task edits."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from src.api.auth import create_access_token
from src.models.task import Task
from src.models.user import User
from src.services.task_service import normalize_date


@pytest.fixture
def headers(test_user):
    return auth_headers(test_user)


def auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id)})}"}


def test_legacy_datetime_normalization_is_utc():
    assert normalize_date(datetime(2026, 10, 27, 9)) == datetime(
        2026, 10, 27, 9, tzinfo=timezone.utc
    )


@pytest.fixture
def colleagues(db_session):
    users = [
        User(username=name, email=f"{name}@example.com", hashed_password="hash")
        for name in ("editor", "viewer", "outsider")
    ]
    db_session.add_all(users)
    db_session.commit()
    return users


def test_oldest_sort_and_deadline_sort(client, headers, test_user, db_session):
    old = Task(
        owner_id=test_user.id,
        title="Old",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    new = Task(
        owner_id=test_user.id,
        title="New",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        due_date=datetime(2026, 12, 1, tzinfo=timezone.utc),
    )
    db_session.add_all([old, new])
    db_session.commit()
    response = client.get("/tasks?sort_by=created_at_asc", headers=headers)
    assert response.status_code == 200
    assert [task["title"] for task in response.json()] == ["Old", "New"]
    response = client.get("/tasks?sort_by=due_date", headers=headers)
    assert response.status_code == 200
    assert [task["title"] for task in response.json()] == ["New", "Old"]


def test_patch_omitted_fields_preserved_and_explicit_null_clears(client, headers):
    task = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Clear fields",
            "description": "Description",
            "due_date": "2026-12-01T10:00:00Z",
            "tags": ["work"],
        },
    ).json()
    path = f"/tasks/{task['id']}"
    changed = client.patch(path, headers=headers, json={"title": "Renamed"}).json()
    assert changed["description"] == "Description"
    assert changed["due_date"] is not None
    changed = client.patch(
        path, headers=headers, json={"description": None, "due_date": None, "tags": []}
    ).json()
    assert changed["description"] is None
    assert changed["due_date"] is None
    assert changed["tags"] == []


@pytest.mark.parametrize(
    "recurrence,start,expected",
    [
        ("daily", "2026-12-31T09:00:00Z", "2027-01-01T09:00:00+00:00"),
        ("weekly", "2026-12-31T09:00:00Z", "2027-01-07T09:00:00+00:00"),
        ("monthly", "2028-01-31T09:00:00Z", "2028-02-29T09:00:00+00:00"),
    ],
)
def test_recurrence_completion_is_idempotent(
    client, headers, recurrence, start, expected
):
    response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Repeat",
            "due_date": start,
            "recurrence": recurrence,
            "tags": ["routine"],
        },
    )
    assert response.status_code == 201
    task = response.json()
    path = f"/tasks/{task['id']}"
    for status in ("completed", "completed", "pending", "completed"):
        assert (
            client.patch(path, headers=headers, json={"status": status}).status_code
            == 200
        )
    tasks = client.get("/tasks", headers=headers).json()
    assert len(tasks) == 2
    successor = next(item for item in tasks if item["id"] != task["id"])
    assert successor["status"] == "pending"
    assert successor["tags"] == ["routine"]
    assert datetime.fromisoformat(successor["due_date"]) == datetime.fromisoformat(
        expected
    )
    if recurrence == "monthly":
        client.patch(
            f"/tasks/{successor['id']}",
            headers=headers,
            json={
                "title": "Updated routine",
                "due_date": successor["due_date"],
                "recurrence": "monthly",
                "recurrence_timezone": "UTC",
            },
        )
        client.patch(
            f"/tasks/{successor['id']}", headers=headers, json={"status": "completed"}
        )
        tasks = client.get("/tasks", headers=headers).json()
        third = next(item for item in tasks if item["status"] == "pending")
        assert datetime.fromisoformat(third["due_date"]).day == 31


def test_daily_recurrence_keeps_local_time_through_dst(client, headers):
    response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Morning routine",
            "due_date": "2026-03-07T09:00:00-05:00",
            "recurrence": "daily",
            "recurrence_timezone": "America/New_York",
        },
    )
    assert response.status_code == 201
    task = response.json()
    client.patch(f"/tasks/{task['id']}", headers=headers, json={"status": "completed"})
    successor = next(
        item
        for item in client.get("/tasks", headers=headers).json()
        if item["status"] == "pending"
    )
    assert datetime.fromisoformat(successor["due_date"]) == datetime(
        2026, 3, 8, 13, tzinfo=timezone.utc
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "Bad", "recurrence": "daily"},
        {"title": "Bad", "recurrence": "yearly", "due_date": "2026-12-01T09:00Z"},
        {"title": "Bad", "recurrence_timezone": "Invalid/Zone"},
        {"title": "x" * 256},
        {"title": "Bad", "tags": ["x" * 51]},
    ],
)
def test_invalid_tasks_do_not_persist(client, headers, payload):
    assert client.post("/tasks", headers=headers, json=payload).status_code in (
        400,
        422,
    )
    assert client.get("/tasks", headers=headers).json() == []


def test_recurrence_can_be_disabled_and_deadline_cleared(client, headers):
    task = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Routine",
            "due_date": "2026-12-01T09:00Z",
            "recurrence": "daily",
        },
    ).json()
    path = f"/tasks/{task['id']}"
    assert client.patch(path, headers=headers, json={"due_date": None}).status_code in (
        400,
        422,
    )
    response = client.patch(
        path, headers=headers, json={"due_date": None, "recurrence": None}
    )
    assert response.status_code == 200
    assert response.json()["due_date"] is None
    client.patch(path, headers=headers, json={"status": "completed"})
    assert len(client.get("/tasks", headers=headers).json()) == 1


def test_project_invitation_acl_assignment_and_removal(client, headers, colleagues):
    editor, viewer, outsider = colleagues
    response = client.post("/projects", headers=headers, json={"name": "Release"})
    assert response.status_code == 201
    project = response.json()
    project_path = f"/projects/{project['id']}"
    for user, role in ((editor, "editor"), (viewer, "viewer")):
        invite = client.post(
            f"{project_path}/invitations",
            headers=headers,
            json={"email": user.email, "role": role},
        )
        assert invite.status_code in (200, 201)
        assert client.get(project_path, headers=auth_headers(user)).status_code == 404
        pending = client.get("/projects/invitations", headers=auth_headers(user)).json()
        assert len(pending) == 1
        assert (
            client.post(
                f"/projects/invitations/{pending[0]['id']}/accept",
                headers=auth_headers(outsider),
            ).status_code
            == 404
        )
        assert (
            client.post(
                f"/projects/invitations/{pending[0]['id']}/accept",
                headers=auth_headers(user),
            ).status_code
            == 200
        )
    editor_headers, viewer_headers = auth_headers(editor), auth_headers(viewer)
    task_payload = {
        "title": "Ship release",
        "project_id": project["id"],
        "assignee_id": str(editor.id),
    }
    created = client.post("/tasks", headers=editor_headers, json=task_payload)
    assert created.status_code == 201
    task = created.json()
    path = f"/tasks/{task['id']}"
    assert client.get("/tasks", headers=editor_headers).json() == []
    assert (
        len(
            client.get(
                f"/tasks?project_id={project['id']}", headers=viewer_headers
            ).json()
        )
        == 1
    )
    assert client.get(path, headers=viewer_headers).status_code == 200
    assert (
        client.patch(
            path, headers=viewer_headers, json={"status": "completed"}
        ).status_code
        == 403
    )
    assert client.delete(path, headers=viewer_headers).status_code == 403
    assert (
        client.post("/tasks", headers=viewer_headers, json=task_payload).status_code
        == 403
    )
    assert client.get(path, headers=auth_headers(outsider)).status_code == 404
    assert (
        client.get(
            f"/tasks?project_id={project['id']}", headers=auth_headers(outsider)
        ).status_code
        == 404
    )
    assert client.patch(
        path, headers=headers, json={"assignee_id": str(outsider.id)}
    ).status_code in (400, 422)
    assert (
        client.post(
            f"{project_path}/invitations",
            headers=editor_headers,
            json={"email": outsider.email, "role": "editor"},
        ).status_code
        == 403
    )
    assert client.delete(
        f"{project_path}/members/{project['owner_id']}", headers=headers
    ).status_code in (400, 403)
    assert (
        client.delete(
            f"{project_path}/members/{editor.id}", headers=headers
        ).status_code
        == 204
    )
    assert client.get(path, headers=editor_headers).status_code == 404
    assert client.get(path, headers=headers).json()["assignee_id"] is None
    assert client.get("/tasks/export", headers=headers).json()["tasks"] == []


@pytest.mark.parametrize("email", [" Mixed@Example.test ", "mixed@example.test"])
def test_project_invites_match_existing_mixed_case_email(
    client, headers, db_session, email
):
    colleague = User(
        username="mixed", email="Mixed@Example.test", hashed_password="hash"
    )
    db_session.add(colleague)
    db_session.commit()
    project = client.post("/projects", headers=headers, json={"name": "Team"}).json()
    invitation = client.post(
        f"/projects/{project['id']}/invitations",
        headers=headers,
        json={"email": email},
    )
    assert invitation.status_code == 201
    assert invitation.json()["user_id"] == str(colleague.id)


def test_project_invites_reject_ambiguous_email_but_prefer_exact_match(
    client, headers, db_session
):
    colleagues = [
        User(username="mixed", email="Mixed@Example.test", hashed_password="hash"),
        User(username="lower", email="mixed@example.test", hashed_password="hash"),
    ]
    db_session.add_all(colleagues)
    db_session.commit()
    project = client.post("/projects", headers=headers, json={"name": "Team"}).json()
    path = f"/projects/{project['id']}/invitations"
    ambiguous = client.post(path, headers=headers, json={"email": "MIXED@EXAMPLE.TEST"})
    assert ambiguous.status_code == 400
    assert "ambiguous" in ambiguous.json()["detail"].lower()
    assert client.get(f"/projects/{project['id']}", headers=headers).json()[
        "members"
    ] == [
        {
            "user_id": project["owner_id"],
            "username": "tester",
            "email": "tester@example.com",
            "role": "owner",
            "accepted": True,
        }
    ]
    exact = client.post(path, headers=headers, json={"email": " Mixed@Example.test "})
    assert exact.status_code == 201
    assert exact.json()["user_id"] == str(colleagues[0].id)


def test_backup_round_trip_dedup_and_atomic_validation(client, headers, colleagues):
    source_task = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Backup me",
            "description": "Details",
            "tags": ["backup"],
            "due_date": "2026-12-01T09:00Z",
            "recurrence": "weekly",
        },
    ).json()
    exported = client.get("/tasks/export", headers=headers)
    assert exported.status_code == 200
    backup = exported.json()
    assert backup["version"] == 1
    assert backup["tasks"][0]["id"] == source_task["id"]
    target_headers = auth_headers(colleagues[0])
    imported = client.post("/tasks/import", headers=target_headers, json=backup)
    assert imported.status_code == 200
    assert imported.json() == {"imported": 1, "skipped": 0}
    restored = client.get("/tasks", headers=target_headers).json()[0]
    assert restored["id"] != source_task["id"]
    assert restored["title"] == source_task["title"]
    assert restored["tags"] == ["backup"]
    assert client.post("/tasks/import", headers=target_headers, json=backup).json() == {
        "imported": 0,
        "skipped": 1,
    }
    invalid = {
        "version": 1,
        "tasks": [
            dict(backup["tasks"][0], id=str(uuid4())),
            {"id": str(uuid4()), "title": ""},
        ],
    }
    assert client.post(
        "/tasks/import", headers=target_headers, json=invalid
    ).status_code in (400, 422)
    assert len(client.get("/tasks", headers=target_headers).json()) == 1
    invalid["tasks"][1]["title"] = "Valid shape but invalid schedule"
    invalid["tasks"][1]["recurrence"] = "daily"
    assert (
        client.post("/tasks/import", headers=target_headers, json=invalid).status_code
        == 400
    )
    assert len(client.get("/tasks", headers=target_headers).json()) == 1
    assert client.post("/tasks/import", headers=headers, json=backup).json() == {
        "imported": 0,
        "skipped": 1,
    }
    assert (
        client.post(
            "/tasks/import", headers=target_headers, json={"version": 2, "tasks": []}
        ).status_code
        == 422
    )
