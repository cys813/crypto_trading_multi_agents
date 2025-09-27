#!/usr/bin/env python3
"""
做空胜率计算与风险评估简化测试
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 模拟必要的类
class MockShortSignalType:
    TREND_REVERSAL = "trend_reversal"
    RSI_OVERBOUGHT = "rsi_overbought"
    BOLLINGER_UPPER = "bollinger_upper"

class MockShortSignalStrength:
    WEAK = 1
    MODERATE = 2
    STRONG = 3

class MockShortSignal:
    def __init__(self, signal_type, strength, confidence_score):
        self.signal_type = signal_type
        self.strength = strength
        self.confidence_score = confidence_score
        self.symbol = "BTC/USDT"
        self.risk_level = random.randint(1, 5)
        self.liquidity_risk = random.random() * 0.5
        self.short_squeeze_risk = random.random() * 0.3
        self.overall_score = (strength + confidence_score) / 4.0
        self.metadata = {}  # 添加metadata属性

from short_analyst.win_rate_calculation.win_rate_models import TradeResult
from short_analyst.win_rate_calculation.win_rate_calculator import WinRateCalculator, WinRateMetric
from short_analyst.win_rate_calculation.risk_assessor import RiskAssessor
from short_analyst.win_rate_calculation.optimization_engine import OptimizationEngine

def generate_mock_trade_history(num_trades: int = 100) -> List[TradeResult]:
    """生成模拟交易历史"""
    trades = []
    base_price = 45000

    for i in range(num_trades):
        # 生成随机交易结果
        is_successful = random.random() > 0.45  # 55%胜率

        if is_successful:
            profit_pct = random.uniform(0.5, 5.0)  # 盈利0.5%-5%
        else:
            profit_pct = random.uniform(-3.0, -0.5)  # 亏损0.5%-3%

        # 随机信号类型和强度
        signal_type = random.choice([MockShortSignalType.TREND_REVERSAL,
                                   MockShortSignalType.RSI_OVERBOUGHT,
                                   MockShortSignalType.BOLLINGER_UPPER])
        signal_strength = random.choice([MockShortSignalStrength.WEAK,
                                       MockShortSignalStrength.MODERATE,
                                       MockShortSignalStrength.STRONG])

        trade = TradeResult(
            trade_id=f"trade_{i}",
            symbol="BTC/USDT",
            entry_price=base_price,
            exit_price=base_price * (1 + profit_pct / 100),
            entry_time=datetime.now() - timedelta(days=random.randint(1, 90)),
            exit_time=datetime.now() - timedelta(days=random.randint(1, 90)),
            profit_loss_pct=profit_pct,
            is_successful=is_successful,
            signal_type=signal_type,
            signal_strength=signal_strength,
            holding_period=random.uniform(1, 72),  # 1-72小时
            volatility_at_entry=random.uniform(0.01, 0.08),
            volume_at_entry=random.uniform(1000000, 100000000),
            exit_reason=random.choice(['profit_target', 'stop_loss', 'timeout']),
            max_drawdown=random.uniform(0.01, 0.05)
        )

        trades.append(trade)
        base_price *= (1 + random.uniform(-0.02, 0.02))  # 价格随机波动

    return trades

def generate_mock_signals(num_signals: int = 20) -> List[MockShortSignal]:
    """生成模拟信号"""
    signals = []

    for i in range(num_signals):
        signal_type = random.choice([MockShortSignalType.TREND_REVERSAL,
                                   MockShortSignalType.RSI_OVERBOUGHT,
                                   MockShortSignalType.BOLLINGER_UPPER])
        signal_strength = random.choice([MockShortSignalStrength.WEAK,
                                       MockShortSignalStrength.MODERATE,
                                       MockShortSignalStrength.STRONG])

        signal = MockShortSignal(
            signal_type=signal_type,
            strength=signal_strength,
            confidence_score=random.uniform(0.4, 0.9)
        )

        signals.append(signal)

    return signals

async def test_win_rate_calculation():
    """测试胜率计算"""
    print("=== 测试胜率计算功能 ===")

    calculator = WinRateCalculator()

    # 生成模拟数据
    trade_history = generate_mock_trade_history(50)
    signal_history = generate_mock_signals(15)

    try:
        # 计算胜率分析
        print("执行胜率分析...")
        analysis = await calculator.calculate_win_rate(
            trade_history=trade_history,
            signal_history=signal_history,
            period="30d"
        )

        print(f"✅ 胜率分析完成")
        print(f"总信号数: {analysis.total_signals}")
        print(f"成功信号数: {analysis.successful_signals}")
        print(f"整体成功率: {analysis.overall_success_rate:.2%}")
        print(f"置信区间: [{analysis.confidence_interval[0]:.2%}, {analysis.confidence_interval[1]:.2%}]")

        if analysis.success_by_signal_type:
            print(f"信号类型成功率: {analysis.success_by_signal_type}")

        if analysis.success_by_strength:
            print(f"强度相关性: {analysis.strength_correlation:.3f}")

        print(f"主要洞察: {analysis.key_insights[:2]}")

        return True

    except Exception as e:
        print(f"❌ 胜率计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance_metrics():
    """测试绩效指标计算"""
    print("\n=== 测试绩效指标计算 ===")

    calculator = WinRateCalculator()
    trade_history = generate_mock_trade_history(80)

    try:
        # 计算绩效指标
        print("执行绩效指标计算...")
        metrics = await calculator.calculate_performance_metrics(
            trade_history=trade_history,
            period="60d",
            benchmark_return=0.05
        )

        print(f"✅ 绩效指标计算完成")
        print(f"总交易次数: {metrics.total_trades}")
        print(f"胜率: {metrics.win_rate:.2%}")
        print(f"加权胜率: {metrics.win_rate_weighted:.2%}")
        print(f"盈亏比: {metrics.profit_factor:.2f}")
        print(f"夏普比率: {metrics.sharpe_ratio:.3f}")
        print(f"最大回撤: {metrics.max_drawdown:.2%}")
        print(f"最大连续盈利: {metrics.max_consecutive_wins}")
        print(f"最大连续亏损: {metrics.max_consecutive_losses}")

        if metrics.performance_by_signal_type:
            print(f"信号类型绩效: {list(metrics.performance_by_signal_type.keys())}")

        return True

    except Exception as e:
        print(f"❌ 绩效指标测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_risk_assessment():
    """测试风险评估"""
    print("\n=== 测试风险评估功能 ===")

    assessor = RiskAssessor()

    # 生成测试数据
    signals = generate_mock_signals(10)
    trade_history = generate_mock_trade_history(40)

    # 模拟市场数据
    market_data = {
        'volume_24h': 50000000,
        'market_cap': 850000000000,
        'correlation_with_btc': 0.8,
        'trend': 'uptrend',
        'volatility': 0.04,
        'funding_rate': 0.0001,
        'long_short_ratio': 2.5,
        'fear_greed_index': 65,
        'regulatory_news': []
    }

    try:
        # 执行风险评估
        print("执行风险评估...")
        assessment = await assessor.assess_risk(
            current_signals=signals,
            trade_history=trade_history,
            market_data=market_data
        )

        print(f"✅ 风险评估完成")
        print(f"整体风险评分: {assessment.overall_risk_score:.3f}")
        print(f"风险等级: {assessment.risk_level}")
        print(f"市场风险: {assessment.market_risk_score:.3f}")
        print(f"流动性风险: {assessment.liquidity_risk_score:.3f}")
        print(f"波动率风险: {assessment.volatility_risk_score:.3f}")
        print(f"轧空风险: {assessment.short_squeeze_risk_score:.3f}")
        print(f"轧空概率: {assessment.short_squeeze_probability:.3f}")
        print(f"VaR(95%): {assessment.var_95:.2%}")
        print(f"建议仓位限制: {assessment.position_size_limit:.1%}")

        if assessment.risk_warnings:
            print(f"风险预警: {assessment.risk_warnings[:2]}")

        return True

    except Exception as e:
        print(f"❌ 风险评估测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_optimization_engine():
    """测试优化引擎"""
    print("\n=== 测试优化引擎 ===")

    engine = OptimizationEngine()

    # 生成测试数据
    trade_history = generate_mock_trade_history(60)
    signal_history = generate_mock_signals(20)

    # 先计算当前绩效指标
    calculator = WinRateCalculator()
    current_metrics = await calculator.calculate_performance_metrics(trade_history, "30d")

    try:
        # 生成优化建议
        print("执行优化分析...")
        recommendations = await engine.generate_optimization_recommendations(
            trade_history=trade_history,
            signal_history=signal_history,
            current_metrics=current_metrics
        )

        print(f"✅ 优化分析完成，生成 {len(recommendations)} 条建议")

        for i, rec in enumerate(recommendations[:3]):  # 显示前3条建议
            print(f"\n建议 {i+1}:")
            print(f"  目标: {rec.optimization_target}")
            print(f"  当前值: {rec.current_value:.3f}")
            print(f"  预期改进: {rec.expected_improvement:.3f}")
            print(f"  策略: {rec.strategy}")
            print(f"  优先级: {rec.priority}")
            print(f"  置信度: {rec.confidence_level:.2%}")

        return True

    except Exception as e:
        print(f"❌ 优化引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 做空胜率计算与风险评估测试")
    print("=" * 50)

    results = []

    # 胜率计算测试
    results.append(await test_win_rate_calculation())

    # 绩效指标测试
    results.append(await test_performance_metrics())

    # 风险评估测试
    results.append(await test_risk_assessment())

    # 优化引擎测试
    results.append(await test_optimization_engine())

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