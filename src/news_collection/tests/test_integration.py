"""
集成测试 - 测试完整的新闻收集流程
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta

from news_collection.news_agent import NewsCollectionAgent
from news_collection.models.base import (
    NewsSourceConfig,
    NewsQuery,
    NewsArticle,
    NewsCategory,
    ConnectionPoolConfig,
    HealthCheckConfig,
    RetryPolicy
)


class TestNewsCollectionIntegration:
    """新闻收集集成测试"""

    @pytest.fixture
    def temp_config_file(self):
        """临时配置文件"""
        config_content = """
global_config:
  version: "1.0.0"
  default_timeout: 30
  max_retries: 3
  cache_enabled: true
  cache_ttl: 300
  log_level: "INFO"

sources:
  test_source_1:
    name: "test_source_1"
    adapter_type: "mock"
    base_url: "https://api.test1.com"
    rate_limit: 60
    timeout: 30
    enabled: true
    priority: 8

  test_source_2:
    name: "test_source_2"
    adapter_type: "mock"
    base_url: "https://api.test2.com"
    rate_limit: 100
    timeout: 30
    enabled: true
    priority: 7

  disabled_source:
    name: "disabled_source"
    adapter_type: "mock"
    base_url: "https://api.disabled.com"
    rate_limit: 50
    timeout: 30
    enabled: false
    priority: 1
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            yield f.name

        os.unlink(f.name)

    @pytest.fixture
    def agent_config(self):
        """代理配置"""
        return {
            'connection_pool_config': ConnectionPoolConfig(
                max_connections_per_source=3,
                connection_timeout=15,
                health_check_interval=10
            ),
            'health_check_config': HealthCheckConfig(
                check_interval=15,
                timeout=5,
                max_failures=2
            ),
            'retry_policy': RetryPolicy(
                max_attempts=2,
                base_delay=0.5,
                max_delay=5.0
            )
        }

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, temp_config_file, agent_config):
        """测试完整的生命周期"""
        agent = NewsCollectionAgent(
            config_path=temp_config_file,
            **agent_config
        )

        try:
            # 1. 初始化
            success = await agent.initialize()
            assert success, "代理初始化失败"

            # 2. 验证配置加载
            available_sources = await agent.get_available_sources()
            assert len(available_sources) == 2, "应该有2个可用新闻源"
            source_names = [s.name for s in available_sources]
            assert "test_source_1" in source_names
            assert "test_source_2" in source_names
            assert "disabled_source" not in source_names

            # 3. 验证健康状态
            health_status = await agent.get_health_status()
            assert "health_status" in health_status
            assert "monitoring_summary" in health_status
            assert "available_sources" in health_status

            # 4. 验证统计信息
            stats = await agent.get_statistics()
            assert "runtime_stats" in stats
            assert stats["runtime_stats"]["is_running"] == True
            assert stats["runtime_stats"]["total_requests"] == 0

            # 5. 模拟新闻收集（这里需要mock适配器行为）
            # 注意：实际测试中需要mock适配器或使用真实适配器

            # 6. 关闭
            await agent.shutdown()

            # 7. 验证关闭状态
            stats = await agent.get_statistics()
            assert stats["runtime_stats"]["is_running"] == False

        finally:
            if agent._running:
                await agent.shutdown()

    @pytest.mark.asyncio
    async def test_dynamic_source_management(self, temp_config_file, agent_config):
        """测试动态新闻源管理"""
        agent = NewsCollectionAgent(
            config_path=temp_config_file,
            **agent_config
        )

        try:
            await agent.initialize()

            # 添加新新闻源
            new_config = NewsSourceConfig(
                name="dynamic_source",
                adapter_type="mock",
                base_url="https://api.dynamic.com",
                rate_limit=75,
                timeout=25,
                enabled=True,
                priority=9
            )

            success = await agent.add_news_source(new_config)
            assert success, "添加新闻源失败"

            # 验证新源已添加
            available_sources = await agent.get_available_sources()
            source_names = [s.name for s in available_sources]
            assert "dynamic_source" in source_names

            # 移除新闻源
            success = await agent.remove_news_source("dynamic_source")
            assert success, "移除新闻源失败"

            # 验证源已移除
            available_sources = await agent.get_available_sources()
            source_names = [s.name for s in available_sources]
            assert "dynamic_source" not in source_names

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_error_handling(self, temp_config_file, agent_config):
        """测试错误处理"""
        agent = NewsCollectionAgent(
            config_path=temp_config_file,
            **agent_config
        )

        try:
            await agent.initialize()

            # 获取初始错误历史（应该为空）
            error_history = await agent.get_error_history()
            assert len(error_history) == 0

            # 这里可以测试特定的错误场景
            # 注意：实际测试中需要模拟错误条件

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, temp_config_file, agent_config):
        """测试性能监控"""
        agent = NewsCollectionAgent(
            config_path=temp_config_file,
            **agent_config
        )

        try:
            await agent.initialize()

            # 获取初始统计
            initial_stats = await agent.get_statistics()

            # 等待一段时间让监控数据收集
            await asyncio.sleep(2)

            # 获取更新后的统计
            updated_stats = await agent.get_statistics()

            # 验证统计信息结构
            assert "runtime_stats" in updated_stats
            assert "connection_stats" in updated_stats
            assert "error_stats" in updated_stats
            assert "config_stats" in updated_stats

            # 验证运行时间增加
            initial_runtime = initial_stats["runtime_stats"]["runtime_seconds"]
            updated_runtime = updated_stats["runtime_stats"]["runtime_seconds"]
            assert updated_runtime >= initial_runtime

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_configuration_reload(self, temp_config_file, agent_config):
        """测试配置重载"""
        agent = NewsCollectionAgent(
            config_path=temp_config_file,
            **agent_config
        )

        try:
            await agent.initialize()

            # 获取初始配置
            initial_sources = await agent.get_available_sources()
            initial_count = len(initial_sources)

            # 修改配置文件（这里简化处理，实际应该修改文件内容）
            # 注意：真实测试中应该修改配置文件并验证重载

            # 验证配置统计
            config_stats = await agent.config_manager.get_config_stats()
            assert "total_sources" in config_stats
            assert "enabled_sources" in config_stats

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, temp_config_file, agent_config):
        """测试并发操作"""
        agent = NewsCollectionAgent(
            config_path=temp_config_file,
            **agent_config
        )

        try:
            await agent.initialize()

            # 并发执行多个操作
            tasks = [
                agent.get_available_sources(),
                agent.get_health_status(),
                agent.get_statistics(),
                agent.get_error_history()
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 验证所有操作都成功完成
            for result in results:
                assert not isinstance(result, Exception), f"并发操作失败: {result}"

            # 验证结果类型
            assert isinstance(results[0], list)  # available_sources
            assert isinstance(results[1], dict)  # health_status
            assert isinstance(results[2], dict)  # statistics
            assert isinstance(results[3], list)  # error_history

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_memory_usage(self, temp_config_file, agent_config):
        """测试内存使用（简化版）"""
        import psutil
        import os

        agent = NewsCollectionAgent(
            config_path=temp_config_file,
            **agent_config
        )

        try:
            # 获取初始内存使用
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss

            await agent.initialize()

            # 执行一些操作
            await agent.get_available_sources()
            await agent.get_health_status()
            await agent.get_statistics()

            # 获取操作后内存使用
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # 内存增加应该在合理范围内（这里设置一个较大的阈值）
            assert memory_increase < 50 * 1024 * 1024, f"内存使用增加过多: {memory_increase / 1024 / 1024:.2f}MB"

        finally:
            await agent.shutdown()

    @pytest.mark.asyncio
    async def test_stress_testing(self, temp_config_file, agent_config):
        """压力测试（简化版）"""
        agent = NewsCollectionAgent(
            config_path=temp_config_file,
            **agent_config
        )

        try:
            await agent.initialize()

            # 并发执行大量请求
            num_requests = 50
            tasks = []

            for i in range(num_requests):
                task = agent.get_available_sources()
                tasks.append(task)

            start_time = datetime.now()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = datetime.now()

            # 验证所有请求都成功
            successful_requests = sum(1 for r in results if not isinstance(r, Exception))
            assert successful_requests == num_requests, f"部分请求失败: {num_requests - successful_requests}/{num_requests}"

            # 验证响应时间
            total_time = (end_time - start_time).total_seconds()
            avg_time_per_request = total_time / num_requests
            assert avg_time_per_request < 1.0, f"平均响应时间过长: {avg_time_per_request:.3f}s"

        finally:
            await agent.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])