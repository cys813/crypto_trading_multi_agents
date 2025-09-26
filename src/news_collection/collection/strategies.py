"""
Multi-source news collection strategies implementation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..core.adapter import NewsSourceAdapter
from ..models.base import (
    NewsArticle,
    NewsQuery,
    NewsQueryResult,
    NewsCategory,
    NewsSourceConfig
)


class CollectionStrategy(Enum):
    """收集策略枚举"""
    INCREMENTAL = "incremental"  # 增量收集
    FULL = "full"  # 全量收集
    PRIORITY_BASED = "priority_based"  # 基于优先级
    BREAKING_NEWS = "breaking_news"  # 突发新闻
    SCHEDULED = "scheduled"  # 定时收集


@dataclass
class CollectionWindow:
    """收集时间窗口配置"""
    start_time: datetime
    end_time: datetime
    max_articles: int = 1000
    enabled: bool = True


@dataclass
class CollectionResult:
    """收集结果"""
    articles: List[NewsArticle]
    sources_used: List[str]
    total_count: int
    execution_time: float
    errors: List[str]
    strategy_used: CollectionStrategy


class CollectionStrategy:
    """收集策略基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    async def collect(self,
                     adapters: Dict[str, NewsSourceAdapter],
                     query: Optional[NewsQuery] = None) -> CollectionResult:
        """执行收集策略"""
        raise NotImplementedError

    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return self.__class__.__name__


class IncrementalCollectionStrategy(CollectionStrategy):
    """增量收集策略 - 只收集最新内容"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.window_days = config.get('window_days', 15)
        self.max_articles_per_source = config.get('max_articles_per_source', 100)

    async def collect(self,
                     adapters: Dict[str, NewsSourceAdapter],
                     query: Optional[NewsQuery] = None) -> CollectionResult:
        """执行增量收集"""
        start_time = datetime.now()
        all_articles: List[NewsArticle] = []
        sources_used: List[str] = []
        errors: List[str] = []

        # 计算时间窗口（最近15天）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.window_days)

        self.logger.info(f"开始增量收集，时间窗口: {start_date} 到 {end_date}")

        # 并行收集所有源
        tasks = []
        for source_name, adapter in adapters.items():
            if adapter.is_connected():
                task = self._collect_from_source(adapter, source_name, start_date, end_date)
                tasks.append((source_name, task))
            else:
                errors.append(f"源 {source_name} 未连接")

        # 执行并行收集
        if tasks:
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )

            for (source_name, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    errors.append(f"源 {source_name} 收集失败: {str(result)}")
                    self.logger.error(f"源 {source_name} 收集失败", exc_info=result)
                elif result:
                    articles, source_errors = result
                    all_articles.extend(articles)
                    sources_used.append(source_name)
                    errors.extend(source_errors)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return CollectionResult(
            articles=all_articles,
            sources_used=sources_used,
            total_count=len(all_articles),
            execution_time=execution_time,
            errors=errors,
            strategy_used=CollectionStrategy.INCREMENTAL
        )

    async def _collect_from_source(self,
                                  adapter: NewsSourceAdapter,
                                  source_name: str,
                                  start_date: datetime,
                                  end_date: datetime) -> Tuple[List[NewsArticle], List[str]]:
        """从单个源收集数据"""
        articles = []
        errors = []

        try:
            # 创建查询
            query = NewsQuery(
                start_date=start_date,
                end_date=end_date,
                limit=self.max_articles_per_source
            )

            # 执行查询
            result = await adapter.fetch_news(query)

            if result.articles:
                articles.extend(result.articles)
                self.logger.info(f"从 {source_name} 收集到 {len(result.articles)} 篇文章")

            if result.errors:
                errors.extend([f"{source_name}: {error}" for error in result.errors])

        except Exception as e:
            errors.append(f"源 {source_name} 异常: {str(e)}")
            self.logger.error(f"从 {source_name} 收集时发生异常", exc_info=e)

        return articles, errors


class FullCollectionStrategy(CollectionStrategy):
    """全量收集策略 - 收集所有可用内容"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_articles_per_source = config.get('max_articles_per_source', 500)

    async def collect(self,
                     adapters: Dict[str, NewsSourceAdapter],
                     query: Optional[NewsQuery] = None) -> CollectionResult:
        """执行全量收集"""
        start_time = datetime.now()
        all_articles: List[NewsArticle] = []
        sources_used: List[str] = []
        errors: List[str] = []

        self.logger.info("开始全量收集")

        # 并行收集所有源
        tasks = []
        for source_name, adapter in adapters.items():
            if adapter.is_connected():
                task = self._collect_all_from_source(adapter, source_name)
                tasks.append((source_name, task))
            else:
                errors.append(f"源 {source_name} 未连接")

        if tasks:
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )

            for (source_name, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    errors.append(f"源 {source_name} 收集失败: {str(result)}")
                elif result:
                    articles, source_errors = result
                    all_articles.extend(articles)
                    sources_used.append(source_name)
                    errors.extend(source_errors)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return CollectionResult(
            articles=all_articles,
            sources_used=sources_used,
            total_count=len(all_articles),
            execution_time=execution_time,
            errors=errors,
            strategy_used=CollectionStrategy.FULL
        )

    async def _collect_all_from_source(self,
                                      adapter: NewsSourceAdapter,
                                      source_name: str) -> Tuple[List[NewsArticle], List[str]]:
        """从单个源收集所有数据"""
        articles = []
        errors = []

        try:
            # 获取最新新闻
            latest_articles = await adapter.get_latest_news(self.max_articles_per_source)
            articles.extend(latest_articles)
            self.logger.info(f"从 {source_name} 全量收集到 {len(latest_articles)} 篇文章")

        except Exception as e:
            errors.append(f"源 {source_name} 异常: {str(e)}")
            self.logger.error(f"从 {source_name} 全量收集时发生异常", exc_info=e)

        return articles, errors


class PriorityBasedCollectionStrategy(CollectionStrategy):
    """基于优先级的收集策略"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.priority_threshold = config.get('priority_threshold', 5)
        self.max_articles_per_source = config.get('max_articles_per_source', 200)

    async def collect(self,
                     adapters: Dict[str, NewsSourceAdapter],
                     query: Optional[NewsQuery] = None) -> CollectionResult:
        """执行基于优先级的收集"""
        start_time = datetime.now()
        all_articles: List[NewsArticle] = []
        sources_used: List[str] = []
        errors: List[str] = []

        self.logger.info("开始基于优先级的收集")

        # 按优先级排序适配器
        sorted_adapters = sorted(
            adapters.items(),
            key=lambda x: x[1].config.priority,
            reverse=True
        )

        # 只收集高优先级源
        high_priority_adapters = [
            (name, adapter) for name, adapter in sorted_adapters
            if adapter.config.priority >= self.priority_threshold and adapter.is_connected()
        ]

        if not high_priority_adapters:
            errors.append("没有高优先级的可用源")
            return CollectionResult(
                articles=[],
                sources_used=[],
                total_count=0,
                execution_time=0,
                errors=errors,
                strategy_used=CollectionStrategy.PRIORITY_BASED
            )

        # 并行收集高优先级源
        tasks = []
        for source_name, adapter in high_priority_adapters:
            task = self._collect_from_source(adapter, source_name)
            tasks.append((source_name, task))

        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        for (source_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                errors.append(f"源 {source_name} 收集失败: {str(result)}")
            elif result:
                articles, source_errors = result
                all_articles.extend(articles)
                sources_used.append(source_name)
                errors.extend(source_errors)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return CollectionResult(
            articles=all_articles,
            sources_used=sources_used,
            total_count=len(all_articles),
            execution_time=execution_time,
            errors=errors,
            strategy_used=CollectionStrategy.PRIORITY_BASED
        )

    async def _collect_from_source(self,
                                  adapter: NewsSourceAdapter,
                                  source_name: str) -> Tuple[List[NewsArticle], List[str]]:
        """从单个源收集数据"""
        articles = []
        errors = []

        try:
            # 获取最新新闻
            latest_articles = await adapter.get_latest_news(self.max_articles_per_source)
            articles.extend(latest_articles)
            self.logger.info(f"从高优先级源 {source_name} 收集到 {len(latest_articles)} 篇文章")

        except Exception as e:
            errors.append(f"源 {source_name} 异常: {str(e)}")
            self.logger.error(f"从 {source_name} 收集时发生异常", exc_info=e)

        return articles, errors


class CollectionStrategyFactory:
    """收集策略工厂"""

    _strategies: Dict[str, type] = {
        "incremental": IncrementalCollectionStrategy,
        "full": FullCollectionStrategy,
        "priority_based": PriorityBasedCollectionStrategy,
    }

    @classmethod
    def create_strategy(cls, strategy_type: str, config: Dict[str, Any]) -> CollectionStrategy:
        """创建收集策略实例"""
        if strategy_type not in cls._strategies:
            raise ValueError(f"不支持的收集策略: {strategy_type}")

        strategy_class = cls._strategies[strategy_type]
        return strategy_class(config)

    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """获取可用策略列表"""
        return list(cls._strategies.keys())

    @classmethod
    def register_strategy(cls, strategy_type: str, strategy_class: type):
        """注册新的收集策略"""
        cls._strategies[strategy_type] = strategy_class