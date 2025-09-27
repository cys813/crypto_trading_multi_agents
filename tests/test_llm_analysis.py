"""
LLM分析与推理引擎测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from src.short_analyst.llm_analysis.llm_engine import (
    LLMAnalysisEngine,
    LLMProvider,
    MockLLMClient,
    PromptTemplate
)
from src.short_analyst.llm_analysis.llm_models import (
    LLMAnalysisInput, LLMAnalysisOutput,
    MarketSentiment, TechnicalExplanation, RiskAssessment, TradingDecision,
    AnalysisType, SentimentPolarity, ConfidenceLevel, RiskTolerance, TimeHorizon,
    FusionSignal, SignalComponent
)

# 模拟信号识别系统中的类
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

class TestLLMAnalysisEngine:
    """LLM分析引擎测试"""

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'provider': 'mock',
            'model': 'gpt-4',
            'api_key': 'test_key',
            'max_tokens': 2000,
            'temperature': 0.3,
            'enable_cache': True,
            'cache_ttl': 300,
            'enable_context': True
        }

    @pytest.fixture
    def llm_engine(self, mock_config):
        """LLM分析引擎实例"""
        return LLMAnalysisEngine(mock_config)

    @pytest.fixture
    def sample_input_data(self):
        """示例输入数据"""
        # 创建模拟信号
        signal1 = MockFusionSignal(
            signal_type=MockShortSignalType.TREND_REVERSAL,
            signal_strength=MockShortSignalStrength.MODERATE,
            overall_confidence=0.75,
            risk_score=0.4
        )
        signal1.components = [MockSignalComponent("MA_CROSSOVER", 0.8)]

        signal2 = MockFusionSignal(
            signal_type=MockShortSignalType.RSI_OVERBOUGHT,
            signal_strength=MockShortSignalStrength.STRONG,
            overall_confidence=0.85,
            risk_score=0.3
        )
        signal2.components = [MockSignalComponent("RSI_OVERBOUGHT", 0.9)]

        return LLMAnalysisInput(
            symbol="BTC/USDT",
            current_price=45000.0,
            price_change_24h=-2.5,
            volume_24h=2500000000,
            market_cap=850000000000,
            fusion_signals=[signal1, signal2],
            news_headlines=[
                "Bitcoin面临监管压力",
                "机构投资者开始减持",
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

    @pytest.mark.asyncio
    async def test_engine_initialization(self, mock_config):
        """测试引擎初始化"""
        engine = LLMAnalysisEngine(mock_config)

        assert engine.provider == LLMProvider.MOCK
        assert engine.model == "gpt-4"
        assert engine.max_tokens == 2000
        assert engine.temperature == 0.3
        assert engine.enable_cache == True
        assert isinstance(engine.client, MockLLMClient)

    @pytest.mark.asyncio
    async def test_basic_analysis(self, llm_engine, sample_input_data):
        """测试基本分析功能"""
        result = await llm_engine.analyze(sample_input_data)

        assert isinstance(result, LLMAnalysisOutput)
        assert result.symbol == "BTC/USDT"
        assert result.overall_score >= 0 and result.overall_score <= 1
        assert result.confidence in ConfidenceLevel

    @pytest.mark.asyncio
    async def test_market_sentiment_analysis(self, llm_engine, sample_input_data):
        """测试市场情绪分析"""
        sample_input_data.analysis_types = [AnalysisType.MARKET_SENTIMENT]

        result = await llm_engine.analyze(sample_input_data)

        assert result.market_sentiment is not None
        assert result.market_sentiment.symbol == "BTC/USDT"
        assert result.market_sentiment.overall_sentiment in SentimentPolarity
        assert -2 <= result.market_sentiment.sentiment_score <= 2
        assert result.market_sentiment.confidence in ConfidenceLevel

    @pytest.mark.asyncio
    async def test_technical_explanation(self, llm_engine, sample_input_data):
        """测试技术指标解释"""
        sample_input_data.analysis_types = [AnalysisType.TECHNICAL_EXPLANATION]

        result = await llm_engine.analyze(sample_input_data)

        assert len(result.technical_explanations) > 0
        for explanation in result.technical_explanations:
            assert explanation.symbol == "BTC/USDT"
            assert explanation.interpretation != ""
            assert explanation.significance in ["high", "medium", "low"]
            assert explanation.outlook_confidence in ConfidenceLevel

    @pytest.mark.asyncio
    async def test_risk_assessment(self, llm_engine, sample_input_data):
        """测试风险评估"""
        sample_input_data.analysis_types = [AnalysisType.RISK_ASSESSMENT]

        result = await llm_engine.analyze(sample_input_data)

        assert result.risk_assessment is not None
        assert result.risk_assessment.symbol == "BTC/USDT"
        assert 0 <= result.risk_assessment.overall_risk_score <= 1
        assert result.risk_assessment.risk_level in ["low", "medium", "high", "extreme"]
        assert result.risk_assessment.confidence in ConfidenceLevel

    @pytest.mark.asyncio
    async def test_trading_decision(self, llm_engine, sample_input_data):
        """测试交易决策"""
        sample_input_data.analysis_types = [AnalysisType.TRADING_DECISION]

        result = await llm_engine.analyze(sample_input_data)

        assert result.trading_decision is not None
        assert result.trading_decision.symbol == "BTC/USDT"
        assert result.trading_decision.action in ["hold", "short", "cover", "reduce"]
        assert result.trading_decision.conviction_level in ConfidenceLevel
        assert result.trading_decision.urgency in ["low", "normal", "high"]

    @pytest.mark.asyncio
    async def test_comprehensive_analysis(self, llm_engine, sample_input_data):
        """测试综合分析"""
        result = await llm_engine.analyze(sample_input_data)

        # 验证所有分析组件
        assert result.market_sentiment is not None
        assert len(result.technical_explanations) > 0
        assert result.risk_assessment is not None
        assert result.trading_decision is not None

        # 验证综合评分
        assert 0 <= result.overall_score <= 1

        # 验证关键洞察
        assert len(result.key_insights) >= 0
        assert len(result.warning_signals) >= 0

    @pytest.mark.asyncio
    async def test_caching_mechanism(self, llm_engine, sample_input_data):
        """测试缓存机制"""
        # 第一次分析
        result1 = await llm_engine.analyze(sample_input_data)

        # 第二次分析（应该使用缓存）
        result2 = await llm_engine.analyze(sample_input_data)

        # 验证结果相同
        assert result1.input_id == result2.input_id
        assert result1.overall_score == result2.overall_score

        # 验证缓存统计
        stats = llm_engine.get_performance_stats()
        assert stats['cache_size'] > 0

    @pytest.mark.asyncio
    async def test_context_management(self, llm_engine, sample_input_data):
        """测试上下文管理"""
        # 执行分析
        result = await llm_engine.analyze(sample_input_data)

        # 验证上下文创建
        assert sample_input_data.symbol in llm_engine.contexts
        context = llm_engine.contexts[sample_input_data.symbol]

        # 验证上下文内容
        assert len(context.analysis_history) > 0
        assert context.symbol == sample_input_data.symbol
        assert context.last_updated is not None

    def test_performance_stats(self, llm_engine):
        """测试性能统计"""
        stats = llm_engine.get_performance_stats()

        assert 'total_analyses' in stats
        assert 'successful_analyses' in stats
        assert 'failed_analyses' in stats
        assert 'avg_processing_time' in stats
        assert 'success_rate' in stats
        assert 'cache_size' in stats
        assert 'provider' in stats
        assert 'model' in stats

    @pytest.mark.asyncio
    async def test_error_handling(self, llm_engine):
        """测试错误处理"""
        # 创建无效输入数据
        invalid_input = LLMAnalysisInput(symbol="")

        # 应该优雅地处理错误
        try:
            result = await llm_engine.analyze(invalid_input)
            # 即使有错误，也应该返回一个有效的结果对象
            assert isinstance(result, LLMAnalysisOutput)
        except Exception as e:
            # 如果抛出异常，应该是预期的异常
            assert isinstance(e, (ValueError, KeyError))

    @pytest.mark.asyncio
    async def test_prompt_template(self):
        """测试提示词模板"""
        template = PromptTemplate.get_template("market_sentiment")
        assert isinstance(template, str)
        assert "交易对" in template
        assert "当前价格" in template
        assert "分析要求" in template

    @pytest.mark.asyncio
    async def test_mock_llm_client(self):
        """测试模拟LLM客户端"""
        client = MockLLMClient()
        prompt = "测试市场情绪分析"

        response = await client.generate_response(prompt)

        assert isinstance(response, str)
        # 验证返回的是有效的JSON
        import json
        try:
            data = json.loads(response)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail("Mock LLM client should return valid JSON")

    def test_cache_operations(self, llm_engine):
        """测试缓存操作"""
        # 清除缓存
        llm_engine.clear_cache()
        assert len(llm_engine.analysis_cache) == 0

        # 清除上下文
        llm_engine.clear_contexts()
        assert len(llm_engine.contexts) == 0

    @pytest.mark.asyncio
    async def test_different_risk_tolerance(self, llm_engine, sample_input_data):
        """测试不同风险承受能力"""
        # 保守型
        sample_input_data.risk_tolerance = RiskTolerance.CONSERVATIVE
        result1 = await llm_engine.analyze(sample_input_data)

        # 激进型
        sample_input_data.risk_tolerance = RiskTolerance.AGGRESSIVE
        result2 = await llm_engine.analyze(sample_input_data)

        # 验证不同风险承受能力产生不同结果
        assert result1.trading_decision is not None
        assert result2.trading_decision is not None
        # 仓位大小应该不同
        assert result1.trading_decision.position_size != result2.trading_decision.position_size

    @pytest.mark.asyncio
    async def test_different_time_horizons(self, llm_engine, sample_input_data):
        """测试不同时间范围"""
        # 短期
        sample_input_data.time_horizon = TimeHorizon.INTRADAY
        result1 = await llm_engine.analyze(sample_input_data)

        # 长期
        sample_input_data.time_horizon = TimeHorizon.LONG_TERM
        result2 = await llm_engine.analyze(sample_input_data)

        # 验证不同时间范围产生不同结果
        assert result1.trading_decision is not None
        assert result2.trading_decision is not None
        # 预期持续时间应该不同
        assert result1.trading_decision.expected_duration != result2.trading_decision.expected_duration

    @pytest.mark.asyncio
    async def test_partial_analysis_types(self, llm_engine, sample_input_data):
        """测试部分分析类型"""
        # 只要求情绪分析
        sample_input_data.analysis_types = [AnalysisType.MARKET_SENTIMENT]
        result = await llm_engine.analyze(sample_input_data)

        assert result.market_sentiment is not None
        # 其他分析应该为空或默认值
        assert len(result.technical_explanations) == 0
        assert result.risk_assessment is None
        assert result.trading_decision is None

    @pytest.mark.asyncio
    async def test_empty_input_data(self, llm_engine):
        """测试空输入数据"""
        empty_input = LLMAnalysisInput(symbol="ETH/USDT")
        result = await llm_engine.analyze(empty_input)

        # 应该返回一个有效的结果，即使输入数据有限
        assert isinstance(result, LLMAnalysisOutput)
        assert result.symbol == "ETH/USDT"

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, llm_engine):
        """测试并发分析"""
        # 创建多个输入数据
        inputs = []
        for i in range(3):
            input_data = LLMAnalysisInput(
                symbol=f"SYMBOL{i}/USDT",
                current_price=45000 + i * 1000,
                analysis_types=[AnalysisType.MARKET_SENTIMENT]
            )
            inputs.append(input_data)

        # 并发执行分析
        tasks = [llm_engine.analyze(input_data) for input_data in inputs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有结果都有效
        assert len(results) == 3
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent analysis failed for symbol {i}: {result}")
            else:
                assert result.symbol == f"SYMBOL{i}/USDT"

    @pytest.mark.asyncio
    async def test_llm_provider_fallback(self):
        """测试LLM提供商回退机制"""
        # 测试OpenAI不可用时的回退
        config = {
            'provider': 'openai',
            'api_key': 'invalid_key',
            'enable_cache': False
        }

        engine = LLMAnalysisEngine(config)
        assert engine.provider == LLMProvider.MOCK
        assert isinstance(engine.client, MockLLMClient)