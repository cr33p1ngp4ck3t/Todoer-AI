import io
import json
import logging
import sys
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
import sentry_sdk
from fastapi.testclient import TestClient
from sentry_sdk.transport import Transport
from src.api.auth import create_access_token
from src.lib.logging import JSONFormatter
from src.lib.logging_config import (
    RequestContextFilter,
    request_context,
    setup_logging,
)


@pytest.mark.parametrize(
    "name",
    ["todo-api", "task_service", "chatbot_service", "mcp_server", "uvicorn.access"],
)
def test_shared_json_logging(name, monkeypatch):
    stream = io.StringIO()
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    uvicorn_handlers = {
        key: logging.getLogger(key).handlers[:]
        for key in ("uvicorn", "uvicorn.error", "uvicorn.access")
    }
    monkeypatch.setattr("sys.stderr", stream)
    context = {"request_id": str(uuid4()), "user_id": str(uuid4())}
    token = request_context.set(context)
    try:
        setup_logging()
        logging.getLogger(name).warning("Sample %s", "message")
        record = json.loads(stream.getvalue())
        assert record.items() >= context.items()
        assert record["level"] == "WARNING"
        assert record["message"] == "Sample message"
        assert record["logger"] == name
        assert record["timestamp"].endswith("+00:00")
    finally:
        request_context.reset(token)
        root.handlers, root.level = handlers, level
        for key, previous in uvicorn_handlers.items():
            logging.getLogger(key).handlers = previous


def test_explicit_context_and_exception():
    try:
        raise ValueError("sample error")
    except ValueError:
        record = logging.LogRecord(
            "todo-api", logging.ERROR, "", 1, "failed", (), sys.exc_info()
        )
    record.user_id = "explicit-user"
    record.trace_id = "legacy-trace"
    RequestContextFilter().filter(record)
    result = json.loads(JSONFormatter().format(record))
    assert result["request_id"] is None
    assert result["user_id"] == "explicit-user"
    assert result["trace_id"] == "legacy-trace"
    assert "ValueError: sample error" in result["exception"]


def test_request_and_user_context_are_cleared(client, test_user, monkeypatch):
    from src.services.task_service import TaskService

    seen = []
    original = TaskService.get_all

    def get_all(self, *args, **kwargs):
        seen.append(request_context.get().copy())
        return original(self, *args, **kwargs)

    monkeypatch.setattr(TaskService, "get_all", get_all)
    request_id = str(uuid4())
    response = client.get(
        "/tasks",
        headers={
            "Authorization": f"Bearer {create_access_token({'sub': str(test_user.id)})}",
            "X-Request-ID": request_id,
        },
    )
    assert response.status_code == 200
    assert response.headers["x-request-id"] == request_id
    assert seen == [{"request_id": request_id, "user_id": str(test_user.id)}]
    anonymous = client.get("/health/live", headers={"X-Request-ID": "invalid"})
    assert str(UUID(anonymous.headers["x-request-id"])) != request_id
    assert client.get("/tasks").status_code == 401
    assert request_context.get() is None


@pytest.mark.parametrize("enabled", [False, True])
def test_optional_sentry_startup(client, monkeypatch, enabled):
    from src.main import app

    monkeypatch.setenv("SENTRY_DSN", "https://key@example.com/1" if enabled else "")
    init = Mock()
    monkeypatch.setattr(sentry_sdk, "init", init)
    with TestClient(app) as test_client:
        assert test_client.get("/health/live").status_code == 200
    assert init.call_count == int(enabled)
    if enabled:
        assert init.call_args.kwargs["include_local_variables"] is False
        assert init.call_args.kwargs["default_integrations"] is False


@pytest.mark.parametrize("enabled", [False, True])
async def test_unhandled_error_has_request_id_and_optional_tracking(
    client, test_user, monkeypatch, enabled
):
    from src.main import app

    monkeypatch.setenv("SENTRY_DSN", "https://key@example.com/1" if enabled else "")
    captured = []
    monkeypatch.setattr(sentry_sdk, "init", Mock())

    class MemoryTransport(Transport):
        def capture_envelope(self, envelope):
            for item in envelope.items:
                if item.type == "event":
                    captured.append(item.payload.json)

    sdk_client = sentry_sdk.Client(
        dsn="https://key@example.com/1",
        transport=MemoryTransport,
        default_integrations=False,
        auto_enabling_integrations=False,
        include_local_variables=False,
    )
    previous_client = sentry_sdk.get_client()
    sentry_sdk.get_global_scope().set_client(sdk_client)
    original = app.router.routes[:]
    request_id = str(uuid4())

    async def fail():
        request_context.get()["user_id"] = str(test_user.id)
        raise RuntimeError("sample crash")

    app.add_api_route("/logging-test-error", fail)
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            response = test_client.get(
                "/logging-test-error", headers={"X-Request-ID": request_id}
            )
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error"}
        assert response.headers["x-request-id"] == request_id
        assert len(captured) == int(enabled)
        if enabled:
            assert captured[0]["tags"]["request_id"] == request_id
            assert captured[0]["user"]["id"] == str(test_user.id)
            assert captured[0]["exception"]["values"][0]["type"] == "RuntimeError"
            assert "request" not in captured[0]
            frames = captured[0]["exception"]["values"][0]["stacktrace"]["frames"]
            assert not any("vars" in frame for frame in frames)
    finally:
        app.router.routes[:] = original
        sentry_sdk.get_global_scope().set_client(previous_client)
        sdk_client.close()
