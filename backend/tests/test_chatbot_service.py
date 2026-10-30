from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlmodel import select
from src.models.conversation import Conversation
from src.models.message import Message
from src.services.chatbot_service import ChatbotService
from src.services.llm_providers import LLMProvider, LLMProviderManager


@pytest.fixture
def chatbot(test_user, db_session):
    return ChatbotService(test_user.id, db_session)


@pytest.mark.parametrize(
    "groq,gemini,fail,preferred,expected",
    [
        (True, True, False, None, LLMProvider.GROQ),
        (True, True, True, None, LLMProvider.GEMINI),
        (True, True, True, LLMProvider.GROQ, LLMProvider.GEMINI),
        (True, False, True, None, None),
        (False, True, False, None, LLMProvider.GEMINI),
        (False, True, False, LLMProvider.GROQ, LLMProvider.GEMINI),
        (False, False, False, None, None),
    ],
)
async def test_provider_fallback(
    chatbot, monkeypatch, groq, gemini, fail, preferred, expected
):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq" if groq else "")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini" if gemini else "")
    monkeypatch.setenv("DEFAULT_LLM_PROVIDER", "groq")
    chatbot.provider_manager = LLMProviderManager()
    groq_client, gemini_client = object(), object()
    create_groq = AsyncMock(
        return_value=groq_client,
        side_effect=RuntimeError("unavailable") if fail else None,
    )
    create_gemini = Mock(return_value=gemini_client)
    monkeypatch.setattr("src.services.chatbot_service.create_groq_client", create_groq)
    monkeypatch.setattr(
        "src.services.chatbot_service.create_gemini_client", create_gemini
    )
    if expected is None:
        with pytest.raises(ValueError, match="Failed to create any|No LLM provider"):
            await chatbot.get_provider_client(preferred)
    else:
        client, provider = await chatbot.get_provider_client(preferred)
        assert provider == expected
        assert client is (
            groq_client if expected == LLMProvider.GROQ else gemini_client
        )
    assert create_groq.await_count == int(groq)
    assert create_gemini.call_count == int(expected == LLMProvider.GEMINI)


@pytest.mark.parametrize("provider", [LLMProvider.GROQ, LLMProvider.GEMINI])
async def test_empty_client_is_rejected(chatbot, monkeypatch, provider):
    config = SimpleNamespace(api_key="test", model="test-model")
    monkeypatch.setattr(
        "src.services.chatbot_service.create_groq_client", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(
        "src.services.chatbot_service.create_gemini_client", Mock(return_value=None)
    )
    with pytest.raises(ValueError, match="API key not configured"):
        if provider == LLMProvider.GROQ:
            await chatbot._create_groq_client(config)
        else:
            chatbot._create_gemini_client(config)


@pytest.mark.parametrize("fail", [False, True])
async def test_chat_stream_persists_history_and_closes_client(
    chatbot, db_session, monkeypatch, fail
):
    client = SimpleNamespace(close=AsyncMock())
    calls = []

    async def chat(**kwargs):
        calls.append(kwargs)
        yield {"content": "hello"}
        if fail:
            raise RuntimeError("provider unavailable")

    client.chat = chat
    monkeypatch.setattr(
        chatbot,
        "get_provider_client",
        AsyncMock(return_value=(client, LLMProvider.GROQ)),
    )
    chunks = [chunk async for chunk in chatbot.chat("new task", stream=False)]
    assert chunks == (
        [{"content": "hello"}, {"error": "provider unavailable"}]
        if fail
        else [{"content": "hello"}]
    )
    client.close.assert_awaited_once()
    assert calls[0]["messages"] == [
        {"role": "system", "content": chatbot.SYSTEM_PROMPT},
        {"role": "user", "content": "new task"},
    ]
    assert calls[0]["tools"] == chatbot.mcp_tools
    assert calls[0]["stream"] is False
    assert db_session.exec(select(Message)).one().content == "new task"


async def test_conversations_are_owned_and_history_is_bounded(chatbot, db_session):
    owned = await chatbot._get_or_create_conversation(None)
    assert await chatbot._get_or_create_conversation(owned.id) is owned
    foreign = Conversation(user_id=uuid4())
    db_session.add(foreign)
    db_session.commit()
    replacement = await chatbot._get_or_create_conversation(foreign.id)
    assert replacement.id != foreign.id and replacement.user_id == chatbot.user_id
    assert (
        await chatbot._get_or_create_conversation(uuid4())
    ).user_id == chatbot.user_id
    for i in range(3):
        db_session.add(
            Message(
                conversation_id=owned.id,
                role="user",
                content=str(i),
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
                + timedelta(seconds=i),
            )
        )
        db_session.commit()
    history = await chatbot._build_message_history(owned.id, max_messages=2)
    assert [item["content"] for item in history[1:]] == ["1", "2"]


async def test_tool_call_dispatches_to_mcp(chatbot):
    result = await chatbot.execute_tool_call("add_task", {"title": "From chat"})
    assert result["success"] and result["data"]["title"] == "From chat"
