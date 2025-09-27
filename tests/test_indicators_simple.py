"""
做空技术指标引擎简单测试

测试内容：
1. 指标初始化
2. 基本计算功能
3. 缓存机制
"""

import pytest
import asyncio
import random
import math
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.short_analyst.indicators.indicator_engine import (
    ShortTechnicalIndicatorsEngine,
    IndicatorResult,
    IndicatorCategory,
    ShortSignalType,
    ShortSignalStrength,
    MovingAverageCrossover,
    RSIOverbought,
)

from src.short_analyst.models.market_data import MarketData, OHLCV, TimeFrame
from src.short_analyst.config.config_manager import ConfigManager


class TestSimpleIndicators:
    """简单指标测试类"""

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
        }
        config_manager.get_config.return_value = mock_config
        return ShortTechnicalIndicatorsEngine(config_manager)

    @pytest.fixture
    def simple_market_data(self):
        """创建简单市场数据"""
        # 创建OHLCV数据（单个蜡烛）
        ohlcv = OHLCV(
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            open=40000,
            high=40500,
            low=39500,
            close=40200,
            volume=1000000,
            timeframe=TimeFrame.ONE_HOUR
        )

        # 为了测试，手动添加close_prices属性
        ohlcv.close_prices = [40000 + i * 100 for i in range(50)]

        return MarketData(
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            ohlcv=ohlcv
        )

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """测试引擎初始化"""
        assert len(engine.indicators) >= 2
        assert 'ma_crossover' in engine.indicators
        assert 'rsi_overbought' in engine.indicators

    @pytest.mark.asyncio
    async def test_ma_crossover_calculation(self, simple_market_data):
        """测试移动平均线交叉计算"""
        config = {'fast_period': 5, 'slow_period': 20}
        indicator = MovingAverageCrossover(config)

        result = await indicator.calculate(simple_market_data)

        assert result.name == 'MA_CROSSOVER'
        assert result.category == IndicatorCategory.TREND_REVERSAL
        assert isinstance(result.value, (int, float))
        assert result.timestamp is not None

    @pytest.mark.asyncio
    async def test_rsi_calculation(self, simple_market_data):
        """测试RSI计算"""
        config = {'period': 14, 'overbought_threshold': 70}
        indicator = RSIOverbought(config)

        result = await indicator.calculate(simple_market_data)

        assert result.name == 'RSI_OVERBOUGHT'
        assert result.category == IndicatorCategory.OVERBOUGHT
        assert isinstance(result.value, (int, float))
        assert result.timestamp is not None

    @pytest.mark.asyncio
    async def test_indicator_validation(self, simple_market_data):
        """测试指标数据验证"""
        config = {'period': 14, 'overbought_threshold': 70}
        indicator = RSIOverbought(config)

        # 创建数据不足的market data
        insufficient_data = MarketData(
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            timeframe="1h",
            ohlcv=OHLCV(
                timestamps=[datetime.now() - timedelta(hours=i) for i in range(5, 0, -1)],
                open_prices=[40000] * 5,
                high_prices=[40100] * 5,
                low_prices=[39900] * 5,
                close_prices=[40050] * 5,
                volumes=[1000000] * 5
            )
        )

        result = await indicator.calculate(insufficient_data)

        # 数据不足时应该返回默认结果
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_cache_functionality(self, engine, simple_market_data):
        """测试缓存功能"""
        # 第一次计算
        result1 = await engine.calculate_indicator('ma_crossover', simple_market_data)

        # 检查缓存
        assert len(engine.cache) > 0

        # 清除缓存
        engine.clear_cache(simple_market_data.symbol)
        cache_key = f"{simple_market_data.symbol}_ma_crossover"
        assert cache_key not in engine.cache

    def test_cache_stats(self, engine):
        """测试缓存统计"""
        stats = engine.get_cache_stats()

        assert 'total_cache_entries' in stats
        assert 'cache_size_mb' in stats
        assert 'symbols_cached' in stats
        assert isinstance(stats['total_cache_entries'], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])