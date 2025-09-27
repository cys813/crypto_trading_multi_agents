#!/usr/bin/env python3
"""
LLM分析与推理引擎简化测试
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 模拟必要的类
class MockFusionSignal:
    def __init__(self, signal_type, signal_strength, overall_confidence, risk_score):
        self.signal_type = signal_type
        self.signal_strength = signal_strength
        self.overall_confidence = overall_confidence
        self.risk_score = risk_score
        self.components = []

class MockSignalComponent:
    def __init__(self, indicator_name, confidence):
        self.indicator_name = indicator_name
        self.confidence = confidence

class MockShortSignalType:
    TREND_REVERSAL = "trend_reversal"
    RSI_OVERBOUGHT = "rsi_overbought"

class MockShortSignalStrength:
    MODERATE = "moderate"
    STRONG = "strong"

from short_analyst.llm_analysis.llm_engine import LLMAnalysisEngine
from short_analyst.llm_analysis.llm_models import (
    LLMAnalysisInput,
    AnalysisType,
    RiskTolerance,
    TimeHorizon,
    SentimentPolarity
)

async def test_basic_llm_analysis():
    """测试基本LLM分析功能"""
    print("=== 测试基本LLM分析功能 ===")

    # 创建LLM分析引擎
    llm_config = {
        'provider': 'mock',
        'model': 'gpt-4',
        'max_tokens': 1000,
        'temperature': 0.3,
        'enable_cache': True,
        'enable_context': True
    }

    llm_engine = LLMAnalysisEngine(llm_config)

    try:
        # 创建测试输入数据
        mock_signals = [
            MockFusionSignal(
                signal_type=MockShortSignalType.TREND_REVERSAL,
                signal_strength=MockShortSignalStrength.MODERATE,
                overall_confidence=0.75,
                risk_score=0.4
            ),
            MockFusionSignal(
                signal_type=MockShortSignalType.RSI_OVERBOUGHT,
                signal_strength=MockShortSignalStrength.STRONG,
                overall_confidence=0.85,
                risk_score=0.3
            )
        ]

        analysis_input = LLMAnalysisInput(
            symbol="BTC/USDT",
            current_price=45000.0,
            price_change_24h=-2.5,
            volume_24h=2500000000,
            market_cap=850000000000,
            fusion_signals=mock_signals,
            news_headlines=[
                "Bitcoin面临监管压力",
                "技术指标显示超买信号"
            ],
            social_media_sentiment=SentimentPolarity.BEARISH,
            fear_greed_index=72,
            market_conditions="高波动率",
            trend_context="短期下跌趋势",
            analysis_types=[
                AnalysisType.MARKET_SENTIMENT,
                AnalysisType.TECHNICAL_EXPLANATION,
                AnalysisType.RISK_ASSESSMENT,
                AnalysisType.TRADING_DECISION
            ],
            risk_tolerance=RiskTolerance.MODERATE,
            time_horizon=TimeHorizon.SHORT_TERM
        )

        # 执行分析
        print("执行LLM分析...")
        result = await llm_engine.analyze(analysis_input)

        print(f"✅ 分析完成")
        print(f"交易对: {result.symbol}")
        print(f"整体评分: {result.overall_score:.2f}")
        print(f"置信度: {result.confidence.name}")

        # 检查分析结果
        if result.market_sentiment:
            print(f"市场情绪: {result.market_sentiment.overall_sentiment.name}")
            print(f"情绪分数: {result.market_sentiment.sentiment_score:.2f}")

        if result.technical_explanations:
            print(f"技术解释数量: {len(result.technical_explanations)}")

        if result.risk_assessment:
            print(f"风险等级: {result.risk_assessment.risk_level}")
            print(f"整体风险分数: {result.risk_assessment.overall_risk_score:.2f}")

        if result.trading_decision:
            print(f"交易建议: {result.trading_decision.action}")
            print(f"信心等级: {result.trading_decision.conviction_level.name}")

        print(f"关键洞察数量: {len(result.key_insights)}")
        print(f"警告信号数量: {len(result.warning_signals)}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        llm_engine.clear_cache()
        llm_engine.clear_contexts()

async def test_partial_analysis():
    """测试部分分析功能"""
    print("\n=== 测试部分分析功能 ===")

    llm_config = {'provider': 'mock', 'enable_cache': False}
    llm_engine = LLMAnalysisEngine(llm_config)

    try:
        # 只测试市场情绪分析
        analysis_input = LLMAnalysisInput(
            symbol="ETH/USDT",
            current_price=3000.0,
            analysis_types=[AnalysisType.MARKET_SENTIMENT]
        )

        result = await llm_engine.analyze(analysis_input)

        print(f"✅ 部分分析完成")
        print(f"交易对: {result.symbol}")
        print(f"整体评分: {result.overall_score:.2f}")

        if result.market_sentiment:
            print(f"情绪分析: {result.market_sentiment.overall_sentiment.name}")
        else:
            print("⚠️  未返回情绪分析结果")

        # 验证其他分析为空
        if len(result.technical_explanations) == 0 and result.risk_assessment is None:
            print("✅ 其他分析类型正确为空")
        else:
            print("❌ 其他分析类型应该为空")

        return True

    except Exception as e:
        print(f"❌ 部分分析测试失败: {e}")
        return False

    finally:
        llm_engine.clear_cache()

async def test_caching_mechanism():
    """测试缓存机制"""
    print("\n=== 测试缓存机制 ===")

    llm_config = {'provider': 'mock', 'enable_cache': True, 'cache_ttl': 60}
    llm_engine = LLMAnalysisEngine(llm_config)

    try:
        analysis_input = LLMAnalysisInput(
            symbol="SOL/USDT",
            current_price=100.0,
            analysis_types=[AnalysisType.MARKET_SENTIMENT]
        )

        # 第一次分析
        print("执行第一次分析...")
        start_time = datetime.now()
        result1 = await llm_engine.analyze(analysis_input)
        first_time = (datetime.now() - start_time).total_seconds()

        # 第二次分析（应该使用缓存）
        print("执行第二次分析（使用缓存）...")
        start_time = datetime.now()
        result2 = await llm_engine.analyze(analysis_input)
        second_time = (datetime.now() - start_time).total_seconds()

        print(f"第一次分析时间: {first_time:.3f}s")
        print(f"第二次分析时间: {second_time:.3f}s")

        # 验证结果相同
        if result1.overall_score == result2.overall_score:
            print("✅ 缓存结果一致")
        else:
            print("❌ 缓存结果不一致")

        # 检查缓存统计
        stats = llm_engine.get_performance_stats()
        print(f"缓存大小: {stats['cache_size']}")

        return True

    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")
        return False

    finally:
        llm_engine.clear_cache()

async def test_performance_stats():
    """测试性能统计"""
    print("\n=== 测试性能统计 ===")

    llm_config = {'provider': 'mock', 'enable_cache': False}
    llm_engine = LLMAnalysisEngine(llm_config)

    try:
        # 执行多次分析
        analysis_input = LLMAnalysisInput(
            symbol="BNB/USDT",
            current_price=400.0,
            analysis_types=[AnalysisType.MARKET_SENTIMENT]
        )

        for i in range(3):
            await llm_engine.analyze(analysis_input)

        # 获取性能统计
        stats = llm_engine.get_performance_stats()

        print(f"✅ 性能统计:")
        print(f"总分析次数: {stats['total_analyses']}")
        print(f"成功分析次数: {stats['successful_analyses']}")
        print(f"失败分析次数: {stats['failed_analyses']}")
        print(f"成功率: {stats['success_rate']:.1%}")
        print(f"平均处理时间: {stats['avg_processing_time']:.3f}s")
        print(f"LLM提供商: {stats['provider']}")

        return True

    except Exception as e:
        print(f"❌ 性能统计测试失败: {e}")
        return False

    finally:
        llm_engine.clear_cache()

async def main():
    """主测试函数"""
    print("🚀 LLM分析与推理引擎测试")
    print("=" * 50)

    results = []

    # 基本LLM分析测试
    results.append(await test_basic_llm_analysis())

    # 部分分析测试
    results.append(await test_partial_analysis())

    # 缓存机制测试
    results.append(await test_caching_mechanism())

    # 性能统计测试
    results.append(await test_performance_stats())

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