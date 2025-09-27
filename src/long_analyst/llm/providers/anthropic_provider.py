"""
Anthropic Provider Implementation.

Implements the Anthropic Claude API integration for LLM services.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
import logging
import json

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderConfig, LLMProviderType


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude API provider implementation.

    Supports Claude 2, Claude 3, and other Anthropic models.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize Anthropic provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library is required. Install with: pip install anthropic")

        # Initialize Anthropic client
        self.client = anthropic.AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url,
            max_retries=0  # We handle retries ourselves
        )

        # Model-specific configuration
        self.model_costs = {
            "claude-3-opus-20240229": 0.015,  # $0.015 per 1K tokens
            "claude-3-sonnet-20240229": 0.003,
            "claude-3-haiku-20240307": 0.00025,
            "claude-2.1": 0.008,
            "claude-2.0": 0.008,
            "claude-instant-1.2": 0.00163,
        }

        self.model_max_tokens = {
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-2.1": 200000,
            "claude-2.0": 100000,
            "claude-instant-1.2": 100000,
        }

        self.logger.info(f"Anthropic provider initialized with model: {config.model}")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using Anthropic API.

        Args:
            request: LLM request parameters

        Returns:
            LLM response
        """
        start_time = time.time()

        try:
            # Prepare the message
            message = await self.client.messages.create(
                model=request.model or self.config.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop_sequences=request.stop_sequences,
                messages=[
                    {"role": "user", "content": request.prompt}
                ]
            )

            # Calculate latency
            latency = time.time() - start_time

            # Extract response content
            content = message.content[0].text
            tokens_used = message.usage.input_tokens + message.usage.output_tokens

            # Calculate cost
            cost_per_1k = self.model_costs.get(request.model or self.config.model, self.config.cost_per_1k_tokens)
            cost = (tokens_used / 1000) * cost_per_1k

            return LLMResponse(
                content=content,
                model=message.model,
                tokens_used=tokens_used,
                cost=cost,
                latency=latency,
                success=True,
                metadata={
                    "stop_reason": message.stop_reason,
                    "usage": {
                        "input_tokens": message.usage.input_tokens,
                        "output_tokens": message.usage.output_tokens,
                        "total_tokens": tokens_used
                    },
                    "type": message.type
                }
            )

        except anthropic.RateLimitError as e:
            self.logger.error(f"Anthropic rate limit error: {e}")
            return LLMResponse(
                content="",
                model=request.model or self.config.model,
                tokens_used=0,
                cost=0.0,
                latency=time.time() - start_time,
                success=False,
                error_message=f"Rate limit exceeded: {e}"
            )

        except anthropic.AuthenticationError as e:
            self.logger.error(f"Anthropic authentication error: {e}")
            return LLMResponse(
                content="",
                model=request.model or self.config.model,
                tokens_used=0,
                cost=0.0,
                latency=time.time() - start_time,
                success=False,
                error_message=f"Authentication failed: {e}"
            )

        except anthropic.APITimeoutError as e:
            self.logger.error(f"Anthropic timeout error: {e}")
            return LLMResponse(
                content="",
                model=request.model or self.config.model,
                tokens_used=0,
                cost=0.0,
                latency=time.time() - start_time,
                success=False,
                error_message=f"Request timeout: {e}"
            )

        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            return LLMResponse(
                content="",
                model=request.model or self.config.model,
                tokens_used=0,
                cost=0.0,
                latency=time.time() - start_time,
                success=False,
                error_message=f"API error: {e}"
            )

    async def batch_generate(self, requests: List[LLMRequest]) -> List[LLMResponse]:
        """
        Generate text for multiple requests concurrently.

        Args:
            requests: List of LLM requests

        Returns:
            List of LLM responses
        """
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests

        async def process_request(request: LLMRequest) -> LLMResponse:
            async with semaphore:
                return await self.generate_with_retry(request)

        # Process all requests concurrently
        tasks = [process_request(request) for request in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                self.logger.error(f"Batch request {i} failed: {response}")
                results.append(LLMResponse(
                    content="",
                    model=requests[i].model or self.config.model,
                    tokens_used=0,
                    cost=0.0,
                    latency=0.0,
                    success=False,
                    error_message=f"Batch processing error: {response}"
                ))
            else:
                results.append(response)

        return results

    async def health_check(self) -> bool:
        """
        Check if Anthropic API is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple health check with minimal request
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "Hello"}],
                timeout=10
            )
            return response is not None
        except Exception as e:
            self.logger.error(f"Anthropic health check failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available Anthropic models.

        Returns:
            Dictionary with model information
        """
        return {
            "provider": "anthropic",
            "available_models": list(self.model_costs.keys()),
            "default_model": self.config.model,
            "costs_per_1k_tokens": self.model_costs,
            "max_tokens": self.model_max_tokens.get(self.config.model, 100000),
            "supports_streaming": True,
            "supports_function_calling": False
        }

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate number of tokens in text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Simple approximation: 1 token ≈ 3.5 characters for Claude models
        return max(1, int(len(text) / 3.5))

    def calculate_cost(self, tokens: int, model: str) -> float:
        """
        Calculate cost for token usage.

        Args:
            tokens: Number of tokens
            model: Model name

        Returns:
            Estimated cost
        """
        cost_per_1k = self.model_costs.get(model, self.config.cost_per_1k_tokens)
        return (tokens / 1000) * cost_per_1k

    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.

        Returns:
            Usage statistics
        """
        try:
            # Note: Anthropic doesn't provide usage stats via API
            return {
                "message": "Usage statistics not available via Anthropic API",
                "local_metrics": self.get_metrics()
            }
        except Exception as e:
            self.logger.error(f"Failed to get usage stats: {e}")
            return {"error": str(e), "local_metrics": self.get_metrics()}

    def is_model_supported(self, model: str) -> bool:
        """
        Check if a model is supported.

        Args:
            model: Model name

        Returns:
            True if supported
        """
        return model in self.model_costs or model.startswith("claude-")

    def get_model_max_tokens(self, model: str) -> int:
        """
        Get maximum tokens for a model.

        Args:
            model: Model name

        Returns:
            Maximum tokens
        """
        return self.model_max_tokens.get(model, 100000)

    async def create_message_stream(self, request: LLMRequest):
        """
        Create a streaming message response.

        Args:
            request: LLM request parameters

        Yields:
            Streaming response chunks
        """
        try:
            async with self.client.messages.stream(
                model=request.model or self.config.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=[{"role": "user", "content": request.prompt}]
            ) as stream:
                async for chunk in stream:
                    yield chunk
        except Exception as e:
            self.logger.error(f"Streaming request failed: {e}")
            yield {"error": str(e)}

    def get_model_capabilities(self, model: str) -> Dict[str, Any]:
        """
        Get model capabilities.

        Args:
            model: Model name

        Returns:
            Model capabilities
        """
        capabilities = {
            "claude-3-opus-20240229": {
                "max_tokens": 200000,
                "vision": True,
                "tool_use": True,
                "streaming": True,
                "multilingual": True
            },
            "claude-3-sonnet-20240229": {
                "max_tokens": 200000,
                "vision": True,
                "tool_use": True,
                "streaming": True,
                "multilingual": True
            },
            "claude-3-haiku-20240307": {
                "max_tokens": 200000,
                "vision": True,
                "tool_use": True,
                "streaming": True,
                "multilingual": True
            }
        }

        return capabilities.get(model, {
            "max_tokens": 100000,
            "vision": False,
            "tool_use": False,
            "streaming": True,
            "multilingual": True
        })