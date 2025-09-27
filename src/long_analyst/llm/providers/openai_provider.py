"""
OpenAI Provider Implementation.

Implements the OpenAI API integration for LLM services.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
import logging
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderConfig, LLMProviderType


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider implementation.

    Supports GPT-3.5, GPT-4, and other OpenAI models.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize OpenAI provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is required. Install with: pip install openai")

        # Initialize OpenAI client
        self.client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=0  # We handle retries ourselves
        )

        # Model-specific configuration
        self.model_costs = {
            "gpt-4": 0.03,      # $0.03 per 1K tokens
            "gpt-4-turbo": 0.01,
            "gpt-4-32k": 0.06,
            "gpt-3.5-turbo": 0.0015,
            "gpt-3.5-turbo-16k": 0.003,
        }

        self.logger.info(f"OpenAI provider initialized with model: {config.model}")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using OpenAI API.

        Args:
            request: LLM request parameters

        Returns:
            LLM response
        """
        start_time = time.time()

        try:
            # Prepare messages
            messages = [{"role": "user", "content": request.prompt}]

            # Make API call
            response = await self.client.chat.completions.create(
                model=request.model or self.config.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop_sequences,
                stream=request.stream,
                timeout=request.timeout
            )

            # Calculate latency
            latency = time.time() - start_time

            # Extract response content
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            # Calculate cost
            cost_per_1k = self.model_costs.get(request.model or self.config.model, self.config.cost_per_1k_tokens)
            cost = (tokens_used / 1000) * cost_per_1k

            return LLMResponse(
                content=content,
                model=response.model,
                tokens_used=tokens_used,
                cost=cost,
                latency=latency,
                success=True,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            )

        except openai.RateLimitError as e:
            self.logger.error(f"OpenAI rate limit error: {e}")
            return LLMResponse(
                content="",
                model=request.model or self.config.model,
                tokens_used=0,
                cost=0.0,
                latency=time.time() - start_time,
                success=False,
                error_message=f"Rate limit exceeded: {e}"
            )

        except openai.AuthenticationError as e:
            self.logger.error(f"OpenAI authentication error: {e}")
            return LLMResponse(
                content="",
                model=request.model or self.config.model,
                tokens_used=0,
                cost=0.0,
                latency=time.time() - start_time,
                success=False,
                error_message=f"Authentication failed: {e}"
            )

        except openai.APITimeoutError as e:
            self.logger.error(f"OpenAI timeout error: {e}")
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
            self.logger.error(f"OpenAI API error: {e}")
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
        Check if OpenAI API is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple health check with minimal request
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
                timeout=10
            )
            return response is not None
        except Exception as e:
            self.logger.error(f"OpenAI health check failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available OpenAI models.

        Returns:
            Dictionary with model information
        """
        return {
            "provider": "openai",
            "available_models": list(self.model_costs.keys()),
            "default_model": self.config.model,
            "costs_per_1k_tokens": self.model_costs,
            "max_tokens": 8192,  # Default max tokens for most models
            "supports_streaming": True,
            "supports_function_calling": True
        }

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate number of tokens in text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Simple approximation: 1 token ≈ 4 characters for English text
        return max(1, len(text) // 4)

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
            # Note: This requires OpenAI organization-level access
            # In most cases, this will not be available to individual API keys
            return {
                "message": "Detailed usage statistics require organization-level API access",
                "local_metrics": self.get_metrics()
            }
        except Exception as e:
            self.logger.error(f"Failed to get usage stats: {e}")
            return {"error": str(e), "local_metrics": self.get_metrics()}

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.

        Returns:
            List of available models
        """
        try:
            models = await self.client.models.list()
            return [
                {
                    "id": model.id,
                    "object": model.object,
                    "created": model.created,
                    "owned_by": model.owned_by
                }
                for model in models.data
            ]
        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return []

    def is_model_supported(self, model: str) -> bool:
        """
        Check if a model is supported.

        Args:
            model: Model name

        Returns:
            True if supported
        """
        return model in self.model_costs or model.startswith("gpt-")

    def get_model_max_tokens(self, model: str) -> int:
        """
        Get maximum tokens for a model.

        Args:
            model: Model name

        Returns:
            Maximum tokens
        """
        model_limits = {
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
        }
        return model_limits.get(model, 4096)