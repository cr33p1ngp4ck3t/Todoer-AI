"""LLM Provider configuration and abstraction layer.

This module provides a unified interface for interacting with multiple LLM providers
(Grok and Gemini), handling API keys, configuration, and provider switching.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


class LLMProvider(Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    GEMINI = "gemini"


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""
    provider: LLMProvider
    model: str
    max_tokens: int = 2000
    temperature: float = 0.7
    api_key: Optional[str] = None

    def is_available(self) -> bool:
        """Check if provider is configured with API key."""
        return self.api_key is not None and self.api_key.strip() != ""


class LLMProviderManager:
    """Manages LLM provider configurations and availability."""

    def __init__(self):
        """Initialize provider manager from environment variables."""
        self.groq_config = LLMConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            temperature=0.7,
            api_key=os.getenv("GROQ_API_KEY"),
        )

        self.gemini_config = LLMConfig(
            provider=LLMProvider.GEMINI,
            model="gemini-1.5-flash",
            max_tokens=2000,
            temperature=0.7,
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        self.default_provider_name = os.getenv("DEFAULT_LLM_PROVIDER", "groq").lower()

    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of providers with valid API keys."""
        providers = []
        if self.groq_config.is_available():
            providers.append(LLMProvider.GROQ)
        if self.gemini_config.is_available():
            providers.append(LLMProvider.GEMINI)
        return providers

    def get_default_provider(self) -> Optional[LLMProvider]:
        """Get the default provider, falling back to first available."""
        if self.default_provider_name == "groq" and self.groq_config.is_available():
            return LLMProvider.GROQ
        if self.default_provider_name == "gemini" and self.gemini_config.is_available():
            return LLMProvider.GEMINI

        # Fallback to first available provider
        available = self.get_available_providers()
        return available[0] if available else None

    def get_config(self, provider: LLMProvider) -> Optional[LLMConfig]:
        """Get configuration for a specific provider."""
        configs = {
            LLMProvider.GROQ: self.groq_config,
            LLMProvider.GEMINI: self.gemini_config,
        }
        return configs.get(provider)

    def get_primary_with_fallback(self) -> tuple[LLMConfig, Optional[LLMConfig]]:
        """Get primary and fallback provider configs.

        Returns:
            Tuple of (primary_config, fallback_config)
        """
        primary = self.get_default_provider()
        if primary is None:
            return None, None

        primary_config = self.get_config(primary)

        # Find fallback (any other available provider)
        available = self.get_available_providers()
        fallback = None
        for provider in available:
            if provider != primary:
                fallback = self.get_config(provider)
                break

        return primary_config, fallback


# Global provider manager instance
provider_manager = LLMProviderManager()


def get_provider_manager() -> LLMProviderManager:
    """Get the global provider manager instance."""
    return provider_manager
