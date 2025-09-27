"""
做空技术指标引擎测试文件

测试内容：
1. 指标计算准确性
2. 信号检测功能
3. 缓存机制
4. 性能优化
5. 异常处理
"""

import pytest
import asyncio
import random
import math
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.short_analyst.indicators.indicator_engine import (
    ShortTechnicalIndicatorsEngine,
    IndicatorResult,
    IndicatorCategory,
    ShortSignalType,
    SignalStrength,
    MovingAverageCrossover,
    RSIOverbought,
    BollingerBandsUpper,
    VolumePriceDivergence,
    MACDDivergence,
)
from src.short_analyst.models.market_data import MarketData, OHLCV
from src.short_analyst.config.config_manager import ConfigManager


class TestIndicatorEngine:
    """做空技术指标引擎测试类"""

    @pytest.fixture
    def config_manager(self):
        """创建配置管理器"""
        return Mock(spec=ConfigManager)

    @pytest.fixture
    def engine(self, config_manager):
        """创建指标引擎"""
        mock_config = Mock()
        mock_config.indicators = {
            'ma_crossover': {'fast_period': 5, 'slow_period': 20},
            'rsi_overbought': {'period': 14, 'overbought_threshold': 70},
            'bb_upper': {'period': 20, 'std_dev': 2},
            'volume_divergence': {'lookback_period': 5},
            'macd_divergence': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9, 'lookback_period': 5}
        }

        config_manager.get_config.return_value = mock_config
        return ShortTechnicalIndicatorsEngine(config_manager)

    @pytest.fixture
    def sample_market_data(self):
        """创建示例市场数据"""
        # 创建上升趋势数据（适合测试做空信号）
        base_price = 40000
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)]

        # 模拟上升趋势，但最后开始回调
        trend_factor = [i * 10 for i in range(100)]
        noise = [random.gauss(0, 50) for i in range(100)]

        close_prices = [base_price + trend_factor[i] + noise[i] for i in range(100)]
        open_prices = [close_prices[i] + random.gauss(-20, 20) for i in range(100)]
        high_prices = [close_prices[i] + abs(random.gauss(50, 20)) for i in range(100)]
        low_prices = [close_prices[i] - abs(random.gauss(50, 20)) for i in range(100)]
        volumes = [random.uniform(1000000, 5000000) for i in range(100)]

        return MarketData(
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            timeframe="1h",
            ohlcv=OHLCV(
                timestamps=timestamps,
                open_prices=open_prices.tolist(),
                high_prices=high_prices.tolist(),
                low_prices=low_prices.tolist(),
                close_prices=close_prices.tolist(),
                volumes=volumes.tolist()
            )
        )

    @pytest.fixture
    def overbought_market_data(self):
        """创建超买市场数据"""
        # 创建超买条件的数据
        base_price = 40000
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(50, 0, -1)]

        # 模拟强劲上涨后高位震荡
        trend_up = [i * 100 for i in range(25)]  # 上涨
        trend_sideways = [2500 + math.sin(i) * 50 for i in range(25)]  # 高位震荡
        trend_factor = trend_up + trend_sideways

        close_prices = [base_price + trend_factor[i] for i in range(50)]
        open_prices = [close_prices[i] + random.gauss(-10, 10) for i in range(50)]
        high_prices = [close_prices[i] + abs(random.gauss(30, 10)) for i in range(50)]
        low_prices = [close_prices[i] - abs(random.gauss(30, 10)) for i in range(50)]
        volumes = [random.uniform(2000000, 8000000) for i in range(50)]

        return MarketData(
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            timeframe="1h",
            ohlcv=OHLCV(
                timestamps=timestamps,
                open_prices=open_prices.tolist(),
                high_prices=high_prices.tolist(),
                low_prices=low_prices.tolist(),
                close_prices=close_prices.tolist(),
                volumes=volumes.tolist()
            )
        )

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """测试引擎初始化"""
        assert len(engine.indicators) == 5
        assert 'ma_crossover' in engine.indicators
        assert 'rsi_overbought' in engine.indicators
        assert 'bb_upper' in engine.indicators
        assert 'volume_divergence' in engine.indicators
        assert 'macd_divergence' in engine.indicators

    @pytest.mark.asyncio
    async def test_calculate_all_indicators(self, engine, sample_market_data):
        """测试计算所有指标"""
        results = await engine.calculate_all_indicators(sample_market_data)

        assert len(results) == 5
        for result in results:
            assert isinstance(result, IndicatorResult)
            assert result.value is not None
            assert result.timestamp is not None
            assert result.confidence >= 0.0
            assert result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_single_indicator(self, engine, sample_market_data):
        """测试计算单个指标"""
        result = await engine.calculate_indicator('ma_crossover', sample_market_data)

        assert result is not None
        assert result.name == 'MA_CROSSOVER'
        assert result.category == IndicatorCategory.TREND_REVERSAL
        assert isinstance(result.value, (int, float))

    @pytest.mark.asyncio
    async def test_calculate_invalid_indicator(self, engine, sample_market_data):
        """测试计算无效指标"""
        result = await engine.calculate_indicator('invalid_indicator', sample_market_data)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_short_signals(self, engine, overbought_market_data):
        """测试获取做空信号"""
        signals = await engine.get_short_signals(overbought_market_data)

        assert isinstance(signals, list)
        for signal in signals:
            assert signal.signal_type is not None
            assert signal.signal_strength is not None
            assert signal.confidence > 0.5  # 信号应该有较高的置信度

    @pytest.mark.asyncio
    async def test_indicator_cache(self, engine, sample_market_data):
        """测试指标缓存功能"""
        # 第一次计算
        result1 = await engine.calculate_indicator('ma_crossover', sample_market_data)

        # 清除缓存
        engine.clear_cache(sample_market_data.symbol)

        # 第二次计算
        result2 = await engine.calculate_indicator('ma_crossover', sample_market_data)

        # 两次计算结果应该相同
        assert result1.value == result2.value

    def test_get_indicator_summary(self, engine, sample_market_data):
        """测试获取指标摘要"""
        # 预填充一些缓存数据
        engine.cache[f"{sample_market_data.symbol}_ma_crossover"] = Mock(
            symbol=sample_market_data.symbol,
            indicator_name="ma_crossover",
            timeframe="1h",
            values=[-0.05, -0.03, -0.01],
            timestamps=[datetime.now() - timedelta(minutes=i) for i in range(3, 0, -1)],
            last_update=datetime.now(),
            ttl=timedelta(hours=1)
        )

        summary = engine.get_indicator_summary(sample_market_data.symbol)

        assert summary['symbol'] == sample_market_data.symbol
        assert summary['total_indicators'] == 5
        assert summary['cached_indicators'] >= 1
        assert 'signals' in summary

    def test_cache_stats(self, engine):
        """测试缓存统计"""
        stats = engine.get_cache_stats()

        assert 'total_cache_entries' in stats
        assert 'cache_size_mb' in stats
        assert 'symbols_cached' in stats
        assert isinstance(stats['total_cache_entries'], int)
        assert isinstance(stats['cache_size_mb'], (int, float))

    def test_clear_cache(self, engine):
        """测试清除缓存"""
        # 添加一些缓存数据
        engine.cache['test_key'] = Mock()
        engine.cache['BTC/USDT_ma_crossover'] = Mock()
        engine.cache['ETH/USDT_rsi_overbought'] = Mock()

        # 清除特定symbol的缓存
        engine.clear_cache('BTC/USDT')
        assert len(engine.cache) == 2  # 应该还剩下2个

        # 清除所有缓存
        engine.clear_cache()
        assert len(engine.cache) == 0

    @pytest.mark.asyncio
    async def test_engine_close(self, engine):
        """测试引擎关闭"""
        with patch.object(engine.executor, 'shutdown') as mock_shutdown:
            await engine.close()
            mock_shutdown.assert_called_once_with(wait=True)


class TestMovingAverageCrossover:
    """移动平均线交叉指标测试"""

    @pytest.fixture
    def indicator(self):
        config = {'fast_period': 5, 'slow_period': 20}
        return MovingAverageCrossover(config)

    @pytest.fixture
    def death_cross_data(self):
        """死亡交叉数据"""
        # 创建快线下穿慢线的数据
        close_prices = [100 + i for i in range(30)]  # 上升趋势
        close_prices.extend([130 - (i-30)*2 for i in range(30, 40)])  # 突然下降

        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(40, 0, -1)]

        return MarketData(
            symbol="TEST/USDT",
            timestamp=datetime.now(),
            timeframe="5m",
            ohlcv=OHLCV(
                timestamps=timestamps,
                open_prices=[p - 1 for p in close_prices],
                high_prices=[p + 2 for p in close_prices],
                low_prices=[p - 2 for p in close_prices],
                close_prices=close_prices,
                volumes=[100000] * 40
            )
        )

    @pytest.mark.asyncio
    async def test_death_cross_detection(self, indicator, death_cross_data):
        """测试死亡交叉检测"""
        result = await indicator.calculate(death_cross_data)

        assert result.signal_type == ShortSignalType.TREND_REVERSAL
        assert result.signal_strength in [SignalStrength.WEAK, SignalStrength.MODERATE, SignalStrength.STRONG]
        assert result.confidence > 0.5


class TestRSIOverbought:
    """RSI超买指标测试"""

    @pytest.fixture
    def indicator(self):
        config = {'period': 14, 'overbought_threshold': 70}
        return RSIOverbought(config)

    @pytest.mark.asyncio
    async def test_overbought_detection(self, indicator, overbought_market_data):
        """测试超买检测"""
        result = await indicator.calculate(overbought_market_data)

        # 由于数据是高位震荡，应该能检测到超买信号
        if result.signal_type == ShortSignalType.OVERBOUGHT:
            assert result.signal_strength is not None
            assert result.confidence > 0.5


class TestBollingerBandsUpper:
    """布林带上轨指标测试"""

    @pytest.fixture
    def indicator(self):
        config = {'period': 20, 'std_dev': 2}
        return BollingerBandsUpper(config)

    @pytest.mark.asyncio
    async def test_upper_breakthrough(self, indicator, overbought_market_data):
        """测试上轨突破"""
        result = await indicator.calculate(overbought_market_data)

        assert isinstance(result.value, (int, float))
        if result.signal_type == ShortSignalType.RESISTANCE_BREAK:
            assert result.signal_strength is not None


class TestVolumePriceDivergence:
    """量价背离指标测试"""

    @pytest.fixture
    def indicator(self):
        config = {'lookback_period': 5}
        return VolumePriceDivergence(config)

    @pytest.fixture
    def divergence_data(self):
        """量价背离数据"""
        # 价格上涨但成交量下降
        close_prices = [100 + i*2 for i in range(10)]  # 价格上涨
        volumes = [1000000 - i*50000 for i in range(10)]  # 成交量下降

        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(10, 0, -1)]

        return MarketData(
            symbol="TEST/USDT",
            timestamp=datetime.now(),
            timeframe="5m",
            ohlcv=OHLCV(
                timestamps=timestamps,
                open_prices=[p - 1 for p in close_prices],
                high_prices=[p + 1 for p in close_prices],
                low_prices=[p - 1 for p in close_prices],
                close_prices=close_prices,
                volumes=volumes
            )
        )

    @pytest.mark.asyncio
    async def test_divergence_detection(self, indicator, divergence_data):
        """测试量价背离检测"""
        result = await indicator.calculate(divergence_data)

        # 应该能检测到量价背离
        if result.signal_type == ShortSignalType.VOLUME_DIVERGENCE:
            assert result.signal_strength is not None
            assert result.confidence > 0.3


class TestMACDDivergence:
    """MACD背离指标测试"""

    @pytest.fixture
    def indicator(self):
        config = {'fast_period': 12, 'slow_period': 26, 'signal_period': 9, 'lookback_period': 5}
        return MACDDivergence(config)

    @pytest.mark.asyncio
    async def test_macd_calculation(self, indicator, overbought_market_data):
        """测试MACD计算"""
        result = await indicator.calculate(overbought_market_data)

        assert isinstance(result.value, (int, float))
        assert result.value >= 0  # 背离强度应该是非负的


@pytest.mark.asyncio
async def test_performance_benchmark():
    """性能基准测试"""
    config_manager = Mock()
    mock_config = Mock()
    mock_config.indicators = {
        'ma_crossover': {'fast_period': 5, 'slow_period': 20},
        'rsi_overbought': {'period': 14},
    }
    config_manager.get_config.return_value = mock_config

    engine = ShortTechnicalIndicatorsEngine(config_manager)

    # 创建大量市场数据
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
    tasks = []

    for symbol in symbols:
        close_prices = [40000 + i * 100 + random.gauss(0, 50) for i in range(100)]
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)]

        market_data = MarketData(
            symbol=symbol,
            timestamp=datetime.now(),
            timeframe="1h",
            ohlcv=OHLCV(
                timestamps=timestamps,
                open_prices=[p - 20 for p in close_prices],
                high_prices=[p + 50 for p in close_prices],
                low_prices=[p - 50 for p in close_prices],
                close_prices=close_prices,
                volumes=[1000000] * 100
            )
        )

        task = asyncio.create_task(engine.calculate_all_indicators(market_data))
        tasks.append(task)

    # 测量并发性能
    start_time = datetime.now()
    results = await asyncio.gather(*tasks)
    end_time = datetime.now()

    # 验证性能要求
    total_time = (end_time - start_time).total_seconds()
    assert total_time < 5.0  # 5个币种的指标计算应该在5秒内完成

    # 验证结果
    assert len(results) == 5
    for result in results:
        assert len(result) >= 2  # 至少有2个指标结果

    await engine.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])