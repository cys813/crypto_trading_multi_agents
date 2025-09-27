"""
Tests for LLM Integration System.

Comprehensive test suite for LLM providers, service layer,
and configuration management.
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.long_analyst.llm.providers import (
    MockProvider, OpenAIProvider, AnthropicProvider, AzureOpenAIProvider,
    LLMProviderType, ProviderConfig, LLMRequest, LLMResponse
)
from src.long_analyst.llm.llm_service import LLMService, ServiceConfig
from src.long_analyst.llm.context_manager import ContextManager
from src.long_analyst.llm.prompt_templates import PromptTemplates
from src.long_analyst.config import (
    ConfigurationManager, ConfigType, ConfigEnvironment,
    get_config_template
)
from src.long_analyst.models.market_data import MarketData, OHLCV, DataSource, TimeFrame


class TestMockProvider:
    """Test cases for Mock LLM provider."""

    @pytest.fixture
    def mock_provider(self):
        """Create mock provider fixture."""
        config = ProviderConfig(
            provider_type=LLMProviderType.MOCK,
            model="mock-model",
            max_tokens=1000,
            temperature=0.7
        )
        return MockProvider(config)

    @pytest.mark.asyncio
    async def test_generate_response(self, mock_provider):
        """Test basic response generation."""
        request = LLMRequest(
            prompt="Test prompt",
            model="mock-model",
            max_tokens=100
        )

        response = await mock_provider.generate(request)

        assert response.success is True
        assert len(response.content) > 0
        assert response.model == "mock-model"
        assert response.tokens_used > 0
        assert response.cost == 0.0
        assert response.latency > 0

    @pytest.mark.asyncio
    async def test_batch_generate(self, mock_provider):
        """Test batch response generation."""
        requests = [
            LLMRequest(prompt=f"Test prompt {i}", model="mock-model")
            for i in range(3)
        ]

        responses = await mock_provider.batch_generate(requests)

        assert len(responses) == 3
        for response in responses:
            assert response.success is True
            assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_health_check(self, mock_provider):
        """Test health check functionality."""
        is_healthy = await mock_provider.health_check()
        assert is_healthy is True

    def test_get_model_info(self, mock_provider):
        """Test model information retrieval."""
        model_info = mock_provider.get_model_info()
        assert "provider" in model_info
        assert "available_models" in model_info
        assert model_info["provider"] == "mock"


class TestLLMService:
    """Test cases for LLM Service."""

    @pytest.fixture
    def service_config(self):
        """Create service configuration fixture."""
        mock_config = ProviderConfig(
            provider_type=LLMProviderType.MOCK,
            model="mock-model",
            max_tokens=1000,
            temperature=0.7
        )

        return ServiceConfig(
            default_provider=LLMProviderType.MOCK,
            provider_configs={LLMProviderType.MOCK: mock_config},
            max_concurrent_requests=5,
            enable_caching=True,
            cache_ttl=3600
        )

    @pytest.fixture
    def llm_service(self, service_config):
        """Create LLM service fixture."""
        return LLMService(service_config)

    @pytest.fixture
    def market_data(self):
        """Create market data fixture."""
        ohlcv = OHLCV(
            timestamp=1640995200,  # 2022-01-01
            open=45000.0,
            high=46000.0,
            low=44000.0,
            close=45500.0,
            volume=1000000.0
        )

        return MarketData(
            symbol="BTCUSDT",
            ohlcv_data=[ohlcv],
            source=DataSource.BINANCE,
            timeframe=TimeFrame.ONE_HOUR
        )

    @pytest.mark.asyncio
    async def test_analyze_market(self, llm_service, market_data):
        """Test market analysis functionality."""
        analysis = await llm_service.analyze_market(market_data)

        assert analysis is not None
        assert analysis.market_context is not None
        assert 0.0 <= analysis.overall_score <= 1.0

    @pytest.mark.asyncio
    async def test_batch_analyze(self, llm_service, market_data):
        """Test batch market analysis."""
        requests = [
            {"market_data": market_data, "template_name": "long_analysis"}
            for _ in range(3)
        ]

        results = await llm_service.batch_analyze(requests)

        assert len(results) == 3
        for result in results:
            assert result is not None
            assert 0.0 <= result.overall_score <= 1.0

    @pytest.mark.asyncio
    async def test_generate_text(self, llm_service):
        """Test text generation."""
        response = await llm_service.generate_text("Test prompt")

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_health_check(self, llm_service):
        """Test service health check."""
        health = await llm_service.health_check()

        assert "service_status" in health
        assert "provider_health" in health
        assert "cache_status" in health

    @pytest.mark.asyncio
    async def test_cache_functionality(self, llm_service, market_data):
        """Test caching functionality."""
        # First call should not be cached
        analysis1 = await llm_service.analyze_market(market_data)

        # Second call should be cached (same data)
        analysis2 = await llm_service.analyze_market(market_data)

        # Results should be identical
        assert analysis1.overall_score == analysis2.overall_score

    @pytest.mark.asyncio
    async def test_cost_tracking(self, llm_service):
        """Test cost tracking functionality."""
        initial_cost = llm_service.daily_usage

        await llm_service.generate_text("Test prompt")

        # Cost should increase (though minimal for mock provider)
        assert llm_service.daily_usage >= initial_cost

    def test_service_metrics(self, llm_service):
        """Test service metrics."""
        metrics = llm_service.metrics

        assert hasattr(metrics, 'total_requests')
        assert hasattr(metrics, 'successful_requests')
        assert hasattr(metrics, 'failed_requests')


class TestContextManager:
    """Test cases for Context Manager."""

    @pytest.fixture
    def context_manager(self):
        """Create context manager fixture."""
        return ContextManager(max_context_size=5, max_tokens=1000)

    @pytest.fixture
    def market_data(self):
        """Create market data fixture."""
        ohlcv = OHLCV(
            timestamp=1640995200,
            open=45000.0,
            high=46000.0,
            low=44000.0,
            close=45500.0,
            volume=1000000.0
        )

        return MarketData(
            symbol="BTCUSDT",
            ohlcv_data=[ohlcv],
            source=DataSource.BINANCE,
            timeframe=TimeFrame.ONE_HOUR
        )

    @pytest.mark.asyncio
    async def test_update_context(self, context_manager, market_data):
        """Test context updating."""
        await context_manager.update_context(market_data)

        context = await context_manager.get_context()
        assert len(context) > 0
        assert "BTCUSDT" in str(context)

    @pytest.mark.asyncio
    async def test_context_size_limit(self, context_manager, market_data):
        """Test context size limiting."""
        # Add more contexts than the limit
        for i in range(10):
            market_data.symbol = f"BTC{i}"
            await context_manager.update_context(market_data)

        context = await context_manager.get_context()
        assert len(context) <= 5  # Max context size

    @pytest.mark.asyncio
    async def test_optimized_context(self, context_manager, market_data):
        """Test optimized context generation."""
        await context_manager.update_context(market_data)

        optimized = await context_manager.get_optimized_context(target_tokens=100)
        assert isinstance(optimized, str)
        assert len(optimized) > 0

    @pytest.mark.asyncio
    async def test_context_summary(self, context_manager, market_data):
        """Test context summary statistics."""
        await context_manager.update_context(market_data)

        summary = await context_manager.get_context_summary()
        assert "total_entries" in summary
        assert "utilization_rate" in summary
        assert summary["total_entries"] >= 1


class TestPromptTemplates:
    """Test cases for Prompt Templates."""

    @pytest.fixture
    def prompt_templates(self):
        """Create prompt templates fixture."""
        return PromptTemplates()

    def test_template_loading(self, prompt_templates):
        """Test template loading."""
        templates = prompt_templates.list_templates()
        assert len(templates) > 0

        template_names = [t["name"] for t in templates]
        assert "long_analysis" in template_names
        assert "signal_evaluation" in template_names

    def test_template_rendering(self, prompt_templates):
        """Test template rendering."""
        context = {
            "market_data": "BTC price: $45,000",
            "context": "Bullish trend",
            "historical_context": "Recent rally",
            "additional_factors": "Low volatility"
        }

        template = prompt_templates.get_template("long_analysis")
        rendered = template.render(context)

        assert "BTC price: $45,000" in rendered
        assert "Bullish trend" in rendered

    def test_template_validation(self, prompt_templates):
        """Test template context validation."""
        template = prompt_templates.get_template("long_analysis")

        # Valid context
        valid_context = {
            "market_data": "Test data",
            "context": "Test context",
            "historical_context": "Test history",
            "additional_factors": "Test factors"
        }
        assert template.validate_context(valid_context) is True

        # Invalid context (missing required fields)
        invalid_context = {"market_data": "Test data"}
        assert template.validate_context(invalid_context) is False

    def test_custom_template(self, prompt_templates):
        """Test custom template functionality."""
        custom_template = prompt_templates.PromptTemplate(
            name="test_template",
            template="Hello {name}!",
            description="Test template",
            variables=["name"]
        )

        prompt_templates.add_template(custom_template)

        rendered = prompt_templates.render_template("test_template", {"name": "World"})
        assert rendered == "Hello World!"


class TestConfigurationManager:
    """Test cases for Configuration Manager."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create configuration manager fixture."""
        return ConfigurationManager(str(temp_config_dir), ConfigEnvironment.DEVELOPMENT)

    @pytest.mark.asyncio
    async def test_load_config(self, config_manager, temp_config_dir):
        """Test configuration loading."""
        # Create test config file
        config_data = {
            "providers": {
                "mock": {
                    "model": "test-model",
                    "max_tokens": 1000
                }
            },
            "cost_control": {
                "daily_budget": 50.0
            }
        }

        config_file = temp_config_dir / "llm.yaml"
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(config_data, f)

        # Load configuration
        loaded_config = await config_manager.load_config(ConfigType.LLM)

        assert loaded_config is not None
        assert "providers" in loaded_config
        assert "cost_control" in loaded_config

    @pytest.mark.asyncio
    async def test_update_config(self, config_manager):
        """Test configuration updating."""
        new_config = {
            "providers": {
                "mock": {
                    "model": "updated-model",
                    "max_tokens": 2000
                }
            },
            "cost_control": {
                "daily_budget": 100.0
            }
        }

        success = await config_manager.update_config(ConfigType.LLM, new_config, "Test update")

        assert success is True

        # Verify update
        loaded_config = await config_manager.get_config(ConfigType.LLM)
        assert loaded_config["providers"]["mock"]["model"] == "updated-model"

    @pytest.mark.asyncio
    async def test_config_validation(self, config_manager):
        """Test configuration validation."""
        # Invalid configuration (missing required fields)
        invalid_config = {
            "providers": {}  # Missing cost_control
        }

        with pytest.raises(ValueError):
            await config_manager.update_config(ConfigType.LLM, invalid_config)

    @pytest.mark.asyncio
    async def test_version_management(self, config_manager):
        """Test configuration version management."""
        initial_config = {"providers": {"mock": {"model": "v1"}}}
        updated_config = {"providers": {"mock": {"model": "v2"}}}

        # Load initial config
        await config_manager.update_config(ConfigType.LLM, initial_config, "Initial version")

        # Update config
        await config_manager.update_config(ConfigType.LLM, updated_config, "Updated version")

        # List versions
        versions = await config_manager.list_versions(ConfigType.LLM)
        assert len(versions) >= 2

        # Test rollback
        initial_version = versions[-1]["version"]
        rollback_success = await config_manager.rollback_config(ConfigType.LLM, initial_version)
        assert rollback_success is True

    @pytest.mark.asyncio
    async def test_config_export_import(self, config_manager, temp_config_dir):
        """Test configuration export and import."""
        # Create and load a configuration
        test_config = {"providers": {"mock": {"model": "test-model"}}}
        await config_manager.update_config(ConfigType.LLM, test_config, "Test config")

        # Export configuration
        export_file = temp_config_dir / "exported_config.yaml"
        await config_manager.export_config(ConfigType.LLM, str(export_file))

        assert export_file.exists()

        # Import configuration
        import_success = await config_manager.import_config(str(export_file))
        assert import_success is True

    @pytest.mark.asyncio
    async def test_health_check(self, config_manager):
        """Test configuration manager health check."""
        health = await config_manager.health_check()

        assert "status" in health
        assert "total_configs" in health
        assert "invalid_configs" in health

    def test_config_templates(self):
        """Test configuration templates."""
        template = get_config_template(ConfigType.LLM)

        assert "providers" in template
        assert "cost_control" in template
        assert isinstance(template, dict)


class TestIntegration:
    """Integration tests for the complete LLM system."""

    @pytest.fixture
    def full_system(self, temp_config_dir):
        """Create complete system fixture."""
        # Create config files
        llm_config = {
            "providers": {
                "mock": {
                    "model": "test-model",
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            },
            "cost_control": {
                "daily_budget": 100.0,
                "monthly_budget": 2000.0
            }
        }

        with open(temp_config_dir / "llm.yaml", 'w') as f:
            import yaml
            yaml.dump(llm_config, f)

        # Create components
        config_manager = ConfigurationManager(str(temp_config_dir), ConfigEnvironment.DEVELOPMENT)
        service_config = ServiceConfig(
            default_provider=LLMProviderType.MOCK,
            enable_caching=True,
            cache_ttl=3600
        )
        llm_service = LLMService(service_config)

        return {
            "config_manager": config_manager,
            "llm_service": llm_service
        }

    @pytest.mark.asyncio
    async def test_end_to_end_analysis(self, full_system):
        """Test end-to-end market analysis."""
        config_manager = full_system["config_manager"]
        llm_service = full_system["llm_service"]

        # Create market data
        ohlcv = OHLCV(
            timestamp=1640995200,
            open=45000.0,
            high=46000.0,
            low=44000.0,
            close=45500.0,
            volume=1000000.0
        )

        market_data = MarketData(
            symbol="BTCUSDT",
            ohlcv_data=[ohlcv],
            source=DataSource.BINANCE,
            timeframe=TimeFrame.ONE_HOUR
        )

        # Perform analysis
        analysis = await llm_service.analyze_market(market_data)

        # Verify results
        assert analysis is not None
        assert analysis.overall_score >= 0.0
        assert analysis.overall_score <= 1.0
        assert analysis.market_context is not None

        # Check metrics
        metrics = await llm_service.get_service_metrics()
        assert "service_metrics" in metrics
        assert metrics["service_metrics"]["total_requests"] >= 1

    @pytest.mark.asyncio
    async def test_configuration_hot_reload(self, full_system, temp_config_dir):
        """Test configuration hot-reload."""
        config_manager = full_system["config_manager"]
        llm_service = full_system["llm_service"]

        # Modify config file
        modified_config = {
            "providers": {
                "mock": {
                    "model": "updated-model",
                    "max_tokens": 2000,
                    "temperature": 0.5
                }
            },
            "cost_control": {
                "daily_budget": 200.0,
                "monthly_budget": 4000.0
            }
        }

        # Wait a moment to ensure file timestamp difference
        import time
        time.sleep(0.1)

        with open(temp_config_dir / "llm.yaml", 'w') as f:
            import yaml
            yaml.dump(modified_config, f)

        # The configuration should be automatically reloaded (in real implementation)
        # For test, we'll manually trigger reload
        await config_manager.load_config(ConfigType.LLM)

        # Verify config was updated
        loaded_config = await config_manager.get_config(ConfigType.LLM)
        assert loaded_config["providers"]["mock"]["model"] == "updated-model"

    @pytest.mark.asyncio
    async def test_error_handling(self, full_system):
        """Test error handling scenarios."""
        llm_service = full_system["llm_service"]

        # Test with invalid market data
        invalid_market_data = MarketData(
            symbol="INVALID",
            ohlcv_data=[],
            source=DataSource.BINANCE
        )

        # Should handle gracefully
        analysis = await llm_service.analyze_market(invalid_market_data)
        assert analysis is not None
        assert analysis.overall_score >= 0.0

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, full_system):
        """Test concurrent request handling."""
        llm_service = full_system["llm_service"]

        # Create multiple market data instances
        market_data_list = []
        for i in range(10):
            ohlcv = OHLCV(
                timestamp=1640995200 + i * 3600,
                open=45000.0 + i * 100,
                high=46000.0 + i * 100,
                low=44000.0 + i * 100,
                close=45500.0 + i * 100,
                volume=1000000.0
            )

            market_data = MarketData(
                symbol=f"BTC{i}",
                ohlcv_data=[ohlcv],
                source=DataSource.BINANCE,
                timeframe=TimeFrame.ONE_HOUR
            )
            market_data_list.append(market_data)

        # Execute concurrent analyses
        tasks = [
            llm_service.analyze_market(market_data)
            for market_data in market_data_list
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all results
        assert len(results) == 10
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent request {i} failed: {result}")
            else:
                assert result is not None
                assert 0.0 <= result.overall_score <= 1.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])