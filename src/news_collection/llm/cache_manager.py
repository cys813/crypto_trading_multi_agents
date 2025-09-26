"""
Result caching system for LLM analysis results
"""

import logging
import time
import json
import hashlib
import pickle
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
from pathlib import Path

from ..models.base import NewsArticle


class CacheLevel(Enum):
    """缓存级别枚举"""
    MEMORY = "memory"
    DISK = "disk"
    HYBRID = "hybrid"


class CacheStrategy(Enum):
    """缓存策略枚举"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用频率
    FIFO = "fifo"  # 先进先出
    TTL = "ttl"  # 基于生存时间


@dataclass
class CacheConfig:
    """缓存配置"""
    cache_level: CacheLevel = CacheLevel.HYBRID
    strategy: CacheStrategy = CacheStrategy.LRU
    max_memory_entries: int = 1000
    max_disk_entries: int = 10000
    default_ttl: int = 3600  # 1 hour in seconds
    disk_cache_path: str = "./cache"
    enable_compression: bool = True
    enable_persistence: bool = True
    cleanup_interval: int = 300  # 5 minutes
    max_entry_size: int = 1024 * 1024  # 1MB
    enable_stats: bool = True
    enable_background_cleanup: bool = True


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = None
    size: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CacheStats:
    """缓存统计"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_evictions: int = 0
    memory_entries: int = 0
    disk_entries: int = 0
    total_size: int = 0
    hit_rate: float = 0.0
    average_access_time: float = 0.0
    last_cleanup_time: datetime = None


class CacheManager:
    """缓存管理器"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats = CacheStats()

        # 内存缓存
        self.memory_cache: Dict[str, CacheEntry] = {}

        # 磁盘缓存路径
        self.disk_cache_path = Path(config.disk_cache_path)
        self.disk_cache_path.mkdir(parents=True, exist_ok=True)

        # 锁机制
        self.memory_lock = threading.RLock()
        self.disk_lock = threading.RLock()

        # 后任务
        self.cleanup_task = None
        self.is_running = False

        # 初始化
        self._initialize_cache()

    def _initialize_cache(self):
        """初始化缓存"""
        if self.config.enable_persistence:
            self._load_disk_cache()

        if self.config.enable_background_cleanup:
            self.start_background_cleanup()

    def _generate_cache_key(self, data: Any, prefix: str = "") -> str:
        """生成缓存键"""
        try:
            # 序列化数据
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, sort_keys=True)
            elif isinstance(data, str):
                data_str = data
            elif isinstance(data, NewsArticle):
                # 为文章生成专门的关键键
                article_data = {
                    "id": data.id,
                    "title": data.title,
                    "content_hash": hashlib.md5(data.content.encode()).hexdigest(),
                    "source": data.source,
                    "published_at": data.published_at.isoformat() if data.published_at else None
                }
                data_str = json.dumps(article_data, sort_keys=True)
            else:
                data_str = str(data)

            # 生成哈希
            hash_obj = hashlib.md5(data_str.encode())
            cache_key = f"{prefix}_{hash_obj.hexdigest()}" if prefix else hash_obj.hexdigest()

            return cache_key

        except Exception as e:
            self.logger.error(f"Error generating cache key: {str(e)}")
            # 降级到简单哈希
            return f"{prefix}_{hash(str(data).encode())}"

    def _get_entry_size(self, value: Any) -> int:
        """获取条目大小"""
        try:
            if self.config.enable_compression:
                # 使用pickle序列化并压缩
                import zlib
                data = pickle.dumps(value)
                compressed = zlib.compress(data)
                return len(compressed)
            else:
                return len(pickle.dumps(value))
        except Exception:
            return len(str(value).encode())

    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查条目是否过期"""
        return datetime.now() > entry.expires_at

    def _should_evict(self) -> bool:
        """检查是否需要清理条目"""
        if self.config.cache_level == CacheLevel.MEMORY:
            return len(self.memory_cache) >= self.config.max_memory_entries
        elif self.config.cache_level == CacheLevel.DISK:
            return len(self._get_disk_cache_files()) >= self.config.max_disk_entries
        else:  # HYBRID
            return (len(self.memory_cache) >= self.config.max_memory_entries or
                   len(self._get_disk_cache_files()) >= self.config.max_disk_entries)

    def _evict_entries(self):
        """清理条目"""
        if self.config.strategy == CacheStrategy.LRU:
            self._evict_lru()
        elif self.config.strategy == CacheStrategy.LFU:
            self._evict_lfu()
        elif self.config.strategy == CacheStrategy.FIFO:
            self._evict_fifo()
        elif self.config.strategy == CacheStrategy.TTL:
            self._evict_ttl()

    def _evict_lru(self):
        """LRU清理策略"""
        if self.config.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
            with self.memory_lock:
                if self.memory_cache:
                    # 按最后访问时间排序
                    sorted_entries = sorted(self.memory_cache.values(), key=lambda x: x.last_accessed)
                    # 移除最旧的20%
                    entries_to_remove = sorted_entries[:max(1, len(sorted_entries) // 5)]
                    for entry in entries_to_remove:
                        del self.memory_cache[entry.key]
                        self.stats.total_evictions += 1

        if self.config.cache_level in [CacheLevel.DISK, CacheLevel.HYBRID]:
            self._evict_disk_lru()

    def _evict_disk_lru(self):
        """磁盘LRU清理"""
        with self.disk_lock:
            disk_files = self._get_disk_cache_files()
            if len(disk_files) >= self.config.max_disk_entries:
                # 按文件修改时间排序
                sorted_files = sorted(disk_files, key=lambda x: x.stat().st_mtime)
                # 移除最旧的20%
                files_to_remove = sorted_files[:max(1, len(sorted_files) // 5)]
                for file_path in files_to_remove:
                    try:
                        file_path.unlink()
                        self.stats.total_evictions += 1
                    except Exception as e:
                        self.logger.error(f"Error removing disk cache file {file_path}: {str(e)}")

    def _evict_lfu(self):
        """LFU清理策略"""
        if self.config.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
            with self.memory_lock:
                if self.memory_cache:
                    # 按访问次数排序
                    sorted_entries = sorted(self.memory_cache.values(), key=lambda x: x.access_count)
                    # 移除最少使用的20%
                    entries_to_remove = sorted_entries[:max(1, len(sorted_entries) // 5)]
                    for entry in entries_to_remove:
                        del self.memory_cache[entry.key]
                        self.stats.total_evictions += 1

    def _evict_fifo(self):
        """FIFO清理策略"""
        if self.config.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
            with self.memory_lock:
                if self.memory_cache:
                    # 按创建时间排序
                    sorted_entries = sorted(self.memory_cache.values(), key=lambda x: x.created_at)
                    # 移除最旧的20%
                    entries_to_remove = sorted_entries[:max(1, len(sorted_entries) // 5)]
                    for entry in entries_to_remove:
                        del self.memory_cache[entry.key]
                        self.stats.total_evictions += 1

    def _evict_ttl(self):
        """TTL清理策略"""
        self._cleanup_expired_entries()

    def _cleanup_expired_entries(self):
        """清理过期条目"""
        current_time = datetime.now()

        # 清理内存缓存
        if self.config.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
            with self.memory_lock:
                expired_keys = []
                for key, entry in self.memory_cache.items():
                    if current_time > entry.expires_at:
                        expired_keys.append(key)

                for key in expired_keys:
                    del self.memory_cache[key]
                    self.stats.total_evictions += 1

        # 清理磁盘缓存
        if self.config.cache_level in [CacheLevel.DISK, CacheLevel.HYBRID]:
            with self.disk_lock:
                for file_path in self.disk_cache_path.glob("*.cache"):
                    try:
                        stat = file_path.stat()
                        file_age = datetime.fromtimestamp(stat.st_mtime)
                        entry_key = file_path.stem

                        # 检查是否过期
                        if current_time - file_age > timedelta(seconds=self.config.default_ttl):
                            file_path.unlink()
                            self.stats.total_evictions += 1
                    except Exception as e:
                        self.logger.error(f"Error cleaning up disk cache file {file_path}: {str(e)}")

    def _get_disk_cache_files(self) -> List[Path]:
        """获取磁盘缓存文件列表"""
        try:
            return list(self.disk_cache_path.glob("*.cache"))
        except Exception:
            return []

    def _get_disk_cache_path(self, key: str) -> Path:
        """获取磁盘缓存文件路径"""
        return self.disk_cache_path / f"{key}.cache"

    def _save_to_disk(self, key: str, entry: CacheEntry):
        """保存到磁盘"""
        if self.config.cache_level not in [CacheLevel.DISK, CacheLevel.HYBRID]:
            return

        file_path = self._get_disk_cache_path(key)

        try:
            with self.disk_lock:
                if self.config.enable_compression:
                    import zlib
                    data = pickle.dumps(entry)
                    compressed = zlib.compress(data)
                    file_path.write_bytes(compressed)
                else:
                    file_path.write_bytes(pickle.dumps(entry))

        except Exception as e:
            self.logger.error(f"Error saving to disk cache: {str(e)}")

    def _load_from_disk(self, key: str) -> Optional[CacheEntry]:
        """从磁盘加载"""
        if self.config.cache_level not in [CacheLevel.DISK, CacheLevel.HYBRID]:
            return None

        file_path = self._get_disk_cache_path(key)

        try:
            with self.disk_lock:
                if not file_path.exists():
                    return None

                if self.config.enable_compression:
                    import zlib
                    compressed = file_path.read_bytes()
                    data = zlib.decompress(compressed)
                    entry = pickle.loads(data)
                else:
                    entry = pickle.loads(file_path.read_bytes())

                # 检查是否过期
                if self._is_expired(entry):
                    file_path.unlink()
                    self.stats.total_evictions += 1
                    return None

                return entry

        except Exception as e:
            self.logger.error(f"Error loading from disk cache: {str(e)}")
            return None

    def _load_disk_cache(self):
        """加载磁盘缓存"""
        if not self.config.enable_persistence:
            return

        self.logger.info("Loading disk cache...")

        try:
            with self.disk_lock:
                for file_path in self.disk_cache_path.glob("*.cache"):
                    try:
                        if self.config.enable_compression:
                            import zlib
                            compressed = file_path.read_bytes()
                            data = zlib.decompress(compressed)
                            entry = pickle.loads(data)
                        else:
                            entry = pickle.loads(file_path.read_bytes())

                        # 只加载未过期的条目
                        if not self._is_expired(entry):
                            # 如果是混合模式，也加载到内存
                            if self.config.cache_level == CacheLevel.HYBRID and len(self.memory_cache) < self.config.max_memory_entries:
                                self.memory_cache[entry.key] = entry
                    except Exception as e:
                        self.logger.error(f"Error loading cache file {file_path}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error loading disk cache: {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        start_time = time.time()
        self.stats.total_requests += 1

        try:
            # 首先检查内存缓存
            if self.config.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
                with self.memory_lock:
                    if key in self.memory_cache:
                        entry = self.memory_cache[key]

                        # 检查是否过期
                        if self._is_expired(entry):
                            del self.memory_cache[key]
                            self.stats.total_evictions += 1
                        else:
                            # 更新访问信息
                            entry.access_count += 1
                            entry.last_accessed = datetime.now()
                            self.stats.cache_hits += 1
                            self._update_access_time(time.time() - start_time)
                            return entry.value

            # 然后检查磁盘缓存
            if self.config.cache_level in [CacheLevel.DISK, CacheLevel.HYBRID]:
                entry = self._load_from_disk(key)
                if entry:
                    # 更新访问信息
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()

                    # 如果是混合模式，也缓存到内存
                    if self.config.cache_level == CacheLevel.HYBRID:
                        with self.memory_lock:
                            if len(self.memory_cache) < self.config.max_memory_entries:
                                self.memory_cache[key] = entry

                    self.stats.cache_hits += 1
                    self._update_access_time(time.time() - start_time)
                    return entry.value

            # 缓存未命中
            self.stats.cache_misses += 1
            self._update_access_time(time.time() - start_time)
            return default

        except Exception as e:
            self.logger.error(f"Error getting from cache: {str(e)}")
            self.stats.cache_misses += 1
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None):
        """设置缓存值"""
        try:
            # 检查条目大小
            entry_size = self._get_entry_size(value)
            if entry_size > self.config.max_entry_size:
                self.logger.warning(f"Cache entry too large: {entry_size} bytes")
                return

            # 创建缓存条目
            current_time = datetime.now()
            entry_ttl = ttl or self.config.default_ttl
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=current_time,
                expires_at=current_time + timedelta(seconds=entry_ttl),
                size=entry_size,
                metadata=metadata or {}
            )

            # 检查是否需要清理
            if self._should_evict():
                self._evict_entries()

            # 保存到内存缓存
            if self.config.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
                with self.memory_lock:
                    self.memory_cache[key] = entry

            # 保存到磁盘缓存
            if self.config.cache_level in [CacheLevel.DISK, CacheLevel.HYBRID]:
                self._save_to_disk(key, entry)

            # 更新统计
            self.stats.total_size += entry_size
            if self.config.cache_level == CacheLevel.MEMORY:
                self.stats.memory_entries = len(self.memory_cache)
            elif self.config.cache_level == CacheLevel.DISK:
                self.stats.disk_entries = len(self._get_disk_cache_files())
            else:  # HYBRID
                self.stats.memory_entries = len(self.memory_cache)
                self.stats.disk_entries = len(self._get_disk_cache_files())

        except Exception as e:
            self.logger.error(f"Error setting cache: {str(e)}")

    def delete(self, key: str):
        """删除缓存值"""
        try:
            # 从内存缓存删除
            if self.config.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
                with self.memory_lock:
                    if key in self.memory_cache:
                        entry = self.memory_cache[key]
                        del self.memory_cache[key]
                        self.stats.total_size -= entry.size

            # 从磁盘缓存删除
            if self.config.cache_level in [CacheLevel.DISK, CacheLevel.HYBRID]:
                file_path = self._get_disk_cache_path(key)
                if file_path.exists():
                    file_path.unlink()

        except Exception as e:
            self.logger.error(f"Error deleting cache: {str(e)}")

    def clear(self):
        """清空缓存"""
        try:
            # 清空内存缓存
            if self.config.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
                with self.memory_lock:
                    self.memory_cache.clear()
                    self.stats.memory_entries = 0

            # 清空磁盘缓存
            if self.config.cache_level in [CacheLevel.DISK, CacheLevel.HYBRID]:
                with self.disk_lock:
                    for file_path in self.disk_cache_path.glob("*.cache"):
                        file_path.unlink()
                    self.stats.disk_entries = 0

            self.stats.total_size = 0
            self.logger.info("Cache cleared")

        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            # 检查内存缓存
            if self.config.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
                with self.memory_lock:
                    if key in self.memory_cache:
                        entry = self.memory_cache[key]
                        if not self._is_expired(entry):
                            return True
                        else:
                            del self.memory_cache[key]

            # 检查磁盘缓存
            if self.config.cache_level in [CacheLevel.DISK, CacheLevel.HYBRID]:
                entry = self._load_from_disk(key)
                if entry:
                    return True

            return False

        except Exception:
            return False

    def _update_access_time(self, access_time: float):
        """更新访问时间统计"""
        if self.stats.total_requests > 0:
            total_time = self.stats.average_access_time * (self.stats.total_requests - 1)
            total_time += access_time
            self.stats.average_access_time = total_time / self.stats.total_requests

        # 更新命中率
        total_requests = self.stats.cache_hits + self.stats.cache_misses
        if total_requests > 0:
            self.stats.hit_rate = self.stats.cache_hits / total_requests

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.memory_lock:
            memory_size = sum(entry.size for entry in self.memory_cache.values())

        disk_size = 0
        if self.config.cache_level in [CacheLevel.DISK, CacheLevel.HYBRID]:
            try:
                with self.disk_lock:
                    for file_path in self.disk_cache_path.glob("*.cache"):
                        disk_size += file_path.stat().st_size
            except Exception:
                pass

        return {
            "total_requests": self.stats.total_requests,
            "cache_hits": self.stats.cache_hits,
            "cache_misses": self.stats.cache_misses,
            "hit_rate": self.stats.hit_rate,
            "total_evictions": self.stats.total_evictions,
            "memory_entries": self.stats.memory_entries,
            "disk_entries": self.stats.disk_entries,
            "memory_size": memory_size,
            "disk_size": disk_size,
            "total_size": self.stats.total_size,
            "average_access_time": self.stats.average_access_time,
            "config": {
                "cache_level": self.config.cache_level.value,
                "strategy": self.config.strategy.value,
                "max_memory_entries": self.config.max_memory_entries,
                "max_disk_entries": self.config.max_disk_entries,
                "default_ttl": self.config.default_ttl,
                "enable_compression": self.config.enable_compression
            }
        }

    def start_background_cleanup(self):
        """启动后台清理"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.is_running = True
            self.cleanup_task = asyncio.create_task(self._background_cleanup_loop())
            self.logger.info("Background cleanup started")

    def stop_background_cleanup(self):
        """停止后台清理"""
        self.is_running = False
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
        self.logger.info("Background cleanup stopped")

    async def _background_cleanup_loop(self):
        """后台清理循环"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                if self.is_running:
                    self._cleanup_expired_entries()
                    self.stats.last_cleanup_time = datetime.now()
                    self.logger.debug("Background cleanup completed")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in background cleanup: {str(e)}")

    def update_config(self, config: CacheConfig):
        """更新配置"""
        self.config = config
        self.logger.info("Cache configuration updated")

        # 重新初始化
        self._initialize_cache()

    def shutdown(self):
        """关闭缓存管理器"""
        self.stop_background_cleanup()

        # 保存内存缓存到磁盘
        if self.config.enable_persistence and self.config.cache_level == CacheLevel.HYBRID:
            with self.memory_lock:
                for key, entry in self.memory_cache.items():
                    self._save_to_disk(key, entry)

        self.logger.info("Cache manager shutdown completed")

    def get_cache_key_for_article(self, article: NewsArticle, analysis_type: str) -> str:
        """为文章分析生成缓存键"""
        return self._generate_cache_key(article, f"{analysis_type}_article")

    def get_cache_key_for_batch(self, articles: List[NewsArticle], analysis_type: str) -> str:
        """为批量分析生成缓存键"""
        # 生成批量数据的哈希
        batch_data = {
            "article_count": len(articles),
            "article_ids": [article.id for article in articles],
            "analysis_type": analysis_type
        }
        return self._generate_cache_key(batch_data, f"{analysis_type}_batch")

    def cache_analysis_result(self, articles: Union[NewsArticle, List[NewsArticle]],
                            analysis_type: str, result: Any, ttl: Optional[int] = None):
        """缓存分析结果"""
        if isinstance(articles, list):
            if len(articles) == 1:
                key = self.get_cache_key_for_article(articles[0], analysis_type)
            else:
                key = self.get_cache_key_for_batch(articles, analysis_type)
        else:
            key = self.get_cache_key_for_article(articles, analysis_type)

        metadata = {
            "analysis_type": analysis_type,
            "article_count": len(articles) if isinstance(articles, list) else 1,
            "cached_at": datetime.now().isoformat()
        }

        self.set(key, result, ttl, metadata)

    def get_cached_analysis_result(self, articles: Union[NewsArticle, List[NewsArticle]],
                                 analysis_type: str) -> Optional[Any]:
        """获取缓存的分析结果"""
        if isinstance(articles, list):
            if len(articles) == 1:
                key = self.get_cache_key_for_article(articles[0], analysis_type)
            else:
                key = self.get_cache_key_for_batch(articles, analysis_type)
        else:
            key = self.get_cache_key_for_article(articles, analysis_type)

        return self.get(key)

    def invalidate_article_cache(self, article_id: str):
        """使文章缓存失效"""
        # 由于键是基于完整内容生成的，我们需要查找所有相关的键
        # 这是一个简化实现，实际可能需要维护索引
        if self.config.cache_level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
            with self.memory_lock:
                keys_to_remove = []
                for key in self.memory_cache.keys():
                    if article_id in key:
                        keys_to_remove.append(key)

                for key in keys_to_remove:
                    del self.memory_cache[key]

        # 类似地清理磁盘缓存
        if self.config.cache_level in [CacheLevel.DISK, CacheLevel.HYBRID]:
            with self.disk_lock:
                for file_path in self.disk_cache_path.glob("*.cache"):
                    if article_id in file_path.stem:
                        try:
                            file_path.unlink()
                        except Exception:
                            pass

        self.logger.info(f"Invalidated cache for article {article_id}")