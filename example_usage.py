"""
新闻收集代理使用示例
"""

import asyncio
import logging
from datetime import datetime, timedelta

from src.news_collection.news_agent import NewsCollectionAgent
from src.news_collection.models.base import (
    NewsSourceConfig,
    NewsQuery,
    NewsCategory,
    ConnectionPoolConfig,
    HealthCheckConfig,
    RetryPolicy
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def basic_usage_example():
    """基本使用示例"""
    print("=== 基本使用示例 ===")

    # 创建代理实例
    agent = NewsCollectionAgent(config_path="config/news_sources.yaml")

    try:
        # 初始化代理
        print("初始化新闻收集代理...")
        success = await agent.initialize()
        if not success:
            print("初始化失败")
            return

        print("初始化成功！")

        # 获取可用新闻源
        available_sources = await agent.get_available_sources()
        print(f"可用新闻源: {[s.name for s in available_sources]}")

        # 获取最新新闻
        print("\n获取最新新闻...")
        latest_news = await agent.get_latest_news(limit=10)
        print(f"获取到 {len(latest_news)} 条最新新闻")

        for i, article in enumerate(latest_news[:5], 1):
            print(f"{i}. {article.title}")
            print(f"   来源: {article.source}")
            print(f"   时间: {article.published_at}")
            print(f"   分类: {article.category.value}")
            print()

        # 搜索新闻
        print("\n搜索比特币相关新闻...")
        search_results = await agent.search_news(["比特币", "bitcoin"], limit=5)
        print(f"搜索到 {len(search_results)} 条相关新闻")

        for i, article in enumerate(search_results[:3], 1):
            print(f"{i}. {article.title}")
            print(f"   来源: {article.source}")
            print()

        # 获取统计信息
        print("\n统计信息:")
        stats = await agent.get_statistics()
        runtime_stats = stats["runtime_stats"]
        print(f"  运行时间: {runtime_stats['runtime_seconds']:.1f}秒")
        print(f"  总请求数: {runtime_stats['total_requests']}")
        print(f"  成功请求数: {runtime_stats['successful_requests']}")
        print(f"  失败请求数: {runtime_stats['failed_requests']}")
        print(f"  收集文章数: {runtime_stats['articles_collected']}")

    finally:
        # 关闭代理
        await agent.shutdown()
        print("\n代理已关闭")

async def advanced_usage_example():
    """高级使用示例"""
    print("\n=== 高级使用示例 ===")

    # 自定义配置
    pool_config = ConnectionPoolConfig(
        max_connections_per_source=3,
        connection_timeout=20,
        health_check_interval=15
    )

    health_config = HealthCheckConfig(
        check_interval=30,
        timeout=10,
        max_failures=3,
        enable_alerts=True
    )

    retry_policy = RetryPolicy(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0
    )

    # 创建代理实例
    agent = NewsCollectionAgent(
        config_path="config/news_sources.yaml",
        connection_pool_config=pool_config,
        health_check_config=health_config,
        retry_policy=retry_policy
    )

    try:
        print("初始化代理（自定义配置）...")
        success = await agent.initialize()
        if not success:
            print("初始化失败")
            return

        print("初始化成功！")

        # 复杂查询
        print("\n执行复杂查询...")
        complex_query = NewsQuery(
            keywords=["以太坊", "升级"],
            categories=[NewsCategory.TECHNOLOGY, NewsCategory.BREAKING],
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            limit=20
        )

        result = await agent.collect_news(complex_query)
        print(f"查询结果: {len(result.articles)} 篇文章")
        print(f"执行时间: {result.execution_time:.2f}ms")
        print(f"使用的新闻源: {result.sources_used}")

        if result.errors:
            print("错误信息:")
            for error in result.errors:
                print(f"  - {error}")

        # 健康状态检查
        print("\n健康状态:")
        health_status = await agent.get_health_status()
        monitoring_summary = health_status["monitoring_summary"]
        print(f"  总新闻源: {monitoring_summary['total_sources']}")
        print(f"  健康新闻源: {monitoring_summary['healthy_sources']}")
        print(f"  健康百分比: {monitoring_summary['health_percentage']:.1f}%")
        print(f"  活跃告警: {monitoring_summary['active_alerts']}")

        # 动态添加新闻源
        print("\n动态添加新闻源...")
        new_source = NewsSourceConfig(
            name="example_source",
            adapter_type="mock",  # 实际使用时应该是有效的适配器类型
            base_url="https://api.example.com",
            rate_limit=50,
            timeout=30,
            enabled=True,
            priority=3
        )

        # 注意：这里需要先实现一个mock适配器才能成功添加
        # success = await agent.add_news_source(new_source)
        # print(f"添加新闻源: {'成功' if success else '失败'}")

        # 错误历史
        print("\n错误历史:")
        error_history = await agent.get_error_history(limit=10)
        if error_history:
            for error in error_history:
                print(f"  {error['timestamp']}: {error['source_name']} - {error['message']}")
        else:
            print("  无错误记录")

    finally:
        await agent.shutdown()
        print("\n代理已关闭")

async def monitoring_example():
    """监控示例"""
    print("\n=== 监控示例 ===")

    agent = NewsCollectionAgent(config_path="config/news_sources.yaml")

    try:
        await agent.initialize()

        print("持续监控健康状态...")
        for i in range(5):
            health_status = await agent.get_health_status()
            monitoring_summary = health_status["monitoring_summary"]

            print(f"\n监控周期 {i+1}:")
            print(f"  健康源: {monitoring_summary['healthy_sources']}/{monitoring_summary['total_sources']}")
            print(f"  状态: {monitoring_summary['health_percentage']:.1f}%")
            print(f"  告警: {monitoring_summary['active_alerts']}")

            # 等待一段时间
            await asyncio.sleep(2)

    finally:
        await agent.shutdown()

async def performance_test():
    """性能测试示例"""
    print("\n=== 性能测试示例 ===")

    agent = NewsCollectionAgent(config_path="config/news_sources.yaml")

    try:
        await agent.initialize()

        # 并发请求测试
        print("执行并发请求测试...")
        num_requests = 10

        start_time = datetime.now()
        tasks = []

        for i in range(num_requests):
            task = agent.get_latest_news(limit=5)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()

        # 统计结果
        successful_requests = sum(1 for r in results if not isinstance(r, Exception))
        failed_requests = num_requests - successful_requests
        total_time = (end_time - start_time).total_seconds()

        print(f"并发请求数: {num_requests}")
        print(f"成功请求数: {successful_requests}")
        print(f"失败请求数: {failed_requests}")
        print(f"总时间: {total_time:.2f}秒")
        print(f"平均每请求时间: {total_time/num_requests:.3f}秒")
        print(f"吞吐量: {successful_requests/total_time:.2f} 请求/秒")

        # 获取最终统计
        stats = await agent.get_statistics()
        runtime_stats = stats["runtime_stats"]
        print(f"\n最终统计:")
        print(f"  总请求数: {runtime_stats['total_requests']}")
        print(f"  收集文章数: {runtime_stats['articles_collected']}")

    finally:
        await agent.shutdown()

async def main():
    """主函数"""
    print("新闻收集代理示例程序")
    print("=" * 50)

    # 运行基本示例
    await basic_usage_example()

    # 运行高级示例
    await advanced_usage_example()

    # 运行监控示例
    await monitoring_example()

    # 运行性能测试
    await performance_test()

    print("\n所有示例运行完成！")

if __name__ == "__main__":
    asyncio.run(main())