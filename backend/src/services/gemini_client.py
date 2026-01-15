"""Gemini LLM client using Google GenAI SDK.

This module provides a client for interacting with Google's Gemini API
for LLM responses with support for function calling using the new google.genai package.
"""
import asyncio
import os
from typing import AsyncIterator, Dict, Any, List, Optional
import google.generativeai as genai
from src.services.llm_providers import LLMConfig, LLMProvider
import logging

logger = logging.getLogger("todo-api")


class GeminiClient:
    """Client for interacting with Gemini API using google.genai."""

    def __init__(self, config: LLMConfig):
        """Initialize Gemini client with configuration.

        Args:
            config: LLM configuration with API key and model settings
        """
        self.config = config
        self._client = None
        self._model = None

    @property
    def provider(self) -> LLMProvider:
        """Get the provider type."""
        return LLMProvider.GEMINI

    @property
    def model(self) -> str:
        """Get the model name."""
        return self.config.model

    def _get_client(self):
        """Get or create the genai client."""
        if self._client is None:
            self._client = genai.Client(api_key=self.config.api_key)
        return self._client

    def _convert_tools_for_gemini(
        self, tools: List[Dict[str, Any]]
    ) -> List[genai.types.FunctionDeclaration]:
        """Convert OpenAI-style tool definitions to Gemini format.

        Args:
            tools: List of OpenAI-style tool definitions

        Returns:
            List of Gemini FunctionDeclaration objects
        """
        gemini_tools = []

        for tool in tools:
            if tool.get("type") == "function":
                func_def = tool.get("function", {})
                declaration = genai.types.FunctionDeclaration(
                    name=func_def.get("name"),
                    description=func_def.get("description", ""),
                    parameters=func_def.get("parameters", {}),
                )
                gemini_tools.append(declaration)

        return gemini_tools

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = True,
    ) -> AsyncIterator[Any]:
        """Send a chat request to Gemini.

        Args:
            messages: List of chat messages with role and content
            tools: Optional list of tool definitions for function calling
            stream: Whether to stream the response

        Yields:
            Response chunks or completion depending on stream mode
        """
        logger.info(f"Sending request to Gemini with {len(messages)} messages")

        try:
            client = self._get_client()
            model_name = f"gemini-{self.config.model}" if not self.config.model.startswith("gemini-") else self.config.model

            # Convert messages to Gemini format
            contents = []
            for msg in messages:
                if msg["role"] == "system":
                    continue  # System prompt handled separately
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

            # Prepare tools if provided
            genai_tools = None
            if tools:
                genai_tools = self._convert_tools_for_gemini(tools)

            config = {
                "generation_config": {
                    "max_output_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                }
            }

            if genai_tools:
                config["tools"] = genai_tools

            # Make the API call
            if stream:
                response = client.models.generate_content_streaming(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                async for chunk in response:
                    yield chunk
            else:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                yield response

        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            raise

    def close(self):
        """Close the client (google.genai doesn't require explicit close)."""
        pass


def create_gemini_client(
    api_key: Optional[str] = None,
    model: str = "gemini-1.5-flash",
) -> Optional[GeminiClient]:
    """Create a Gemini client instance.

    Args:
        api_key: Optional API key (defaults to environment variable)
        model: Model name to use

    Returns:
        GeminiClient instance or None if API key not available
    """
    from src.services.llm_providers import LLMProvider, get_provider_manager

    if api_key is None:
        manager = get_provider_manager()
        config = manager.get_config(LLMProvider.GEMINI)
        if config is None or not config.is_available():
            logger.warning("Gemini API key not configured")
            return None
        return GeminiClient(config)

    config = LLMConfig(
        provider=LLMProvider.GEMINI,
        model=model,
        api_key=api_key,
    )
    return GeminiClient(config)
