"""
Test suite for Data Processing Pipeline (Tasks 031 & 032).

This test suite validates the integration between data reception,
processing, and technical indicators for the Long Analyst Agent.
"""

import asyncio
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from long_analyst.data_processing.data_receiver import DataReceiver, DataReceiverConfig, DataType, DataQuality
from long_analyst.indicators.indicator_engine import IndicatorEngine, IndicatorConfig
from long_analyst.integration.data_indicators_integration import DataIndicatorsIntegration, IntegrationConfig
from long_analyst.models.market_data import MarketData, Timeframe, DataSource


class TestDataReceiver:
    """Test cases for DataReceiver functionality."""

    @pytest.fixture
    def data_receiver_config(self):
        """Create test configuration for data receiver."""
        return DataReceiverConfig(
            max_concurrent_requests=10,
            request_timeout_seconds=30,
            min_data_quality=DataQuality.GOOD,
            enable_caching=False  # Disable caching for tests
        )

    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        np.random.seed(42)  # For reproducible results
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')

        data = pd.DataFrame({
            'timestamp': dates.astype(np.int64) // 10**9,
            'open': np.random.uniform(40000, 45000, 100),
            'high': np.random.uniform(41000, 46000, 100),
            'low': np.random.uniform(39000, 44000, 100),
            'close': np.random.uniform(40000, 45000, 100),
            'volume': np.random.uniform(1000, 10000, 100)
        })

        # Ensure high >= low >= open/close
        data['high'] = data[['open', 'high', 'close']].max(axis=1) + np.random.uniform(0, 500, 100)
        data['low'] = data[['open', 'low', 'close']].min(axis=1) - np.random.uniform(0, 500, 100)

        return data

    @pytest.mark.asyncio
    async def test_data_receiver_initialization(self, data_receiver_config):
        """Test DataReceiver initialization."""
        receiver = DataReceiver(data_receiver_config)

        assert receiver.config == data_receiver_config
        assert receiver.total_received == 0
        assert receiver.total_processed == 0
        assert receiver.error_count == 0

    @pytest.mark.asyncio
    async def test_data_receiver_start_stop(self, data_receiver_config):
        """Test DataReceiver start and stop functionality."""
        receiver = DataReceiver(data_receiver_config)

        # Test start
        await receiver.start()
        assert receiver.session is not None

        # Test stop
        await receiver.stop()
        assert receiver.session is None

    @pytest.mark.asyncio
    async def test_data_validation(self, data_receiver_config, sample_market_data):
        """Test data validation functionality."""
        receiver = DataReceiver(data_receiver_config)

        # Test with valid data
        validator = receiver.processor._validate_data
        result = await validator(sample_market_data, DataType.MARKET_DATA)

        assert result['is_valid'] is True
        assert result['quality_score'] > 0.7
        assert len(result['errors']) == 0

    @pytest.mark.asyncio
    async def test_data_quality_scoring(self, data_receiver_config, sample_market_data):
        """Test data quality scoring."""
        receiver = DataReceiver(data_receiver_config)

        # Test with good quality data
        processed_data = await receiver.processor.process_data(
            sample_market_data, DataSource.BINANCE, DataType.MARKET_DATA
        )

        assert processed_data.quality in [DataQuality.EXCELLENT, DataQuality.GOOD]
        assert processed_data.quality_score > 0.7
        assert len(processed_data.validation_errors) == 0

    @pytest.mark.asyncio
    async def test_data_processing_pipeline(self, data_receiver_config, sample_market_data):
        """Test complete data processing pipeline."""
        receiver = DataReceiver(data_receiver_config)
        await receiver.start()

        try:
            # Test data reception and processing
            processed_data = await receiver.receive_data(
                DataSource.BINANCE,
                DataType.MARKET_DATA,
                sample_market_data
            )

            assert processed_data is not None
            assert processed_data.quality != DataQuality.INVALID
            assert processed_data.processing_time_ms > 0
            assert len(processed_data.data) == len(sample_market_data)

        finally:
            await receiver.stop()


class TestIndicatorEngine:
    """Test cases for IndicatorEngine functionality."""

    @pytest.fixture
    def indicator_config(self):
        """Create test configuration for indicator engine."""
        return IndicatorConfig(
            max_concurrent_calculations=5,
            calculation_timeout_ms=1000,
            enable_redis_cache=False,  # Disable Redis for tests
            rsi_long_threshold=(30, 60),
            min_data_points=20
        )

    @pytest.fixture
    def test_data(self):
        """Create test data for indicator calculations."""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')

        # Create realistic price movements
        price_trend = np.linspace(40000, 45000, 100)
        price_noise = np.random.normal(0, 500, 100)
        close_prices = price_trend + price_noise

        data = pd.DataFrame({
            'timestamp': dates.astype(np.int64) // 10**9,
            'open': close_prices + np.random.uniform(-200, 200, 100),
            'high': close_prices + np.random.uniform(0, 800, 100),
            'low': close_prices - np.random.uniform(0, 800, 100),
            'close': close_prices,
            'volume': np.random.uniform(1000, 10000, 100)
        })

        # Ensure price consistency
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)

        return data

    @pytest.mark.asyncio
    async def test_indicator_engine_initialization(self, indicator_config):
        """Test IndicatorEngine initialization."""
        engine = IndicatorEngine(indicator_config)

        assert engine.config == indicator_config
        assert len(engine.calculators) >= 5  # At least 5 basic indicators
        assert 'rsi' in engine.calculators
        assert 'macd' in engine.calculators
        assert 'bollinger_bands' in engine.calculators
        assert 'support_resistance' in engine.calculators
        assert 'pattern_recognition' in engine.calculators

    @pytest.mark.asyncio
    async def test_single_indicator_calculation(self, indicator_config, test_data):
        """Test calculation of single indicator."""
        engine = IndicatorEngine(indicator_config)

        # Test RSI calculation
        result = await engine.calculate('rsi', test_data)

        assert result is not None
        assert result.indicator_name == 'RSI'
        assert result.indicator_type.value == 'momentum'
        assert result.category.value == 'primary'
        assert 'rsi' in result.values
        assert 'long_signals' in result.values
        assert result.calculation_time_ms > 0
        assert result.quality_score > 0.5

    @pytest.mark.asyncio
    async def test_rsi_long_optimization(self, indicator_config, test_data):
        """Test RSI optimization for long signals."""
        engine = IndicatorEngine(indicator_config)

        result = await engine.calculate('rsi', test_data)

        # Check that RSI is optimized for long signals
        long_signals = result.values['long_signals']
        current_rsi = result.values['current_rsi']

        assert len(long_signals) == len(test_data)
        assert 30 <= current_rsi <= 100  # RSI should be in valid range

        # Check long signal generation
        optimal_range_mask = (current_rsi >= 30) & (current_rsi <= 60)
        if optimal_range_mask:
            assert long_signals.iloc[-1] >= 0.6  # Should generate strong long signal in optimal range

    @pytest.mark.asyncio
    async def test_batch_indicator_calculation(self, indicator_config, test_data):
        """Test batch calculation of multiple indicators."""
        engine = IndicatorEngine(indicator_config)

        indicators = ['rsi', 'macd', 'bollinger_bands']
        results = await engine.batch_calculate(indicators, test_data)

        assert len(results) == 3
        assert 'rsi' in results
        assert 'macd' in results
        assert 'bollinger_bands' in results

        for result in results.values():
            assert result is not None
            assert result.calculation_time_ms > 0

    @pytest.mark.asyncio
    async def test_long_signals_generation(self, indicator_config, test_data):
        """Test comprehensive long signals generation."""
        engine = IndicatorEngine(indicator_config)

        long_signals = await engine.calculate_long_signals(test_data)

        assert 'signals' in long_signals
        assert 'overall_strength' in long_signals
        assert 'indicator_results' in long_signals
        assert 'recommendation' in long_signals
        assert 'detailed_analysis' in long_signals

        assert 0.0 <= long_signals['overall_strength'] <= 1.0
        assert long_signals['recommendation'] in ['STRONG_BUY', 'BUY', 'WEAK_BUY', 'HOLD', 'WAIT']

    @pytest.mark.asyncio
    async def test_support_resistance_detection(self, indicator_config, test_data):
        """Test support and resistance level detection."""
        engine = IndicatorEngine(indicator_config)

        result = await engine.calculate('support_resistance', test_data)

        assert result is not None
        assert 'levels' in result.values
        assert 'long_signals' in result.values

        levels = result.values['levels']
        assert len(levels) > 0

        # Check that levels have required properties
        for level in levels:
            assert hasattr(level, 'price')
            assert hasattr(level, 'level_type')
            assert hasattr(level, 'strength')

    @pytest.mark.asyncio
    async def test_pattern_recognition(self, indicator_config, test_data):
        """Test chart pattern recognition."""
        engine = IndicatorEngine(indicator_config)

        result = await engine.calculate('pattern_recognition', test_data)

        assert result is not None
        assert 'patterns' in result.values
        assert 'long_signals' in result.values

        patterns = result.values['patterns']
        # Patterns may or may not be detected depending on data
        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_indicator_caching(self, indicator_config, test_data):
        """Test indicator calculation caching."""
        engine = IndicatorEngine(indicator_config)

        # Calculate indicator first time
        result1 = await engine.calculate('rsi', test_data)

        # Calculate same indicator again (should use cache)
        result2 = await engine.calculate('rsi', test_data)

        assert result1 is not None
        assert result2 is not None

        # Results should be identical
        assert result1.values['rsi'].equals(result2.values['rsi'])

    @pytest.mark.asyncio
    async def test_performance_metrics(self, indicator_config, test_data):
        """Test performance metrics collection."""
        engine = IndicatorEngine(indicator_config)

        # Calculate some indicators
        await engine.calculate('rsi', test_data)
        await engine.calculate('macd', test_data)

        metrics = await engine.get_metrics()

        assert 'total_calculations' in metrics
        assert 'average_calculation_time_ms' in metrics
        assert 'cache_stats' in metrics
        assert metrics['total_calculations'] >= 2

    @pytest.mark.asyncio
    async def test_data_validation_in_indicators(self, indicator_config):
        """Test data validation in indicator calculations."""
        engine = IndicatorEngine(indicator_config)

        # Test with empty data
        empty_data = pd.DataFrame()
        result = await engine.calculate('rsi', empty_data)

        assert result is None  # Should return None for invalid data

        # Test with insufficient data
        small_data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104]  # Only 5 data points
        })
        result = await engine.calculate('rsi', small_data)

        assert result is None  # Should return None for insufficient data


class TestIntegration:
    """Test cases for Data-Indicators Integration."""

    @pytest.fixture
    def integration_config(self):
        """Create test configuration for integration."""
        return IntegrationConfig(
            enable_real_time_analysis=False,  # Disable for tests
            enable_batch_analysis=False,  # Disable for tests
            min_data_quality_score=0.5,
            min_data_points=20,
            signal_threshold=0.6
        )

    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for integration tests."""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')

        price_trend = np.linspace(40000, 45000, 100)
        price_noise = np.random.normal(0, 300, 100)
        close_prices = price_trend + price_noise

        return pd.DataFrame({
            'timestamp': dates.astype(np.int64) // 10**9,
            'open': close_prices + np.random.uniform(-100, 100, 100),
            'high': close_prices + np.random.uniform(0, 400, 100),
            'low': close_prices - np.random.uniform(0, 400, 100),
            'close': close_prices,
            'volume': np.random.uniform(1000, 5000, 100)
        })

    @pytest.mark.asyncio
    async def test_integration_initialization(self, integration_config):
        """Test integration layer initialization."""
        integration = DataIndicatorsIntegration(integration_config=integration_config)

        assert integration.integration_config == integration_config
        assert integration.state.value == 'idle'
        assert integration.active_pipelines == 0

    @pytest.mark.asyncio
    async def test_complete_analysis_pipeline(self, integration_config, sample_market_data):
        """Test complete analysis pipeline from data to signals."""
        integration = DataIndicatorsIntegration(integration_config=integration_config)

        # Mock the data receiver to return our test data
        with patch.object(integration.data_receiver, 'fetch_market_data') as mock_fetch:
            from long_analyst.data_processing.data_receiver import ProcessedData

            mock_processed_data = ProcessedData(
                source=DataSource.BINANCE,
                data_type=DataType.MARKET_DATA,
                timestamp=time.time(),
                quality=DataQuality.GOOD,
                data=sample_market_data,
                metadata={'quality_score': 0.8},
                processing_time_ms=50.0,
                validation_errors=[]
            )
            mock_fetch.return_value = mock_processed_data

            await integration.start()

            try:
                # Run complete analysis pipeline
                result = await integration.analyze_market_data(
                    'BTC/USDT', Timeframe.H1, DataSource.BINANCE, limit=100
                )

                assert result.success is True
                assert result.symbol == 'BTC/USDT'
                assert result.timeframe == Timeframe.H1
                assert result.processed_data is not None
                assert len(result.indicator_results) > 0
                assert result.processing_time_ms > 0

                # Check that long signals were generated
                if result.long_signals:
                    assert 'overall_strength' in result.long_signals
                    assert 'recommendation' in result.long_signals
                    assert 'detailed_analysis' in result.long_signals

            finally:
                await integration.stop()

    @pytest.mark.asyncio
    async def test_batch_analysis(self, integration_config, sample_market_data):
        """Test batch analysis functionality."""
        integration = DataIndicatorsIntegration(integration_config=integration_config)

        # Mock the data receiver
        with patch.object(integration.data_receiver, 'fetch_market_data') as mock_fetch:
            from long_analyst.data_processing.data_receiver import ProcessedData

            mock_processed_data = ProcessedData(
                source=DataSource.BINANCE,
                data_type=DataType.MARKET_DATA,
                timestamp=time.time(),
                quality=DataQuality.GOOD,
                data=sample_market_data,
                metadata={'quality_score': 0.8},
                processing_time_ms=50.0,
                validation_errors=[]
            )
            mock_fetch.return_value = mock_processed_data

            await integration.start()

            try:
                # Run batch analysis
                symbols = ['BTC/USDT', 'ETH/USDT']
                timeframes = [Timeframe.H1, Timeframe.H4]

                results = await integration.batch_analyze_symbols(
                    symbols, timeframes, DataSource.BINANCE, limit=100
                )

                assert len(results) == 4  # 2 symbols * 2 timeframes

                # Check that all results are successful
                for key, result in results.items():
                    assert result.success is True
                    assert 'BTC/USDT' in key or 'ETH/USDT' in key
                    assert 'H1' in key or 'H4' in key

            finally:
                await integration.stop()

    @pytest.mark.asyncio
    async def test_error_handling(self, integration_config):
        """Test error handling in integration layer."""
        integration = DataIndicatorsIntegration(integration_config=integration_config)

        # Mock the data receiver to return None (error case)
        with patch.object(integration.data_receiver, 'fetch_market_data') as mock_fetch:
            mock_fetch.return_value = None

            await integration.start()

            try:
                result = await integration.analyze_market_data(
                    'BTC/USDT', Timeframe.H1, DataSource.BINANCE, limit=100
                )

                assert result.success is False
                assert result.error_message is not None
                assert result.processing_time_ms > 0

            finally:
                await integration.stop()

    @pytest.mark.asyncio
    async def test_health_check(self, integration_config):
        """Test health check functionality."""
        integration = DataIndicatorsIntegration(integration_config=integration_config)

        await integration.start()

        try:
            health_status = await integration.health_check()

            assert 'status' in health_status
            assert 'components' in health_status
            assert 'metrics' in health_status
            assert health_status['status'] in ['healthy', 'degraded', 'unhealthy']

        finally:
            await integration.stop()

    @pytest.mark.asyncio
    async def test_metrics_collection(self, integration_config, sample_market_data):
        """Test metrics collection."""
        integration = DataIndicatorsIntegration(integration_config=integration_config)

        with patch.object(integration.data_receiver, 'fetch_market_data') as mock_fetch:
            from long_analyst.data_processing.data_receiver import ProcessedData

            mock_processed_data = ProcessedData(
                source=DataSource.BINANCE,
                data_type=DataType.MARKET_DATA,
                timestamp=time.time(),
                quality=DataQuality.GOOD,
                data=sample_market_data,
                metadata={'quality_score': 0.8},
                processing_time_ms=50.0,
                validation_errors=[]
            )
            mock_fetch.return_value = mock_processed_data

            await integration.start()

            try:
                # Run some analyses to generate metrics
                await integration.analyze_market_data('BTC/USDT', Timeframe.H1)
                await integration.analyze_market_data('ETH/USDT', Timeframe.H1)

                metrics = await integration.get_metrics()

                assert 'total_pipelines' in metrics
                assert 'successful_pipelines' in metrics
                assert 'total_analyses' in metrics
                assert 'average_processing_time_ms' in metrics
                assert metrics['total_pipelines'] >= 2

            finally:
                await integration.stop()


@pytest.mark.asyncio
async def test_end_to_end_pipeline():
    """End-to-end test of the complete data processing pipeline."""
    # Create test data
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='15T')  # 200 periods of 15-minute data

    # Create realistic price movements with trend
    base_price = 42000
    trend = np.linspace(0, 2000, 200)  # Upward trend
    noise = np.random.normal(0, 200, 200)
    close_prices = base_price + trend + noise

    test_data = pd.DataFrame({
        'timestamp': dates.astype(np.int64) // 10**9,
        'open': close_prices + np.random.uniform(-100, 100, 200),
        'high': close_prices + np.random.uniform(0, 300, 200),
        'low': close_prices - np.random.uniform(0, 300, 200),
        'close': close_prices,
        'volume': np.random.uniform(1000, 10000, 200)
    })

    # Ensure price consistency
    test_data['high'] = test_data[['open', 'high', 'close']].max(axis=1)
    test_data['low'] = test_data[['open', 'low', 'close']].min(axis=1)

    # Initialize integration
    config = IntegrationConfig(
        enable_real_time_analysis=False,
        enable_batch_analysis=False,
        min_data_quality_score=0.5,
        signal_threshold=0.5
    )

    integration = DataIndicatorsIntegration(integration_config=config)

    # Mock data reception
    with patch.object(integration.data_receiver, 'fetch_market_data') as mock_fetch:
        from long_analyst.data_processing.data_receiver import ProcessedData

        mock_processed_data = ProcessedData(
            source=DataSource.BINANCE,
            data_type=DataType.MARKET_DATA,
            timestamp=time.time(),
            quality=DataQuality.GOOD,
            data=test_data,
            metadata={'quality_score': 0.85},
            processing_time_ms=100.0,
            validation_errors=[]
        )
        mock_fetch.return_value = mock_processed_data

        await integration.start()

        try:
            # Run complete pipeline
            result = await integration.analyze_market_data(
                'BTC/USDT', Timeframe.M15, DataSource.BINANCE, limit=200
            )

            # Validate end-to-end functionality
            assert result.success is True
            assert result.symbol == 'BTC/USDT'
            assert result.timeframe == Timeframe.M15

            # Check data processing
            assert result.processed_data is not None
            assert result.processed_data.quality == DataQuality.GOOD

            # Check indicator calculations
            assert len(result.indicator_results) >= 5  # Should have multiple indicators

            # Check specific indicators
            assert 'rsi' in result.indicator_results
            assert 'macd' in result.indicator_results
            assert 'bollinger_bands' in result.indicator_results

            # Check long signals
            assert result.long_signals is not None
            assert 'overall_strength' in result.long_signals
            assert 'recommendation' in result.long_signals
            assert 'detailed_analysis' in result.long_signals

            # Check signal quality
            overall_strength = result.long_signals['overall_strength']
            assert 0.0 <= overall_strength <= 1.0

            # Check processing time performance
            assert result.processing_time_ms < 5000  # Should complete within 5 seconds

            # Check detailed analysis
            detailed_analysis = result.long_signals['detailed_analysis']
            assert 'technical_summary' in detailed_analysis
            assert 'indicator_signals' in detailed_analysis
            assert 'opportunities' in detailed_analysis

            print(f"✅ End-to-end test passed successfully!")
            print(f"   Symbol: {result.symbol}")
            print(f"   Timeframe: {result.timeframe.value}")
            print(f"   Overall Strength: {overall_strength:.2f}")
            print(f"   Recommendation: {result.long_signals['recommendation']}")
            print(f"   Processing Time: {result.processing_time_ms:.1f}ms")
            print(f"   Indicators Calculated: {len(result.indicator_results)}")

        finally:
            await integration.stop()


if __name__ == '__main__':
    # Run the end-to-end test
    asyncio.run(test_end_to_end_pipeline())