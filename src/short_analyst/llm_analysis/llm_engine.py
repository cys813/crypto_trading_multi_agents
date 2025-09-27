"""
LLM分析与推理引擎核心模块

该模块实现了基于大语言模型的智能分析系统，包括：
1. 市场情绪分析
2. 技术指标解释
3. 风险评估推理
4. 交易决策建议
5. 上下文管理和学习适应
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict
from abc import ABC, abstractmethod
from enum import Enum
import re
import hashlib

from .llm_models import (
    LLMAnalysisInput, LLMAnalysisOutput, LLMAnalysisContext,
    MarketSentiment, TechnicalExplanation, RiskAssessment, TradingDecision,
    AnalysisType, SentimentPolarity, ConfidenceLevel, RiskTolerance, TimeHorizon,
    FusionSignal
)

# 尝试导入LLM库，如果不可用则使用模拟版本
try:
    import openai
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: OpenAI library not available, using mock LLM")

from ..signal_recognition.intelligent_signal_recognition import IntelligentSignalRecognition


class LLMProvider(Enum):
    """LLM提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"


class AnalysisQuality(Enum):
    """分析质量等级"""
    POOR = 1
    FAIR = 2
    GOOD = 3
    EXCELLENT = 4


class PromptTemplate:
    """提示词模板管理"""

    TEMPLATES = {
        "market_sentiment": """
你是一位资深的市场分析师，专门分析加密货币市场的情绪和趋势。

基于以下信息进行市场情绪分析：

**交易对**: {symbol}
**当前价格**: ${current_price:.2f}
**24小时变化**: {price_change_24h:+.2f}%
**成交量**: ${volume_24h:,.0f}
**市场条件**: {market_conditions}
**趋势背景**: {trend_context}

**技术信号**:
{technical_signals}

**新闻标题**:
{news_headlines}

**社交媒体情绪**: {social_sentiment}
**恐惧贪婪指数**: {fear_greed_index}

**分析要求**:
1. 评估整体市场情绪（极度看跌/看跌/中性/看涨/极度看涨）
2. 识别关键情绪驱动因素
3. 分析情绪变化趋势
4. 识别可能的反向信号
5. 评估极端市场条件

**输出格式**:
请以JSON格式返回，包含以下字段：
- overall_sentiment: 情绪极性 (-2到2)
- sentiment_score: 详细情绪分数
- key_factors: 关键影响因素列表
- contrarian_signals: 反向信号列表
- extreme_conditions: 极端条件列表
- sentiment_trend: 情绪趋势
- momentum: 情绪动量
- confidence: 置信度等级 (1-5)
""",

        "technical_explanation": """
你是一位技术分析专家，擅长解释各种技术指标的含义和交易意义。

**交易对**: {symbol}
**指标名称**: {indicator_name}
**指标值**: {indicator_value}
**当前价格**: ${current_price:.2f}

**市场背景**:
{market_context}

**相关指标**:
{related_indicators}

**分析要求**:
1. 解释该指标的当前含义
2. 分析其对做空交易的暗示
3. 识别关键支撑/阻力位
4. 评估信号强度和可靠性
5. 提供短期和中期展望

**输出格式**:
JSON格式，包含：
- interpretation: 指标解释
- significance: 重要性程度 (high/medium/low)
- bearish_implications: 做空暗示列表
- support_levels: 支撑位列表
- resistance_levels: 阻力位列表
- short_term_outlook: 短期展望
- medium_term_outlook: 中期展望
- outlook_confidence: 展望置信度 (1-5)
""",

        "risk_assessment": """
你是一位风险管理专家，专门评估加密货币做空交易的风险。

**交易对**: {symbol}
**当前价格**: ${current_price:.2f}
**目标仓位**: {position_size:.1%}

**市场数据**:
- 24小时波动率: {volatility:.2%}
- 成交量: ${volume_24h:,.0f}
- 市值: ${market_cap:,.0f}

**技术信号风险**:
{technical_risks}

**市场情绪风险**:
{sentiment_risks}

**分析要求**:
1. 评估整体风险水平 (0-1)
2. 分析各维度风险
3. 识别特殊风险因素
4. 提供风险控制建议
5. 设定关键风险指标

**输出格式**:
JSON格式，包含：
- overall_risk_score: 整体风险分数
- risk_level: 风险等级
- market_risk: 市场风险分数
- liquidity_risk: 流动性风险分数
- short_squeeze_risk: 轧空风险分数
- position_size_limit: 建议仓位限制
- stop_loss_distance: 止损距离建议
- key_risk_indicators: 关键风险指标列表
- confidence: 分析置信度 (1-5)
""",

        "trading_decision": """
你是一位资深的交易策略师，基于综合分析制定做空交易决策。

**交易对**: {symbol}
**当前价格**: ${current_price:.2f}
**风险承受能力**: {risk_tolerance}
**时间范围**: {time_horizon}

**信号汇总**:
{signal_summary}

**风险评估**:
{risk_assessment}

**市场情绪**:
{market_sentiment}

**技术分析**:
{technical_analysis}

**决策要求**:
1. 给出明确的交易建议 (hold/short/cover/reduce)
2. 设定具体的交易参数
3. 评估决策的信心水平
4. 提供备选方案
5. 制定应急计划

**输出格式**:
JSON格式，包含：
- action: 交易动作
- conviction_level: 信心等级 (1-5)
- urgency: 紧急程度
- recommended_entry: 建议入场价
- stop_loss: 止损价
- take_profit: 止盈价列表
- position_size: 建议仓位比例
- risk_reward_ratio: 风险收益比
- win_probability: 胜率估计
- primary_reasons: 主要原因列表
- confidence_score: 置信度分数
"""
    }

    @classmethod
    def get_template(cls, template_name: str) -> str:
        """获取提示词模板"""
        return cls.TEMPLATES.get(template_name, "")


class MockLLMClient:
    """模拟LLM客户端，用于测试和开发"""

    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成模拟LLM响应"""
        await asyncio.sleep(0.1)  # 模拟网络延迟

        # 简单的关键词匹配来生成模拟响应
        if "市场情绪" in prompt or "sentiment" in prompt:
            return json.dumps({
                "overall_sentiment": -1,
                "sentiment_score": -0.7,
                "key_factors": ["技术指标显示超买", "成交量放大", "市场情绪转淡"],
                "contrarian_signals": ["恐慌情绪可能过度", "技术支撑位附近"],
                "extreme_conditions": ["RSI超买", "成交量异常"],
                "sentiment_trend": "falling",
                "momentum": -0.5,
                "confidence": 4
            })

        elif "技术指标" in prompt or "technical" in prompt:
            return json.dumps({
                "interpretation": "RSI指标显示超买状态，表明可能存在回调压力",
                "significance": "high",
                "bearish_implications": ["短期回调可能", "做空机会"],
                "support_levels": [42000, 41000],
                "resistance_levels": [44000, 45000],
                "short_term_outlook": "看跌",
                "medium_term_outlook": "中性",
                "outlook_confidence": 4
            })

        elif "风险" in prompt or "risk" in prompt:
            return json.dumps({
                "overall_risk_score": 0.6,
                "risk_level": "medium",
                "market_risk": 0.5,
                "liquidity_risk": 0.3,
                "short_squeeze_risk": 0.4,
                "position_size_limit": 0.05,
                "stop_loss_distance": 0.03,
                "key_risk_indicators": ["高波动率", "流动性风险", "轧空风险"],
                "confidence": 4
            })

        elif "交易决策" in prompt or "trading" in prompt:
            return json.dumps({
                "action": "short",
                "conviction_level": 4,
                "urgency": "normal",
                "recommended_entry": 43800,
                "stop_loss": 45200,
                "take_profit": [41000, 39000],
                "position_size": 0.03,
                "risk_reward_ratio": 2.5,
                "win_probability": 0.65,
                "primary_reasons": ["技术指标超买", "市场情绪转淡", "风险可控"],
                "confidence_score": 0.75
            })

        else:
            return json.dumps({"error": "Unknown analysis type"})


class LLMAnalysisEngine:
    """LLM分析与推理引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # LLM配置
        self.provider = LLMProvider(config.get('provider', 'mock'))
        self.model = config.get('model', 'gpt-4')
        self.api_key = config.get('api_key', '')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.3)

        # 初始化LLM客户端
        self._initialize_llm_client()

        # 分析配置
        self.enable_cache = config.get('enable_cache', True)
        self.cache_ttl = config.get('cache_ttl', 300)  # 5分钟
        self.enable_context = config.get('enable_context', True)

        # 性能统计
        self.stats = {
            'total_analyses': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'avg_processing_time': 0.0,
            'total_tokens': 0,
            'total_cost': 0.0
        }

        # 缓存
        self.analysis_cache: Dict[str, Tuple[LLMAnalysisOutput, datetime]] = {}

        # 上下文管理
        self.contexts: Dict[str, LLMAnalysisContext] = {}

    def _initialize_llm_client(self):
        """初始化LLM客户端"""
        if self.provider == LLMProvider.OPENAI and LLM_AVAILABLE:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
            except Exception as e:
                self.logger.warning(f"OpenAI初始化失败，使用模拟客户端: {e}")
                self.client = MockLLMClient()
                self.provider = LLMProvider.MOCK
        else:
            self.client = MockLLMClient()

    async def analyze(self, input_data: LLMAnalysisInput) -> LLMAnalysisOutput:
        """执行LLM分析"""
        start_time = time.time()
        self.stats['total_analyses'] += 1

        try:
            # 检查缓存
            cache_key = self._generate_cache_key(input_data)
            if self.enable_cache and cache_key in self.analysis_cache:
                cached_result, cache_time = self.analysis_cache[cache_key]
                if (datetime.now() - cache_time).total_seconds() < self.cache_ttl:
                    self.logger.info(f"使用缓存分析结果: {cache_key}")
                    return cached_result

            # 获取分析上下文
            context = self._get_analysis_context(input_data.symbol)

            # 执行分析
            result = await self._perform_analysis(input_data, context)

            # 更新上下文
            if self.enable_context:
                self._update_context(context, result)

            # 更新缓存
            if self.enable_cache:
                self.analysis_cache[cache_key] = (result, datetime.now())

            # 更新统计
            processing_time = time.time() - start_time
            self._update_stats(result, processing_time)

            self.logger.info(f"LLM分析完成: {input_data.symbol}, "
                           f"处理时间: {processing_time:.2f}s, "
                           f"置信度: {result.confidence.name}")

            return result

        except Exception as e:
            self.stats['failed_analyses'] += 1
            self.logger.error(f"LLM分析失败: {e}")
            raise

    async def _perform_analysis(self, input_data: LLMAnalysisInput,
                              context: LLMAnalysisContext) -> LLMAnalysisOutput:
        """执行具体的分析任务"""
        result = LLMAnalysisOutput(
            input_id=input_data.input_id,
            symbol=input_data.symbol,
            analysis_time=datetime.now()
        )

        # 准备分析任务
        tasks = []
        for analysis_type in input_data.analysis_types:
            if analysis_type == AnalysisType.MARKET_SENTIMENT:
                tasks.append(self._analyze_market_sentiment(input_data))
            elif analysis_type == AnalysisType.TECHNICAL_EXPLANATION:
                tasks.append(self._analyze_technical_indicators(input_data))
            elif analysis_type == AnalysisType.RISK_ASSESSMENT:
                tasks.append(self._assess_risks(input_data))
            elif analysis_type == AnalysisType.TRADING_DECISION:
                tasks.append(self._generate_trading_decision(input_data))

        # 并行执行分析任务
        if tasks:
            analysis_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理分析结果
            for analysis_result in analysis_results:
                if isinstance(analysis_result, Exception):
                    self.logger.warning(f"分析任务失败: {analysis_result}")
                    continue

                if isinstance(analysis_result, MarketSentiment):
                    result.market_sentiment = analysis_result
                elif isinstance(analysis_result, list):
                    result.technical_explanations.extend(analysis_result)
                elif isinstance(analysis_result, RiskAssessment):
                    result.risk_assessment = analysis_result
                elif isinstance(analysis_result, TradingDecision):
                    result.trading_decision = analysis_result

        # 生成综合分析
        await self._generate_comprehensive_analysis(result, input_data, context)

        return result

    async def _analyze_market_sentiment(self, input_data: LLMAnalysisInput) -> MarketSentiment:
        """分析市场情绪"""
        prompt = PromptTemplate.get_template("market_sentiment")

        # 格式化技术信号
        technical_signals = []
        for signal in input_data.fusion_signals:
            technical_signals.append(f"- {signal.signal_type.value}: "
                                   f"强度={signal.signal_strength.value}, "
                                   f"置信度={signal.overall_confidence:.2f}")

        # 格式化新闻
        news_headlines = "\\n".join(f"- {headline}" for headline in input_data.news_headlines)

        # 填充模板
        formatted_prompt = prompt.format(
            symbol=input_data.symbol,
            current_price=input_data.current_price,
            price_change_24h=input_data.price_change_24h,
            volume_24h=input_data.volume_24h,
            market_conditions=input_data.market_conditions,
            trend_context=input_data.trend_context,
            technical_signals="\\n".join(technical_signals),
            news_headlines=news_headlines,
            social_sentiment=input_data.social_media_sentiment.value if input_data.social_media_sentiment else "未知",
            fear_greed_index=input_data.fear_greed_index or "未知"
        )

        # 调用LLM
        response = await self.client.generate_response(
            formatted_prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        # 解析响应
        try:
            response_data = json.loads(response)
            sentiment = MarketSentiment(
                symbol=input_data.symbol,
                overall_sentiment=SentimentPolarity(int(response_data.get('overall_sentiment', 0))),
                sentiment_score=float(response_data.get('sentiment_score', 0)),
                confidence=ConfidenceLevel(int(response_data.get('confidence', 3))),
                key_factors=response_data.get('key_factors', []),
                contrarian_signals=response_data.get('contrarian_signals', []),
                extreme_conditions=response_data.get('extreme_conditions', []),
                sentiment_trend=response_data.get('sentiment_trend', 'stable'),
                momentum=float(response_data.get('momentum', 0))
            )

            if input_data.fear_greed_index:
                sentiment.fear_greed_index = input_data.fear_greed_index
            if input_data.social_media_sentiment:
                sentiment.social_sentiment = input_data.social_media_sentiment

            return sentiment

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"情绪分析响应解析失败: {e}")
            return MarketSentiment(
                symbol=input_data.symbol,
                overall_sentiment=SentimentPolarity.NEUTRAL,
                sentiment_score=0.0,
                confidence=ConfidenceLevel.LOW
            )

    async def _analyze_technical_indicators(self, input_data: LLMAnalysisInput) -> List[TechnicalExplanation]:
        """分析技术指标"""
        explanations = []

        # 为每个技术信号生成解释
        for signal in input_data.fusion_signals:
            prompt = PromptTemplate.get_template("technical_explanation")

            # 格式化相关指标
            related_indicators = []
            for component in signal.components:
                related_indicators.append(f"- {component.indicator_name}: "
                                        f"置信度={component.confidence:.2f}")

            # 填充模板
            formatted_prompt = prompt.format(
                symbol=input_data.symbol,
                indicator_name=signal.signal_type.value,
                indicator_value=signal.signal_strength.value,
                current_price=input_data.current_price,
                market_context=input_data.market_conditions,
                related_indicators="\\n".join(related_indicators)
            )

            # 调用LLM
            response = await self.client.generate_response(
                formatted_prompt,
                max_tokens=self.max_tokens // 2,
                temperature=self.temperature
            )

            # 解析响应
            try:
                response_data = json.loads(response)
                explanation = TechnicalExplanation(
                    symbol=input_data.symbol,
                    indicator_name=signal.signal_type.value,
                    indicator_value=signal.signal_strength.value,
                    interpretation=response_data.get('interpretation', ''),
                    significance=response_data.get('significance', 'medium'),
                    bearish_implications=response_data.get('bearish_implications', []),
                    support_levels=response_data.get('support_levels', []),
                    resistance_levels=response_data.get('resistance_levels', []),
                    short_term_outlook=response_data.get('short_term_outlook', ''),
                    medium_term_outlook=response_data.get('medium_term_outlook', ''),
                    outlook_confidence=ConfidenceLevel(int(response_data.get('outlook_confidence', 3)))
                )
                explanations.append(explanation)

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self.logger.error(f"技术分析响应解析失败: {e}")

        return explanations

    async def _assess_risks(self, input_data: LLMAnalysisInput) -> RiskAssessment:
        """评估风险"""
        prompt = PromptTemplate.get_template("risk_assessment")

        # 格式化技术风险
        technical_risks = []
        for signal in input_data.fusion_signals:
            risk_score = signal.risk_score
            risk_level = "高" if risk_score > 0.7 else "中" if risk_score > 0.4 else "低"
            technical_risks.append(f"- {signal.signal_type.value}: 风险等级{risk_level} ({risk_score:.2f})")

        # 格式化情绪风险
        sentiment_risks = []
        if input_data.social_media_sentiment:
            sentiment_risks.append(f"社交媒体情绪: {input_data.social_media_sentiment.value}")
        if input_data.fear_greed_index:
            fg_level = "极度贪婪" if input_data.fear_greed_index > 75 else "极度恐惧" if input_data.fear_greed_index < 25 else "中性"
            sentiment_risks.append(f"恐惧贪婪指数: {fg_level} ({input_data.fear_greed_index})")

        # 填充模板
        formatted_prompt = prompt.format(
            symbol=input_data.symbol,
            current_price=input_data.current_price,
            position_size=input_data.position_size * 100,
            volatility=abs(input_data.price_change_24h),
            volume_24h=input_data.volume_24h,
            market_cap=input_data.market_cap or 0,
            technical_risks="\\n".join(technical_risks),
            sentiment_risks="\\n".join(sentiment_risks)
        )

        # 调用LLM
        response = await self.client.generate_response(
            formatted_prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        # 解析响应
        try:
            response_data = json.loads(response)
            risk_assessment = RiskAssessment(
                symbol=input_data.symbol,
                overall_risk_score=float(response_data.get('overall_risk_score', 0.5)),
                risk_level=response_data.get('risk_level', 'medium'),
                market_risk=float(response_data.get('market_risk', 0.5)),
                liquidity_risk=float(response_data.get('liquidity_risk', 0.3)),
                short_squeeze_risk=float(response_data.get('short_squeeze_risk', 0.4)),
                position_size_limit=float(response_data.get('position_size_limit', 0.05)),
                stop_loss_distance=float(response_data.get('stop_loss_distance', 0.03)),
                key_risk_indicators=response_data.get('key_risk_indicators', []),
                confidence=ConfidenceLevel(int(response_data.get('confidence', 3)))
            )

            return risk_assessment

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"风险评估响应解析失败: {e}")
            return RiskAssessment(
                symbol=input_data.symbol,
                overall_risk_score=0.5,
                risk_level="medium",
                confidence=ConfidenceLevel.LOW
            )

    async def _generate_trading_decision(self, input_data: LLMAnalysisInput) -> TradingDecision:
        """生成交易决策"""
        prompt = PromptTemplate.get_template("trading_decision")

        # 格式化信号汇总
        signal_summary = []
        for signal in input_data.fusion_signals:
            signal_summary.append(f"- {signal.signal_type.value}: "
                                f"强度={signal.signal_strength.value}, "
                                f"置信度={signal.overall_confidence:.2f}")

        # 填充模板
        formatted_prompt = prompt.format(
            symbol=input_data.symbol,
            current_price=input_data.current_price,
            risk_tolerance=input_data.risk_tolerance.name,
            time_horizon=input_data.time_horizon.value,
            signal_summary="\\n".join(signal_summary),
            risk_assessment="基于技术指标的风险评估",
            market_sentiment="基于新闻和社交媒体的情绪分析",
            technical_analysis="基于技术指标的综合分析"
        )

        # 调用LLM
        response = await self.client.generate_response(
            formatted_prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        # 解析响应
        try:
            response_data = json.loads(response)
            decision = TradingDecision(
                symbol=input_data.symbol,
                action=response_data.get('action', 'hold'),
                conviction_level=ConfidenceLevel(int(response_data.get('conviction_level', 3))),
                urgency=response_data.get('urgency', 'normal'),
                recommended_entry=response_data.get('recommended_entry'),
                stop_loss=response_data.get('stop_loss'),
                take_profit=response_data.get('take_profit', []),
                position_size=float(response_data.get('position_size', 0.02)),
                risk_reward_ratio=float(response_data.get('risk_reward_ratio', 2.0)),
                win_probability=float(response_data.get('win_probability', 0.5)),
                primary_reasons=response_data.get('primary_reasons', []),
                confidence_score=float(response_data.get('confidence_score', 0.5))
            )

            return decision

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"交易决策响应解析失败: {e}")
            return TradingDecision(
                symbol=input_data.symbol,
                action="hold",
                conviction_level=ConfidenceLevel.LOW,
                confidence_score=0.3
            )

    async def _generate_comprehensive_analysis(self, result: LLMAnalysisOutput,
                                            input_data: LLMAnalysisInput,
                                            context: LLMAnalysisContext):
        """生成综合分析"""
        # 计算整体评分
        scores = []
        if result.market_sentiment:
            sentiment_score = abs(result.market_sentiment.sentiment_score) / 2.0
            scores.append(sentiment_score)

        if result.technical_explanations:
            tech_scores = [exp.outlook_confidence.value / 5.0 for exp in result.technical_explanations]
            scores.extend(tech_scores)

        if result.risk_assessment:
            risk_score = 1.0 - result.risk_assessment.overall_risk_score  # 风险越低分数越高
            scores.append(risk_score)

        if result.trading_decision:
            decision_score = result.trading_decision.confidence_score
            scores.append(decision_score)

        result.overall_score = sum(scores) / len(scores) if scores else 0.5

        # 设置置信度
        confidences = []
        if result.market_sentiment:
            confidences.append(result.market_sentiment.confidence.value)
        if result.risk_assessment:
            confidences.append(result.risk_assessment.confidence.value)
        if result.trading_decision:
            confidences.append(result.trading_decision.conviction_level.value)

        result.confidence = ConfidenceLevel(int(sum(confidences) / len(confidences))) if confidences else ConfidenceLevel.MEDIUM

        # 生成关键洞察
        result.key_insights = self._generate_key_insights(result)
        result.warning_signals = self._generate_warning_signals(result)

    def _generate_key_insights(self, result: LLMAnalysisOutput) -> List[str]:
        """生成关键洞察"""
        insights = []

        if result.market_sentiment:
            if result.market_sentiment.sentiment_score < -1.5:
                insights.append("市场情绪极度悲观，可能存在反向机会")
            elif result.market_sentiment.sentiment_score > 1.5:
                insights.append("市场情绪极度乐观，需警惕回调风险")

        if result.risk_assessment:
            if result.risk_assessment.overall_risk_score > 0.7:
                insights.append("整体风险较高，建议谨慎操作")
            elif result.risk_assessment.overall_risk_score < 0.3:
                insights.append("风险可控，可考虑适度参与")

        if result.trading_decision:
            if result.trading_decision.action == "short":
                insights.append("技术分析支持做空策略")
            elif result.trading_decision.conviction_level.value >= 4:
                insights.append("决策信心较高，可考虑执行")

        return insights[:5]  # 限制洞察数量

    def _generate_warning_signals(self, result: LLMAnalysisOutput) -> List[str]:
        """生成警告信号"""
        warnings = []

        if result.risk_assessment:
            if result.risk_assessment.short_squeeze_risk > 0.6:
                warnings.append("轧空风险较高，需警惕空头回补")
            if result.risk_assessment.liquidity_risk > 0.7:
                warnings.append("流动性风险较高，可能影响平仓")

        if result.market_sentiment:
            if result.market_sentiment.momentum < -0.8:
                warnings.append("情绪动量过强，可能存在超调风险")

        return warnings[:3]  # 限制警告数量

    def _generate_cache_key(self, input_data: LLMAnalysisInput) -> str:
        """生成缓存键"""
        # 基于关键数据生成哈希键
        key_data = {
            'symbol': input_data.symbol,
            'timestamp': input_data.timestamp.isoformat(),
            'price': input_data.current_price,
            'signals': [(s.signal_type.value, s.signal_strength.value) for s in input_data.fusion_signals],
            'analysis_types': [t.value for t in input_data.analysis_types]
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_analysis_context(self, symbol: str) -> LLMAnalysisContext:
        """获取分析上下文"""
        if symbol not in self.contexts:
            self.contexts[symbol] = LLMAnalysisContext(symbol=symbol)
        return self.contexts[symbol]

    def _update_context(self, context: LLMAnalysisContext, result: LLMAnalysisOutput):
        """更新分析上下文"""
        context.analysis_history.append(result)
        if result.trading_decision:
            context.decision_history.append(result.trading_decision)

        context.last_updated = datetime.now()
        context.context_size = len(context.analysis_history)

    def _update_stats(self, result: LLMAnalysisOutput, processing_time: float):
        """更新性能统计"""
        self.stats['successful_analyses'] += 1

        # 更新平均处理时间
        total_time = self.stats['avg_processing_time'] * (self.stats['successful_analyses'] - 1) + processing_time
        self.stats['avg_processing_time'] = total_time / self.stats['successful_analyses']

        # 更新token统计（如果有）
        if hasattr(result, 'token_count'):
            self.stats['total_tokens'] += result.token_count

        # 更新成本统计（如果有）
        if hasattr(result, 'cost_estimate'):
            self.stats['total_cost'] += result.cost_estimate

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        success_rate = (self.stats['successful_analyses'] /
                       self.stats['total_analyses']) if self.stats['total_analyses'] > 0 else 0

        return {
            **self.stats,
            'success_rate': success_rate,
            'cache_size': len(self.analysis_cache),
            'active_contexts': len(self.contexts),
            'provider': self.provider.value,
            'model': self.model
        }

    def clear_cache(self):
        """清除分析缓存"""
        self.analysis_cache.clear()
        self.logger.info("LLM分析缓存已清除")

    def clear_contexts(self):
        """清除分析上下文"""
        self.contexts.clear()
        self.logger.info("LLM分析上下文已清除")