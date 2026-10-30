"""Exercise a fresh local stack; creates a unique test account and deletes its task."""

import json
from urllib.request import Request, urlopen
from uuid import uuid4


def request(path, payload=None, token=None, method=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode() if payload is not None else None
    with urlopen(
        Request(
            f"http://localhost:8000{path}", data=data, headers=headers, method=method
        ),
        timeout=10,
    ) as response:
        body = response.read()
        return response.status, json.loads(body) if body else None


def main():
    username = f"smoke-{uuid4().hex}"
    account = {
        "username": username,
        "email": f"{username}@example.com",
        "password": uuid4().hex,
    }
    status, user = request("/users/register", account)
    assert status == 201 and user["username"] == username
    status, tokens = request("/users/login", account)
    assert status == 200
    token = tokens["access_token"]
    status, task = request(
        "/tasks", {"title": "Compose smoke test", "tags": ["smoke"]}, token
    )
    assert status == 201 and task["tags"] == ["smoke"]
    try:
        status, tasks = request("/tasks", token=token)
        assert status == 200 and any(item["id"] == task["id"] for item in tasks)
        status, updated = request(
            f"/tasks/{task['id']}", {"status": "completed"}, token, method="PATCH"
        )
        assert status == 200 and updated["status"] == "completed"
        status, _ = request("/auth/refresh", {"refresh_token": tokens["refresh_token"]})
        assert status == 200
    finally:
        status, _ = request(f"/tasks/{task['id']}", token=token, method="DELETE")
        assert status == 204
    print("Registration, login, task CRUD, and token refresh passed.")


if __name__ == "__main__":
    main()
