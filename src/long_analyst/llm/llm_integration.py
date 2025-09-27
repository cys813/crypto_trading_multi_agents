"""
LLM Integration Engine for the Long Analyst Agent.

Provides advanced LLM-powered analysis capabilities including
market understanding, signal evaluation, and contextual reasoning.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import time
from concurrent.futures import ThreadPoolExecutor

from ..models.market_data import MarketData
from ..models.analysis_result import AnalysisResult, AnalysisDimension, AnalysisStatus, LLMAnalysis
from ..models.signal import Signal, SignalType, SignalStrength
from ..utils.performance_monitor import PerformanceMonitor
from .llm_service import LLMService, ServiceConfig, LLMProviderType, ProviderConfig
from .context_manager import ContextManager
from .prompt_templates import PromptTemplates
from ..config import ConfigurationManager, ConfigType, ConfigEnvironment


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""
    model_name: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout_seconds: int = 30
    max_retries: int = 3
    context_window_size: int = 10
    enable_caching: bool = True
    cache_ttl_seconds: int = 300

    # API settings
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None

    # Analysis settings
    enable_technical_analysis: bool = True
    enable_fundamental_analysis: bool = True
    enable_sentiment_analysis: bool = True
    enable_risk_assessment: bool = True


class LLMAnalysisEngine:
    """
    Advanced LLM-powered analysis engine.

    This engine leverages large language models to provide
    contextual analysis, signal evaluation, and market intelligence.
    """

    def __init__(self, config: LLMConfig, config_manager: Optional[ConfigurationManager] = None):
        """Initialize the LLM analysis engine."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()

        # Initialize configuration manager
        self.config_manager = config_manager or self._create_default_config_manager()

        # Initialize LLM service
        self.llm_service = self._create_llm_service()

        # Initialize components
        self.context_manager = ContextManager(config.context_window_size)
        self.prompt_templates = PromptTemplates()

        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=5)

        # Analysis cache (LLM service handles main caching, this is for engine-specific caching)
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_lock = asyncio.Lock()

        # Metrics
        self.total_analyses = 0
        self.average_response_time = 0.0
        self.cache_hit_rate = 0.0
        self.error_rate = 0.0

        self.logger.info("LLM analysis engine initialized")

    def _create_default_config_manager(self) -> ConfigurationManager:
        """Create default configuration manager."""
        return ConfigurationManager(config_dir="config", environment=ConfigEnvironment.DEVELOPMENT)

    def _create_llm_service(self) -> LLMService:
        """Create LLM service with configuration."""
        # Load LLM configuration from config manager
        llm_config = self.config_manager.get_config(ConfigType.LLM) or {}

        # Create service config
        provider_configs = {}
        default_provider = LLMProviderType.MOCK
        fallback_provider = LLMProviderType.MOCK

        # Parse provider configurations
        for provider_name, provider_data in llm_config.get("providers", {}).items():
            try:
                provider_type = LLMProviderType(provider_name)
                provider_configs[provider_type] = ProviderConfig(
                    provider_type=provider_type,
                    model=provider_data.get("model", "gpt-4"),
                    api_key=provider_data.get("api_key"),
                    base_url=provider_data.get("base_url"),
                    max_tokens=provider_data.get("max_tokens", 4000),
                    temperature=provider_data.get("temperature", 0.7),
                    timeout=provider_data.get("timeout", 30),
                    metadata=provider_data
                )

                if provider_name == llm_config.get("default_provider", "mock"):
                    default_provider = provider_type

            except ValueError:
                self.logger.warning(f"Unknown provider: {provider_name}")

        # Create service config
        service_config = ServiceConfig(
            default_provider=default_provider,
            fallback_provider=fallback_provider,
            provider_configs=provider_configs,
            max_concurrent_requests=10,
            request_timeout=30,
            max_retries=3,
            enable_caching=self.config.enable_caching,
            cache_ttl=self.config.cache_ttl_seconds,
            enable_cost_tracking=True,
            daily_budget=llm_config.get("cost_control", {}).get("daily_budget", 100.0),
            monthly_budget=llm_config.get("cost_control", {}).get("monthly_budget", 2000.0),
            max_context_size=self.config.context_window_size,
            max_context_tokens=4000
        )

        return LLMService(service_config)

    async def analyze_market(self, market_data: MarketData, additional_context: Optional[Dict[str, Any]] = None) -> LLMAnalysis:
        """
        Perform comprehensive LLM analysis of market data.

        Args:
            market_data: Market data to analyze
            additional_context: Additional context information

        Returns:
            LLM analysis results
        """
        start_time = time.time()

        try:
            # Use LLM service for analysis
            analysis_result = await self.llm_service.analyze_market(
                market_data,
                template_name="long_analysis",
                additional_context=additional_context
            )

            # Update metrics
            self.total_analyses += 1
            response_time = time.time() - start_time
            self.average_response_time = (
                (self.average_response_time * (self.total_analyses - 1) + response_time) /
                self.total_analyses
            )

            self.performance_monitor.record_metric("llm_analysis_time", response_time)
            self.performance_monitor.record_metric("llm_analyses_performed", 1)

            self.logger.info(f"LLM analysis completed for {market_data.symbol} in {response_time:.2f}s")
            return analysis_result

        except Exception as e:
            self.logger.error(f"LLM analysis failed for {market_data.symbol}: {e}")
            self.error_rate += 1

            # Return a fallback analysis
            return LLMAnalysis(
                market_context=f"Analysis failed due to error: {str(e)}",
                technical_patterns=[],
                key_levels=[],
                investment_thesis="Unable to generate thesis due to analysis error",
                overall_score=0.3
            )

    async def enhance_analysis(self, analysis_results: List[AnalysisResult], market_data: MarketData) -> List[AnalysisResult]:
        """
        Enhance existing analysis results with LLM insights.

        Args:
            analysis_results: Existing analysis results to enhance
            market_data: Market data context

        Returns:
            Enhanced analysis results
        """
        try:
            # Combine analysis results
            combined_context = self._combine_analysis_results(analysis_results)

            # Use LLM service for enhancement
            enhancement_prompt = self.prompt_templates.render_template(
                "analysis_enhancement",
                {
                    "original_analysis": str(analysis_results),
                    "new_data": self._prepare_market_data_summary(market_data),
                    "performance_metrics": {}
                }
            )

            enhancement_response = await self.llm_service.generate_text(enhancement_prompt)

            # Apply enhancements to each analysis result
            enhanced_results = []
            for result in analysis_results:
                enhanced_result = await self._apply_enhancements(result, {"response": enhancement_response})
                enhanced_results.append(enhanced_result)

            return enhanced_results

        except Exception as e:
            self.logger.error(f"Analysis enhancement failed: {e}")
            return analysis_results  # Return original results if enhancement fails

    async def evaluate_signal_quality(self, signal: Signal, market_data: MarketData) -> Dict[str, Any]:
        """
        Evaluate the quality and reliability of a trading signal.

        Args:
            signal: Signal to evaluate
            market_data: Market data context

        Returns:
            Signal quality evaluation results
        """
        try:
            # Use LLM service for signal evaluation
            evaluation_prompt = self.prompt_templates.render_template(
                "signal_evaluation",
                {
                    "signal_details": signal.to_dict(),
                    "market_context": self._prepare_market_data_summary(market_data),
                    "risk_factors": []
                }
            )

            evaluation_response = await self.llm_service.generate_text(evaluation_prompt)

            # Parse evaluation results
            quality_evaluation = self._parse_signal_evaluation({"response": evaluation_response})

            return quality_evaluation

        except Exception as e:
            self.logger.error(f"Signal quality evaluation failed: {e}")
            return {
                "quality_score": 0.5,
                "confidence": 0.3,
                "reasoning": f"Evaluation failed due to error: {str(e)}",
                "recommendations": ["Manual review required"]
            }

    async def generate_market_narrative(self, market_data: MarketData, analysis_results: List[AnalysisResult]) -> str:
        """
        Generate a comprehensive market narrative based on analysis.

        Args:
            market_data: Market data
            analysis_results: Analysis results to include

        Returns:
            Market narrative string
        """
        try:
            # Generate narrative prompt
            narrative_prompt = await self._generate_narrative_prompt(market_data, analysis_results)

            # Execute LLM narrative generation
            narrative_response = await self._execute_llm_analysis(narrative_prompt)

            return narrative_response.get("narrative", "Unable to generate narrative")

        except Exception as e:
            self.logger.error(f"Market narrative generation failed: {e}")
            return f"Narrative generation failed: {str(e)}"

    async def _generate_analysis_prompt(self, market_data: MarketData, additional_context: Optional[Dict[str, Any]]) -> str:
        """Generate analysis prompt for LLM."""
        context = await self.context_manager.get_context()
        base_prompt = self.prompt_templates.get_analysis_template()

        # Prepare market data summary
        market_summary = self._prepare_market_data_summary(market_data)

        # Prepare additional context
        context_summary = self._prepare_additional_context(additional_context)

        # Format the prompt
        prompt = base_prompt.format(
            market_data=market_summary,
            context=context_summary,
            historical_context=json.dumps(context[-5:], indent=2) if context else "No historical context available"
        )

        return prompt

    async def _generate_enhancement_prompt(self, analysis_results: Dict[str, Any], market_data: MarketData) -> str:
        """Generate enhancement prompt for LLM."""
        enhancement_template = self.prompt_templates.get_enhancement_template()

        prompt = enhancement_template.format(
            analysis_results=json.dumps(analysis_results, indent=2),
            market_data=self._prepare_market_data_summary(market_data)
        )

        return prompt

    async def _generate_signal_evaluation_prompt(self, signal: Signal, market_data: MarketData) -> str:
        """Generate signal evaluation prompt for LLM."""
        evaluation_template = self.prompt_templates.get_signal_evaluation_template()

        prompt = evaluation_template.format(
            signal=signal.to_dict(),
            market_data=self._prepare_market_data_summary(market_data)
        )

        return prompt

    async def _generate_narrative_prompt(self, market_data: MarketData, analysis_results: List[AnalysisResult]) -> str:
        """Generate narrative prompt for LLM."""
        narrative_template = self.prompt_templates.get_narrative_template()

        analysis_summary = self._prepare_analysis_summary(analysis_results)

        prompt = narrative_template.format(
            market_data=self._prepare_market_data_summary(market_data),
            analysis_summary=analysis_summary
        )

        return prompt

    async def _execute_llm_analysis(self, prompt: str) -> Dict[str, Any]:
        """Execute LLM analysis (mock implementation)."""
        # In a real implementation, this would call the actual LLM API
        # For now, we'll simulate a response

        await asyncio.sleep(0.1)  # Simulate API call delay

        # Mock response based on prompt content
        if "analysis" in prompt.lower():
            return {
                "market_context": "The market is showing strong upward momentum with increasing volume",
                "trend_assessment": "Bullish trend confirmed by multiple indicators",
                "risk_factors": ["High volatility", "Potential resistance at key levels"],
                "opportunities": ["Breakout potential", "Strong support levels"],
                "technical_patterns": ["Ascending triangle", "Higher highs and higher lows"],
                "key_levels": [50000, 52000, 48000],
                "expected_price_action": "Continuation of upward movement with possible consolidation",
                "investment_thesis": "Strong long opportunity with favorable risk-reward ratio",
                "overall_score": 0.8
            }
        elif "enhancement" in prompt.lower():
            return {
                "enhancements": ["Increased confidence in technical signals", "Improved risk assessment"],
                "additional_insights": ["Market sentiment strongly bullish", "Institutional accumulation detected"],
                "quality_improvements": ["Better pattern recognition", "Enhanced risk management"]
            }
        elif "evaluation" in prompt.lower():
            return {
                "quality_score": 0.85,
                "confidence": 0.8,
                "reasoning": "Signal shows strong technical confirmation and volume support",
                "recommendations": ["Consider position scaling", "Set appropriate stop-loss"]
            }
        elif "narrative" in prompt.lower():
            return {
                "narrative": "The market is currently experiencing strong bullish momentum, supported by technical indicators and increasing trading volume. Multiple signals confirm the upward trend, suggesting favorable conditions for long positions."
            }
        else:
            return {"response": "Analysis completed"}

    async def _parse_llm_response(self, llm_response: Dict[str, Any], market_data: MarketData) -> LLMAnalysis:
        """Parse LLM response into structured analysis."""
        return LLMAnalysis(
            market_context=llm_response.get("market_context", ""),
            trend_assessment=llm_response.get("trend_assessment", ""),
            risk_factors=llm_response.get("risk_factors", []),
            opportunities=llm_response.get("opportunities", []),
            signal_reasoning=llm_response.get("signal_reasoning", ""),
            confidence_assessment=llm_response.get("confidence_assessment", ""),
            alternative_scenarios=llm_response.get("alternative_scenarios", []),
            technical_patterns=llm_response.get("technical_patterns", []),
            key_levels=llm_response.get("key_levels", []),
            expected_price_action=llm_response.get("expected_price_action", ""),
            competitive_position=llm_response.get("competitive_position", ""),
            growth_potential=llm_response.get("growth_potential", ""),
            regulatory_outlook=llm_response.get("regulatory_outlook", ""),
            sentiment_narrative=llm_response.get("sentiment_narrative", ""),
            market_psychology=llm_response.get("market_psychology", ""),
            contrarian_signals=llm_response.get("contrarian_signals", []),
            investment_thesis=llm_response.get("investment_thesis", ""),
            time_horizon=llm_response.get("time_horizon", "medium-term"),
            risk_management=llm_response.get("risk_management", ""),
            technical_score=llm_response.get("technical_score", 0.5),
            fundamental_score=llm_response.get("fundamental_score", 0.5),
            sentiment_score=llm_response.get("sentiment_score", 0.5),
            overall_score=llm_response.get("overall_score", 0.5)
        )

    def _parse_signal_evaluation(self, evaluation_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse signal evaluation response."""
        return {
            "quality_score": evaluation_response.get("quality_score", 0.5),
            "confidence": evaluation_response.get("confidence", 0.5),
            "reasoning": evaluation_response.get("reasoning", ""),
            "recommendations": evaluation_response.get("recommendations", [])
        }

    def _prepare_market_data_summary(self, market_data: MarketData) -> str:
        """Prepare market data summary for LLM prompt."""
        price = market_data.get_price()
        volume = market_data.get_volume()

        summary = f"""
Symbol: {market_data.symbol}
Current Price: ${price:.2f}
Volume: {volume:,.0f}
Data Source: {market_data.source.value}
Data Age: {market_data.age_seconds:.1f} seconds
Timeframe: {market_data.timeframe.value if market_data.timeframe else 'N/A'}
"""

        if market_data.ohlcv_data:
            latest_ohlcv = market_data.ohlcv_data[-1]
            summary += f"""
Latest OHLCV:
Open: ${latest_ohlcv.open:.2f}
High: ${latest_ohlcv.high:.2f}
Low: ${latest_ohlcv.low:.2f}
Close: ${latest_ohlcv.close:.2f}
Volume: {latest_ohlcv.volume:,.0f}
"""

        return summary

    def _prepare_additional_context(self, additional_context: Optional[Dict[str, Any]]) -> str:
        """Prepare additional context for LLM prompt."""
        if not additional_context:
            return "No additional context provided"

        return json.dumps(additional_context, indent=2)

    def _combine_analysis_results(self, analysis_results: List[AnalysisResult]) -> Dict[str, Any]:
        """Combine multiple analysis results into a single context."""
        combined = {
            "technical": {},
            "fundamental": {},
            "sentiment": {},
            "signals": [],
            "metrics": []
        }

        for result in analysis_results:
            if result.technical_indicators:
                combined["technical"].update(result.technical_indicators.to_dict())
            if result.fundamental_metrics:
                combined["fundamental"].update(result.fundamental_metrics.to_dict())
            if result.sentiment_metrics:
                combined["sentiment"].update(result.sentiment_metrics.to_dict())

            combined["signals"].extend(result.signals)
            combined["metrics"].extend([metric.to_dict() for metric in result.metrics])

        return combined

    def _prepare_analysis_summary(self, analysis_results: List[AnalysisResult]) -> str:
        """Prepare analysis summary for narrative generation."""
        summary_parts = []

        for result in analysis_results:
            part = f"""
{result.dimension.value.title()} Analysis:
- Score: {result.score:.2f}
- Confidence: {result.confidence:.2f}
- Signals: {', '.join(result.signals[:3])}
"""
            summary_parts.append(part)

        return "\n".join(summary_parts)

    def _generate_cache_key(self, market_data: MarketData, additional_context: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for analysis results."""
        key_data = {
            "symbol": market_data.symbol,
            "timestamp": market_data.timestamp,
            "data_type": market_data.data_type.value,
            "context": additional_context
        }
        return json.dumps(key_data, sort_keys=True)

    async def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result."""
        if not self.config.enable_caching:
            return None

        async with self.cache_lock:
            if cache_key in self.analysis_cache:
                cache_entry = self.analysis_cache[cache_key]
                if time.time() - cache_entry["timestamp"] < self.config.cache_ttl_seconds:
                    self.logger.debug("Cache hit for LLM analysis")
                    return cache_entry["data"]
                else:
                    # Remove expired cache entry
                    del self.analysis_cache[cache_key]

        return None

    async def _cache_analysis(self, cache_key: str, analysis_data: Dict[str, Any]):
        """Cache analysis result."""
        if not self.config.enable_caching:
            return

        async with self.cache_lock:
            self.analysis_cache[cache_key] = {
                "timestamp": time.time(),
                "data": analysis_data
            }

    async def _apply_enhancements(self, result: AnalysisResult, enhancement_response: Dict[str, Any]) -> AnalysisResult:
        """Apply LLM enhancements to analysis result."""
        enhanced_result = result.copy()

        # Apply enhancements based on response
        if "enhancements" in enhancement_response:
            enhanced_result.reasoning += " LLM enhancements: " + ", ".join(enhancement_response["enhancements"])

        # Add additional insights as recommendations
        if "additional_insights" in enhancement_response:
            enhanced_result.recommendations.extend(enhancement_response["additional_insights"])

        # Adjust confidence based on quality improvements
        if "quality_improvements" in enhancement_response:
            confidence_boost = len(enhancement_response["quality_improvements"]) * 0.05
            enhanced_result.confidence = min(1.0, enhanced_result.confidence + confidence_boost)

        return enhanced_result

    async def get_metrics(self) -> Dict[str, Any]:
        """Get LLM engine metrics."""
        cache_size = len(self.analysis_cache)
        total_requests = self.total_analyses
        cache_hits = sum(1 for entry in self.analysis_cache.values() if time.time() - entry["timestamp"] < self.config.cache_ttl_seconds)

        return {
            "total_analyses": self.total_analyses,
            "average_response_time": self.average_response_time,
            "cache_size": cache_size,
            "cache_hit_rate": (cache_hits / total_requests) if total_requests > 0 else 0.0,
            "error_rate": (self.error_rate / total_requests) if total_requests > 0 else 0.0,
            "context_size": len(await self.context_manager.get_context()),
            "model_name": self.config.model_name,
            "max_tokens": self.config.max_tokens
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on LLM engine."""
        return {
            "status": "healthy",
            "metrics": await self.get_metrics(),
            "cache_status": "normal" if len(self.analysis_cache) < 1000 else "warning",
            "context_status": "normal" if len(await self.context_manager.get_context()) < 100 else "warning",
            "llm_client_status": "connected"  # In real implementation, check actual client status
        }

    async def shutdown(self):
        """Shutdown the LLM analysis engine."""
        self.logger.info("Shutting down LLM analysis engine")

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        # Clear cache
        self.analysis_cache.clear()

        self.logger.info("LLM analysis engine shutdown complete")