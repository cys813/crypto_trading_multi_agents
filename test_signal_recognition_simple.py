#!/usr/bin/env python3
"""
智能信号识别系统简化测试
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from short_analyst.signal_recognition.intelligent_signal_recognition import (
    IntelligentSignalRecognition,
    SignalFusionMethod,
    FusionSignal,
    SignalComponent,
    MarketData,
    MockMarketData
)
from short_analyst.indicators.indicator_engine import (
    IndicatorResult,
    IndicatorCategory,
    ShortSignalType,
    ShortSignalStrength
)

# 模拟OHLCV数据
class MockOHLCVData:
    def __init__(self, timestamps, open_prices, high_prices, low_prices, close_prices, volumes):
        self.timestamps = timestamps
        self.open_prices = open_prices
        self.high_prices = high_prices
        self.low_prices = low_prices
        self.close_prices = close_prices
        self.volumes = volumes

async def test_basic_signal_recognition():
    """测试基本信号识别功能"""
    print("=== 测试基本信号识别功能 ===")

    # 创建模拟指标引擎
    mock_indicator_engine = Mock()

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
                signal_type=ShortSignalType.RSI_OVERBOUGHT,
                signal_strength=ShortSignalStrength.STRONG,
                confidence=0.9,
                metadata={'rsi_value': 75.0}
            ),
            IndicatorResult(
                name="BB_UPPER",
                category=IndicatorCategory.RESISTANCE,
                value=42000,
                timestamp=market_data.timestamp,
                signal_type=ShortSignalType.BOLLINGER_UPPER,
                signal_strength=ShortSignalStrength.MODERATE,
                confidence=0.7,
                metadata={'upper_band': 42000, 'current_price': 41800}
            )
        ]

    mock_indicator_engine.calculate_all_indicators = AsyncMock(side_effect=mock_calculate_all_indicators)

    # 创建信号识别系统
    config = {
        'fusion_method': 'weighted_sum',
        'min_confidence_threshold': 0.6,
        'min_supporting_indicators': 1,
        'indicator_weights': {
            'MA_CROSSOVER': 0.4,
            'RSI_OVERBOUGHT': 0.3,
            'BOLLINGER_UPPER': 0.2,
            'VOLUME_DIVERGENCE': 0.1
        }
    }

    signal_recognition = IntelligentSignalRecognition(mock_indicator_engine, config)

    # 创建测试市场数据
    ohlcv = MockOHLCVData(
        timestamps=[datetime.now() - timedelta(minutes=i) for i in range(50, 0, -1)],
        open_prices=[40000 + i * 100 for i in range(50)],
        high_prices=[40100 + i * 100 for i in range(50)],
        low_prices=[39900 + i * 100 for i in range(50)],
        close_prices=[40000 + i * 100 for i in range(50)],
        volumes=[1000 + i * 10 for i in range(50)]
    )

    market_data = MockMarketData(
        symbol="BTC/USDT",
        timestamp=datetime.now(),
        ohlcv=ohlcv,
        source="test"
    )

    try:
        # 测试信号识别
        signals = await signal_recognition.recognize_signals(market_data)

        print(f"识别到 {len(signals)} 个融合信号")

        # 显示信号详情
        for i, signal in enumerate(signals, 1):
            print(f"\n=== 融合信号 {i} ===")
            print(f"信号ID: {signal.signal_id}")
            print(f"信号类型: {signal.signal_type.value}")
            print(f"信号强度: {signal.signal_strength.value}")
            print(f"总体置信度: {signal.overall_confidence:.2f}")
            print(f"融合方法: {signal.fusion_method.value}")
            print(f"风险分数: {signal.risk_score:.2f}")
            print(f"支持指标: {', '.join(signal.supporting_indicators)}")
            print(f"信号组成数: {len(signal.components)}")

            for component in signal.components:
                print(f"  - {component.indicator_name}: 权重={component.weight:.2f}, "
                      f"置信度={component.confidence:.2f}")

        print("\n✅ 基本信号识别测试通过")

        # 测试不同融合方法
        print("\n=== 测试不同融合方法 ===")
        methods = [
            SignalFusionMethod.WEIGHTED_SUM,
            SignalFusionMethod.CONSENSUS,
            SignalFusionMethod.HIERARCHICAL
        ]

        for method in methods:
            signal_recognition.fusion_config.fusion_method = method
            method_signals = await signal_recognition.recognize_signals(market_data)
            print(f"{method.value}: {len(method_signals)} 个信号")

        print("\n✅ 不同融合方法测试通过")

        # 测试统计功能
        print("\n=== 测试统计功能 ===")
        stats = signal_recognition.get_signal_statistics()
        print(f"总信号数: {stats['performance_metrics']['total_signals']}")
        print(f"平均置信度: {stats['performance_metrics']['avg_confidence']:.2f}")
        print(f"缓存大小: {stats['cache_size']}")

        print("\n✅ 统计功能测试通过")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

async def test_signal_filtering():
    """测试信号过滤功能"""
    print("\n=== 测试信号过滤功能 ===")

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
            signal_type=ShortSignalType.RSI_OVERBOUGHT,
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

    # 创建信号识别系统
    mock_engine = Mock()
    config = {
        'fusion_method': 'weighted_sum',
        'min_confidence_threshold': 0.6,
        'min_supporting_indicators': 1,
        'max_conflicting_indicators': 2
    }
    signal_recognition = IntelligentSignalRecognition(mock_engine, config)

    # 过滤信号
    filtered = signal_recognition._filter_and_rank_signals(signals)

    print(f"过滤前信号数: {len(signals)}")
    print(f"过滤后信号数: {len(filtered)}")

    if len(filtered) == 1 and filtered[0].signal_id == "test1":
        print("✅ 信号过滤测试通过")
        return True
    else:
        print("❌ 信号过滤测试失败")
        return False

async def main():
    """主测试函数"""
    print("开始智能信号识别系统测试...")
    print("=" * 50)

    results = []

    # 基本信号识别测试
    results.append(await test_basic_signal_recognition())

    # 信号过滤测试
    results.append(await test_signal_filtering())

    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)