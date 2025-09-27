"""
LLM Provider Package.

Exports all available LLM provider implementations.
"""

from .base_provider import (
    BaseLLMProvider,
    LLMRequest,
    LLMResponse,
    ProviderConfig,
    LLMProviderType
)

from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .azure_openai_provider import AzureOpenAIProvider
from .mock_provider import MockProvider

__all__ = [
    "BaseLLMProvider",
    "LLMRequest",
    "LLMResponse",
    "ProviderConfig",
    "LLMProviderType",
    "OpenAIProvider",
    "AnthropicProvider",
    "AzureOpenAIProvider",
    "MockProvider"
]


def create_provider(provider_type: LLMProviderType, config: ProviderConfig) -> BaseLLMProvider:
    """
    Factory function to create LLM providers.

    Args:
        provider_type: Type of provider to create
        config: Provider configuration

    Returns:
        Initialized provider instance

    Raises:
        ValueError: If provider type is not supported
    """
    providers = {
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.ANTHROPIC: AnthropicProvider,
        LLMProviderType.AZURE_OPENAI: AzureOpenAIProvider,
        LLMProviderType.MOCK: MockProvider,
        LLMProviderType.LOCAL: MockProvider  # Local provider uses mock for now
    }

    if provider_type not in providers:
        raise ValueError(f"Unsupported provider type: {provider_type}")

    return providers[provider_type](config)