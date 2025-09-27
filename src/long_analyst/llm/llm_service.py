"""
LLM Service - Main Service Layer.

Provides a unified interface for LLM operations with provider abstraction,
caching, cost management, and performance optimization.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor

from .providers import (
    BaseLLMProvider, LLMRequest, LLMResponse, ProviderConfig, LLMProviderType,
    create_provider
)
from .context_manager import ContextManager
from .prompt_templates import PromptTemplates
from ..models.market_data import MarketData
from ..models.analysis_result import AnalysisResult, LLMAnalysis


class ServiceStatus(Enum):
    """Service status states."""
    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class ServiceConfig:
    """LLM Service configuration."""
    # Provider settings
    default_provider: LLMProviderType = LLMProviderType.MOCK
    fallback_provider: LLMProviderType = LLMProviderType.MOCK
    provider_configs: Dict[LLMProviderType, ProviderConfig] = field(default_factory=dict)

    # Performance settings
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    # Caching settings
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_cache_size: int = 1000

    # Cost management
    enable_cost_tracking: bool = True
    daily_budget: float = 100.0
    monthly_budget: float = 2000.0
    cost_alert_threshold: float = 0.8

    # Context management
    max_context_size: int = 10
    max_context_tokens: int = 4000

    # Performance monitoring
    enable_metrics: bool = True
    metrics_interval: int = 60  # seconds


@dataclass
class ServiceMetrics:
    """Service performance metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_cost: float = 0.0
    average_latency: float = 0.0
    uptime_start: datetime = field(default_factory=datetime.utcnow)
    last_health_check: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return self.cache_hits / total_cache_requests


class LLMService:
    """
    Main LLM service providing unified interface for all LLM operations.

    Features:
    - Multi-provider support with automatic failover
    - Intelligent caching
    - Cost tracking and budget management
    - Performance monitoring
    - Context management
    - Load balancing
    """

    def __init__(self, config: ServiceConfig):
        """
        Initialize LLM service.

        Args:
            config: Service configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.status = ServiceStatus.INITIALIZING

        # Initialize components
        self.providers: Dict[LLMProviderType, BaseLLMProvider] = {}
        self.active_provider: Optional[BaseLLMProvider] = None
        self.context_manager = ContextManager(
            max_context_size=config.max_context_size,
            max_tokens=config.max_context_tokens
        )
        self.prompt_templates = PromptTemplates()

        # Performance management
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_requests)
        self.semaphore = asyncio.Semaphore(config.max_concurrent_requests)

        # Caching
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_lock = asyncio.Lock()

        # Metrics
        self.metrics = ServiceMetrics()

        # Cost tracking
        self.daily_usage = 0.0
        self.monthly_usage = 0.0
        self.cost_alerts: List[str] = []

        # Service health
        self.health_checks: Dict[LLMProviderType, bool] = {}
        self.last_provider_switch = None

        # Initialize providers
        self._initialize_providers()

        # Start background tasks
        self._start_background_tasks()

        self.logger.info(f"LLM service initialized with {len(self.providers)} providers")

    def _initialize_providers(self):
        """Initialize all configured providers."""
        for provider_type, provider_config in self.config.provider_configs.items():
            try:
                provider = create_provider(provider_type, provider_config)
                self.providers[provider_type] = provider
                self.logger.info(f"Initialized {provider_type.value} provider")
            except Exception as e:
                self.logger.error(f"Failed to initialize {provider_type.value} provider: {e}")

        # Set default active provider
        if self.config.default_provider in self.providers:
            self.active_provider = self.providers[self.config.default_provider]
            self.logger.info(f"Set active provider to {self.config.default_provider.value}")
        elif self.providers:
            # Use first available provider
            self.active_provider = next(iter(self.providers.values()))
            self.logger.warning(f"Default provider not available, using {type(self.active_provider).__name__}")

        if not self.active_provider:
            raise RuntimeError("No LLM providers available")

    async def analyze_market(self, market_data: MarketData, template_name: str = "long_analysis", **kwargs) -> LLMAnalysis:
        """
        Perform market analysis using LLM.

        Args:
            market_data: Market data to analyze
            template_name: Name of prompt template to use
            **kwargs: Additional analysis parameters

        Returns:
            LLM analysis result
        """
        request_id = str(uuid.uuid4())
        self.logger.info(f"Starting market analysis for {market_data.symbol} (request_id: {request_id})")

        try:
            # Update context
            await self.context_manager.update_context(market_data, kwargs.get("additional_context"))

            # Generate analysis prompt
            context = await self._prepare_analysis_context(market_data, **kwargs)
            prompt = self.prompt_templates.render_template(template_name, context)

            # Check cache
            cache_key = self._generate_cache_key("analysis", market_data.symbol, prompt)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                self.logger.debug(f"Using cached analysis for {market_data.symbol}")
                return cached_result

            # Execute LLM analysis
            async with self.semaphore:
                request = LLMRequest(
                    prompt=prompt,
                    model=self.active_provider.config.model,
                    max_tokens=2000,
                    temperature=0.3,
                    timeout=self.config.request_timeout,
                    metadata={"request_id": request_id, "analysis_type": "market_analysis"}
                )

                response = await self.active_provider.generate_with_retry(request)

            # Parse response
            analysis_result = self._parse_analysis_response(response.content, market_data)

            # Cache result
            if self.config.enable_caching:
                await self._cache_result(cache_key, analysis_result)

            # Update metrics
            self._update_metrics(response)

            # Update cost tracking
            if self.config.enable_cost_tracking:
                self._update_cost_tracking(response.cost)

            self.logger.info(f"Market analysis completed for {market_data.symbol}")
            return analysis_result

        except Exception as e:
            self.logger.error(f"Market analysis failed for {market_data.symbol}: {e}")
            self.metrics.failed_requests += 1

            # Try fallback provider
            if self.config.fallback_provider and self.config.fallback_provider != self.config.default_provider:
                try:
                    self.logger.info(f"Attempting fallback to {self.config.fallback_provider.value}")
                    return await self._fallback_analysis(market_data, template_name, **kwargs)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback analysis also failed: {fallback_error}")

            # Return error result
            return LLMAnalysis(
                market_context=f"Analysis failed: {str(e)}",
                technical_patterns=[],
                key_levels=[],
                investment_thesis="Unable to generate thesis due to analysis error",
                overall_score=0.3
            )

    async def batch_analyze(self, requests: List[Dict[str, Any]]) -> List[LLMAnalysis]:
        """
        Perform batch analysis of multiple requests.

        Args:
            requests: List of analysis requests

        Returns:
            List of analysis results
        """
        self.logger.info(f"Starting batch analysis of {len(requests)} requests")

        # Create concurrent tasks
        tasks = []
        for i, request in enumerate(requests):
            task = self.analyze_market(
                market_data=request["market_data"],
                template_name=request.get("template_name", "long_analysis"),
                **request.get("kwargs", {})
            )
            tasks.append(task)

        # Execute with concurrency control
        semaphore = asyncio.Semaphore(min(5, self.config.max_concurrent_requests))

        async def process_task(task):
            async with semaphore:
                return await task

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch request {i} failed: {result}")
                # Create error result
                market_data = requests[i]["market_data"]
                error_result = LLMAnalysis(
                    market_context=f"Batch analysis failed: {str(result)}",
                    technical_patterns=[],
                    key_levels=[],
                    investment_thesis="Unable to generate thesis due to batch processing error",
                    overall_score=0.3
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)

        self.logger.info(f"Batch analysis completed: {len(processed_results)} results")
        return processed_results

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        request = LLMRequest(
            prompt=prompt,
            model=self.active_provider.config.model,
            max_tokens=kwargs.get("max_tokens", 1000),
            temperature=kwargs.get("temperature", 0.7),
            timeout=self.config.request_timeout
        )

        response = await self.active_provider.generate_with_retry(request)
        self._update_metrics(response)

        return response.content

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.

        Returns:
            Health check results
        """
        self.metrics.last_health_check = datetime.utcnow()

        # Check individual providers
        provider_health = {}
        healthy_providers = []

        for provider_type, provider in self.providers.items():
            try:
                is_healthy = await provider.health_check()
                provider_health[provider_type.value] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "last_check": datetime.utcnow().isoformat(),
                    "metrics": provider.get_metrics()
                }
                if is_healthy:
                    healthy_providers.append(provider_type)
            except Exception as e:
                provider_health[provider_type.value] = {
                    "status": "error",
                    "last_check": datetime.utcnow().isoformat(),
                    "error": str(e)
                }

        # Determine overall service status
        if not healthy_providers:
            overall_status = "error"
            self.status = ServiceStatus.ERROR
        elif len(healthy_providers) < len(self.providers):
            overall_status = "degraded"
            self.status = ServiceStatus.DEGRADED
        else:
            overall_status = "healthy"
            self.status = ServiceStatus.READY

        return {
            "service_status": overall_status,
            "service_uptime": (datetime.utcnow() - self.metrics.uptime_start).total_seconds(),
            "active_provider": type(self.active_provider).__name__,
            "provider_health": provider_health,
            "cache_status": {
                "size": len(self.cache),
                "hit_rate": self.metrics.cache_hit_rate
            },
            "cost_tracking": {
                "daily_usage": self.daily_usage,
                "monthly_usage": self.monthly_usage,
                "daily_budget": self.config.daily_budget,
                "monthly_budget": self.config.monthly_budget,
                "alerts": self.cost_alerts[-5:] if self.cost_alerts else []
            },
            "performance_metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": self.metrics.success_rate,
                "average_latency": self.metrics.average_latency
            }
        }

    async def get_service_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive service metrics.

        Returns:
            Service metrics
        """
        provider_metrics = {}
        for provider_type, provider in self.providers.items():
            provider_metrics[provider_type.value] = provider.get_metrics()

        return {
            "service_metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": self.metrics.success_rate,
                "average_latency": self.metrics.average_latency,
                "uptime_seconds": (datetime.utcnow() - self.metrics.uptime_start).total_seconds()
            },
            "cache_metrics": {
                "size": len(self.cache),
                "hits": self.metrics.cache_hits,
                "misses": self.metrics.cache_misses,
                "hit_rate": self.metrics.cache_hit_rate
            },
            "cost_metrics": {
                "total_cost": self.metrics.total_cost,
                "daily_usage": self.daily_usage,
                "monthly_usage": self.monthly_usage,
                "daily_budget_utilization": self.daily_usage / self.config.daily_budget,
                "monthly_budget_utilization": self.monthly_usage / self.config.monthly_budget
            },
            "provider_metrics": provider_metrics,
            "context_metrics": await self.context_manager.get_context_summary()
        }

    async def switch_provider(self, new_provider_type: LLMProviderType) -> bool:
        """
        Switch active provider.

        Args:
            new_provider_type: Type of provider to switch to

        Returns:
            True if switch successful
        """
        if new_provider_type not in self.providers:
            self.logger.error(f"Provider {new_provider_type.value} not available")
            return False

        try:
            # Health check new provider
            new_provider = self.providers[new_provider_type]
            is_healthy = await new_provider.health_check()

            if not is_healthy:
                self.logger.error(f"Provider {new_provider_type.value} is not healthy")
                return False

            # Switch provider
            old_provider = self.active_provider
            self.active_provider = new_provider
            self.last_provider_switch = datetime.utcnow()

            self.logger.info(f"Switched provider from {type(old_provider).__name__} to {type(self.active_provider).__name__}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to switch provider to {new_provider_type.value}: {e}")
            return False

    async def clear_cache(self):
        """Clear all cached results."""
        async with self.cache_lock:
            self.cache.clear()
            self.logger.info("Cache cleared")

    async def shutdown(self):
        """Shutdown the LLM service."""
        self.logger.info("Shutting down LLM service")
        self.status = ServiceStatus.SHUTTING_DOWN

        # Shutdown executor
        self.executor.shutdown(wait=True)

        # Clear cache
        await self.clear_cache()

        # Shutdown providers
        for provider in self.providers.values():
            try:
                await provider.__aexit__(None, None, None)
            except Exception as e:
                self.logger.error(f"Error shutting down provider: {e}")

        self.logger.info("LLM service shutdown complete")

    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        # In a real implementation, this would start tasks for:
        # - Cache cleanup
        # - Metrics collection
        # - Health monitoring
        # - Cost alerts
        pass

    async def _prepare_analysis_context(self, market_data: MarketData, **kwargs) -> Dict[str, Any]:
        """Prepare analysis context."""
        context = {
            "market_data": self._format_market_data(market_data),
            "context": await self.context_manager.get_optimized_context(),
            "historical_context": json.dumps(await self.context_manager.get_context(5)),
            "additional_factors": kwargs.get("additional_context", {})
        }
        return context

    def _format_market_data(self, market_data: MarketData) -> str:
        """Format market data for LLM prompt."""
        price = market_data.get_price()
        volume = market_data.get_volume()

        summary = f"""
Symbol: {market_data.symbol}
Current Price: ${price:.2f}
Volume: {volume:,.0f}
Data Source: {market_data.source.value}
Timeframe: {market_data.timeframe.value if market_data.timeframe else 'N/A'}
Age: {market_data.age_seconds:.1f} seconds
"""

        if market_data.ohlcv_data and len(market_data.ohlcv_data) > 0:
            latest = market_data.ohlcv_data[-1]
            summary += f"""
Latest OHLCV:
Open: ${latest.open:.2f}
High: ${latest.high:.2f}
Low: ${latest.low:.2f}
Close: ${latest.close:.2f}
Volume: {latest.volume:,.0f}
"""

        return summary

    def _generate_cache_key(self, operation: str, symbol: str, prompt: str) -> str:
        """Generate cache key for results."""
        key_data = f"{operation}:{symbol}:{prompt}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def _get_cached_result(self, cache_key: str) -> Optional[LLMAnalysis]:
        """Get cached result."""
        if not self.config.enable_caching:
            return None

        async with self.cache_lock:
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if time.time() - cache_entry["timestamp"] < self.config.cache_ttl:
                    self.metrics.cache_hits += 1
                    return cache_entry["data"]
                else:
                    # Remove expired entry
                    del self.cache[cache_key]

        self.metrics.cache_misses += 1
        return None

    async def _cache_result(self, cache_key: str, result: LLMAnalysis):
        """Cache analysis result."""
        if not self.config.enable_caching:
            return

        async with self.cache_lock:
            # Clean cache if needed
            if len(self.cache) >= self.config.max_cache_size:
                # Remove oldest entries
                oldest_keys = sorted(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
                for key in oldest_keys[:len(self.cache) // 4]:  # Remove 25% of oldest entries
                    del self.cache[key]

            self.cache[cache_key] = {
                "data": result,
                "timestamp": time.time()
            }

    def _parse_analysis_response(self, response_content: str, market_data: MarketData) -> LLMAnalysis:
        """Parse LLM response into structured analysis."""
        try:
            # Try to parse as JSON first
            if response_content.strip().startswith('{'):
                analysis_dict = json.loads(response_content)
                return LLMAnalysis.from_dict(analysis_dict)
        except json.JSONDecodeError:
            pass

        # Fallback to text parsing
        return LLMAnalysis(
            market_context=response_content,
            technical_patterns=[],
            key_levels=[],
            investment_thesis="Analysis completed (text format)",
            overall_score=0.7
        )

    def _update_metrics(self, response: LLMResponse):
        """Update service metrics."""
        self.metrics.total_requests += 1

        if response.success:
            self.metrics.successful_requests += 1

            # Update average latency
            if self.metrics.successful_requests == 1:
                self.metrics.average_latency = response.latency
            else:
                self.metrics.average_latency = (
                    (self.metrics.average_latency * (self.metrics.successful_requests - 1) + response.latency) /
                    self.metrics.successful_requests
                )
        else:
            self.metrics.failed_requests += 1

    def _update_cost_tracking(self, cost: float):
        """Update cost tracking."""
        self.metrics.total_cost += cost
        self.daily_usage += cost
        self.monthly_usage += cost

        # Check budget thresholds
        daily_utilization = self.daily_usage / self.config.daily_budget
        monthly_utilization = self.monthly_usage / self.config.monthly_budget

        if daily_utilization > self.config.cost_alert_threshold:
            alert = f"Daily budget {daily_utilization:.1%} utilized (${self.daily_usage:.2f}/${self.config.daily_budget:.2f})"
            if alert not in self.cost_alerts:
                self.cost_alerts.append(alert)
                self.logger.warning(alert)

        if monthly_utilization > self.config.cost_alert_threshold:
            alert = f"Monthly budget {monthly_utilization:.1%} utilized (${self.monthly_usage:.2f}/${self.config.monthly_budget:.2f})"
            if alert not in self.cost_alerts:
                self.cost_alerts.append(alert)
                self.logger.warning(alert)

    async def _fallback_analysis(self, market_data: MarketData, template_name: str, **kwargs) -> LLMAnalysis:
        """Perform analysis with fallback provider."""
        if self.config.fallback_provider not in self.providers:
            raise RuntimeError("Fallback provider not available")

        # Temporarily switch provider
        original_provider = self.active_provider
        self.active_provider = self.providers[self.config.fallback_provider]

        try:
            result = await self.analyze_market(market_data, template_name, **kwargs)
            self.logger.info(f"Fallback analysis successful for {market_data.symbol}")
            return result
        finally:
            # Restore original provider
            self.active_provider = original_provider