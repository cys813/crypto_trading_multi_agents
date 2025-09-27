"""
Tests for cache manager module
"""

import pytest
import asyncio
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from ..cache_manager import (
    CacheManager, CacheConfig, CacheEntry, CacheStats,
    CacheLevel, CacheStrategy
)
from ...models.base import NewsArticle


class TestCacheConfig:
    """测试缓存配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = CacheConfig()
        assert config.cache_level == CacheLevel.HYBRID
        assert config.strategy == CacheStrategy.LRU
        assert config.max_memory_entries == 1000
        assert config.max_disk_entries == 10000
        assert config.default_ttl == 3600
        assert config.disk_cache_path == "./cache"
        assert config.enable_compression is True
        assert config.enable_persistence is True
        assert config.cleanup_interval == 300
        assert config.max_entry_size == 1024 * 1024
        assert config.enable_stats is True
        assert config.enable_background_cleanup is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = CacheConfig(
            cache_level=CacheLevel.MEMORY,
            strategy=CacheStrategy.LFU,
            max_memory_entries=500,
            max_disk_entries=5000,
            default_ttl=1800,
            disk_cache_path="/tmp/cache",
            enable_compression=False,
            enable_persistence=False,
            cleanup_interval=600,
            max_entry_size=512 * 1024
        )
        assert config.cache_level == CacheLevel.MEMORY
        assert config.strategy == CacheStrategy.LFU
        assert config.max_memory_entries == 500
        assert config.max_disk_entries == 5000
        assert config.default_ttl == 1800
        assert config.disk_cache_path == "/tmp/cache"
        assert config.enable_compression is False
        assert config.enable_persistence is False
        assert config.cleanup_interval == 600
        assert config.max_entry_size == 512 * 1024


class TestCacheEntry:
    """测试缓存条目类"""

    def test_entry_creation(self):
        """测试条目创建"""
        now = datetime.now()
        entry = CacheEntry(
            key="test-key",
            value="test-value",
            created_at=now,
            expires_at=now + timedelta(hours=1),
            size=100
        )
        assert entry.key == "test-key"
        assert entry.value == "test-value"
        assert entry.created_at == now
        assert entry.expires_at == now + timedelta(hours=1)
        assert entry.access_count == 0
        assert entry.last_accessed == now
        assert entry.size == 100
        assert entry.metadata == {}

    def test_entry_with_metadata(self):
        """测试带元数据的条目"""
        now = datetime.now()
        metadata = {"source": "test", "type": "analysis"}

        entry = CacheEntry(
            key="test-key",
            value={"data": "test"},
            created_at=now,
            expires_at=now + timedelta(hours=2),
            access_count=5,
            last_accessed=now + timedelta(minutes=10),
            size=200,
            metadata=metadata
        )
        assert entry.access_count == 5
        assert entry.last_accessed == now + timedelta(minutes=10)
        assert entry.size == 200
        assert entry.metadata == metadata


class TestCacheManager:
    """测试缓存管理器"""

    @pytest.fixture
    def temp_cache_dir(self):
        """临时缓存目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def cache_config(self, temp_cache_dir):
        """缓存配置"""
        return CacheConfig(
            cache_level=CacheLevel.HYBRID,
            strategy=CacheStrategy.LRU,
            max_memory_entries=10,
            max_disk_entries=20,
            default_ttl=60,  # 短TTL用于测试
            disk_cache_path=temp_cache_dir,
            enable_compression=False,  # 禁用压缩以便测试
            enable_background_cleanup=False,  # 禁用后台清理
            enable_persistence=False  # 禁用持久化以便测试
        )

    @pytest.fixture
    def cache_manager(self, cache_config):
        """缓存管理器实例"""
        return CacheManager(cache_config)

    @pytest.fixture
    def sample_article(self):
        """示例文章"""
        return NewsArticle(
            id="test-article-1",
            title="Test Article",
            content="This is a test article content for caching.",
            source="Test Source",
            published_at=datetime.now()
        )

    def test_init(self, cache_manager, cache_config):
        """测试初始化"""
        assert cache_manager.config == cache_config
        assert isinstance(cache_manager.memory_cache, dict)
        assert len(cache_manager.memory_cache) == 0
        assert cache_manager.disk_cache_path.exists()
        assert cache_manager.stats.total_requests == 0
        assert cache_manager.stats.cache_hits == 0
        assert cache_manager.stats.cache_misses == 0

    def test_generate_cache_key_for_string(self, cache_manager):
        """测试为字符串生成缓存键"""
        key = cache_manager._generate_cache_key("test data", "prefix")
        assert isinstance(key, str)
        assert "prefix_" in key
        assert len(key) > len("prefix_")  # 应该包含哈希值

    def test_generate_cache_key_for_dict(self, cache_manager):
        """测试为字典生成缓存键"""
        data = {"key": "value", "number": 42}
        key = cache_manager._generate_cache_key(data)
        assert isinstance(key, str)

        # 相同数据应该生成相同键
        key2 = cache_manager._generate_cache_key({"key": "value", "number": 42})
        assert key == key2

    def test_generate_cache_key_for_article(self, cache_manager, sample_article):
        """测试为文章生成缓存键"""
        key = cache_manager._generate_cache_key(sample_article, "sentiment")
        assert isinstance(key, str)
        assert "sentiment_article" in key
        assert sample_article.id in key

    def test_get_entry_size(self, cache_manager):
        """测试获取条目大小"""
        size = cache_manager._get_entry_size("small data")
        assert isinstance(size, int)
        assert size > 0

        large_data = "x" * 1000
        large_size = cache_manager._get_entry_size(large_data)
        assert large_size > size

    def test_is_expired(self, cache_manager):
        """测试过期检查"""
        now = datetime.now()

        # 未过期的条目
        valid_entry = CacheEntry(
            key="valid",
            value="data",
            created_at=now,
            expires_at=now + timedelta(hours=1)
        )
        assert cache_manager._is_expired(valid_entry) is False

        # 已过期的条目
        expired_entry = CacheEntry(
            key="expired",
            value="data",
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1)
        )
        assert cache_manager._is_expired(expired_entry) is True

    def test_should_evict_memory(self, cache_manager):
        """测试内存缓存是否需要清理"""
        # 初始状态不需要清理
        assert cache_manager._should_evict() is False

        # 填充内存缓存到极限
        for i in range(cache_manager.config.max_memory_entries + 1):
            cache_manager.memory_cache[f"key_{i}"] = CacheEntry(
                key=f"key_{i}",
                value=f"value_{i}",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=1)
            )

        # 现在应该需要清理
        assert cache_manager._should_evict() is True

    def test_should_evict_disk(self, cache_manager, temp_cache_dir):
        """测试磁盘缓存是否需要清理"""
        # 创建一些缓存文件
        for i in range(cache_manager.config.max_disk_entries + 1):
            file_path = Path(temp_cache_dir) / f"key_{i}.cache"
            file_path.write_text(f"data_{i}")

        # 现在应该需要清理
        assert cache_manager._should_evict() is True

    def test_evict_lru(self, cache_manager):
        """测试LRU清理策略"""
        now = datetime.now()

        # 创建多个条目，不同的最后访问时间
        old_entry = CacheEntry(
            key="old",
            value="old_data",
            created_at=now - timedelta(minutes=10),
            expires_at=now + timedelta(hours=1),
            last_accessed=now - timedelta(minutes=5)
        )

        new_entry = CacheEntry(
            key="new",
            value="new_data",
            created_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(hours=1),
            last_accessed=now
        )

        cache_manager.memory_cache["old"] = old_entry
        cache_manager.memory_cache["new"] = new_entry

        # 模拟需要清理的情况
        cache_manager.config.max_memory_entries = 1

        # 执行LRU清理
        cache_manager._evict_lru()

        # 应该移除最旧的条目
        assert "old" not in cache_manager.memory_cache
        assert "new" in cache_manager.memory_cache

    def test_evict_lfu(self, cache_manager):
        """测试LFU清理策略"""
        now = datetime.now()

        # 创建多个条目，不同的访问次数
        rare_entry = CacheEntry(
            key="rare",
            value="rare_data",
            created_at=now,
            expires_at=now + timedelta(hours=1),
            access_count=1
        )

        frequent_entry = CacheEntry(
            key="frequent",
            value="frequent_data",
            created_at=now,
            expires_at=now + timedelta(hours=1),
            access_count=10
        )

        cache_manager.memory_cache["rare"] = rare_entry
        cache_manager.memory_cache["frequent"] = frequent_entry

        # 模拟需要清理的情况
        cache_manager.config.max_memory_entries = 1
        cache_manager.config.strategy = CacheStrategy.LFU

        # 执行LFU清理
        cache_manager._evict_lfu()

        # 应该移除最少使用的条目
        assert "rare" not in cache_manager.memory_cache
        assert "frequent" in cache_manager.memory_cache

    def test_set_and_get_memory_cache(self, cache_manager):
        """测试内存缓存的设置和获取"""
        # 设置缓存
        cache_manager.set("test_key", "test_value", ttl=60)

        # 获取缓存
        value = cache_manager.get("test_key")
        assert value == "test_value"

        # 验证统计信息
        assert cache_manager.stats.total_requests == 1
        assert cache_manager.stats.cache_hits == 1
        assert cache_manager.stats.cache_misses == 0
        assert cache_manager.stats.hit_rate == 1.0

    def test_get_cache_miss(self, cache_manager):
        """测试缓存未命中"""
        value = cache_manager.get("nonexistent_key")
        assert value is None

        # 验证统计信息
        assert cache_manager.stats.total_requests == 1
        assert cache_manager.stats.cache_hits == 0
        assert cache_manager.stats.cache_misses == 1
        assert cache_manager.stats.hit_rate == 0.0

    def test_set_with_ttl(self, cache_manager):
        """测试设置TTL"""
        # 设置短TTL
        cache_manager.set("short_ttl_key", "value", ttl=1)

        # 立即获取应该成功
        value = cache_manager.get("short_ttl_key")
        assert value == "value"

        # 等待过期
        time.sleep(1.1)

        # 现在应该获取不到
        value = cache_manager.get("short_ttl_key")
        assert value is None

    def test_delete_cache_entry(self, cache_manager):
        """测试删除缓存条目"""
        # 设置缓存
        cache_manager.set("delete_key", "delete_value")

        # 验证存在
        assert cache_manager.get("delete_key") == "delete_value"

        # 删除
        cache_manager.delete("delete_key")

        # 验证已删除
        assert cache_manager.get("delete_key") is None

    def test_exists_cache_entry(self, cache_manager):
        """测试检查缓存条目是否存在"""
        # 设置缓存
        cache_manager.set("exists_key", "exists_value")

        # 检查存在
        assert cache_manager.exists("exists_key") is True

        # 检查不存在
        assert cache_manager.exists("nonexistent_key") is False

    def test_clear_cache(self, cache_manager):
        """测试清空缓存"""
        # 设置多个缓存
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        cache_manager.set("key3", "value3")

        # 清空缓存
        cache_manager.clear()

        # 验证所有缓存都被清空
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
        assert cache_manager.get("key3") is None
        assert len(cache_manager.memory_cache) == 0

    def test_get_stats(self, cache_manager):
        """测试获取统计信息"""
        # 执行一些操作
        cache_manager.set("key1", "value1")
        cache_manager.get("key1")  # hit
        cache_manager.get("key2")  # miss

        stats = cache_manager.get_stats()
        assert isinstance(stats, dict)
        assert "total_requests" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "hit_rate" in stats
        assert stats["total_requests"] == 2
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_cache_key_for_article(self, cache_manager, sample_article):
        """测试文章缓存键生成"""
        key = cache_manager.get_cache_key_for_article(sample_article, "sentiment")
        assert isinstance(key, str)
        assert "sentiment_article" in key
        assert sample_article.id in key

    def test_cache_key_for_batch(self, cache_manager):
        """测试批量缓存键生成"""
        articles = [
            NewsArticle(id="art1", title="Article 1", content="Content 1"),
            NewsArticle(id="art2", title="Article 2", content="Content 2")
        ]

        key = cache_manager.get_cache_key_for_batch(articles, "batch_summary")
        assert isinstance(key, str)
        assert "batch_summary_batch" in key

    def test_cache_analysis_result(self, cache_manager, sample_article):
        """测试缓存分析结果"""
        result = {"summary": "Test summary", "confidence": 0.8}

        # 缓存单个文章分析结果
        cache_manager.cache_analysis_result(sample_article, "summary", result, ttl=60)

        # 获取缓存的分析结果
        cached_result = cache_manager.get_cached_analysis_result(sample_article, "summary")
        assert cached_result == result

    def test_cache_batch_analysis_result(self, cache_manager):
        """测试缓存批量分析结果"""
        articles = [
            NewsArticle(id="art1", title="Article 1", content="Content 1"),
            NewsArticle(id="art2", title="Article 2", content="Content 2")
        ]
        result = {"summaries": ["Summary 1", "Summary 2"], "total": 2}

        # 缓存批量分析结果
        cache_manager.cache_analysis_result(articles, "batch_summary", result, ttl=60)

        # 获取缓存的批量分析结果
        cached_result = cache_manager.get_cached_analysis_result(articles, "batch_summary")
        assert cached_result == result

    def test_invalidate_article_cache(self, cache_manager, sample_article):
        """测试使文章缓存失效"""
        # 缓存不同类型的分析结果
        cache_manager.cache_analysis_result(sample_article, "summary", {"summary": "test"})
        cache_manager.cache_analysis_result(sample_article, "sentiment", {"sentiment": "positive"})

        # 验证缓存存在
        assert cache_manager.get_cached_analysis_result(sample_article, "summary") is not None
        assert cache_manager.get_cached_analysis_result(sample_article, "sentiment") is not None

        # 使缓存失效
        cache_manager.invalidate_article_cache(sample_article.id)

        # 验证缓存已失效
        assert cache_manager.get_cached_analysis_result(sample_article, "summary") is None
        assert cache_manager.get_cached_analysis_result(sample_article, "sentiment") is None

    def test_max_entry_size_enforcement(self, cache_manager):
        """测试最大条目大小限制"""
        # 创建超过大小限制的数据
        large_data = "x" * (cache_manager.config.max_entry_size + 1)

        # 尝试缓存大条目（应该被拒绝）
        cache_manager.set("large_key", large_data)

        # 验证没有被缓存
        assert cache_manager.get("large_key") is None

    def test_update_config(self, cache_manager):
        """测试更新配置"""
        new_config = CacheConfig(
            cache_level=CacheLevel.MEMORY,
            max_memory_entries=50,
            strategy=CacheStrategy.FIFO
        )

        cache_manager.update_config(new_config)
        assert cache_manager.config.cache_level == CacheLevel.MEMORY
        assert cache_manager.config.max_memory_entries == 50
        assert cache_manager.config.strategy == CacheStrategy.FIFO

    @pytest.mark.asyncio
    async def test_background_cleanup(self, cache_manager):
        """测试后台清理"""
        # 设置短TTL的缓存
        cache_manager.set("expire_soon", "value", ttl=1)

        # 启动后台清理
        cache_manager.start_background_cleanup()
        assert cache_manager.is_running is True

        # 等待清理
        await asyncio.sleep(1.1)

        # 停止后台清理
        cache_manager.stop_background_cleanup()
        assert cache_manager.is_running is False

        # 验证过期条目被清理
        assert cache_manager.get("expire_soon") is None

    def test_cleanup_expired_entries(self, cache_manager):
        """测试清理过期条目"""
        now = datetime.now()

        # 添加过期条目
        expired_entry = CacheEntry(
            key="expired",
            value="expired_value",
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1)
        )
        cache_manager.memory_cache["expired"] = expired_entry

        # 添加有效条目
        valid_entry = CacheEntry(
            key="valid",
            value="valid_value",
            created_at=now,
            expires_at=now + timedelta(hours=1)
        )
        cache_manager.memory_cache["valid"] = valid_entry

        # 执行清理
        cache_manager._cleanup_expired_entries()

        # 验证过期条目被删除，有效条目保留
        assert "expired" not in cache_manager.memory_cache
        assert "valid" in cache_manager.memory_cache
        assert cache_manager.stats.total_evictions > 0

    def test_disk_cache_operations(self, cache_manager):
        """测试磁盘缓存操作"""
        # 临时启用磁盘缓存
        original_config = cache_manager.config
        cache_manager.config.cache_level = CacheLevel.DISK

        # 设置缓存
        cache_manager.set("disk_key", "disk_value", ttl=60)

        # 验证文件存在
        disk_files = list(cache_manager.disk_cache_path.glob("*.cache"))
        assert len(disk_files) > 0

        # 从磁盘获取
        value = cache_manager.get("disk_key")
        assert value == "disk_value"

        # 删除磁盘缓存
        cache_manager.delete("disk_key")

        # 验证文件被删除
        value = cache_manager.get("disk_key")
        assert value is None

        # 恢复原始配置
        cache_manager.config = original_config

    def test_hybrid_cache_operations(self, cache_manager):
        """测试混合缓存操作"""
        # 临时启用混合缓存
        original_config = cache_manager.config
        cache_manager.config.cache_level = CacheLevel.HYBRID

        # 设置缓存
        cache_manager.set("hybrid_key", "hybrid_value", ttl=60)

        # 验证在内存中
        assert "hybrid_key" in cache_manager.memory_cache

        # 验证在磁盘上
        disk_files = list(cache_manager.disk_cache_path.glob("*.cache"))
        assert len(disk_files) > 0

        # 获取缓存
        value = cache_manager.get("hybrid_key")
        assert value == "hybrid_value"

        # 恢复原始配置
        cache_manager.config = original_config

    def test_compression_enabled(self, temp_cache_dir):
        """测试启用压缩"""
        config = CacheConfig(
            cache_level=CacheLevel.MEMORY,
            disk_cache_path=temp_cache_dir,
            enable_compression=True,
            max_entry_size=1024 * 1024
        )
        cache_manager = CacheManager(config)

        # 设置大型数据
        large_data = "x" * 10000
        cache_manager.set("compressed_key", large_data)

        # 获取数据
        retrieved_data = cache_manager.get("compressed_key")
        assert retrieved_data == large_data

    def test_error_handling(self, cache_manager):
        """测试错误处理"""
        # 测试无效键
        assert cache_manager.get(None) is None
        assert cache_manager.exists(None) is False

        # 测试设置None值
        cache_manager.set("none_key", None)
        assert cache_manager.get("none_key") is None

    def test_shutdown(self, cache_manager):
        """测试关闭"""
        # 设置一些缓存
        cache_manager.set("shutdown_key", "shutdown_value")

        # 关闭缓存管理器
        cache_manager.shutdown()

        # 验证后台清理已停止
        assert cache_manager.is_running is False

    def test_memory_cache_only(self, temp_cache_dir):
        """测试仅内存缓存"""
        config = CacheConfig(
            cache_level=CacheLevel.MEMORY,
            disk_cache_path=temp_cache_dir,
            max_memory_entries=5
        )
        cache_manager = CacheManager(config)

        # 设置缓存
        cache_manager.set("mem_key", "mem_value")

        # 验证在内存中
        assert "mem_key" in cache_manager.memory_cache

        # 验证不在磁盘上
        disk_files = list(cache_manager.disk_cache_path.glob("*.cache"))
        assert len(disk_files) == 0

        # 获取缓存
        value = cache_manager.get("mem_key")
        assert value == "mem_value"

    def test_disk_cache_only(self, temp_cache_dir):
        """测试仅磁盘缓存"""
        config = CacheConfig(
            cache_level=CacheLevel.DISK,
            disk_cache_path=temp_cache_dir,
            max_memory_entries=5
        )
        cache_manager = CacheManager(config)

        # 设置缓存
        cache_manager.set("disk_only_key", "disk_only_value")

        # 验证不在内存中
        assert "disk_only_key" not in cache_manager.memory_cache

        # 验证在磁盘上
        disk_files = list(cache_manager.disk_cache_path.glob("*.cache"))
        assert len(disk_files) > 0

        # 获取缓存
        value = cache_manager.get("disk_only_key")
        assert value == "disk_only_value"


if __name__ == "__main__":
    pytest.main([__file__])