"""
Quality scoring system for content assessment and evaluation
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import json

from ..models.base import NewsArticle, NewsCategory
from .models import QualityMetrics, ProcessingConfig


@dataclass
class QualityFactors:
    """质量因子"""
    content_length: float
    readability: float
    source_credibility: float
    timeliness: float
    completeness: float
    structure: float
    relevance: float
    originality: float
    engagement: float


@dataclass
class QualityScore:
    """质量分数"""
    overall_score: float
    grade: str  # A+, A, B, C, D, F
    factors: QualityFactors
    breakdown: Dict[str, float]
    confidence: float
    recommendation: str


class QualityScorer:
    """质量评分器 - 评估和评分内容质量"""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 信誉权重
        self.credibility_weights = config.credibility_weights

        # 可读性权重
        self.readability_weights = config.readability_weights

        # 来源信誉评分
        self.source_reputation_scores = {
            'reuters.com': 0.95,
            'bloomberg.com': 0.90,
            'coindesk.com': 0.85,
            'cointelegraph.com': 0.80,
            'decrypt.co': 0.75,
            'theblock.co': 0.85,
            'forbes.com': 0.80,
            'wsj.com': 0.90,
            'ft.com': 0.85,
            'cnbc.com': 0.75,
            'yahoo.com': 0.60,
            'twitter.com': 0.40,
            'reddit.com': 0.35,
        }

        # 质量阈值
        self.quality_thresholds = {
            'A+': 0.95,
            'A': 0.85,
            'B': 0.70,
            'C': 0.55,
            'D': 0.40,
            'F': 0.0
        }

        # 作者信誉评分
        self.author_reputation = {
            'verified': 0.80,
            'staff_writer': 0.75,
            'contributor': 0.60,
            'guest': 0.40,
            'anonymous': 0.20
        }

    async def score_quality(self, article: NewsArticle) -> QualityScore:
        """评分内容质量"""
        try:
            # 计算各个质量因子
            factors = QualityFactors(
                content_length=await self._score_content_length(article),
                readability=await self._score_readability(article),
                source_credibility=await self._score_source_credibility(article),
                timeliness=await self._score_timeliness(article),
                completeness=await self._score_completeness(article),
                structure=await self._score_structure(article),
                relevance=await self._score_relevance(article),
                originality=await self._score_originality(article),
                engagement=await self._score_engagement(article)
            )

            # 计算综合分数
            overall_score = self._calculate_overall_score(factors)

            # 确定等级
            grade = self._determine_grade(overall_score)

            # 生成详细分解
            breakdown = self._create_breakdown(factors)

            # 计算置信度
            confidence = self._calculate_confidence(factors)

            # 生成建议
            recommendation = self._generate_recommendation(overall_score, factors)

            quality_score = QualityScore(
                overall_score=overall_score,
                grade=grade,
                factors=factors,
                breakdown=breakdown,
                confidence=confidence,
                recommendation=recommendation
            )

            self.logger.info(f"质量评分完成: {grade} ({overall_score:.2f})")
            return quality_score

        except Exception as e:
            self.logger.error(f"质量评分失败: {str(e)}", exc_info=True)
            # 返回默认分数
            return QualityScore(
                overall_score=0.5,
                grade='C',
                factors=QualityFactors(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
                breakdown={},
                confidence=0.0,
                recommendation="评分失败"
            )

    async def batch_score_quality(self, articles: List[NewsArticle]) -> List[QualityScore]:
        """批量质量评分"""
        self.logger.info(f"开始批量质量评分 {len(articles)} 篇文章")

        scores = []
        for article in articles:
            try:
                score = await self.score_quality(article)
                scores.append(score)
            except Exception as e:
                self.logger.error(f"批量质量评分失败: {str(e)}", exc_info=True)
                # 返回默认分数
                scores.append(QualityScore(
                    overall_score=0.5,
                    grade='C',
                    factors=QualityFactors(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
                    breakdown={},
                    confidence=0.0,
                    recommendation="评分失败"
                ))

        self.logger.info(f"批量质量评分完成，平均分数: {sum(s.overall_score for s in scores) / len(scores):.2f}")
        return scores

    async def _score_content_length(self, article: NewsArticle) -> float:
        """评分内容长度"""
        content_length = len(article.content)

        # 理想长度范围
        ideal_min = 500
        ideal_max = 3000

        if content_length < 100:
            return 0.0  # 过短
        elif content_length < ideal_min:
            return (content_length - 100) / (ideal_min - 100) * 0.7
        elif content_length <= ideal_max:
            return 1.0
        else:
            # 过长，适当降低分数
            return max(0.7, 1.0 - (content_length - ideal_max) / ideal_max * 0.3)

    async def _score_readability(self, article: NewsArticle) -> float:
        """评分可读性"""
        content = article.content

        # 计算词数和句数
        words = content.split()
        sentences = re.split(r'[.!?。！？]', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not words or not sentences:
            return 0.0

        # 平均词长
        avg_word_length = sum(len(word) for word in words) / len(words)

        # 平均句长
        avg_sentence_length = len(words) / len(sentences)

        # 计算可读性分数
        readability_score = 0.0

        # 词长分数 (理想: 4-6个字符)
        if 4 <= avg_word_length <= 6:
            readability_score += 0.3
        elif 3 <= avg_word_length <= 7:
            readability_score += 0.2
        else:
            readability_score += 0.1

        # 句长分数 (理想: 15-25个词)
        if 15 <= avg_sentence_length <= 25:
            readability_score += 0.4
        elif 10 <= avg_sentence_length <= 35:
            readability_score += 0.3
        else:
            readability_score += 0.1

        # 段落结构分数
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 3:
            readability_score += 0.3
        elif len(paragraphs) >= 2:
            readability_score += 0.2
        else:
            readability_score += 0.1

        return min(1.0, readability_score)

    async def _score_source_credibility(self, article: NewsArticle) -> float:
        """评分来源信誉"""
        if not article.source:
            return 0.5  # 未知来源

        # 检查域名信誉
        source_score = 0.5
        for domain, reputation in self.source_reputation_scores.items():
            if domain in article.source.lower():
                source_score = reputation
                break

        # 检查作者信誉
        author_score = 0.5
        if article.author:
            author_lower = article.author.lower()
            if 'verified' in author_lower or 'official' in author_lower:
                author_score = self.author_reputation['verified']
            elif 'staff' in author_lower or 'editor' in author_lower:
                author_score = self.author_reputation['staff_writer']
            elif 'contributor' in author_lower:
                author_score = self.author_reputation['contributor']
            elif 'guest' in author_lower:
                author_score = self.author_reputation['guest']
            else:
                author_score = self.author_reputation['anonymous']

        # 综合信誉分数
        credibility_score = (
            self.credibility_weights['source_reputation'] * source_score +
            self.credibility_weights['author_credibility'] * author_score
        )

        return credibility_score

    async def _score_timeliness(self, article: NewsArticle) -> float:
        """评分时效性"""
        if not article.published_at:
            return 0.5  # 无时间信息

        now = datetime.now()
        age = (now - article.published_at).total_seconds()

        # 时间权重
        if age < 3600:  # 1小时内
            return 1.0
        elif age < 86400:  # 24小时内
            return 0.9
        elif age < 604800:  # 7天内
            return 0.8
        elif age < 2592000:  # 30天内
            return 0.6
        elif age < 7776000:  # 90天内
            return 0.4
        else:
            return 0.2

    async def _score_completeness(self, article: NewsArticle) -> float:
        """评分完整性"""
        completeness_score = 0.0
        total_checks = 0

        # 检查标题
        if article.title and len(article.title.strip()) > 10:
            completeness_score += 0.2
        total_checks += 1

        # 检查内容
        if article.content and len(article.content.strip()) > 200:
            completeness_score += 0.3
        total_checks += 1

        # 检查摘要
        if article.summary and len(article.summary.strip()) > 20:
            completeness_score += 0.2
        total_checks += 1

        # 检查作者
        if article.author:
            completeness_score += 0.1
        total_checks += 1

        # 检查来源
        if article.source:
            completeness_score += 0.1
        total_checks += 1

        # 检查URL
        if article.url:
            completeness_score += 0.1
        total_checks += 1

        return completeness_score / total_checks if total_checks > 0 else 0.0

    async def _score_structure(self, article: NewsArticle) -> float:
        """评分结构"""
        content = article.content
        structure_score = 0.0

        # 检查段落结构
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 3:
            structure_score += 0.3
        elif len(paragraphs) >= 2:
            structure_score += 0.2
        else:
            structure_score += 0.1

        # 检查标题结构
        has_headers = bool(re.search(r'^#+\s+', content, re.MULTILINE))
        if has_headers:
            structure_score += 0.3

        # 检查列表结构
        has_lists = bool(re.search(r'^[\*\-\+]\s+|^\d+\.\s+', content, re.MULTILINE))
        if has_lists:
            structure_score += 0.2

        # 检查链接结构
        has_links = bool(re.search(r'http[s]?://', content))
        if has_links:
            structure_score += 0.2

        return min(1.0, structure_score)

    async def _score_relevance(self, article: NewsArticle) -> float:
        """评分相关性"""
        content = f"{article.title} {article.content}".lower()
        relevance_score = 0.0

        # 加密货币相关关键词
        crypto_keywords = [
            'bitcoin', 'ethereum', 'cryptocurrency', 'blockchain', 'defi', 'nft',
            'trading', 'investment', 'market', 'price', 'analysis', 'forecast',
            'regulation', 'adoption', 'technology', 'innovation', 'mining',
            'wallet', 'exchange', 'token', 'coin', 'digital', 'virtual'
        ]

        # 计算关键词匹配
        keyword_count = sum(1 for keyword in crypto_keywords if keyword in content)
        keyword_score = min(1.0, keyword_count / 5.0)  # 5个关键词得满分

        relevance_score += keyword_score * 0.7

        # 检查分类相关性
        if article.category != NewsCategory.GENERAL:
            relevance_score += 0.3

        return min(1.0, relevance_score)

    async def _score_originality(self, article: NewsArticle) -> float:
        """评分原创性"""
        content = article.content.lower()
        originality_score = 0.5  # 基础分数

        # 检查引用和转载标识
        quotation_marks = content.count('"') + content.count('"')
        if quotation_marks > len(content) / 100:  # 引用过多
            originality_score -= 0.2

        # 检查转载标识
        repost_indicators = ['转载', '来源', '原文', 'repost', 'source', 'original']
        if any(indicator in content for indicator in repost_indicators):
            originality_score -= 0.1

        # 检查版权声明
        copyright_indicators = ['copyright', '版权', 'all rights reserved']
        if any(indicator in content for indicator in copyright_indicators):
            originality_score += 0.1

        return max(0.0, min(1.0, originality_score))

    async def _score_engagement(self, article: NewsArticle) -> float:
        """评分参与度"""
        engagement_score = 0.0

        # 检查标题吸引力
        title = article.title.lower()
        engagement_words = ['breaking', 'exclusive', 'analysis', 'forecast', 'prediction',
                           'guide', 'tutorial', 'review', 'interview', 'opinion']

        if any(word in title for word in engagement_words):
            engagement_score += 0.3

        # 检查内容互动性
        content = article.content.lower()
        question_marks = content.count('?')
        if question_marks > 0:
            engagement_score += min(0.2, question_marks * 0.05)

        # 检查号召性用语
        call_to_action = ['read more', 'learn more', 'find out', 'discover', 'explore']
        if any(phrase in content for phrase in call_to_action):
            engagement_score += 0.2

        # 检查数据和分析
        data_indicators = ['data', 'statistics', 'analysis', 'chart', 'graph', 'report']
        if any(indicator in content for indicator in data_indicators):
            engagement_score += 0.3

        return min(1.0, engagement_score)

    def _calculate_overall_score(self, factors: QualityFactors) -> float:
        """计算综合分数"""
        # 权重配置
        weights = {
            'content_length': 0.15,
            'readability': 0.15,
            'source_credibility': 0.20,
            'timeliness': 0.10,
            'completeness': 0.10,
            'structure': 0.10,
            'relevance': 0.10,
            'originality': 0.05,
            'engagement': 0.05
        }

        overall_score = (
            weights['content_length'] * factors.content_length +
            weights['readability'] * factors.readability +
            weights['source_credibility'] * factors.source_credibility +
            weights['timeliness'] * factors.timeliness +
            weights['completeness'] * factors.completeness +
            weights['structure'] * factors.structure +
            weights['relevance'] * factors.relevance +
            weights['originality'] * factors.originality +
            weights['engagement'] * factors.engagement
        )

        return round(overall_score, 3)

    def _determine_grade(self, score: float) -> str:
        """确定等级"""
        for grade, threshold in self.quality_thresholds.items():
            if score >= threshold:
                return grade
        return 'F'

    def _create_breakdown(self, factors: QualityFactors) -> Dict[str, float]:
        """创建详细分解"""
        return {
            'content_length': factors.content_length,
            'readability': factors.readability,
            'source_credibility': factors.source_credibility,
            'timeliness': factors.timeliness,
            'completeness': factors.completeness,
            'structure': factors.structure,
            'relevance': factors.relevance,
            'originality': factors.originality,
            'engagement': factors.engagement
        }

    def _calculate_confidence(self, factors: QualityFactors) -> float:
        """计算置信度"""
        # 基于分数的稳定性计算置信度
        factor_scores = [
            factors.content_length,
            factors.readability,
            factors.source_credibility,
            factors.timeliness,
            factors.completeness,
            factors.structure,
            factors.relevance,
            factors.originality,
            factors.engagement
        ]

        # 计算标准差
        mean_score = sum(factor_scores) / len(factor_scores)
        variance = sum((score - mean_score) ** 2 for score in factor_scores) / len(factor_scores)
        std_dev = variance ** 0.5

        # 标准差越小，置信度越高
        confidence = max(0.0, 1.0 - std_dev)
        return round(confidence, 3)

    def _generate_recommendation(self, score: float, factors: QualityFactors) -> str:
        """生成建议"""
        if score >= 0.85:
            return "优秀内容，建议优先处理和传播"
        elif score >= 0.70:
            return "良好内容，建议正常处理"
        elif score >= 0.55:
            return "一般内容，建议检查后处理"
        elif score >= 0.40:
            return "较差内容，建议进一步筛选"
        else:
            return "低质量内容，建议过滤掉"

    def get_quality_distribution(self, scores: List[QualityScore]) -> Dict[str, int]:
        """获取质量分布"""
        distribution = defaultdict(int)
        for score in scores:
            distribution[score.grade] += 1
        return dict(distribution)

    def get_average_scores(self, scores: List[QualityScore]) -> Dict[str, float]:
        """获取平均分数"""
        if not scores:
            return {}

        factors = ['content_length', 'readability', 'source_credibility', 'timeliness',
                   'completeness', 'structure', 'relevance', 'originality', 'engagement']

        avg_scores = {}
        for factor in factors:
            avg_scores[factor] = sum(getattr(score.factors, factor) for score in scores) / len(scores)

        avg_scores['overall'] = sum(score.overall_score for score in scores) / len(scores)
        return avg_scores

    def update_source_reputation(self, source: str, reputation: float):
        """更新来源信誉"""
        self.source_reputation_scores[source.lower()] = reputation
        self.logger.info(f"已更新来源信誉: {source} -> {reputation}")

    def get_source_reputation(self) -> Dict[str, float]:
        """获取来源信誉"""
        return self.source_reputation_scores.copy()