"""Groq LLM client using OpenAI-compatible API.

Groq's API is fully compatible with the OpenAI API format,
making it easy to integrate with existing OpenAI client libraries.

Groq provides ultra-fast inference for open-source models like Llama, Gemma, etc.
"""
import asyncio
from typing import AsyncIterator, Dict, Any, List, Optional
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk, ChatCompletion
from src.services.llm_providers import LLMConfig, LLMProvider
import logging

logger = logging.getLogger("todo-api")


class GroqClient:
    """Client for interacting with Groq API (OpenAI-compatible)."""

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, config: LLMConfig):
        """Initialize Groq client with configuration.

        Args:
            config: LLM configuration with API key and model settings
        """
        self.config = config
        self.client = AsyncOpenAI(
            base_url=self.BASE_URL,
            api_key=config.api_key,
        )

    @property
    def provider(self) -> LLMProvider:
        """Get the provider type."""
        return LLMProvider.GROQ

    @property
    def model(self) -> str:
        """Get the model name."""
        return self.config.model

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = True,
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Send a chat request to Groq.

        Args:
            messages: List of chat messages with role and content
            tools: Optional list of tool definitions for function calling
            stream: Whether to stream the response

        Yields:
            Chat completion chunks if streaming
        """
        logger.info(f"Sending request to Groq with {len(messages)} messages, model: {self.config.model}")

        try:
            if tools:
                # Request with tool definitions
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    tools=tools,
                    stream=stream,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )
            else:
                # Simple chat request
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    stream=stream,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )

            if stream:
                async for chunk in response:
                    yield chunk
            else:
                yield response

        except Exception as e:
            logger.error(f"Groq API error: {e}", exc_info=True)
            raise

    async def close(self):
        """Close the async client."""
        await self.client.close()


async def create_groq_client(
    api_key: Optional[str] = None,
    model: str = "llama-3.3-70b-versatile",
) -> Optional[GroqClient]:
    """Create a Groq client instance.

    Args:
        api_key: Optional API key (defaults to environment variable)
        model: Model name to use (default: llama-3.3-70b-versatile)

    Returns:
        GroqClient instance or None if API key not available
    """
    from src.services.llm_providers import LLMProvider, get_provider_manager

    if api_key is None:
        manager = get_provider_manager()
        config = manager.get_config(LLMProvider.GROQ)
        if config is None or not config.is_available():
            logger.warning("Groq API key not configured")
            return None
        return GroqClient(config)

    config = LLMConfig(
        provider=LLMProvider.GROQ,
        model=model,
        api_key=api_key,
    )
    return GroqClient(config)
