"""
Sentiment analysis engine for news articles using LLM
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


class SentimentCategory(Enum):
    """情感分类枚举"""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class SentimentAspect(Enum):
    """情感分析维度枚举"""
    OVERALL = "overall"
    MARKET_SENTIMENT = "market_sentiment"
    REGULATORY_SENTIMENT = "regulatory_sentiment"
    TECHNOLOGY_SENTIMENT = "technology_sentiment"
    ADOPTION_SENTIMENT = "adoption_sentiment"
    SECURITY_SENTIMENT = "security_sentiment"


@dataclass
class SentimentConfig:
    """情感分析配置"""
    enable_aspect_analysis: bool = True
    enable_intensity_scoring: bool = True
    enable_emotion_detection: bool = True
    enable_confidence_scoring: bool = True
    enable_context_analysis: bool = True
    aspects_to_analyze: List[SentimentAspect] = field(default_factory=lambda: [
        SentimentAspect.OVERALL,
        SentimentAspect.MARKET_SENTIMENT
    ])
    language: str = "en"
    output_format: str = "structured"  # structured, detailed, simple
    include_explanation: bool = True
    include_key_phrases: bool = True
    max_key_phrases: int = 10


@dataclass
class SentimentScore:
    """情感分数"""
    category: SentimentCategory
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    explanation: str
    intensity: float  # 0.0 to 1.0
    key_phrases: List[str] = None
    emotions: Dict[str, float] = None
    aspects: Dict[str, Any] = None

    def __post_init__(self):
        if self.key_phrases is None:
            self.key_phrases = []
        if self.emotions is None:
            self.emotions = {}
        if self.aspects is None:
            self.aspects = {}


@dataclass
class SentimentAnalysisResult:
    """情感分析结果"""
    overall_sentiment: SentimentScore
    aspect_sentiments: Dict[SentimentAspect, SentimentScore]
    market_impact_indicators: Dict[str, float]
    temporal_indicators: Dict[str, Any]
    reliability_score: float
    processing_time: float
    metadata: Dict[str, Any]


@dataclass
class SentimentStats:
    """情感分析统计"""
    total_analyses: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    average_processing_time: float = 0.0
    average_confidence: float = 0.0
    sentiment_distribution: Dict[str, int] = field(default_factory=dict)
    aspect_analysis_count: Dict[str, int] = field(default_factory=dict)


class SentimentAnalyzer:
    """情感分析器"""

    def __init__(self, llm_connector: LLMConnector, config: SentimentConfig):
        self.llm_connector = llm_connector
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats = SentimentStats()

        # 初始化情感分布
        for category in SentimentCategory:
            self.stats.sentiment_distribution[category.value] = 0

        # 初始化维度分析计数
        for aspect in SentimentAspect:
            self.stats.aspect_analysis_count[aspect.value] = 0

    def _create_system_prompt(self) -> str:
        """创建系统提示"""
        system_prompt = """You are an expert sentiment analyst specializing in cryptocurrency and financial news analysis.

Your task is to analyze the sentiment of news articles with high accuracy and provide detailed insights.

Analysis Requirements:

1. Overall Sentiment Analysis:
   - Analyze the general emotional tone and sentiment
   - Consider the balance of positive and negative elements
   - Identify the primary sentiment category

2. Aspect-Based Sentiment Analysis:
   - Market sentiment: Focus on market trends, price movements, trading activity
   - Regulatory sentiment: Focus on regulatory changes, compliance, legal aspects
   - Technology sentiment: Focus on technological developments, innovations
   - Adoption sentiment: Focus on adoption rates, partnerships, mainstream acceptance
   - Security sentiment: Focus on security issues, hacks, vulnerabilities

3. Sentiment Intensity:
   - Rate the strength of the sentiment (0.0 = weak, 1.0 = very strong)
   - Consider the language intensity and emotional weight

4. Confidence Assessment:
   - Rate your confidence in the analysis (0.0 = low confidence, 1.0 = high confidence)
   - Consider article clarity, bias, and available information

5. Key Phrases:
   - Extract phrases that indicate sentiment
   - Include both positive and negative indicators

6. Emotional Analysis:
   - Identify specific emotions (fear, excitement, uncertainty, optimism, etc.)
   - Rate the intensity of each emotion

Scoring System:
- Sentiment Score: -1.0 (very negative) to 1.0 (very positive)
- Confidence Score: 0.0 (low) to 1.0 (high)
- Intensity Score: 0.0 (weak) to 1.0 (strong)

Market Impact Indicators:
- Volatility potential: 0.0 (low) to 1.0 (high)
- Market reaction: -1.0 (negative) to 1.0 (positive)
- Time horizon impact: immediate, short-term, medium-term, long-term
"""

        if self.config.enable_context_analysis:
            system_prompt += """

7. Context Analysis:
   - Consider the broader market context
   - Account for recent market events
   - Consider source credibility and potential bias
"""

        system_prompt += f"""

Output format: {'structured JSON' if self.config.output_format == 'structured' else 'detailed text'}

If using structured format, respond with JSON containing:
- overall_sentiment: object with category, score, confidence, explanation, intensity
- aspect_sentiments: object with detailed aspect analysis
- market_impact_indicators: object with volatility, reaction, time_horizon
- key_phrases: array of sentiment-indicating phrases
- emotions: object mapping emotion types to intensity scores
- reliability_score: float (0-1)
- analysis_confidence: float (0-1)

Ensure your analysis is:
- Objective and evidence-based
- Contextually aware of cryptocurrency markets
- Sensitive to market-moving sentiment
- Comprehensive in aspect coverage"""

        return system_prompt

    def _create_user_prompt(self, article: NewsArticle) -> str:
        """创建用户提示"""
        prompt = f"""Please analyze the sentiment of the following news article:

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

        if article.metadata:
            # 添加相关元数据
            relevant_metadata = {k: v for k, v in article.metadata.items() if k in ['market_data', 'price_data', 'volume_data']}
            if relevant_metadata:
                prompt += f"Market Context: {json.dumps(relevant_metadata, indent=2)}\n"

        aspects_to_analyze = [aspect.value for aspect in self.config.aspects_to_analyze]
        prompt += f"""

Please focus your analysis on these aspects: {', '.join(aspects_to_analyze)}

Provide a comprehensive sentiment analysis following the requirements specified."""

        return prompt

    def _parse_sentiment_response(self, response: str) -> Dict[str, Any]:
        """解析情感分析响应"""
        try:
            # 尝试解析JSON
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            # 如果不是有效的JSON，尝试从文本中提取
            self.logger.warning("Failed to parse JSON sentiment response, extracting from text")
            return self._extract_sentiment_from_text(response)

    def _extract_sentiment_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中提取情感信息"""
        lines = text.strip().split('\n')
        result = {
            "overall_sentiment": {
                "category": "neutral",
                "score": 0.0,
                "confidence": 0.5,
                "explanation": "Unable to parse structured response",
                "intensity": 0.5
            },
            "aspect_sentiments": {},
            "market_impact_indicators": {
                "volatility": 0.5,
                "reaction": 0.0,
                "time_horizon": "short-term"
            },
            "key_phrases": [],
            "emotions": {},
            "reliability_score": 0.5,
            "analysis_confidence": 0.5
        }

        current_section = "overall"
        current_aspect = None

        for line in lines:
            line = line.strip().lower()

            if not line:
                continue

            # 检测标题
            if 'overall' in line or 'general' in line:
                current_section = "overall"
            elif 'market' in line:
                current_section = "market_sentiment"
                current_aspect = SentimentAspect.MARKET_SENTIMENT
            elif 'regulatory' in line:
                current_section = "regulatory_sentiment"
                current_aspect = SentimentAspect.REGULATORY_SENTIMENT
            elif 'technology' in line or 'tech' in line:
                current_section = "technology_sentiment"
                current_aspect = SentimentAspect.TECHNOLOGY_SENTIMENT
            elif 'adoption' in line:
                current_section = "adoption_sentiment"
                current_aspect = SentimentAspect.ADOPTION_SENTIMENT
            elif 'security' in line:
                current_section = "security_sentiment"
                current_aspect = SentimentAspect.SECURITY_SENTIMENT

            # 简单的关键词匹配
            if 'positive' in line or 'optimistic' in line or 'bullish' in line:
                score = 0.7
                category = "positive"
            elif 'negative' in line or 'pessimistic' in line or 'bearish' in line:
                score = -0.7
                category = "negative"
            else:
                score = 0.0
                category = "neutral"

            if current_section == "overall":
                result["overall_sentiment"]["score"] = score
                result["overall_sentiment"]["category"] = category
                result["overall_sentiment"]["explanation"] = line
            elif current_aspect:
                result["aspect_sentiments"][current_aspect.value] = {
                    "category": category,
                    "score": score,
                    "confidence": 0.6,
                    "explanation": line,
                    "intensity": 0.6
                }

        return result

    def _create_sentiment_score(self, sentiment_data: Dict[str, Any]) -> SentimentScore:
        """创建情感分数对象"""
        category_map = {
            "very_negative": SentimentCategory.VERY_NEGATIVE,
            "negative": SentimentCategory.NEGATIVE,
            "neutral": SentimentCategory.NEUTRAL,
            "positive": SentimentCategory.POSITIVE,
            "very_positive": SentimentCategory.VERY_POSITIVE
        }

        return SentimentScore(
            category=category_map.get(sentiment_data.get("category", "neutral"), SentimentCategory.NEUTRAL),
            score=sentiment_data.get("score", 0.0),
            confidence=sentiment_data.get("confidence", 0.5),
            explanation=sentiment_data.get("explanation", ""),
            intensity=sentiment_data.get("intensity", 0.5),
            key_phrases=sentiment_data.get("key_phrases", []),
            emotions=sentiment_data.get("emotions", {}),
            aspects=sentiment_data.get("aspects", {})
        )

    async def analyze_sentiment(self, article: NewsArticle) -> SentimentAnalysisResult:
        """分析文章情感"""
        start_time = time.time()
        self.stats.total_analyses += 1

        try:
            # 创建消息
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(article)

            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ]

            # 调用LLM
            response = await self.llm_connector.generate_response(messages)

            # 解析响应
            sentiment_data = self._parse_sentiment_response(response.content)

            # 创建整体情感分数
            overall_sentiment = self._create_sentiment_score(sentiment_data.get("overall_sentiment", {}))

            # 创建维度情感分数
            aspect_sentiments = {}
            aspect_data = sentiment_data.get("aspect_sentiments", {})

            for aspect in self.config.aspects_to_analyze:
                if aspect.value in aspect_data:
                    aspect_sentiments[aspect] = self._create_sentiment_score(aspect_data[aspect.value])
                else:
                    # 如果没有特定维度分析，使用整体情感
                    aspect_sentiments[aspect] = overall_sentiment

            # 创建结果
            result = SentimentAnalysisResult(
                overall_sentiment=overall_sentiment,
                aspect_sentiments=aspect_sentiments,
                market_impact_indicators=sentiment_data.get("market_impact_indicators", {}),
                temporal_indicators=self._analyze_temporal_indicators(article, sentiment_data),
                reliability_score=sentiment_data.get("reliability_score", 0.5),
                processing_time=time.time() - start_time,
                metadata={
                    "llm_provider": response.provider.value,
                    "llm_model": response.model,
                    "response_time": response.response_time,
                    "tokens_used": response.usage.get("total_tokens", 0),
                    "cached": response.cached,
                    "analysis_confidence": sentiment_data.get("analysis_confidence", 0.5)
                }
            )

            # 更新统计
            self.stats.successful_analyses += 1
            self._update_stats(result)

            self.logger.info(f"Successfully analyzed sentiment for article {article.id}: {overall_sentiment.category.value} ({overall_sentiment.score:.2f})")
            return result

        except Exception as e:
            self.stats.failed_analyses += 1
            self.logger.error(f"Failed to analyze sentiment for article {article.id}: {str(e)}")

            # 返回默认结果
            default_sentiment = SentimentScore(
                category=SentimentCategory.NEUTRAL,
                score=0.0,
                confidence=0.0,
                explanation=f"Analysis failed: {str(e)}",
                intensity=0.0,
                key_phrases=[],
                emotions={},
                aspects={}
            )

            return SentimentAnalysisResult(
                overall_sentiment=default_sentiment,
                aspect_sentiments={},
                market_impact_indicators={},
                temporal_indicators={},
                reliability_score=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )

    def _analyze_temporal_indicators(self, article: NewsArticle, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析时间指标"""
        temporal_indicators = {
            "time_horizon": sentiment_data.get("market_impact_indicators", {}).get("time_horizon", "unknown"),
            "urgency": 0.5,  # 0.0 = low urgency, 1.0 = high urgency
            "duration": "unknown",  # short-term, medium-term, long-term
            "seasonal_relevance": False
        }

        # 基于文章内容分析时间指标
        content_lower = article.content.lower()

        # 检测紧急程度
        urgent_keywords = ["urgent", "immediate", "breaking", "critical", "alert", "emergency"]
        urgent_count = sum(1 for keyword in urgent_keywords if keyword in content_lower)
        temporal_indicators["urgency"] = min(1.0, urgent_count / 3.0)

        # 检测时间范围
        if any(word in content_lower for word in ["long-term", "sustained", "permanent", "fundamental"]):
            temporal_indicators["duration"] = "long-term"
        elif any(word in content_lower for word in ["short-term", "temporary", "immediate", "quick"]):
            temporal_indicators["duration"] = "short-term"
        else:
            temporal_indicators["duration"] = "medium-term"

        return temporal_indicators

    async def analyze_batch_sentiment(self, articles: List[NewsArticle]) -> List[SentimentAnalysisResult]:
        """批量情感分析"""
        self.logger.info(f"Starting batch sentiment analysis of {len(articles)} articles")

        tasks = []
        for article in articles:
            task = self.analyze_sentiment(article)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        sentiment_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch sentiment analysis failed for article {articles[i].id}: {str(result)}")
                # 创建失败结果
                default_sentiment = SentimentScore(
                    category=SentimentCategory.NEUTRAL,
                    score=0.0,
                    confidence=0.0,
                    explanation=f"Batch processing failed: {str(result)}",
                    intensity=0.0,
                    key_phrases=[],
                    emotions={},
                    aspects={}
                )

                sentiment_results.append(SentimentAnalysisResult(
                    overall_sentiment=default_sentiment,
                    aspect_sentiments={},
                    market_impact_indicators={},
                    temporal_indicators={},
                    reliability_score=0.0,
                    processing_time=0.0,
                    metadata={"error": str(result), "batch_failed": True}
                ))
            else:
                sentiment_results.append(result)

        self.logger.info(f"Batch sentiment analysis completed: {len(sentiment_results)} articles processed")
        return sentiment_results

    def _update_stats(self, result: SentimentAnalysisResult):
        """更新统计信息"""
        # 更新情感分布
        self.stats.sentiment_distribution[result.overall_sentiment.category.value] += 1

        # 更新维度分析计数
        for aspect in result.aspect_sentiments:
            self.stats.aspect_analysis_count[aspect.value] += 1

        # 更新平均处理时间
        total_time = self.stats.average_processing_time * (self.stats.successful_analyses - 1)
        total_time += result.processing_time
        self.stats.average_processing_time = total_time / self.stats.successful_analyses

        # 更新平均置信度
        total_confidence = self.stats.average_confidence * (self.stats.successful_analyses - 1)
        total_confidence += result.overall_sentiment.confidence
        self.stats.average_confidence = total_confidence / self.stats.successful_analyses

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = self.stats.successful_analyses / max(1, self.stats.total_analyses)
        return {
            "total_analyses": self.stats.total_analyses,
            "successful_analyses": self.stats.successful_analyses,
            "failed_analyses": self.stats.failed_analyses,
            "success_rate": success_rate,
            "average_processing_time": self.stats.average_processing_time,
            "average_confidence": self.stats.average_confidence,
            "sentiment_distribution": self.stats.sentiment_distribution,
            "aspect_analysis_count": self.stats.aspect_analysis_count,
            "config": {
                "enable_aspect_analysis": self.config.enable_aspect_analysis,
                "enable_intensity_scoring": self.config.enable_intensity_scoring,
                "enable_emotion_detection": self.config.enable_emotion_detection,
                "aspects_to_analyze": [aspect.value for aspect in self.config.aspects_to_analyze]
            }
        }

    def update_config(self, config: SentimentConfig):
        """更新配置"""
        self.config = config
        self.logger.info("Sentiment analyzer configuration updated")

    def get_market_sentiment_summary(self, results: List[SentimentAnalysisResult]) -> Dict[str, Any]:
        """获取市场情感摘要"""
        if not results:
            return {"error": "No results to analyze"}

        # 计算整体情感分布
        sentiment_counts = {}
        for result in results:
            category = result.overall_sentiment.category.value
            sentiment_counts[category] = sentiment_counts.get(category, 0) + 1

        # 计算平均分数
        avg_score = sum(result.overall_sentiment.score for result in results) / len(results)
        avg_confidence = sum(result.overall_sentiment.confidence for result in results) / len(results)

        # 计算市场影响指标
        market_impact = {
            "avg_volatility": sum(result.market_impact_indicators.get("volatility", 0.5) for result in results) / len(results),
            "avg_reaction": sum(result.market_impact_indicators.get("reaction", 0.0) for result in results) / len(results),
        }

        # 分析主要情感
        dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1]) if sentiment_counts else ("neutral", 0)

        return {
            "total_articles": len(results),
            "sentiment_distribution": sentiment_counts,
            "dominant_sentiment": dominant_sentiment[0],
            "dominant_sentiment_count": dominant_sentiment[1],
            "average_sentiment_score": avg_score,
            "average_confidence": avg_confidence,
            "market_impact_indicators": market_impact,
            "reliability_score": sum(result.reliability_score for result in results) / len(results)
        }

    def validate_article(self, article: NewsArticle) -> bool:
        """验证文章是否适合情感分析"""
        if not article.content or len(article.content.strip()) < 50:
            self.logger.warning(f"Article {article.id} has insufficient content for sentiment analysis")
            return False

        if not article.title or len(article.title.strip()) < 10:
            self.logger.warning(f"Article {article.id} has insufficient title for sentiment analysis")
            return False

        return True