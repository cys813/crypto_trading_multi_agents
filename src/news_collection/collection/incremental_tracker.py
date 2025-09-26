"""
Incremental tracker for timestamp-based deduplication and rolling window management
"""

import hashlib
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
import os
import pickle
from pathlib import Path

from ..models.base import NewsArticle, NewsSourceConfig


@dataclass
class ArticleFingerprint:
    """文章指纹"""
    title_hash: str
    content_hash: str
    source: str
    url: str
    published_at: datetime
    created_at: datetime


@dataclass
class SourceTrackingInfo:
    """源跟踪信息"""
    source_name: str
    last_collection_time: Optional[datetime] = None
    last_article_id: Optional[str] = None
    total_articles_collected: int = 0
    last_successful_collection: Optional[datetime] = None
    consecutive_failures: int = 0
    collection_stats: Dict[str, int] = None

    def __post_init__(self):
        if self.collection_stats is None:
            self.collection_stats = {}


class IncrementalTracker:
    """增量跟踪器 - 基于时间戳的去重和滚动窗口管理"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 配置参数
        self.window_days = config.get('window_days', 15)
        self.max_articles_in_memory = config.get('max_articles_in_memory', 10000)
        self.persistence_interval = config.get('persistence_interval', 300)  # 5分钟
        self.storage_path = config.get('storage_path', 'incremental_tracker_data')

        # 数据存储
        self.article_fingerprints: Dict[str, ArticleFingerprint] = {}  # fingerprint_id -> fingerprint
        self.source_tracking: Dict[str, SourceTrackingInfo] = {}  # source_name -> tracking_info
        self.url_index: Dict[str, str] = {}  # url -> fingerprint_id
        self.title_source_index: Dict[str, Set[str]] = {}  # (title_hash, source) -> set of fingerprint_ids

        # 持久化
        self.last_persistence_time = datetime.now()
        self.persistence_task: Optional[asyncio.Task] = None

        # 初始化存储路径
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """初始化跟踪器"""
        self.logger.info("初始化增量跟踪器")

        # 加载持久化数据
        await self._load_data()

        # 启动持久化任务
        self.persistence_task = asyncio.create_task(self._persistence_loop())

        # 清理过期数据
        await self._cleanup_expired_data()

    async def shutdown(self):
        """关闭跟踪器"""
        self.logger.info("关闭增量跟踪器")

        if self.persistence_task:
            self.persistence_task.cancel()
            try:
                await self.persistence_task
            except asyncio.CancelledError:
                pass

        # 最后保存数据
        await self._save_data()

    def is_duplicate(self, article: NewsArticle) -> bool:
        """检查文章是否重复"""
        if not article.url:
            # 如果没有URL，使用标题和来源检查
            title_hash = self._generate_hash(article.title)
            key = f"{title_hash}_{article.source}"
            return key in self.title_source_index

        # 检查URL是否已存在
        if article.url in self.url_index:
            return True

        return False

    def get_fingerprint(self, article: NewsArticle) -> str:
        """生成文章指纹"""
        if article.url:
            return self._generate_hash(article.url)
        else:
            return self._generate_hash(f"{article.title}_{article.source}_{article.published_at}")

    def track_article(self, article: NewsArticle) -> str:
        """跟踪文章"""
        fingerprint_id = self.get_fingerprint(article)

        if fingerprint_id in self.article_fingerprints:
            return fingerprint_id  # 已存在

        # 创建文章指纹
        title_hash = self._generate_hash(article.title)
        content_hash = self._generate_hash(article.content[:1000]) if article.content else ""

        fingerprint = ArticleFingerprint(
            title_hash=title_hash,
            content_hash=content_hash,
            source=article.source or "unknown",
            url=article.url or "",
            published_at=article.published_at or datetime.now(),
            created_at=datetime.now()
        )

        # 存储指纹
        self.article_fingerprints[fingerprint_id] = fingerprint

        # 更新索引
        if article.url:
            self.url_index[article.url] = fingerprint_id

        title_source_key = f"{title_hash}_{fingerprint.source}"
        if title_source_key not in self.title_source_index:
            self.title_source_index[title_source_key] = set()
        self.title_source_index[title_source_key].add(fingerprint_id)

        return fingerprint_id

    def update_source_tracking(self,
                              source_name: str,
                              collection_time: datetime,
                              articles_count: int,
                              last_article_id: Optional[str] = None,
                              success: bool = True):
        """更新源跟踪信息"""
        if source_name not in self.source_tracking:
            self.source_tracking[source_name] = SourceTrackingInfo(source_name=source_name)

        tracking_info = self.source_tracking[source_name]
        tracking_info.last_collection_time = collection_time
        tracking_info.total_articles_collected += articles_count

        if success:
            tracking_info.last_successful_collection = collection_time
            tracking_info.consecutive_failures = 0
            if last_article_id:
                tracking_info.last_article_id = last_article_id
        else:
            tracking_info.consecutive_failures += 1

        # 更新统计信息
        date_key = collection_time.strftime('%Y-%m-%d')
        tracking_info.collection_stats[date_key] = tracking_info.collection_stats.get(date_key, 0) + articles_count

    def get_source_tracking_info(self, source_name: str) -> Optional[SourceTrackingInfo]:
        """获取源跟踪信息"""
        return self.source_tracking.get(source_name)

    def get_last_collection_time(self, source_name: str) -> Optional[datetime]:
        """获取源最后收集时间"""
        tracking_info = self.source_tracking.get(source_name)
        return tracking_info.last_collection_time if tracking_info else None

    def get_collection_window(self, source_name: str = None) -> Tuple[datetime, datetime]:
        """获取收集时间窗口"""
        end_time = datetime.now()

        if source_name:
            last_collection = self.get_last_collection_time(source_name)
            if last_collection:
                # 从上次收集时间开始
                start_time = last_collection
            else:
                # 默认15天窗口
                start_time = end_time - timedelta(days=self.window_days)
        else:
            # 默认15天窗口
            start_time = end_time - timedelta(days=self.window_days)

        return start_time, end_time

    def get_articles_in_window(self,
                              start_time: datetime,
                              end_time: datetime,
                              source: Optional[str] = None) -> List[ArticleFingerprint]:
        """获取时间窗口内的文章"""
        articles = []

        for fingerprint in self.article_fingerprints.values():
            if start_time <= fingerprint.published_at <= end_time:
                if source is None or fingerprint.source == source:
                    articles.append(fingerprint)

        return sorted(articles, key=lambda x: x.published_at, reverse=True)

    def remove_expired_articles(self, cutoff_time: datetime) -> int:
        """移除过期文章"""
        removed_count = 0
        fingerprints_to_remove = []

        # 找出过期文章
        for fingerprint_id, fingerprint in self.article_fingerprints.items():
            if fingerprint.created_at < cutoff_time:
                fingerprints_to_remove.append(fingerprint_id)

        # 移除文章和相关索引
        for fingerprint_id in fingerprints_to_remove:
            fingerprint = self.article_fingerprints[fingerprint_id]

            # 从URL索引中移除
            if fingerprint.url and fingerprint.url in self.url_index:
                del self.url_index[fingerprint.url]

            # 从标题源索引中移除
            title_source_key = f"{fingerprint.title_hash}_{fingerprint.source}"
            if title_source_key in self.title_source_index:
                self.title_source_index[title_source_key].discard(fingerprint_id)
                if not self.title_source_index[title_source_key]:
                    del self.title_source_index[title_source_key]

            # 从主存储中移除
            del self.article_fingerprints[fingerprint_id]
            removed_count += 1

        self.logger.info(f"移除了 {removed_count} 篇过期文章")
        return removed_count

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_articles = len(self.article_fingerprints)
        total_sources = len(self.source_tracking)

        # 计算内存使用情况
        estimated_memory = (
            total_articles * 500 +  # 每个文章指纹约500字节
            len(self.url_index) * 100 +  # URL索引每项约100字节
            len(self.title_source_index) * 200  # 标题源索引每项约200字节
        )

        # 源统计
        source_stats = {}
        for source_name, tracking_info in self.source_tracking.items():
            source_stats[source_name] = {
                'total_articles_collected': tracking_info.total_articles_collected,
                'last_collection_time': tracking_info.last_collection_time.isoformat() if tracking_info.last_collection_time else None,
                'last_successful_collection': tracking_info.last_successful_collection.isoformat() if tracking_info.last_successful_collection else None,
                'consecutive_failures': tracking_info.consecutive_failures,
                'collection_days': len(tracking_info.collection_stats)
            }

        return {
            'total_articles_tracked': total_articles,
            'total_sources_tracked': total_sources,
            'estimated_memory_usage_bytes': estimated_memory,
            'window_days': self.window_days,
            'sources': source_stats
        }

    def _generate_hash(self, text: str) -> str:
        """生成哈希值"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    async def _persistence_loop(self):
        """持久化循环"""
        while True:
            try:
                await asyncio.sleep(self.persistence_interval)

                # 检查是否需要持久化
                if (datetime.now() - self.last_persistence_time).total_seconds() >= self.persistence_interval:
                    await self._save_data()
                    self.last_persistence_time = datetime.now()

                    # 内存清理
                    if len(self.article_fingerprints) > self.max_articles_in_memory:
                        await self._cleanup_expired_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("持久化循环异常", exc_info=e)

    async def _save_data(self):
        """保存数据到磁盘"""
        try:
            # 保存文章指纹
            fingerprints_file = os.path.join(self.storage_path, 'fingerprints.pkl')
            with open(fingerprints_file, 'wb') as f:
                pickle.dump(self.article_fingerprints, f)

            # 保存源跟踪信息
            tracking_file = os.path.join(self.storage_path, 'tracking.json')
            tracking_data = {}
            for source_name, tracking_info in self.source_tracking.items():
                tracking_data[source_name] = {
                    'source_name': tracking_info.source_name,
                    'last_collection_time': tracking_info.last_collection_time.isoformat() if tracking_info.last_collection_time else None,
                    'last_article_id': tracking_info.last_article_id,
                    'total_articles_collected': tracking_info.total_articles_collected,
                    'last_successful_collection': tracking_info.last_successful_collection.isoformat() if tracking_info.last_successful_collection else None,
                    'consecutive_failures': tracking_info.consecutive_failures,
                    'collection_stats': tracking_info.collection_stats
                }

            with open(tracking_file, 'w', encoding='utf-8') as f:
                json.dump(tracking_data, f, indent=2, ensure_ascii=False)

            # 保存索引
            indexes_file = os.path.join(self.storage_path, 'indexes.json')
            indexes_data = {
                'url_index': self.url_index,
                'title_source_index': {k: list(v) for k, v in self.title_source_index.items()}
            }

            with open(indexes_file, 'w', encoding='utf-8') as f:
                json.dump(indexes_data, f, indent=2, ensure_ascii=False)

            self.logger.debug("数据持久化完成")

        except Exception as e:
            self.logger.error("保存数据失败", exc_info=e)

    async def _load_data(self):
        """从磁盘加载数据"""
        try:
            # 加载文章指纹
            fingerprints_file = os.path.join(self.storage_path, 'fingerprints.pkl')
            if os.path.exists(fingerprints_file):
                with open(fingerprints_file, 'rb') as f:
                    self.article_fingerprints = pickle.load(f)

            # 加载源跟踪信息
            tracking_file = os.path.join(self.storage_path, 'tracking.json')
            if os.path.exists(tracking_file):
                with open(tracking_file, 'r', encoding='utf-8') as f:
                    tracking_data = json.load(f)

                for source_name, data in tracking_data.items():
                    self.source_tracking[source_name] = SourceTrackingInfo(
                        source_name=data['source_name'],
                        last_collection_time=datetime.fromisoformat(data['last_collection_time']) if data['last_collection_time'] else None,
                        last_article_id=data['last_article_id'],
                        total_articles_collected=data['total_articles_collected'],
                        last_successful_collection=datetime.fromisoformat(data['last_successful_collection']) if data['last_successful_collection'] else None,
                        consecutive_failures=data['consecutive_failures'],
                        collection_stats=data['collection_stats']
                    )

            # 加载索引
            indexes_file = os.path.join(self.storage_path, 'indexes.json')
            if os.path.exists(indexes_file):
                with open(indexes_file, 'r', encoding='utf-8') as f:
                    indexes_data = json.load(f)

                self.url_index = indexes_data.get('url_index', {})
                self.title_source_index = {
                    k: set(v) for k, v in indexes_data.get('title_source_index', {}).items()
                }

            self.logger.info(f"加载了 {len(self.article_fingerprints)} 篇文章和 {len(self.source_tracking)} 个源的跟踪数据")

        except Exception as e:
            self.logger.error("加载数据失败", exc_info=e)

    async def _cleanup_expired_data(self):
        """清理过期数据"""
        # 计算15天前的截止时间
        cutoff_time = datetime.now() - timedelta(days=self.window_days)

        # 移除过期文章
        removed_count = self.remove_expired_articles(cutoff_time)

        if removed_count > 0:
            self.logger.info(f"清理完成，移除了 {removed_count} 篇过期文章")

        # 清理过期的收集统计（保留最近30天）
        stats_cutoff = datetime.now() - timedelta(days=30)
        for tracking_info in self.source_tracking.values():
            expired_stats = []
            for date_key in tracking_info.collection_stats:
                try:
                    stat_date = datetime.strptime(date_key, '%Y-%m-%d')
                    if stat_date < stats_cutoff:
                        expired_stats.append(date_key)
                except ValueError:
                    expired_stats.append(date_key)

            for date_key in expired_stats:
                del tracking_info.collection_stats[date_key]

    def export_data(self, export_path: str) -> bool:
        """导出数据"""
        try:
            export_data = {
                'fingerprints': {k: asdict(v) for k, v in self.article_fingerprints.items()},
                'source_tracking': {k: asdict(v) for k, v in self.source_tracking.items()},
                'url_index': self.url_index,
                'title_source_index': {k: list(v) for k, v in self.title_source_index.items()},
                'export_time': datetime.now().isoformat(),
                'statistics': self.get_statistics()
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"数据导出到: {export_path}")
            return True

        except Exception as e:
            self.logger.error("导出数据失败", exc_info=e)
            return False