from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from src import main


@pytest.mark.parametrize("path", ["/health", "/health/ready", "/health/live"])
def test_health_endpoints(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "status" in response.json()


@pytest.mark.parametrize("path", ["/health", "/health/ready"])
def test_database_failure_is_unhealthy(client, monkeypatch, path):
    @contextmanager
    def unavailable_session():
        raise OperationalError("SELECT 1", {}, RuntimeError("private database details"))
        yield

    monkeypatch.setattr(main, "get_session", unavailable_session)
    response = client.get(path)
    assert response.status_code == 503
    assert "private database details" not in response.text
    assert client.get("/health/live").status_code == 200


@pytest.mark.parametrize(
    "origin, allowed_origin",
    [
        ("http://localhost:3000", "http://localhost:3000"),
        ("https://untrusted.example", None),
    ],
)
def test_unhandled_errors_preserve_cors_without_exposing_details(
    client, monkeypatch, origin, allowed_origin
):
    def broken_query(*args, **kwargs):
        raise RuntimeError("private database credentials")

    with TestClient(main.app, raise_server_exceptions=False) as safe_client:
        monkeypatch.setattr(main, "select", broken_query)
        response = safe_client.get("/health/ready", headers={"Origin": origin})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert response.headers.get("access-control-allow-origin") == allowed_origin
    if allowed_origin:
        assert response.headers["access-control-allow-credentials"] == "true"
        assert response.headers["access-control-expose-headers"] == "X-Request-ID"
        assert "Origin" in response.headers["vary"]
    assert response.headers["x-request-id"]
