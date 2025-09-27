#!/usr/bin/env python3
"""
智能做空信号识别系统演示

该脚本演示了如何使用智能信号识别系统来识别高质量的做空信号。
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

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
    ShortTechnicalIndicatorsEngine,
    IndicatorResult,
    IndicatorCategory,
    ShortSignalType,
    ShortSignalStrength
)

# 模拟配置管理器
class MockConfig:
    def __init__(self):
        self.indicators = {
            'ma_crossover': {'fast_period': 5, 'slow_period': 20},
            'rsi_overbought': {'period': 14, 'overbought_threshold': 70},
            'bollinger_upper': {'period': 20, 'std_dev': 2}
        }

class MockConfigManager:
    def __init__(self):
        self._config = MockConfig()

    def get_config(self):
        return self._config

# 模拟OHLCV数据
class MockOHLCVData:
    def __init__(self, timestamps, open_prices, high_prices, low_prices, close_prices, volumes):
        self.timestamps = timestamps
        self.open_prices = open_prices
        self.high_prices = high_prices
        self.low_prices = low_prices
        self.close_prices = close_prices
        self.volumes = volumes

async def create_sample_market_data(symbol: str, trend: str = "neutral") -> MarketData:
    """创建示例市场数据"""
    base_price = 50000.0

    if trend == "bullish":
        # 上涨趋势 - 可能出现反转信号
        price_change = [i * 100 for i in range(50)]
    elif trend == "bearish":
        # 下跌趋势 - 强化做空信号
        price_change = [-i * 80 for i in range(50)]
    else:
        # 中性趋势
        price_change = [i * 20 - 500 for i in range(50)]

    ohlcv = MockOHLCVData(
        timestamps=[datetime.now() - timedelta(minutes=i) for i in range(50, 0, -1)],
        open_prices=[base_price + change for change in price_change],
        high_prices=[base_price + change + 100 for change in price_change],
        low_prices=[base_price + change - 100 for change in price_change],
        close_prices=[base_price + change + 50 for change in price_change],
        volumes=[1000000 + i * 10000 for i in range(50)]
    )

    return MockMarketData(
        symbol=symbol,
        timestamp=datetime.now(),
        ohlcv=ohlcv,
        source="demo"
    )

async def demonstrate_signal_recognition():
    """演示信号识别功能"""
    print("🚀 智能做空信号识别系统演示")
    print("=" * 60)

    # 创建组件
    config_manager = MockConfigManager()
    indicator_engine = ShortTechnicalIndicatorsEngine(config_manager)

    # 信号识别配置
    signal_config = {
        'fusion_method': 'weighted_sum',
        'min_confidence_threshold': 0.6,
        'min_supporting_indicators': 2,
        'max_conflicting_indicators': 1,
        'indicator_weights': {
            'MA_CROSSOVER': 0.30,
            'RSI_OVERBOUGHT': 0.25,
            'BB_UPPER': 0.20,
            'VOLUME_DIVERGENCE': 0.15,
            'MACD_DIVERGENCE': 0.10
        },
        'risk_weights': {
            'market_volatility': 0.3,
            'signal_consistency': 0.4,
            'technical_confirmation': 0.3
        }
    }

    signal_recognition = IntelligentSignalRecognition(indicator_engine, signal_config)

    try:
        # 演示不同市场条件下的信号识别
        scenarios = [
            ("BTC/USDT", "bullish", "📈 上涨趋势（可能反转）"),
            ("ETH/USDT", "bearish", "📉 下跌趋势（强化做空）"),
            ("BNB/USDT", "neutral", "➡️  中性市场")
        ]

        for symbol, trend, description in scenarios:
            print(f"\n{description}")
            print("-" * 40)

            # 创建市场数据
            market_data = await create_sample_market_data(symbol, trend)

            # 识别信号
            signals = await signal_recognition.recognize_signals(market_data)

            print(f"📊 识别结果: {len(signals)} 个融合信号")

            if signals:
                for i, signal in enumerate(signals, 1):
                    print(f"\n🎯 融合信号 #{i}:")
                    print(f"   类型: {signal.signal_type.value}")
                    print(f"   强度: {signal.signal_strength.value}")
                    print(f"   置信度: {signal.overall_confidence:.2f}")
                    print(f"   风险分数: {signal.risk_score:.2f}")
                    print(f"   预期持续时间: {signal.expected_duration}")
                    print(f"   支持指标: {', '.join(signal.supporting_indicators)}")

                    if signal.conflicting_indicators:
                        print(f"   ⚠️  冲突指标: {', '.join(signal.conflicting_indicators)}")

                    print("   📈 信号组成:")
                    for component in signal.components:
                        print(f"      • {component.indicator_name}: "
                              f"权重={component.weight:.2f}, "
                              f"置信度={component.confidence:.2f}")

            else:
                print("   🔍 未检测到高置信度做空信号")

        # 演示不同融合方法
        print(f"\n🔬 融合方法对比")
        print("-" * 40)

        test_market_data = await create_sample_market_data("SOL/USDT", "bullish")

        fusion_methods = [
            ("加权求和", SignalFusionMethod.WEIGHTED_SUM),
            ("共识投票", SignalFusionMethod.CONSENSUS),
            ("分层融合", SignalFusionMethod.HIERARCHICAL)
        ]

        for method_name, method_enum in fusion_methods:
            signal_recognition.fusion_config.fusion_method = method_enum
            method_signals = await signal_recognition.recognize_signals(test_market_data)

            print(f"\n{method_name}方法:")
            if method_signals:
                for signal in method_signals:
                    print(f"   ✅ {signal.signal_type.value} "
                          f"(置信度: {signal.overall_confidence:.2f}, "
                          f"强度: {signal.signal_strength.value})")
            else:
                print(f"   ❌ 无信号")

        # 显示系统统计
        print(f"\n📈 系统统计")
        print("-" * 40)
        stats = signal_recognition.get_signal_statistics()
        print(f"总信号数: {stats['performance_metrics']['total_signals']}")
        print(f"平均置信度: {stats['performance_metrics']['avg_confidence']:.2f}")
        print(f"缓存大小: {stats['cache_size']} 条目")

        # 显示最近的信号历史
        print(f"\n📜 最近信号历史")
        print("-" * 40)
        recent_signals = signal_recognition.get_recent_signals(limit=5)
        if recent_signals:
            for signal in recent_signals:
                print(f"   {signal.timestamp.strftime('%H:%M:%S')} - "
                      f"{signal.signal_type.value} "
                      f"({signal.signal_strength.value})")
        else:
            print("   暂无信号历史")

    finally:
        await indicator_engine.close()

    print(f"\n✨ 演示完成！")
    print("\n💡 提示:")
    print("   • 系统整合了多个技术指标来生成高质量的做空信号")
    print("   • 支持多种信号融合算法")
    print("   • 包含风险评估和置信度计算")
    print("   • 提供信号历史追踪和统计分析")

async def main():
    """主函数"""
    try:
        await demonstrate_signal_recognition()
    except KeyboardInterrupt:
        print("\n\n⏹️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())