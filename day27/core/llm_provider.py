"""LLM provider abstraction for supporting multiple AI backends."""

from enum import Enum
from typing import Optional, Union
import os

from core.gemini_client import GeminiApiClient, GeminiModel
from core.ollama_client import OllamaApiClient, OllamaModel


class LLMProvider(Enum):
    """Available LLM providers"""
    GEMINI = "gemini"
    OLLAMA = "ollama"


class LLMClientFactory:
    """Factory for creating LLM clients based on provider type."""

    @staticmethod
    def create_client(
            provider: LLMProvider,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None
    ) -> Union[GeminiApiClient, OllamaApiClient]:
        """Create an LLM client based on provider type.

        Args:
            provider: LLM provider to use
            api_key: API key for cloud providers (required for Gemini)
            base_url: Base URL for local providers (optional for Ollama)

        Returns:
            Initialized LLM client

        Raises:
            ValueError: If required parameters are missing
        """
        if provider == LLMProvider.GEMINI:
            if not api_key:
                # Try to get from environment
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "GEMINI_API_KEY is required for Gemini provider. "
                        "Set it via environment variable or pass as parameter."
                    )
            return GeminiApiClient(api_key=api_key)

        elif provider == LLMProvider.OLLAMA:
            base_url = base_url or "http://localhost:11434"
            return OllamaApiClient(base_url=base_url)

        else:
            raise ValueError(f"Unknown provider: {provider}")

    @staticmethod
    def get_default_model(provider: LLMProvider) -> str:
        """Get default model for provider.

        Args:
            provider: LLM provider

        Returns:
            Default model name
        """
        if provider == LLMProvider.GEMINI:
            return GeminiModel.GEMINI_2_5_FLASH
        elif provider == LLMProvider.OLLAMA:
            return OllamaModel.QWEN_CODER
        else:
            raise ValueError(f"Unknown provider: {provider}")

    @staticmethod
    def from_string(provider_str: str) -> LLMProvider:
        """Convert string to LLMProvider enum.

        Args:
            provider_str: Provider name as string

        Returns:
            LLMProvider enum value

        Raises:
            ValueError: If provider string is invalid
        """
        provider_str = provider_str.lower().strip()
        try:
            return LLMProvider(provider_str)
        except ValueError:
            valid_providers = [p.value for p in LLMProvider]
            raise ValueError(
                f"Invalid provider: '{provider_str}'. "
                f"Valid options: {', '.join(valid_providers)}"
            )


class LLMConfig:
    """Configuration for LLM providers."""

    def __init__(
            self,
            provider: LLMProvider = LLMProvider.OLLAMA,
            model: Optional[str] = None,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None
    ):
        """Initialize LLM configuration.

        Args:
            provider: LLM provider to use
            model: Model name (uses default if not specified)
            api_key: API key for cloud providers
            base_url: Base URL for local providers
        """
        self.provider = provider
        self.model = model or LLMClientFactory.get_default_model(provider)
        self.api_key = api_key
        self.base_url = base_url

    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """Create configuration from environment variables.

        Environment variables:
            LLM_PROVIDER: Provider name (default: ollama)
            LLM_MODEL: Model name (uses provider default if not set)
            GEMINI_API_KEY: API key for Gemini
            OLLAMA_BASE_URL: Base URL for Ollama (default: http://localhost:11434)

        Returns:
            LLMConfig instance
        """
        provider_str = os.getenv("LLM_PROVIDER", "ollama")
        provider = LLMClientFactory.from_string(provider_str)

        model = os.getenv("LLM_MODEL")
        api_key = os.getenv("GEMINI_API_KEY")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url
        )

    def create_client(self) -> Union[GeminiApiClient, OllamaApiClient]:
        """Create LLM client from this configuration.

        Returns:
            Initialized LLM client
        """
        return LLMClientFactory.create_client(
            provider=self.provider,
            api_key=self.api_key,
            base_url=self.base_url
        )

    def __str__(self) -> str:
        """String representation of configuration."""
        return f"LLMConfig(provider={self.provider.value}, model={self.model})"
