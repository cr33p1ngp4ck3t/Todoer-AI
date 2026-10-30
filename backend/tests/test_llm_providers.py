"""Tests for LLM provider integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.services.chatbot_service import ChatbotService
from src.services.gemini_client import GeminiClient, create_gemini_client
from src.services.groq_client import GroqClient, create_groq_client
from src.services.llm_providers import (
    LLMConfig,
    LLMProvider,
    LLMProviderManager,
)


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""

    def test_config_creation(self):
        """Test creating an LLM config."""
        config = LLMConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.3-70b-versatile",
            api_key="test-key",
        )

        assert config.provider == LLMProvider.GROQ
        assert config.model == "llama-3.3-70b-versatile"
        assert config.api_key == "test-key"
        assert config.max_tokens == 2000
        assert config.temperature == 0.7

    def test_is_available_with_key(self):
        """Test is_available returns True when key is set."""
        config = LLMConfig(
            provider=LLMProvider.GROQ,
            model="test",
            api_key="valid-key",
        )
        assert config.is_available() is True

    def test_is_available_without_key(self):
        """Test is_available returns False when key is missing."""
        config = LLMConfig(
            provider=LLMProvider.GROQ,
            model="test",
            api_key=None,
        )
        assert config.is_available() is False

    def test_is_available_with_empty_key(self):
        """Test is_available returns False when key is empty string."""
        config = LLMConfig(
            provider=LLMProvider.GROQ,
            model="test",
            api_key="",
        )
        assert config.is_available() is False


class TestLLMProviderManager:
    """Tests for LLMProviderManager."""

    def test_get_available_providers_all_configured(self):
        """Test getting providers when all are configured."""
        with patch.dict(
            "os.environ", {"GROQ_API_KEY": "groq-key", "GEMINI_API_KEY": "gemini-key"}
        ):
            manager = LLMProviderManager()
            providers = manager.get_available_providers()

            assert LLMProvider.GROQ in providers
            assert LLMProvider.GEMINI in providers

    def test_get_available_providers_only_groq(self):
        """Test getting providers when only Groq is configured."""
        with patch.dict("os.environ", {"GROQ_API_KEY": "groq-key"}, clear=False):
            # Clear other env vars
            import os

            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]

            manager = LLMProviderManager()
            providers = manager.get_available_providers()

            assert LLMProvider.GROQ in providers
            assert LLMProvider.GEMINI not in providers

    def test_get_default_provider_groq(self):
        """Test default provider selection when Groq is set."""
        with patch.dict(
            "os.environ",
            {
                "GROQ_API_KEY": "groq-key",
                "GEMINI_API_KEY": "gemini-key",
                "DEFAULT_LLM_PROVIDER": "groq",
            },
        ):
            manager = LLMProviderManager()
            default = manager.get_default_provider()

            assert default == LLMProvider.GROQ

    def test_get_default_provider_gemini(self):
        """Test default provider selection when Gemini is set."""
        with patch.dict(
            "os.environ",
            {
                "GROQ_API_KEY": "groq-key",
                "GEMINI_API_KEY": "gemini-key",
                "DEFAULT_LLM_PROVIDER": "gemini",
            },
        ):
            manager = LLMProviderManager()
            default = manager.get_default_provider()

            assert default == LLMProvider.GEMINI

    def test_get_default_fallback(self):
        """Test fallback when default provider is not available."""
        with patch.dict(
            "os.environ",
            {
                "GROQ_API_KEY": "groq-key",
                "GEMINI_API_KEY": "gemini-key",
                "DEFAULT_LLM_PROVIDER": "groq",
            },
        ):
            manager = LLMProviderManager()
            primary, fallback = manager.get_primary_with_fallback()

            # With both configured, primary should be Groq (default)
            assert primary is not None
            assert primary.provider == LLMProvider.GROQ
            # Fallback should be Gemini
            assert fallback is not None
            assert fallback.provider == LLMProvider.GEMINI

    def test_get_config(self):
        """Test getting config for a specific provider."""
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
            manager = LLMProviderManager()
            config = manager.get_config(LLMProvider.GROQ)

            assert config is not None
            assert config.provider == LLMProvider.GROQ
            assert config.api_key == "test-key"


class TestGroqClient:
    """Tests for GroqClient."""

    def test_client_initialization(self):
        """Test client creation with config."""
        config = LLMConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.3-70b-versatile",
            api_key="test-key",
        )
        client = GroqClient(config)

        assert client.provider == LLMProvider.GROQ
        assert client.model == "llama-3.3-70b-versatile"

    @pytest.mark.asyncio
    async def test_chat_without_tools(self):
        """Test basic chat request without tools."""
        config = LLMConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.3-70b-versatile",
            api_key="test-key",
        )
        client = GroqClient(config)

        # Mock the client response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="Hello!"))]

        # Create an async iterator
        async def mock_stream():
            yield mock_chunk

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()
            messages = [{"role": "user", "content": "Hi"}]

            response_chunks = []
            async for chunk in client.chat(messages, stream=True):
                response_chunks.append(chunk)

            assert len(response_chunks) == 1


class TestGeminiClient:
    """Tests for GeminiClient."""

    def test_client_initialization(self):
        """Test client creation with config."""
        config = LLMConfig(
            provider=LLMProvider.GEMINI,
            model="gemini-1.5-flash",
            api_key="test-key",
        )
        client = GeminiClient(config)

        assert client.provider == LLMProvider.GEMINI
        assert client.model == "gemini-1.5-flash"


class TestChatbotService:
    """Tests for ChatbotService."""

    def test_service_initialization(self, test_user, db_session):
        """Test service creation with user context."""
        service = ChatbotService(
            user_id=test_user.id,
            session=db_session,
        )

        assert service.user_id == test_user.id
        assert service.session == db_session
        assert service.mcp_handler is not None
        assert len(service.mcp_tools) == 7

    def test_system_prompt(self, test_user, db_session):
        """Test system prompt is properly set."""
        service = ChatbotService(
            user_id=test_user.id,
            session=db_session,
        )

        assert "You are a helpful AI assistant" in service.SYSTEM_PROMPT
        assert "Add tasks" in service.SYSTEM_PROMPT  # "Add tasks" not "add_task"
        assert "List tasks" in service.SYSTEM_PROMPT  # "List tasks" not "list_tasks"

    @pytest.mark.asyncio
    async def test_get_provider_client_fails_without_config(
        self, test_user, db_session
    ):
        """Test that service fails gracefully when no provider is configured."""
        # Mock provider manager to return no providers
        mock_manager = MagicMock()
        mock_manager.get_primary_with_fallback.return_value = (None, None)

        service = ChatbotService(
            user_id=test_user.id,
            session=db_session,
            provider_manager=mock_manager,
        )

        with pytest.raises(ValueError, match="No LLM provider is configured"):
            await service.get_provider_client()


class TestProviderFactory:
    """Tests for provider factory functions."""

    @pytest.mark.asyncio
    async def test_create_groq_client_no_key(self):
        """Test create_groq_client returns None without API key."""
        with patch("src.services.llm_providers.get_provider_manager") as mock_manager:
            mock_manager.return_value.get_config.return_value = None

            client = await create_groq_client()
            assert client is None

    def test_create_gemini_client_no_key(self):
        """Test create_gemini_client returns None without API key."""
        with patch("src.services.llm_providers.get_provider_manager") as mock_manager:
            mock_manager.return_value.get_config.return_value = None

            client = create_gemini_client()
            assert client is None
