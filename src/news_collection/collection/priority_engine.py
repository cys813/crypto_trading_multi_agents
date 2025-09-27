"""
Priority engine for intelligent collection prioritization and breakthrough news detection
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import re

from ..core.adapter import NewsSourceAdapter
from ..models.base import NewsArticle, NewsCategory, NewsSourceConfig
from .relevance_filter import RelevanceFilter, RelevanceScore


class PriorityLevel(Enum):
    """优先级级别"""
    CRITICAL = "critical"  # 紧急 (需要立即处理)
    HIGH = "high"  # 高优先级 (30分钟内)
    MEDIUM = "medium"  # 中优先级 (2小时内)
    LOW = "low"  # 低优先级 (6小时内)
    ROUTINE = "routine"  # 常规 (24小时内)


@dataclass
class PriorityFactors:
    """优先级因子"""
    # 基础因子
    source_reliability: float = 0.0  # 源可靠性 (0-10)
    source_priority: int = 1  # 源优先级 (1-10)
    article_relevance: float = 0.0  # 文章相关性 (0-100)
    content_quality: float = 0.0  # 内容质量 (0-100)

    # 时间因子
    recency: float = 0.0  # 新鲜度 (0-100)
    time_sensitivity: float = 0.0  # 时间敏感性 (0-100)

    # 影响因子
    market_impact: float = 0.0  # 市场影响 (0-100)
    breakout_potential: float = 0.0  # 突破潜力 (0-100)
    urgency: float = 0.0  # 紧急性 (0-100)

    # 交互因子
    engagement_indicators: float = 0.0  # 参与度指标 (0-100)
    viral_indicators: float = 0.0  # 病毒传播指标 (0-100)


@dataclass
class CollectionPriority:
    """收集优先级"""
    priority_score: float  # 0-100
    priority_level: PriorityLevel
    factors: PriorityFactors
    recommended_action: str
    estimated_processing_time: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    retry_priority: bool = False
    max_retries: int = 3


class PriorityEngine:
    """优先级引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 初始化相关性过滤器
        self.relevance_filter = RelevanceFilter(config.get('relevance_filter', {}))

        # 配置参数
        self.critical_threshold = config.get('critical_threshold', 90)
        self.high_threshold = config.get('high_threshold', 75)
        self.medium_threshold = config.get('medium_threshold', 60)
        self.low_threshold = config.get('low_threshold', 40)

        # 源可靠性评分
        self.source_reliability_scores = config.get('source_reliability', {
            'coindesk': 9.0,
            'cointelegraph': 8.5,
            'decrypt': 8.0,
            'bloomberg': 9.5,
            'reuters': 9.0,
            'cnbc': 8.0
        })

        # 突破新闻检测配置
        self.breakout_detection_config = config.get('breakout_detection', {
            'price_movement_threshold': 5.0,  # 5%价格变动
            'volume_spike_threshold': 3.0,  # 3倍成交量
            'social_mention_threshold': 10.0,  # 10倍社交媒体提及
            'news_density_threshold': 5.0  # 5倍新闻密度
        })

        # 关键词权重
        self.keyword_weights = {
            'critical': ['hack', 'breach', 'exploit', 'sec', 'lawsuit', 'ban', 'approved', 'launched'],
            'high': ['partnership', 'acquisition', 'funding', 'upgrade', 'hard fork', 'airdrop'],
            'medium': ['adoption', 'integration', 'listing', 'staking', 'defi', 'nft'],
            'low': ['analysis', 'prediction', 'opinion', 'tutorial', 'guide']
        }

        # 缓存
        self.priority_cache: Dict[str, CollectionPriority] = {}
        self.breaking_news_cache: Set[str] = set()
        self.last_breaking_check = datetime.now()

    async def calculate_collection_priority(self,
                                           adapters: Dict[str, NewsSourceAdapter],
                                           current_time: Optional[datetime] = None) -> Dict[str, CollectionPriority]:
        """计算收集优先级"""
        if current_time is None:
            current_time = datetime.now()

        priorities = {}

        # 检查突破新闻
        await self._check_breaking_news()

        # 为每个适配器计算优先级
        for source_name, adapter in adapters.items():
            if adapter.is_connected():
                priority = await self._calculate_adapter_priority(adapter, source_name, current_time)
                priorities[source_name] = priority
            else:
                # 离线源给予低优先级
                priorities[source_name] = CollectionPriority(
                    priority_score=10.0,
                    priority_level=PriorityLevel.ROUTINE,
                    factors=PriorityFactors(),
                    recommended_action="等待源恢复连接",
                    retry_priority=True
                )

        return priorities

    async def _calculate_adapter_priority(self,
                                        adapter: NewsSourceAdapter,
                                        source_name: str,
                                        current_time: datetime) -> CollectionPriority:
        """计算单个适配器的优先级"""
        factors = PriorityFactors()

        # 1. 源可靠性评分
        factors.source_reliability = self.source_reliability_scores.get(source_name, 5.0)

        # 2. 源配置优先级
        factors.source_priority = adapter.config.priority if adapter.config.priority else 5

        # 3. 最后收集时间计算新鲜度
        stats = adapter.get_stats()
        last_used = adapter.get_connection_info().last_used if adapter.get_connection_info() else None

        if last_used:
            time_diff = (current_time - last_used).total_seconds()
            factors.recency = max(0, 100 - (time_diff / 3600))  # 1小时降10分
        else:
            factors.recency = 100  # 新连接给满分

        # 4. 成功率计算内容质量
        success_rate = stats.get('success_rate', 0.0) * 100
        factors.content_quality = success_rate

        # 5. 错误率计算可靠性
        error_rate = stats.get('error_count', 0) / max(stats.get('request_count', 1), 1)
        reliability_factor = max(0, 100 - (error_rate * 100))
        factors.urgency = reliability_factor  # 错误率高表示需要紧急关注

        # 6. 检查是否是突破新闻源
        if self._is_breaking_news_source(source_name):
            factors.breakout_potential = 95
            factors.market_impact = 90
            factors.urgency = 100

        # 7. 计算综合优先级分数
        priority_score = self._calculate_priority_score(factors, source_name)

        # 8. 确定优先级级别
        priority_level = self._determine_priority_level(priority_score)

        # 9. 生成推荐行动
        recommended_action = self._generate_recommended_action(
            priority_level, factors, source_name
        )

        # 10. 估算处理时间
        estimated_time = self._estimate_processing_time(factors, source_name)

        return CollectionPriority(
            priority_score=priority_score,
            priority_level=priority_level,
            factors=factors,
            recommended_action=recommended_action,
            estimated_processing_time=estimated_time,
            retry_priority=factors.urgency > 70
        )

    def _calculate_priority_score(self, factors: PriorityFactors, source_name: str) -> float:
        """计算优先级分数"""
        # 权重配置
        weights = {
            'source_reliability': 0.25,
            'source_priority': 0.20,
            'content_quality': 0.15,
            'recency': 0.15,
            'breakout_potential': 0.15,
            'urgency': 0.10
        }

        # 标准化因子
        normalized_factors = {
            'source_reliability': factors.source_reliability * 10,  # 0-10 -> 0-100
            'source_priority': factors.source_priority * 10,  # 1-10 -> 10-100
            'content_quality': factors.content_quality,
            'recency': factors.recency,
            'breakout_potential': factors.breakout_potential,
            'urgency': factors.urgency
        }

        # 计算加权分数
        weighted_score = sum(
            weights[key] * normalized_factors[key]
            for key in weights.keys()
        )

        # 突破新闻加成
        if factors.breakout_potential > 80:
            weighted_score += 20

        # 紧急情况加成
        if factors.urgency > 80:
            weighted_score += 15

        return max(0, min(100, weighted_score))

    def _determine_priority_level(self, score: float) -> PriorityLevel:
        """确定优先级级别"""
        if score >= self.critical_threshold:
            return PriorityLevel.CRITICAL
        elif score >= self.high_threshold:
            return PriorityLevel.HIGH
        elif score >= self.medium_threshold:
            return PriorityLevel.MEDIUM
        elif score >= self.low_threshold:
            return PriorityLevel.LOW
        else:
            return PriorityLevel.ROUTINE

    def _generate_recommended_action(self,
                                   priority_level: PriorityLevel,
                                   factors: PriorityFactors,
                                   source_name: str) -> str:
        """生成推荐行动"""
        if priority_level == PriorityLevel.CRITICAL:
            if factors.breakout_potential > 80:
                return f"立即收集 {source_name} - 检测到突破新闻"
            else:
                return f"立即收集 {source_name} - 高优先级源需要关注"

        elif priority_level == PriorityLevel.HIGH:
            return f"优先收集 {source_name} - 30分钟内执行"

        elif priority_level == PriorityLevel.MEDIUM:
            return f"正常收集 {source_name} - 2小时内执行"

        elif priority_level == PriorityLevel.LOW:
            return f"延迟收集 {source_name} - 6小时内执行"

        else:
            return f"常规收集 {source_name} - 24小时内执行"

    def _estimate_processing_time(self,
                                 factors: PriorityFactors,
                                 source_name: str) -> timedelta:
        """估算处理时间"""
        base_time = timedelta(minutes=30)

        # 基于因子调整时间
        if factors.breakout_potential > 80:
            return timedelta(minutes=10)  # 突破新闻快速处理
        elif factors.urgency > 80:
            return timedelta(minutes=15)  # 紧急情况快速处理
        elif factors.source_reliability < 5:
            return timedelta(minutes=45)  # 低可靠性源需要更多时间

        return base_time

    async def _check_breaking_news(self):
        """检查突破新闻"""
        current_time = datetime.now()

        # 每5分钟检查一次
        if (current_time - self.last_breaking_check).total_seconds() < 300:
            return

        self.last_breaking_check = current_time

        try:
            # 这里可以集成外部API来检测突破新闻
            # 例如：价格监控API、社交媒体趋势API等
            # 现在简化处理，基于关键词检测

            breaking_keywords = [
                'bitcoin hack', 'ethereum breach', 'crypto exchange hack',
                'sec approval', 'crypto ban', 'major partnership',
                'price crash', 'market crash', 'bull run', 'bear market'
            ]

            # 模拟检测到突破新闻
            # 实际项目中这里会调用外部API
            await self._simulate_breaking_news_detection(breaking_keywords)

        except Exception as e:
            self.logger.error("检查突破新闻失败", exc_info=e)

    async def _simulate_breaking_news_detection(self, keywords: List[str]):
        """模拟突破新闻检测（实际项目中应替换为真实API调用）"""
        # 这里是模拟逻辑，实际项目中应该：
        # 1. 调用价格监控API
        # 2. 调用社交媒体趋势API
        # 3. 调用新闻聚合API
        # 4. 分析异常模式

        # 模拟：随机选择一些关键词作为突破新闻
        import random
        detected_breaking = random.sample(keywords, min(2, len(keywords)))

        for keyword in detected_breaking:
            self.breaking_news_cache.add(keyword)
            self.logger.info(f"检测到突破新闻关键词: {keyword}")

        # 清理旧的突破新闻（保留1小时）
        one_hour_ago = current_time - timedelta(hours=1)
        self.breaking_news_cache = {
            keyword for keyword in self.breaking_news_cache
            if self._is_keyword_recent(keyword, one_hour_ago)
        }

    def _is_keyword_recent(self, keyword: str, cutoff_time: datetime) -> bool:
        """检查关键词是否最近（模拟实现）"""
        # 实际项目中应该跟踪关键词的检测时间
        return True  # 简化处理

    def _is_breaking_news_source(self, source_name: str) -> bool:
        """检查是否是突破新闻源"""
        # 基于源可靠性和优先级判断
        reliability = self.source_reliability_scores.get(source_name, 5.0)
        return reliability >= 8.0  # 高可靠性源可能是突破新闻源

    def calculate_article_priority(self, article: NewsArticle) -> CollectionPriority:
        """计算单篇文章的优先级"""
        factors = PriorityFactors()

        # 计算相关性
        relevance_score = self.relevance_filter.calculate_relevance(article)
        factors.article_relevance = relevance_score.score

        # 计算新鲜度
        if article.published_at:
            time_diff = (datetime.now() - article.published_at).total_seconds()
            factors.recency = max(0, 100 - (time_diff / 3600))  # 1小时降10分

        # 计算市场影响
        factors.market_impact = self._calculate_market_impact(article)

        # 计算突破潜力
        factors.breakout_potential = self._calculate_breakout_potential(article)

        # 计算紧急性
        factors.urgency = self._calculate_urgency(article)

        # 计算综合分数
        priority_score = self._calculate_article_priority_score(factors, article)

        # 确定优先级级别
        priority_level = self._determine_priority_level(priority_score)

        return CollectionPriority(
            priority_score=priority_score,
            priority_level=priority_level,
            factors=factors,
            recommended_action=self._generate_article_recommendation(priority_level, article)
        )

    def _calculate_market_impact(self, article: NewsArticle) -> float:
        """计算市场影响分数"""
        text = f"{article.title} {article.content or ''}".lower()
        impact_score = 0.0

        # 高影响关键词
        high_impact_keywords = [
            'sec', 'regulation', 'lawsuit', 'ban', 'approved', 'launch',
            'partnership', 'acquisition', 'merger', 'investment', 'funding'
        ]

        for keyword in high_impact_keywords:
            if keyword in text:
                impact_score += 10

        # 类别影响
        if article.category == NewsCategory.REGULATION:
            impact_score += 20
        elif article.category == NewsCategory.BREAKING:
            impact_score += 30
        elif article.category == NewsCategory.MARKET_ANALYSIS:
            impact_score += 15

        return min(impact_score, 100)

    def _calculate_breakout_potential(self, article: NewsArticle) -> float:
        """计算突破潜力分数"""
        text = f"{article.title} {article.content or ''}".lower()
        breakout_score = 0.0

        # 突破关键词
        breakout_keywords = [
            'breakthrough', 'revolutionary', 'game-changing', 'innovative',
            'first-ever', 'record-breaking', 'unprecedented', 'milestone'
        ]

        for keyword in breakout_keywords:
            if keyword in text:
                breakout_score += 15

        # 技术突破
        tech_keywords = ['upgrade', 'hard fork', 'protocol', 'network', 'scaling']
        for keyword in tech_keywords:
            if keyword in text:
                breakout_score += 10

        return min(breakout_score, 100)

    def _calculate_urgency(self, article: NewsArticle) -> float:
        """计算紧急性分数"""
        text = f"{article.title} {article.content or ''}".lower()
        urgency_score = 0.0

        # 紧急关键词
        urgent_keywords = [
            'immediately', 'urgent', 'critical', 'emergency', 'alert',
            'breaking', 'just in', 'developing', 'update'
        ]

        for keyword in urgent_keywords:
            if keyword in text:
                urgency_score += 20

        # 时间紧急性
        if article.published_at:
            time_diff = (datetime.now() - article.published_at).total_seconds()
            if time_diff < 3600:  # 1小时内
                urgency_score += 50
            elif time_diff < 7200:  # 2小时内
                urgency_score += 30

        return min(urgency_score, 100)

    def _calculate_article_priority_score(self, factors: PriorityFactors, article: NewsArticle) -> float:
        """计算文章优先级分数"""
        weights = {
            'article_relevance': 0.35,
            'market_impact': 0.25,
            'breakout_potential': 0.20,
            'urgency': 0.20
        }

        weighted_score = sum(
            weights[key] * getattr(factors, key)
            for key in weights.keys()
        )

        return max(0, min(100, weighted_score))

    def _generate_article_recommendation(self,
                                       priority_level: PriorityLevel,
                                       article: NewsArticle) -> str:
        """生成文章处理推荐"""
        if priority_level == PriorityLevel.CRITICAL:
            return "立即处理 - 高影响突破新闻"
        elif priority_level == PriorityLevel.HIGH:
            return "优先处理 - 重要市场新闻"
        elif priority_level == PriorityLevel.MEDIUM:
            return "正常处理 - 常规相关新闻"
        elif priority_level == PriorityLevel.LOW:
            return "延后处理 - 低优先级新闻"
        else:
            return "归档处理 - 历史参考新闻"

    def get_priority_statistics(self,
                               priorities: Dict[str, CollectionPriority]) -> Dict[str, Any]:
        """获取优先级统计信息"""
        if not priorities:
            return {}

        # 优先级分布
        level_counts = {level.value: 0 for level in PriorityLevel}
        total_score = 0

        for priority in priorities.values():
            level_counts[priority.priority_level.value] += 1
            total_score += priority.priority_score

        # 因子分析
        avg_factors = PriorityFactors()
        for priority in priorities.values():
            factors = priority.factors
            for field in factors.__dataclass_fields__:
                current_value = getattr(avg_factors, field)
                new_value = getattr(factors, field)
                setattr(avg_factors, field, current_value + new_value)

        # 平均化因子
        for field in avg_factors.__dataclass_fields__:
            current_value = getattr(avg_factors, field)
            setattr(avg_factors, field, current_value / len(priorities))

        return {
            'total_sources': len(priorities),
            'average_priority_score': total_score / len(priorities),
            'priority_distribution': level_counts,
            'average_factors': {
                field: getattr(avg_factors, field)
                for field in avg_factors.__dataclass_fields__
            },
            'critical_sources': [
                source for source, priority in priorities.items()
                if priority.priority_level == PriorityLevel.CRITICAL
            ],
            'high_priority_sources': [
                source for source, priority in priorities.items()
                if priority.priority_level == PriorityLevel.HIGH
            ]
        }