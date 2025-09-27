"""
News summarization module using LLM
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

from ..models.base import NewsArticle
from .llm_connector import LLMConnector, LLMMessage, LLMConfig, LLMResponse


class SummaryLength(Enum):
    """摘要长度枚举"""
    VERY_SHORT = "very_short"  # 1-2 sentences
    SHORT = "short"  # 3-5 sentences
    MEDIUM = "medium"  # 1 paragraph
    LONG = "long"  # 2-3 paragraphs
    COMPREHENSIVE = "comprehensive"  # Full summary


class SummaryFocus(Enum):
    """摘要焦点枚举"""
    GENERAL = "general"  # General summary
    MARKET_IMPACT = "market_impact"  # Focus on market implications
    TECHNICAL = "technical"  # Focus on technical details
    REGULATORY = "regulatory"  # Focus on regulatory aspects
    SECURITY = "security"  # Focus on security concerns
    ADOPTION = "adoption"  # Focus on adoption news


@dataclass
class SummaryConfig:
    """摘要配置"""
    length: SummaryLength = SummaryLength.MEDIUM
    focus: SummaryFocus = SummaryFocus.GENERAL
    include_key_points: bool = True
    include_entities: bool = True
    include_sentiment: bool = True
    max_bullet_points: int = 5
    language: str = "en"
    style: str = "professional"  # professional, casual, technical
    output_format: str = "structured"  # structured, plain_text, markdown


@dataclass
class SummaryResult:
    """摘要结果"""
    summary: str
    key_points: List[str]
    entities: List[Dict[str, Any]]
    sentiment: Dict[str, Any]
    confidence: float
    processing_time: float
    word_count: Dict[str, int]  # original, summary
    metadata: Dict[str, Any]


@dataclass
class SummaryStats:
    """摘要统计"""
    total_articles: int = 0
    successful_summaries: int = 0
    failed_summaries: int = 0
    average_processing_time: float = 0.0
    average_confidence: float = 0.0
    word_count_ratio: float = 0.0  # summary_word_count / original_word_count


class NewsSummarizer:
    """新闻摘要生成器"""

    def __init__(self, llm_connector: LLMConnector, config: SummaryConfig):
        self.llm_connector = llm_connector
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats = SummaryStats()

        # 预编译正则表达式
        self.word_count_pattern = re.compile(r'\b\w+\b')

    def _create_system_prompt(self) -> str:
        """创建系统提示"""
        focus_instructions = {
            SummaryFocus.GENERAL: "Provide a comprehensive overview covering all important aspects.",
            SummaryFocus.MARKET_IMPACT: "Focus on market implications, price movements, and trading effects.",
            SummaryFocus.TECHNICAL: "Focus on technical details, technology changes, and development aspects.",
            SummaryFocus.REGULATORY: "Focus on regulatory changes, compliance, and legal aspects.",
            SummaryFocus.SECURITY: "Focus on security vulnerabilities, hacks, and safety concerns.",
            SummaryFocus.ADOPTION: "Focus on adoption rates, partnerships, and mainstream acceptance."
        }

        length_instructions = {
            SummaryLength.VERY_SHORT: "Create a very brief summary (1-2 sentences).",
            SummaryLength.SHORT: "Create a short summary (3-5 sentences).",
            SummaryLength.MEDIUM: "Create a medium-length summary (1 paragraph).",
            SummaryLength.LONG: "Create a longer summary (2-3 paragraphs).",
            SummaryLength.COMPREHENSIVE: "Create a comprehensive summary covering all major points."
        }

        system_prompt = f"""You are an expert news summarizer specializing in cryptocurrency and financial news.

Your task is to analyze news articles and create concise, accurate summaries.

Requirements:
1. {length_instructions[self.config.length]}
2. Focus: {focus_instructions[self.config.focus]}
3. Style: {self.config.style}
4. Language: {self.config.language}

Important guidelines:
- Extract the most important information
- Maintain objectivity and accuracy
- Include key numbers, dates, and facts
- Avoid speculation unless clearly stated
- Preserve the original meaning and tone
- Identify and highlight market-relevant information
"""

        if self.config.include_key_points:
            system_prompt += f"\n- Extract up to {self.config.max_bullet_points} key bullet points"

        if self.config.include_entities:
            system_prompt += "\n- Identify and categorize important entities (companies, people, cryptocurrencies)"

        if self.config.include_sentiment:
            system_prompt += "\n- Analyze the sentiment of the article"

        system_prompt += f"""

Output format: {'structured JSON' if self.config.output_format == 'structured' else 'plain text'}

If using structured format, respond with JSON containing:
- summary: string
- key_points: array of strings
- entities: array of objects with type, name, and relevance
- sentiment: object with overall_sentiment, confidence, and explanation
- confidence: float (0-1)

Ensure your summary captures the essence of the news while being concise and informative."""

        return system_prompt

    def _create_user_prompt(self, article: NewsArticle) -> str:
        """创建用户提示"""
        prompt = f"""Please summarize the following news article:

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
            prompt += f"Additional context: {json.dumps(article.metadata, indent=2)}\n"

        prompt += "\nPlease provide a comprehensive summary following the requirements specified."

        return prompt

    def _extract_word_count(self, text: str) -> int:
        """提取单词数量"""
        return len(self.word_count_pattern.findall(text))

    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """解析结构化响应"""
        try:
            # 尝试解析JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果不是有效的JSON，尝试提取结构化信息
            self.logger.warning("Failed to parse JSON response, falling back to text extraction")
            return self._extract_structured_from_text(response)

    def _extract_structured_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中提取结构化信息"""
        lines = text.strip().split('\n')
        result = {
            "summary": "",
            "key_points": [],
            "entities": [],
            "sentiment": {"overall_sentiment": "neutral", "confidence": 0.5, "explanation": "Unknown"},
            "confidence": 0.5
        }

        current_section = "summary"
        key_points_count = 0

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # 检测标题
            if line.lower().startswith(('summary:', 'summarization:', '概要:')):
                current_section = "summary"
                continue
            elif line.lower().startswith(('key points:', '要点:', 'bullet points:')):
                current_section = "key_points"
                continue
            elif line.lower().startswith(('entities:', '实体:', 'organizations:')):
                current_section = "entities"
                continue
            elif line.lower().startswith(('sentiment:', '情感:', '情绪:')):
                current_section = "sentiment"
                continue

            # 处理内容
            if current_section == "summary":
                if result["summary"]:
                    result["summary"] += " "
                result["summary"] += line
            elif current_section == "key_points" and key_points_count < self.config.max_bullet_points:
                if line.startswith(('-', '•', '*', '•')):
                    result["key_points"].append(line[1:].strip())
                    key_points_count += 1
            elif current_section == "entities":
                # 简单的实体提取
                if ':' in line:
                    entity_type, entity_name = line.split(':', 1)
                    result["entities"].append({
                        "type": entity_type.strip(),
                        "name": entity_name.strip(),
                        "relevance": 0.8
                    })
            elif current_section == "sentiment":
                # 简单的情感提取
                if 'positive' in line.lower():
                    result["sentiment"]["overall_sentiment"] = "positive"
                elif 'negative' in line.lower():
                    result["sentiment"]["overall_sentiment"] = "negative"

        # 如果摘要为空，使用第一段
        if not result["summary"]:
            result["summary"] = text.split('\n\n')[0] if text else "No summary available"

        return result

    async def summarize_article(self, article: NewsArticle) -> SummaryResult:
        """摘要单篇文章"""
        start_time = time.time()
        self.stats.total_articles += 1

        try:
            # 计算原始单词数量
            original_word_count = self._extract_word_count(article.content)

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
            if self.config.output_format == "structured":
                structured_data = self._parse_structured_response(response.content)
            else:
                structured_data = {
                    "summary": response.content,
                    "key_points": [],
                    "entities": [],
                    "sentiment": {"overall_sentiment": "neutral", "confidence": 0.5, "explanation": "Not analyzed"},
                    "confidence": 0.7
                }

            # 计算摘要单词数量
            summary_word_count = self._extract_word_count(structured_data["summary"])

            # 创建结果
            result = SummaryResult(
                summary=structured_data["summary"],
                key_points=structured_data.get("key_points", []),
                entities=structured_data.get("entities", []),
                sentiment=structured_data.get("sentiment", {"overall_sentiment": "neutral", "confidence": 0.5, "explanation": "Not analyzed"}),
                confidence=structured_data.get("confidence", 0.7),
                processing_time=time.time() - start_time,
                word_count={
                    "original": original_word_count,
                    "summary": summary_word_count
                },
                metadata={
                    "llm_provider": response.provider.value,
                    "llm_model": response.model,
                    "response_time": response.response_time,
                    "tokens_used": response.usage.get("total_tokens", 0),
                    "cached": response.cached
                }
            )

            # 更新统计
            self.stats.successful_summaries += 1
            self._update_stats(result)

            self.logger.info(f"Successfully summarized article {article.id}: {original_word_count} -> {summary_word_count} words")
            return result

        except Exception as e:
            self.stats.failed_summaries += 1
            self.logger.error(f"Failed to summarize article {article.id}: {str(e)}")

            # 返回默认结果
            return SummaryResult(
                summary=f"Failed to generate summary: {str(e)}",
                key_points=[],
                entities=[],
                sentiment={"overall_sentiment": "neutral", "confidence": 0.0, "explanation": "Error occurred"},
                confidence=0.0,
                processing_time=time.time() - start_time,
                word_count={"original": self._extract_word_count(article.content), "summary": 0},
                metadata={"error": str(e)}
            )

    async def summarize_batch(self, articles: List[NewsArticle]) -> List[SummaryResult]:
        """批量摘要文章"""
        self.logger.info(f"Starting batch summarization of {len(articles)} articles")

        tasks = []
        for article in articles:
            task = self.summarize_article(article)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        summary_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch summarization failed for article {articles[i].id}: {str(result)}")
                # 创建失败结果
                summary_results.append(SummaryResult(
                    summary=f"Batch processing failed: {str(result)}",
                    key_points=[],
                    entities=[],
                    sentiment={"overall_sentiment": "neutral", "confidence": 0.0, "explanation": "Error occurred"},
                    confidence=0.0,
                    processing_time=0.0,
                    word_count={"original": self._extract_word_count(articles[i].content), "summary": 0},
                    metadata={"error": str(result), "batch_failed": True}
                ))
            else:
                summary_results.append(result)

        self.logger.info(f"Batch summarization completed: {len(summary_results)} articles processed")
        return summary_results

    def _update_stats(self, result: SummaryResult):
        """更新统计信息"""
        # 更新平均处理时间
        total_time = self.stats.average_processing_time * (self.stats.successful_summaries - 1)
        total_time += result.processing_time
        self.stats.average_processing_time = total_time / self.stats.successful_summaries

        # 更新平均置信度
        total_confidence = self.stats.average_confidence * (self.stats.successful_summaries - 1)
        total_confidence += result.confidence
        self.stats.average_confidence = total_confidence / self.stats.successful_summaries

        # 更新单词计数比率
        if result.word_count["original"] > 0:
            word_ratio = result.word_count["summary"] / result.word_count["original"]
            total_ratio = self.stats.word_count_ratio * (self.stats.successful_summaries - 1)
            total_ratio += word_ratio
            self.stats.word_count_ratio = total_ratio / self.stats.successful_summaries

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = self.stats.successful_summaries / max(1, self.stats.total_articles)
        return {
            "total_articles": self.stats.total_articles,
            "successful_summaries": self.stats.successful_summaries,
            "failed_summaries": self.stats.failed_summaries,
            "success_rate": success_rate,
            "average_processing_time": self.stats.average_processing_time,
            "average_confidence": self.stats.average_confidence,
            "word_count_ratio": self.stats.word_count_ratio,
            "config": {
                "length": self.config.length.value,
                "focus": self.config.focus.value,
                "include_key_points": self.config.include_key_points,
                "include_entities": self.config.include_entities,
                "include_sentiment": self.config.include_sentiment
            }
        }

    def update_config(self, config: SummaryConfig):
        """更新配置"""
        self.config = config
        self.logger.info("Summarizer configuration updated")

    def validate_article(self, article: NewsArticle) -> bool:
        """验证文章是否适合摘要"""
        if not article.content or len(article.content.strip()) < 50:
            self.logger.warning(f"Article {article.id} has insufficient content for summarization")
            return False

        if not article.title or len(article.title.strip()) < 10:
            self.logger.warning(f"Article {article.id} has insufficient title for summarization")
            return False

        return True

    def get_quality_metrics(self, result: SummaryResult) -> Dict[str, Any]:
        """获取质量指标"""
        quality_metrics = {
            "confidence_score": result.confidence,
            "processing_time": result.processing_time,
            "word_count_ratio": result.word_count["summary"] / max(1, result.word_count["original"]),
            "key_points_count": len(result.key_points),
            "entities_count": len(result.entities),
            "has_sentiment": result.sentiment.get("overall_sentiment") != "neutral" or result.sentiment.get("confidence", 0) > 0.5
        }

        # 计算综合质量分数
        quality_score = 0.0
        weights = {
            "confidence": 0.3,
            "length_ratio": 0.2,
            "key_points": 0.2,
            "entities": 0.1,
            "sentiment": 0.1,
            "speed": 0.1
        }

        # 置信度分数
        quality_score += quality_metrics["confidence_score"] * weights["confidence"]

        # 长度比率分数 (理想的摘要应该是原文的20-40%)
        ideal_ratio = 0.3
        ratio_diff = abs(quality_metrics["word_count_ratio"] - ideal_ratio)
        length_score = max(0, 1 - ratio_diff / ideal_ratio)
        quality_score += length_score * weights["length_ratio"]

        # 要点数量分数
        key_points_score = min(1.0, quality_metrics["key_points_count"] / self.config.max_bullet_points)
        quality_score += key_points_score * weights["key_points"]

        # 实体数量分数
        entities_score = min(1.0, quality_metrics["entities_count"] / 5)
        quality_score += entities_score * weights["entities"]

        # 情感分析分数
        sentiment_score = 1.0 if quality_metrics["has_sentiment"] else 0.0
        quality_score += sentiment_score * weights["sentiment"]

        # 处理速度分数 (应该在30秒内完成)
        speed_score = 1.0 if quality_metrics["processing_time"] < 30 else max(0, 1 - (quality_metrics["processing_time"] - 30) / 30)
        quality_score += speed_score * weights["speed"]

        quality_metrics["overall_quality_score"] = quality_score

        return quality_metrics