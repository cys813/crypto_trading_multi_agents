"""
Base LLM Provider Interface.

Defines the abstract interface for all LLM providers,
ensuring consistent behavior across different implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import asyncio
import logging
from enum import Enum


class LLMProviderType(Enum):
    """Supported LLM provider types."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"


@dataclass
class LLMRequest:
    """Standard LLM request structure."""
    prompt: str
    model: str
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    stream: bool = False
    timeout: int = 30
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Standard LLM response structure."""
    content: str
    model: str
    tokens_used: int
    cost: float
    latency: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProviderConfig:
    """Configuration for LLM providers."""
    provider_type: LLMProviderType
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    cost_per_1k_tokens: float = 0.002  # Default cost estimate
    rate_limit_rpm: int = 60  # Requests per minute
    rate_limit_tpm: int = 100000  # Tokens per minute


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM provider implementations must inherit from this class
    and implement the required methods.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize the LLM provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Rate limiting
        self.request_timestamps = []
        self.token_usage = []

        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.average_latency = 0.0

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using the LLM.

        Args:
            request: LLM request parameters

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    async def batch_generate(self, requests: List[LLMRequest]) -> List[LLMResponse]:
        """
        Generate text for multiple requests concurrently.

        Args:
            requests: List of LLM requests

        Returns:
            List of LLM responses
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and accessible.

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available models.

        Returns:
            Dictionary with model information
        """
        pass

    async def generate_with_retry(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text with automatic retry logic.

        Args:
            request: LLM request parameters

        Returns:
            LLM response
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                # Check rate limits
                await self._check_rate_limits(request)

                # Make the request
                response = await self.generate(request)

                # Update metrics
                self._update_metrics(response)

                return response

            except Exception as e:
                last_error = e
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")

                if attempt < self.config.max_retries:
                    # Exponential backoff
                    delay = self.config.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    break

        # All attempts failed
        self.logger.error(f"All retry attempts failed. Last error: {last_error}")
        return LLMResponse(
            content="",
            model=request.model,
            tokens_used=0,
            cost=0.0,
            latency=0.0,
            success=False,
            error_message=str(last_error)
        )

    async def _check_rate_limits(self, request: LLMRequest):
        """Check and enforce rate limits."""
        now = asyncio.get_event_loop().time()

        # Clean old timestamps
        cutoff_time = now - 60  # 1 minute window
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff_time]

        # Check requests per minute
        if len(self.request_timestamps) >= self.config.rate_limit_rpm:
            sleep_time = 60 - (now - self.request_timestamps[0])
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)

        # Add current request timestamp
        self.request_timestamps.append(now)

    def _update_metrics(self, response: LLMResponse):
        """Update provider metrics."""
        self.total_requests += 1

        if response.success:
            self.successful_requests += 1
            self.total_tokens_used += response.tokens_used
            self.total_cost += response.cost

            # Update average latency
            if self.successful_requests == 1:
                self.average_latency = response.latency
            else:
                self.average_latency = (
                    (self.average_latency * (self.successful_requests - 1) + response.latency) /
                    self.successful_requests
                )
        else:
            self.failed_requests += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get provider metrics."""
        success_rate = self.successful_requests / self.total_requests if self.total_requests > 0 else 0
        avg_cost_per_request = self.total_cost / self.successful_requests if self.successful_requests > 0 else 0

        return {
            "provider_type": self.config.provider_type.value,
            "model": self.config.model,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "total_tokens_used": self.total_tokens_used,
            "total_cost": self.total_cost,
            "average_cost_per_request": avg_cost_per_request,
            "average_latency": self.average_latency,
            "current_rate": len(self.request_timestamps)
        }

    def reset_metrics(self):
        """Reset provider metrics."""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.average_latency = 0.0
        self.request_timestamps = []

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass