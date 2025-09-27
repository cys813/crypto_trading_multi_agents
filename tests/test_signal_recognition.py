"""
智能做空信号识别系统测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

from src.short_analyst.signal_recognition.intelligent_signal_recognition import (
    IntelligentSignalRecognition,
    SignalFusionMethod,
    FusionSignal,
    SignalComponent
)
from src.short_analyst.indicators.indicator_engine import (
    ShortTechnicalIndicatorsEngine,
    IndicatorResult,
    IndicatorCategory,
    ShortSignalType,
    ShortSignalStrength
)
# 模拟数据类
class MockOHLCVData:
    def __init__(self, timestamps, open_prices, high_prices, low_prices, close_prices, volumes):
        self.timestamps = timestamps
        self.open_prices = open_prices
        self.high_prices = high_prices
        self.low_prices = low_prices
        self.close_prices = close_prices
        self.volumes = volumes

class MockMarketData:
    def __init__(self, symbol, timestamp, ohlcv, source="test"):
        self.symbol = symbol
        self.timestamp = timestamp
        self.ohlcv = ohlcv
        self.source = source

# 类型别名
MarketData = MockMarketData
OHLCVData = MockOHLCVData


class TestSignalRecognition:
    """信号识别系统测试"""

    @pytest.fixture
    def mock_indicator_engine(self):
        """模拟指标引擎"""
        engine = Mock(spec=ShortTechnicalIndicatorsEngine)

        # 模拟指标结果
        def mock_calculate_all_indicators(market_data):
            return [
                IndicatorResult(
                    name="MA_CROSSOVER",
                    category=IndicatorCategory.TREND_REVERSAL,
                    value=-0.5,
                    timestamp=market_data.timestamp,
                    signal_type=ShortSignalType.TREND_REVERSAL,
                    signal_strength=ShortSignalStrength.MODERATE,
                    confidence=0.8,
                    metadata={'fast_ma': 40500, 'slow_ma': 41000}
                ),
                IndicatorResult(
                    name="RSI_OVERBOUGHT",
                    category=IndicatorCategory.OVERBOUGHT,
                    value=75.0,
                    timestamp=market_data.timestamp,
                    signal_type=ShortSignalType.OVERBOUGHT_REVERSAL,
                    signal_strength=ShortSignalStrength.STRONG,
                    confidence=0.9,
                    metadata={'rsi_value': 75.0}
                ),
                IndicatorResult(
                    name="BOLLINGER_UPPER",
                    category=IndicatorCategory.PRESSURE,
                    value=42000,
                    timestamp=market_data.timestamp,
                    signal_type=None,  # 无信号
                    signal_strength=None,
                    confidence=0.3,
                    metadata={'upper_band': 42000, 'current_price': 41800}
                )
            ]

        engine.calculate_all_indicators = AsyncMock(side_effect=mock_calculate_all_indicators)
        return engine

    @pytest.fixture
    def signal_recognition(self, mock_indicator_engine):
        """信号识别系统实例"""
        config = {
            'fusion_method': 'weighted_sum',
            'min_confidence_threshold': 0.6,
            'min_supporting_indicators': 1,
            'max_conflicting_indicators': 2
        }
        return IntelligentSignalRecognition(mock_indicator_engine, config)

    @pytest.fixture
    def sample_market_data(self):
        """示例市场数据"""
        ohlcv = OHLCVData(
            timestamps=[datetime.now() - timedelta(minutes=i) for i in range(50, 0, -1)],
            open_prices=[40000 + i * 100 for i in range(50)],
            high_prices=[40100 + i * 100 for i in range(50)],
            low_prices=[39900 + i * 100 for i in range(50)],
            close_prices=[40000 + i * 100 for i in range(50)],
            volumes=[1000 + i * 10 for i in range(50)]
        )

        return MarketData(
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            ohlcv=ohlcv,
            source="test"
        )

    @pytest.mark.asyncio
    async def test_recognize_signals_basic(self, signal_recognition, sample_market_data):
        """测试基本信号识别功能"""
        signals = await signal_recognition.recognize_signals(sample_market_data)

        assert len(signals) > 0
        assert all(isinstance(signal, FusionSignal) for signal in signals)
        assert all(signal.signal_type is not None for signal in signals)

    @pytest.mark.asyncio
    async def test_weighted_sum_fusion(self, signal_recognition, sample_market_data):
        """测试加权求和融合"""
        config = signal_recognition.fusion_config
        config.fusion_method = SignalFusionMethod.WEIGHTED_SUM

        signals = await signal_recognition.recognize_signals(sample_market_data)

        assert len(signals) > 0
        signal = signals[0]
        assert signal.fusion_method == SignalFusionMethod.WEIGHTED_SUM
        assert signal.overall_confidence > 0
        assert len(signal.components) > 0

    @pytest.mark.asyncio
    async def test_consensus_fusion(self, signal_recognition, sample_market_data):
        """测试共识投票融合"""
        config = signal_recognition.fusion_config
        config.fusion_method = SignalFusionMethod.CONSENSUS

        signals = await signal_recognition.recognize_signals(sample_market_data)

        assert len(signals) >= 0  # 可能为空，如果共识不足
        for signal in signals:
            assert signal.fusion_method == SignalFusionMethod.CONSENSUS
            assert 'consensus_score' in signal.metadata

    @pytest.mark.asyncio
    async def test_hierarchical_fusion(self, signal_recognition, sample_market_data):
        """测试分层融合"""
        config = signal_recognition.fusion_config
        config.fusion_method = SignalFusionMethod.HIERARCHICAL

        signals = await signal_recognition.recognize_signals(sample_market_data)

        assert len(signals) >= 0  # 可能为空，如果没有主信号
        for signal in signals:
            assert signal.fusion_method == SignalFusionMethod.HIERARCHICAL
            assert 'hierarchy_level' in signal.metadata

    def test_signal_filtering(self, signal_recognition):
        """测试信号过滤"""
        # 创建测试信号
        signals = [
            FusionSignal(
                signal_id="test1",
                signal_type=ShortSignalType.TREND_REVERSAL,
                signal_strength=ShortSignalStrength.STRONG,
                overall_confidence=0.8,
                fusion_method=SignalFusionMethod.WEIGHTED_SUM,
                components=[],
                market_data=None,
                timestamp=datetime.now(),
                risk_score=0.3,
                expected_duration="2-4h",
                supporting_indicators={'MA_CROSSOVER', 'RSI_OVERBOUGHT'},
                conflicting_indicators=set(),
                metadata={}
            ),
            FusionSignal(
                signal_id="test2",
                signal_type=ShortSignalType.OVERBOUGHT_REVERSAL,
                signal_strength=ShortSignalStrength.WEAK,
                overall_confidence=0.5,  # 低于阈值
                fusion_method=SignalFusionMethod.WEIGHTED_SUM,
                components=[],
                market_data=None,
                timestamp=datetime.now(),
                risk_score=0.3,
                expected_duration="1-2h",
                supporting_indicators={'RSI_OVERBOUGHT'},
                conflicting_indicators=set(),
                metadata={}
            )
        ]

        # 过滤信号
        filtered = signal_recognition._filter_and_rank_signals(signals)

        assert len(filtered) == 1
        assert filtered[0].signal_id == "test1"

    def test_risk_score_calculation(self, signal_recognition):
        """测试风险分数计算"""
        components = [
            SignalComponent(
                indicator_name="MA_CROSSOVER",
                category=IndicatorCategory.TREND_REVERSAL,
                weight=0.5,
                signal_type=ShortSignalType.TREND_REVERSAL,
                signal_strength=ShortSignalStrength.MODERATE,
                confidence=0.8,
                timestamp=datetime.now()
            ),
            SignalComponent(
                indicator_name="RSI_OVERBOUGHT",
                category=IndicatorCategory.OVERBOUGHT,
                weight=0.3,
                signal_type=ShortSignalType.OVERBOUGHT_REVERSAL,
                signal_strength=ShortSignalStrength.STRONG,
                confidence=0.9,
                timestamp=datetime.now()
            )
        ]

        # 创建模拟市场数据
        ohlcv = OHLCVData(
            timestamps=[datetime.now() - timedelta(minutes=i) for i in range(20, 0, -1)],
            open_prices=[40000 + i * 50 for i in range(20)],
            high_prices=[40050 + i * 50 for i in range(20)],
            low_prices=[39950 + i * 50 for i in range(20)],
            close_prices=[40000 + i * 50 for i in range(20)],
            volumes=[1000] * 20
        )

        market_data = MarketData(
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            ohlcv=ohlcv,
            source="test"
        )

        risk_score = signal_recognition._calculate_risk_score(components, market_data)

        assert 0 <= risk_score <= 1
        assert isinstance(risk_score, float)

    def test_signal_strength_calculation(self, signal_recognition):
        """测试信号强度计算"""
        # 创建模拟指标结果
        signals = [
            IndicatorResult(
                name="MA_CROSSOVER",
                category=IndicatorCategory.TREND_REVERSAL,
                value=-0.5,
                timestamp=datetime.now(),
                signal_type=ShortSignalType.TREND_REVERSAL,
                signal_strength=ShortSignalStrength.STRONG,
                confidence=0.8
            ),
            IndicatorResult(
                name="RSI_OVERBOUGHT",
                category=IndicatorCategory.OVERBOUGHT,
                value=75.0,
                timestamp=datetime.now(),
                signal_type=ShortSignalType.OVERBOUGHT_REVERSAL,
                signal_strength=ShortSignalStrength.MODERATE,
                confidence=0.7
            )
        ]

        strength = signal_recognition._calculate_overall_signal_strength(signals)

        assert strength in ShortSignalStrength
        assert strength.value >= ShortSignalStrength.VERY_WEAK.value

    def test_conflicting_indicators_identification(self, signal_recognition):
        """测试冲突指标识别"""
        components = [
            SignalComponent(
                indicator_name="MA_CROSSOVER",
                category=IndicatorCategory.TREND_REVERSAL,
                weight=0.5,
                signal_type=ShortSignalType.TREND_REVERSAL,
                signal_strength=ShortSignalStrength.MODERATE,
                confidence=0.8,
                timestamp=datetime.now()
            ),
            SignalComponent(
                indicator_name="RSI_OVERBOUGHT",
                category=IndicatorCategory.OVERBOUGHT,
                weight=0.3,
                signal_type=ShortSignalType.OVERBOUGHT_REVERSAL,
                signal_strength=ShortSignalStrength.STRONG,
                confidence=0.9,
                timestamp=datetime.now()
            )
        ]

        conflicting = signal_recognition._identify_conflicting_indicators(components)

        # 由于有不同类型的信号，应该识别为冲突
        assert len(conflicting) > 0

    def test_signal_history_tracking(self, signal_recognition, sample_market_data):
        """测试信号历史追踪"""
        # 创建测试信号
        test_signal = FusionSignal(
            signal_id="history_test",
            signal_type=ShortSignalType.TREND_REVERSAL,
            signal_strength=ShortSignalStrength.MODERATE,
            overall_confidence=0.7,
            fusion_method=SignalFusionMethod.WEIGHTED_SUM,
            components=[],
            market_data=sample_market_data,
            timestamp=datetime.now(),
            risk_score=0.4,
            expected_duration="2-4h",
            supporting_indicators={'MA_CROSSOVER'},
            conflicting_indicators=set(),
            metadata={}
        )

        # 更新历史
        signal_recognition._update_signal_history([test_signal])

        # 验证历史记录
        assert len(signal_recognition.signal_history) == 1
        assert test_signal.signal_id in signal_recognition.recent_signals
        assert signal_recognition.signal_stats['trend_reversal'] == 1
        assert signal_recognition.performance_metrics['total_signals'] == 1

    def test_signal_statistics(self, signal_recognition):
        """测试信号统计功能"""
        stats = signal_recognition.get_signal_statistics()

        assert 'signal_stats' in stats
        assert 'performance_metrics' in stats
        assert 'recent_signal_count' in stats
        assert 'cache_size' in stats

        # 验证默认值
        assert isinstance(stats['signal_stats'], dict)
        assert isinstance(stats['performance_metrics'], dict)
        assert isinstance(stats['recent_signal_count'], int)
        assert isinstance(stats['cache_size'], int)

    def test_cache_operations(self, signal_recognition):
        """测试缓存操作"""
        # 验证初始缓存为空
        assert len(signal_recognition._indicator_cache) == 0

        # 清除缓存（应该不会出错）
        signal_recognition.clear_cache()
        assert len(signal_recognition._indicator_cache) == 0

    @pytest.mark.asyncio
    async def test_error_handling(self, signal_recognition):
        """测试错误处理"""
        # 创建会引发异常的市场数据
        invalid_market_data = None

        # 应该优雅地处理错误并返回空列表
        signals = await signal_recognition.recognize_signals(invalid_market_data)
        assert signals == []

    @pytest.mark.asyncio
    async def test_empty_indicator_results(self, signal_recognition, sample_market_data):
        """测试空指标结果处理"""
        # 配置指标引擎返回空结果
        signal_recognition.indicator_engine.calculate_all_indicators = AsyncMock(return_value=[])

        signals = await signal_recognition.recognize_signals(sample_market_data)

        assert signals == []

    def test_duration_estimation(self, signal_recognition):
        """测试持续时间估计"""
        components = [
            SignalComponent(
                indicator_name="MA_CROSSOVER",
                category=IndicatorCategory.TREND_REVERSAL,
                weight=0.5,
                signal_type=ShortSignalType.TREND_REVERSAL,
                signal_strength=ShortSignalStrength.MODERATE,
                confidence=0.8,
                timestamp=datetime.now()
            )
        ]

        duration = signal_recognition._estimate_duration(
            ShortSignalType.TREND_REVERSAL, components
        )

        assert isinstance(duration, str)
        assert 'h' in duration  # 应该包含小时单位