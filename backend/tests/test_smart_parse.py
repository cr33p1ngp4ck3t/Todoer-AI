"""AI drafts stay bounded and safe when providers fail or return bad data."""

import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from src.api.auth import create_access_token
from src.services.chatbot_service import ChatbotService
from src.services.llm_providers import LLMProvider


@pytest.fixture
def chatbot(test_user, db_session):
    return ChatbotService(test_user.id, db_session)


def provider_reply(monkeypatch, chatbot, payload, provider=LLMProvider.GROQ):
    client = SimpleNamespace(close=AsyncMock())

    async def chat(**kwargs):
        client.messages = kwargs["messages"]
        if isinstance(payload, Exception):
            raise payload
        content = payload if isinstance(payload, str) else json.dumps(payload)
        if provider == LLMProvider.GEMINI:
            yield SimpleNamespace(text=content)
        else:
            yield SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
            )

    client.chat = chat
    monkeypatch.setattr(
        chatbot, "get_provider_client", AsyncMock(return_value=(client, provider))
    )
    return client


async def test_draft_preserves_deadline_and_ignores_provider_authority(
    chatbot, monkeypatch
):
    client = provider_reply(
        monkeypatch,
        chatbot,
        {
            "title": "  Standup  ",
            "priority": "high",
            "tags": [" Work ", "work", "TEAM"],
            "due_date": "2026-10-28T09:00:00+05:00",
            "recurrence": "weekly",
            "owner_id": "someone-else",
            "project_id": "someone-elses-project",
            "status": "completed",
            "source": "fallback",
            "warnings": ["provider-injected"],
            "recurrence_timezone": "UTC",
        },
    )
    result = await chatbot.smart_parse_task(
        "Standup tomorrow at 9 every week",
        reference_time=datetime(2026, 10, 27, 12, tzinfo=timezone.utc),
        timezone="Asia/Karachi",
    )
    assert result["title"] == "Standup"
    assert result["tags"] == ["work", "team"]
    assert datetime.fromisoformat(result["due_date"]) == datetime(
        2026, 10, 28, 4, tzinfo=timezone.utc
    )
    assert result["recurrence"] == "weekly"
    assert result["recurrence_timezone"] == "Asia/Karachi"
    assert result["source"] == "ai"
    assert result["warnings"] == []
    assert not {"owner_id", "project_id", "status"}.intersection(result)
    prompt = "\n".join(message["content"] for message in client.messages)
    assert "2026-10-27T17:00:00+05:00" in prompt
    assert "Asia/Karachi" in prompt
    client.close.assert_awaited_once()


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        [],
        {"title": " "},
        {"title": "x" * 256},
        {"title": "Valid", "description": "x" * 1001},
        {"title": "Valid", "tags": ["x" * 51]},
        {"title": "Valid", "tags": ["tag"] * 21},
        {"title": "Valid", "priority": "urgent"},
        {"title": "Valid", "due_date": "not-a-date"},
        {"title": "Valid", "due_date": "2026-10-28T09:00:00"},
        {"title": "Valid", "recurrence": "weekly"},
        RuntimeError("provider internal details"),
    ],
)
async def test_bad_provider_output_falls_back_without_invented_dates(
    chatbot, monkeypatch, payload
):
    client = provider_reply(monkeypatch, chatbot, payload)
    result = await chatbot.smart_parse_task("  Keep my original task  ")
    assert result["title"] == "Keep my original task"
    assert result["due_date"] is None
    assert result["recurrence"] is None
    assert result["source"] == "fallback"
    assert result["warnings"]
    assert "internal details" not in str(result)
    client.close.assert_awaited_once()


async def test_no_provider_has_usable_bounded_fallback(chatbot, monkeypatch):
    monkeypatch.setattr(
        chatbot, "get_provider_client", AsyncMock(side_effect=ValueError("No provider"))
    )
    result = await chatbot.smart_parse_task("x" * 4000)
    assert len(result["title"]) == 255
    assert len(result["description"]) <= 1000
    assert result["source"] == "fallback"
    assert result["due_date"] is None


async def test_gemini_fenced_json_and_sync_cleanup(chatbot, monkeypatch):
    client = provider_reply(
        monkeypatch,
        chatbot,
        '```json\n{"title":"Buy milk","priority":"low"}\n```',
        provider=LLMProvider.GEMINI,
    )
    client.close = Mock()
    result = await chatbot.smart_parse_task("Buy milk")
    assert result["title"] == "Buy milk"
    assert result["source"] == "ai"
    client.close.assert_called_once()


async def test_cleanup_failure_does_not_lose_draft(chatbot, monkeypatch):
    client = provider_reply(monkeypatch, chatbot, {"title": "Buy milk"})
    client.close.side_effect = RuntimeError("cleanup failed")
    result = await chatbot.smart_parse_task("Buy milk")
    assert result["source"] == "ai"


async def test_slow_provider_times_out_and_closes(chatbot, monkeypatch):
    client = SimpleNamespace(close=AsyncMock())

    async def chat(**kwargs):
        await asyncio.sleep(1)
        yield SimpleNamespace(text="{}")

    client.chat = chat
    monkeypatch.setattr(
        chatbot,
        "get_provider_client",
        AsyncMock(return_value=(client, LLMProvider.GROQ)),
    )
    monkeypatch.setattr("src.services.chatbot_service.SMART_PARSE_TIMEOUT", 0.01)
    result = await chatbot.smart_parse_task("Buy milk")
    assert result["source"] == "fallback"
    client.close.assert_awaited_once()


@pytest.fixture
def auth_headers(test_user):
    return {
        "Authorization": f"Bearer {create_access_token({'sub': str(test_user.id)})}"
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"text": ""},
        {"text": " "},
        {"text": "x" * 4001},
        {"text": "Buy milk", "timezone": "Imaginary/Place"},
        {"text": "Buy milk", "reference_time": "2026-10-27T12:00:00"},
        {"text": "Buy milk", "reference_time": "invalid"},
    ],
)
def test_endpoint_validates_text_and_time_context(client, auth_headers, payload):
    assert (
        client.post(
            "/api/chat/smart-parse", headers=auth_headers, json=payload
        ).status_code
        == 422
    )


def test_endpoint_requires_authentication(client):
    assert (
        client.post("/api/chat/smart-parse", json={"text": "Buy milk"}).status_code
        == 401
    )


def test_endpoint_without_provider_returns_previewable_draft(client, auth_headers):
    response = client.post(
        "/api/chat/smart-parse",
        headers=auth_headers,
        json={"text": "Buy milk", "timezone": "Asia/Karachi"},
    )
    assert response.status_code == 200
    draft = response.json()
    assert draft["title"] == "Buy milk"
    assert draft["source"] == "fallback"
    assert draft["warnings"]
    assert draft["recurrence_timezone"] == "Asia/Karachi"
