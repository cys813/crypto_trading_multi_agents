"""
Azure OpenAI Provider Implementation.

Implements the Azure OpenAI Service integration for LLM services.
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


class AzureOpenAIProvider(BaseLLMProvider):
    """
    Azure OpenAI Service provider implementation.

    Supports Azure-hosted OpenAI models with enterprise features.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize Azure OpenAI provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is required. Install with: pip install openai")

        # Extract Azure-specific configuration from metadata
        azure_config = config.metadata or {}
        self.deployment_name = azure_config.get("deployment_name", config.model)
        self.api_version = azure_config.get("api_version", "2024-02-15-preview")
        self.resource_name = azure_config.get("resource_name")

        # Initialize Azure OpenAI client
        self.client = openai.AsyncAzureOpenAI(
            api_key=config.api_key,
            azure_endpoint=config.base_url,
            api_version=self.api_version,
            azure_deployment=self.deployment_name,
            timeout=config.timeout,
            max_retries=0  # We handle retries ourselves
        )

        # Model-specific configuration (Azure uses same pricing as OpenAI)
        self.model_costs = {
            "gpt-4": 0.03,
            "gpt-4-32k": 0.06,
            "gpt-35-turbo": 0.0015,
            "gpt-35-turbo-16k": 0.003,
        }

        self.logger.info(f"Azure OpenAI provider initialized with deployment: {self.deployment_name}")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using Azure OpenAI API.

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
                deployment_id=self.deployment_name,
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
                    "deployment_name": self.deployment_name,
                    "api_version": self.api_version,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            )

        except openai.RateLimitError as e:
            self.logger.error(f"Azure OpenAI rate limit error: {e}")
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
            self.logger.error(f"Azure OpenAI authentication error: {e}")
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
            self.logger.error(f"Azure OpenAI timeout error: {e}")
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
            self.logger.error(f"Azure OpenAI API error: {e}")
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
        # Azure OpenAI may have different rate limits
        semaphore = asyncio.Semaphore(3)  # More conservative for Azure

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
        Check if Azure OpenAI API is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple health check with minimal request
            response = await self.client.chat.completions.create(
                deployment_id=self.deployment_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
                timeout=10
            )
            return response is not None
        except Exception as e:
            self.logger.error(f"Azure OpenAI health check failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available Azure OpenAI models.

        Returns:
            Dictionary with model information
        """
        return {
            "provider": "azure_openai",
            "deployment_name": self.deployment_name,
            "api_version": self.api_version,
            "available_models": list(self.model_costs.keys()),
            "default_model": self.config.model,
            "costs_per_1k_tokens": self.model_costs,
            "max_tokens": 8192,
            "supports_streaming": True,
            "supports_function_calling": True,
            "enterprise_features": True,
            "regional_deployment": True
        }

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate number of tokens in text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Same as OpenAI
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

    async def get_deployment_info(self) -> Dict[str, Any]:
        """
        Get deployment information.

        Returns:
            Deployment information
        """
        try:
            # Note: Azure OpenAI doesn't provide deployment info via API
            # This would typically be managed through Azure Portal
            return {
                "deployment_name": self.deployment_name,
                "api_version": self.api_version,
                "endpoint": self.config.base_url,
                "status": "active"
            }
        except Exception as e:
            self.logger.error(f"Failed to get deployment info: {e}")
            return {"error": str(e)}

    def get_azure_capabilities(self) -> Dict[str, Any]:
        """
        Get Azure-specific capabilities.

        Returns:
            Azure capabilities
        """
        return {
            "enterprise_features": True,
            "regional_deployment": True,
            "virtual_network_support": True,
            "private_endpoints": True,
            "managed_identity": True,
            "monitoring_integration": True,
            "content_filtering": True,
            "data_residency": True,
            "compliance_certifications": [
                "SOC 1",
                "SOC 2",
                "SOC 3",
                "HIPAA",
                "PCI DSS",
                "ISO 27001"
            ]
        }

    async def get_quota_info(self) -> Dict[str, Any]:
        """
        Get quota information for the deployment.

        Returns:
            Quota information
        """
        try:
            # Note: Quota info would typically be retrieved from Azure Portal
            # This is a placeholder implementation
            return {
                "message": "Quota information available through Azure Portal",
                "local_metrics": self.get_metrics()
            }
        except Exception as e:
            self.logger.error(f"Failed to get quota info: {e}")
            return {"error": str(e)}

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
            "gpt-35-turbo": 4096,
            "gpt-35-turbo-16k": 16384,
        }
        return model_limits.get(model, 4096)

    async def create_embedding(self, text: str) -> List[float]:
        """
        Create embeddings using Azure OpenAI.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        try:
            response = await self.client.embeddings.create(
                deployment_id=self.deployment_name,  # Use same deployment for embeddings
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"Failed to create embedding: {e}")
            raise