"""
Market impact assessment module for evaluating news impact on cryptocurrency markets
"""

import logging
import time
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from ..models.base import NewsArticle
from .llm_connector import LLMConnector, LLMMessage, LLMConfig, LLMResponse
from .sentiment_analyzer import SentimentAnalysisResult, SentimentCategory
from .entity_extractor import EntityExtractionResult, Entity, EntityType


class ImpactType(Enum):
    """影响类型枚举"""
    PRICE_VOLATILITY = "price_volatility"
    TRADING_VOLUME = "trading_volume"
    MARKET_SENTIMENT = "market_sentiment"
    REGULATORY_IMPACT = "regulatory_impact"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    SECURITY_TRUST = "security_trust"
    INSTITUTIONAL_ADOPTION = "institutional_adoption"
    RETAIL_ADOPTION = "retail_adoption"
    LIQUIDITY_IMPACT = "liquidity_impact"
    CORRELATION_IMPACT = "correlation_impact"


class ImpactTimeframe(Enum):
    """影响时间范围枚举"""
    IMMEDIATE = "immediate"  # 0-24 hours
    SHORT_TERM = "short_term"  # 1-7 days
    MEDIUM_TERM = "medium_term"  # 1-4 weeks
    LONG_TERM = "long_term"  # 1+ months


class ImpactMagnitude(Enum):
    """影响程度枚举"""
    NONE = "none"
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    EXTREME = "extreme"


@dataclass
class MarketImpactConfig:
    """市场影响评估配置"""
    enable_multi_factor_analysis: bool = True
    enable_correlation_analysis: bool = True
    enable_risk_assessment: bool = True
    enable_opportunity_identification: bool = True
    impact_types_to_analyze: List[ImpactType] = field(default_factory=lambda: [
        ImpactType.PRICE_VOLATILITY,
        ImpactType.TRADING_VOLUME,
        ImpactType.MARKET_SENTIMENT
    ])
    timeframes_to_analyze: List[ImpactTimeframe] = field(default_factory=lambda: [
        ImpactTimeframe.IMMEDIATE,
        ImpactTimeframe.SHORT_TERM
    ])
    min_confidence_threshold: float = 0.4
    include_probability_assessment: bool = True
    include_market_context: bool = True
    language: str = "en"
    output_format: str = "structured"


@dataclass
class ImpactScore:
    """影响分数"""
    impact_type: ImpactType
    timeframe: ImpactTimeframe
    magnitude: ImpactMagnitude
    confidence: float  # 0.0 to 1.0
    probability: float  # 0.0 to 1.0
    direction: str  # "positive", "negative", "neutral"
    reasoning: str
    key_factors: List[str] = None
    affected_assets: List[str] = None
    risk_level: str = None

    def __post_init__(self):
        if self.key_factors is None:
            self.key_factors = []
        if self.affected_assets is None:
            self.affected_assets = []


@dataclass
class MarketImpactResult:
    """市场影响评估结果"""
    overall_impact: ImpactScore
    impact_breakdown: Dict[ImpactType, List[ImpactScore]]
    market_sentiment: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    opportunity_analysis: Dict[str, Any]
    correlation_analysis: Dict[str, Any]
    processing_time: float
    metadata: Dict[str, Any]


@dataclass
class MarketImpactStats:
    """市场影响评估统计"""
    total_analyses: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    average_processing_time: float = 0.0
    average_confidence_score: float = 0.0
    impact_type_distribution: Dict[str, int] = field(default_factory=dict)
    magnitude_distribution: Dict[str, int] = field(default_factory=dict)
    high_impact_articles: int = 0


class MarketImpactAssessor:
    """市场影响评估器"""

    def __init__(self, llm_connector: LLMConnector, config: MarketImpactConfig):
        self.llm_connector = llm_connector
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats = MarketImpactStats()

        # 初始化分布统计
        for impact_type in ImpactType:
            self.stats.impact_type_distribution[impact_type.value] = 0
        for magnitude in ImpactMagnitude:
            self.stats.magnitude_distribution[magnitude.value] = 0

        # 影响因子权重
        self.impact_weights = {
            "sentiment_strength": 0.25,
            "entity_relevance": 0.20,
            "content_urgency": 0.15,
            "source_credibility": 0.15,
            "market_timing": 0.15,
            "novelty_factor": 0.10
        }

    def _create_system_prompt(self) -> str:
        """创建系统提示"""
        system_prompt = """You are an expert market impact analyst specializing in cryptocurrency news and its effects on financial markets.

Your task is to analyze news articles and assess their potential impact on cryptocurrency markets with high precision.

Impact Analysis Framework:

1. Impact Types to Analyze:

   Price Volatility Impact:
   - Short-term price movements and volatility
   - Potential for pumps or dumps
   - Support/resistance level effects
   - Market depth and liquidity effects

   Trading Volume Impact:
   - Expected volume changes
   - Buy/sell pressure indicators
   - Market participation effects
   - Liquidity changes

   Market Sentiment Impact:
   - Fear/greed index effects
   - Social media sentiment changes
   - Investor psychology effects
   - Market confidence shifts

   Regulatory Impact:
   - Compliance requirement changes
   - Legal status implications
   - Regulatory approval/rejection effects
   - Government policy impacts

   Technology Adoption Impact:
   - Network effect changes
   - User adoption rate changes
   - Technical upgrade impacts
   - Development milestone effects

   Security Trust Impact:
   - Hack/breach confidence effects
   - Security perception changes
   - Trust level impacts
   - Risk assessment changes

   Institutional Adoption Impact:
   - Institutional investment effects
   - Corporate adoption signals
   - Traditional finance integration effects
   - Market maturation indicators

   Retail Adoption Impact:
   - Mainstream acceptance effects
   - User accessibility impacts
   - Public perception changes
   - Mass adoption signals

   Liquidity Impact:
   - Market depth changes
   - Trading pair availability effects
   - Exchange listing impacts
   - Market maker participation

   Correlation Impact:
   - Cross-asset correlation changes
   - Market sector rotation effects
   - Risk-on/risk-off signals
   - Market decoupling indicators

2. Timeframe Analysis:
   - Immediate (0-24 hours): Short-term reactions
   - Short-term (1-7 days): Market adjustments
   - Medium-term (1-4 weeks): Trend developments
   - Long-term (1+ months): Fundamental changes

3. Impact Magnitude Assessment:
   - None: No discernible impact expected
   - Minimal: Very minor effects, barely noticeable
   - Low: Minor effects, may cause small fluctuations
   - Moderate: Noticeable effects, could cause trends
   - High: Significant effects, likely to cause major movements
   - Very High: Major effects, potential for dramatic changes
   - Extreme: Transformative effects, could redefine markets

4. Impact Direction:
   - Positive: Bullish, growth-oriented impacts
   - Negative: Bearish, risk-oriented impacts
   - Neutral: Balanced or mixed effects

5. Risk Assessment:
   - Identify potential downside risks
   - Assess volatility potential
   - Evaluate uncertainty factors
   - Consider worst-case scenarios

6. Opportunity Analysis:
   - Identify trading opportunities
   - Suggest investment strategies
   - Highlight arbitrage possibilities
   - Note long-term potential

Analysis Requirements:

1. Multi-factor Analysis:
   - Consider sentiment, entities, urgency, credibility, timing, novelty
   - Weight factors based on relevance to cryptocurrency markets
   - Account for market conditions and context

2. Probability Assessment:
   - Provide likelihood estimates for impact scenarios
   - Consider confidence levels in predictions
   - Include alternative scenarios

3. Market Context Integration:
   - Consider current market conditions
   - Account for recent market events
   - Factor in sector-specific dynamics

4. Risk-Opportunity Balance:
   - Present both risks and opportunities
   - Provide balanced assessment
   - Consider different investor perspectives

Output format: structured JSON

Respond with JSON containing:
- overall_impact: object with main impact assessment
- impact_breakdown: object with detailed impact by type and timeframe
- market_sentiment: object with sentiment analysis and effects
- risk_assessment: object with risk factors and mitigation
- opportunity_analysis: object with potential opportunities
- correlation_analysis: object with cross-market effects
- confidence_assessment: object with overall confidence and reasoning

Ensure your analysis is:
- Market-relevant and cryptocurrency-focused
- Evidence-based and well-reasoned
- Comprehensive in scope
- Practical and actionable
- Balanced in perspective"""

        return system_prompt

    def _create_user_prompt(self, article: NewsArticle,
                           sentiment_result: Optional[SentimentAnalysisResult] = None,
                           entity_result: Optional[EntityExtractionResult] = None) -> str:
        """创建用户提示"""
        prompt = f"""Please analyze the market impact of the following news article:

Title: {article.title}
Source: {article.source or 'Unknown'}
Published: {article.published_at or 'Unknown date'}
Category: {article.category.value if article.category else 'General'}
Author: {article.author or 'Unknown'}

Content:
{article.content}

"""

        if article.tags:
            prompt += f"Tags: {', '.join(article.tags)}\n"

        # 添加情感分析结果
        if sentiment_result:
            prompt += f"\nSentiment Analysis:\n"
            prompt += f"- Overall sentiment: {sentiment_result.overall_sentiment.category.value}\n"
            prompt += f"- Sentiment score: {sentiment_result.overall_sentiment.score:.2f}\n"
            prompt += f"- Confidence: {sentiment_result.overall_sentiment.confidence:.2f}\n"

        # 添加实体提取结果
        if entity_result:
            # 按类型分组实体
            entities_by_type = {}
            for entity in entity_result.entities:
                entity_type = entity.type.value
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append(entity.text)

            prompt += f"\nKey Entities:\n"
            for entity_type, entities in entities_by_type.items():
                if entities:
                    prompt += f"- {entity_type}: {', '.join(entities[:5])}\n"  # 限制显示数量

        # 添加配置说明
        impact_types = [impact_type.value for impact_type in self.config.impact_types_to_analyze]
        prompt += f"\nFocus on these impact types: {', '.join(impact_types)}\n"

        timeframes = [timeframe.value for timeframe in self.config.timeframes_to_analyze]
        prompt += f"Analyze these timeframes: {', '.join(timeframes)}\n"

        config_features = []
        if self.config.enable_multi_factor_analysis:
            config_features.append("multi-factor analysis")
        if self.config.enable_correlation_analysis:
            config_features.append("correlation analysis")
        if self.config.enable_risk_assessment:
            config_features.append("risk assessment")
        if self.config.enable_opportunity_identification:
            config_features.append("opportunity identification")

        if config_features:
            prompt += f"\nInclude: {', '.join(config_features)}\n"

        prompt += f"\nMinimum confidence threshold: {self.config.min_confidence_threshold}\n"

        prompt += "\nPlease provide comprehensive market impact analysis following the requirements specified."

        return prompt

    def _parse_impact_response(self, response: str) -> Dict[str, Any]:
        """解析市场影响响应"""
        try:
            # 尝试解析JSON
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            # 如果不是有效的JSON，执行基础分析
            self.logger.warning("Failed to parse JSON market impact response, using basic analysis")
            return self._basic_impact_analysis(response)

    def _basic_impact_analysis(self, content: str) -> Dict[str, Any]:
        """基础市场影响分析逻辑"""
        # 简单的关键词分析
        content_lower = content.lower()

        # 影响程度评估
        impact_indicators = {
            "extreme": ["breaking", "unprecedented", "historic", "transformative"],
            "very_high": ["major", "significant", "critical", "essential"],
            "high": ["important", "substantial", "meaningful", "notable"],
            "moderate": ["moderate", "reasonable", "considerable"],
            "low": ["minor", "small", "limited"],
            "minimal": ["minimal", "negligible", "insignificant"]
        }

        max_magnitude = "none"
        for magnitude, keywords in impact_indicators.items():
            if any(keyword in content_lower for keyword in keywords):
                max_magnitude = magnitude
                break

        # 方向分析
        if any(word in content_lower for word in ["positive", "bullish", "growth", "up", "increase"]):
            direction = "positive"
        elif any(word in content_lower for word in ["negative", "bearish", "decline", "down", "decrease"]):
            direction = "negative"
        else:
            direction = "neutral"

        return {
            "overall_impact": {
                "impact_type": "market_sentiment",
                "timeframe": "immediate",
                "magnitude": max_magnitude,
                "confidence": 0.5,
                "probability": 0.5,
                "direction": direction,
                "reasoning": "Basic keyword-based analysis",
                "key_factors": ["content keywords", "market relevance"]
            },
            "impact_breakdown": {},
            "market_sentiment": {"overall": direction, "confidence": 0.5},
            "risk_assessment": {"risk_level": "low", "factors": []},
            "opportunity_analysis": {"opportunities": [], "confidence": 0.3},
            "correlation_analysis": {"correlations": []}
        }

    def _create_impact_score(self, impact_data: Dict[str, Any], impact_type: ImpactType, timeframe: ImpactTimeframe) -> ImpactScore:
        """创建影响分数对象"""
        magnitude_map = {
            "none": ImpactMagnitude.NONE,
            "minimal": ImpactMagnitude.MINIMAL,
            "low": ImpactMagnitude.LOW,
            "moderate": ImpactMagnitude.MODERATE,
            "high": ImpactMagnitude.HIGH,
            "very_high": ImpactMagnitude.VERY_HIGH,
            "extreme": ImpactMagnitude.EXTREME
        }

        timeframe_map = {
            "immediate": ImpactTimeframe.IMMEDIATE,
            "short_term": ImpactTimeframe.SHORT_TERM,
            "medium_term": ImpactTimeframe.MEDIUM_TERM,
            "long_term": ImpactTimeframe.LONG_TERM
        }

        # 风险等级评估
        magnitude_value = impact_data.get("magnitude", "low")
        confidence = impact_data.get("confidence", 0.5)

        risk_level = "low"
        if magnitude_value in ["high", "very_high", "extreme"] and confidence > 0.7:
            risk_level = "high"
        elif magnitude_value in ["moderate", "high"] and confidence > 0.5:
            risk_level = "medium"

        return ImpactScore(
            impact_type=impact_type,
            timeframe=timeframe_map.get(impact_data.get("timeframe", "immediate"), ImpactTimeframe.IMMEDIATE),
            magnitude=magnitude_map.get(magnitude_value, ImpactMagnitude.LOW),
            confidence=impact_data.get("confidence", 0.5),
            probability=impact_data.get("probability", 0.5),
            direction=impact_data.get("direction", "neutral"),
            reasoning=impact_data.get("reasoning", ""),
            key_factors=impact_data.get("key_factors", []),
            affected_assets=impact_data.get("affected_assets", []),
            risk_level=risk_level
        )

    async def assess_market_impact(self, article: NewsArticle,
                                  sentiment_result: Optional[SentimentAnalysisResult] = None,
                                  entity_result: Optional[EntityExtractionResult] = None) -> MarketImpactResult:
        """评估市场影响"""
        start_time = time.time()
        self.stats.total_analyses += 1

        try:
            # 创建消息
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(article, sentiment_result, entity_result)

            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ]

            # 调用LLM
            response = await self.llm_connector.generate_response(messages)

            # 解析响应
            impact_data = self._parse_impact_response(response.content)

            # 创建整体影响分数
            overall_impact_data = impact_data.get("overall_impact", {})
            overall_impact = self._create_impact_score(
                overall_impact_data,
                ImpactType.MARKET_SENTIMENT,
                ImpactTimeframe.IMMEDIATE
            )

            # 创建影响细分
            impact_breakdown = {}
            for impact_type in self.config.impact_types_to_analyze:
                impact_breakdown[impact_type] = []
                for timeframe in self.config.timeframes_to_analyze:
                    # 尝试从响应中获取特定类型和时间框架的影响
                    impact_key = f"{impact_type.value}_{timeframe.value}"
                    if impact_key in impact_data.get("impact_breakdown", {}):
                        impact_score_data = impact_data["impact_breakdown"][impact_key]
                        impact_score = self._create_impact_score(impact_score_data, impact_type, timeframe)
                        impact_breakdown[impact_type].append(impact_score)

            # 检查是否为高影响文章
            is_high_impact = (overall_impact.magnitude in [ImpactMagnitude.HIGH, ImpactMagnitude.VERY_HIGH, ImpactMagnitude.EXTREME] and
                             overall_impact.confidence > 0.7)

            # 创建结果
            result = MarketImpactResult(
                overall_impact=overall_impact,
                impact_breakdown=impact_breakdown,
                market_sentiment=impact_data.get("market_sentiment", {}),
                risk_assessment=impact_data.get("risk_assessment", {}),
                opportunity_analysis=impact_data.get("opportunity_analysis", {}),
                correlation_analysis=impact_data.get("correlation_analysis", {}),
                processing_time=time.time() - start_time,
                metadata={
                    "llm_provider": response.provider.value,
                    "llm_model": response.model,
                    "response_time": response.response_time,
                    "tokens_used": response.usage.get("total_tokens", 0),
                    "cached": response.cached,
                    "analysis_confidence": impact_data.get("confidence_assessment", {}).get("overall_confidence", 0.5)
                }
            )

            # 更新统计
            self.stats.successful_analyses += 1
            if is_high_impact:
                self.stats.high_impact_articles += 1
            self._update_stats(result)

            self.logger.info(f"Successfully assessed market impact for article {article.id}: {overall_impact.magnitude.value} impact")
            return result

        except Exception as e:
            self.stats.failed_analyses += 1
            self.logger.error(f"Failed to assess market impact for article {article.id}: {str(e)}")

            # 返回默认结果
            default_impact = ImpactScore(
                impact_type=ImpactType.MARKET_SENTIMENT,
                timeframe=ImpactTimeframe.IMMEDIATE,
                magnitude=ImpactMagnitude.NONE,
                confidence=0.0,
                probability=0.0,
                direction="neutral",
                reasoning=f"Analysis failed: {str(e)}"
            )

            return MarketImpactResult(
                overall_impact=default_impact,
                impact_breakdown={},
                market_sentiment={},
                risk_assessment={},
                opportunity_analysis={},
                correlation_analysis={},
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )

    async def assess_batch_market_impact(self, articles: List[NewsArticle],
                                       sentiment_results: Optional[List[SentimentAnalysisResult]] = None,
                                       entity_results: Optional[List[EntityExtractionResult]] = None) -> List[MarketImpactResult]:
        """批量市场影响评估"""
        self.logger.info(f"Starting batch market impact assessment of {len(articles)} articles")

        tasks = []
        for i, article in enumerate(articles):
            sentiment_result = sentiment_results[i] if sentiment_results and i < len(sentiment_results) else None
            entity_result = entity_results[i] if entity_results and i < len(entity_results) else None

            task = self.assess_market_impact(article, sentiment_result, entity_result)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        impact_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch market impact assessment failed for article {articles[i].id}: {str(result)}")
                default_impact = ImpactScore(
                    impact_type=ImpactType.MARKET_SENTIMENT,
                    timeframe=ImpactTimeframe.IMMEDIATE,
                    magnitude=ImpactMagnitude.NONE,
                    confidence=0.0,
                    probability=0.0,
                    direction="neutral",
                    reasoning=f"Batch processing failed: {str(result)}"
                )

                impact_results.append(MarketImpactResult(
                    overall_impact=default_impact,
                    impact_breakdown={},
                    market_sentiment={},
                    risk_assessment={},
                    opportunity_analysis={},
                    correlation_analysis={},
                    processing_time=0.0,
                    metadata={"error": str(result), "batch_failed": True}
                ))
            else:
                impact_results.append(result)

        self.logger.info(f"Batch market impact assessment completed: {len(impact_results)} articles processed")
        return impact_results

    def _update_stats(self, result: MarketImpactResult):
        """更新统计信息"""
        # 更新平均处理时间
        total_time = self.stats.average_processing_time * (self.stats.successful_analyses - 1)
        total_time += result.processing_time
        self.stats.average_processing_time = total_time / self.stats.successful_analyses

        # 更新平均置信度
        total_confidence = self.stats.average_confidence_score * (self.stats.successful_analyses - 1)
        total_confidence += result.overall_impact.confidence
        self.stats.average_confidence_score = total_confidence / self.stats.successful_analyses

        # 更新影响类型分布
        for impact_type, impact_scores in result.impact_breakdown.items():
            self.stats.impact_type_distribution[impact_type.value] += len(impact_scores)

        # 更新程度分布
        self.stats.magnitude_distribution[result.overall_impact.magnitude.value] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = self.stats.successful_analyses / max(1, self.stats.total_analyses)
        high_impact_rate = self.stats.high_impact_articles / max(1, self.stats.successful_analyses)
        return {
            "total_analyses": self.stats.total_analyses,
            "successful_analyses": self.stats.successful_analyses,
            "failed_analyses": self.stats.failed_analyses,
            "success_rate": success_rate,
            "average_processing_time": self.stats.average_processing_time,
            "average_confidence_score": self.stats.average_confidence_score,
            "high_impact_articles": self.stats.high_impact_articles,
            "high_impact_rate": high_impact_rate,
            "impact_type_distribution": self.stats.impact_type_distribution,
            "magnitude_distribution": self.stats.magnitude_distribution,
            "config": {
                "enable_multi_factor_analysis": self.config.enable_multi_factor_analysis,
                "enable_correlation_analysis": self.config.enable_correlation_analysis,
                "enable_risk_assessment": self.config.enable_risk_assessment,
                "enable_opportunity_identification": self.config.enable_opportunity_identification,
                "impact_types_to_analyze": [t.value for t in self.config.impact_types_to_analyze],
                "timeframes_to_analyze": [t.value for t in self.config.timeframes_to_analyze]
            }
        }

    def update_config(self, config: MarketImpactConfig):
        """更新配置"""
        self.config = config
        self.logger.info("Market impact assessor configuration updated")

    def get_market_impact_summary(self, results: List[MarketImpactResult]) -> Dict[str, Any]:
        """获取市场影响摘要"""
        if not results:
            return {"error": "No results to analyze"}

        # 统计影响分布
        magnitude_counts = {}
        direction_counts = {}
        impact_type_counts = {}
        high_confidence_results = 0

        for result in results:
            # 程度分布
            magnitude = result.overall_impact.magnitude.value
            magnitude_counts[magnitude] = magnitude_counts.get(magnitude, 0) + 1

            # 方向分布
            direction = result.overall_impact.direction
            direction_counts[direction] = direction_counts.get(direction, 0) + 1

            # 影响类型分布
            for impact_type, impact_scores in result.impact_breakdown.items():
                impact_type_counts[impact_type.value] = impact_type_counts.get(impact_type.value, 0) + len(impact_scores)

            # 高置信度结果
            if result.overall_impact.confidence > 0.7:
                high_confidence_results += 1

        # 计算平均指标
        avg_confidence = sum(result.overall_impact.confidence for result in results) / len(results)
        avg_probability = sum(result.overall_impact.probability for result in results) / len(results)

        # 识别主要影响类型
        dominant_impact_type = max(impact_type_counts.items(), key=lambda x: x[1]) if impact_type_counts else ("unknown", 0)
        dominant_magnitude = max(magnitude_counts.items(), key=lambda x: x[1]) if magnitude_counts else ("unknown", 0)

        return {
            "total_articles": len(results),
            "average_confidence": avg_confidence,
            "average_probability": avg_probability,
            "high_confidence_articles": high_confidence_results,
            "magnitude_distribution": magnitude_counts,
            "direction_distribution": direction_counts,
            "impact_type_distribution": impact_type_counts,
            "dominant_impact_type": dominant_impact_type[0],
            "dominant_magnitude": dominant_magnitude[0],
            "high_impact_ratio": sum(1 for r in results if r.overall_impact.magnitude.value in ["high", "very_high", "extreme"]) / len(results)
        }

    def filter_by_impact_level(self, results: List[MarketImpactResult], min_magnitude: ImpactMagnitude) -> List[MarketImpactResult]:
        """按影响程度过滤结果"""
        return [result for result in results if result.overall_impact.magnitude.value >= min_magnitude.value]

    def filter_by_confidence(self, results: List[MarketImpactResult], min_confidence: float) -> List[MarketImpactResult]:
        """按置信度过滤结果"""
        return [result for result in results if result.overall_impact.confidence >= min_confidence]

    def get_risk_alerts(self, results: List[MarketImpactResult]) -> List[Dict[str, Any]]:
        """获取风险警报"""
        alerts = []

        for result in results:
            # 检查高风险条件
            if (result.overall_impact.magnitude in [ImpactMagnitude.HIGH, ImpactMagnitude.VERY_HIGH, ImpactMagnitude.EXTREME] and
                result.overall_impact.confidence > 0.6):

                alert = {
                    "article_id": result.metadata.get("article_id", "unknown"),
                    "impact_level": result.overall_impact.magnitude.value,
                    "confidence": result.overall_impact.confidence,
                    "direction": result.overall_impact.direction,
                    "timeframe": result.overall_impact.timeframe.value,
                    "risk_factors": result.risk_assessment.get("factors", []),
                    "recommendation": self._generate_risk_recommendation(result)
                }
                alerts.append(alert)

        return sorted(alerts, key=lambda x: x["confidence"], reverse=True)

    def _generate_risk_recommendation(self, result: MarketImpactResult) -> str:
        """生成风险建议"""
        if result.overall_impact.direction == "negative":
            return "Consider defensive positions or reduced exposure"
        elif result.overall_impact.direction == "positive":
            return "Monitor for potential opportunities, exercise caution"
        else:
            return "Monitor market conditions closely"

    def validate_article(self, article: NewsArticle) -> bool:
        """验证文章是否适合市场影响分析"""
        if not article.content or len(article.content.strip()) < 100:
            self.logger.warning(f"Article {article.id} has insufficient content for market impact analysis")
            return False

        return True