"""
Example usage of the multi-source news collection framework
"""

import asyncio
import logging
from datetime import datetime
from typing import List

from .orchestrator import CollectionOrchestrator
from ..models.base import NewsSourceConfig, NewsQuery, NewsCategory
from ..adapters.coindesk_adapter import CoinDeskAdapter
from ..adapters.cointelegraph_adapter import CoinTelegraphAdapter
from ..adapters.decrypt_adapter import DecryptAdapter


async def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def example_basic_collection():
    """基本收集示例"""
    print("=== 基本收集示例 ===")

    # 创建协调器
    orchestrator = CollectionOrchestrator()

    try:
        # 初始化
        await orchestrator.initialize()

        # 配置新闻源
        source_configs = [
            NewsSourceConfig(
                name="coindesk",
                adapter_type="coindesk",
                base_url="https://api.coindesk.com/v1",
                rate_limit=100,
                priority=9
            ),
            NewsSourceConfig(
                name="cointelegraph",
                adapter_type="cointelegraph",
                base_url="https://cointelegraph.com/api",
                rate_limit=80,
                priority=8
            ),
            NewsSourceConfig(
                name="decrypt",
                adapter_type="decrypt",
                base_url="https://decrypt.co/api",
                rate_limit=60,
                priority=7
            )
        ]

        # 注册适配器
        orchestrator.register_adapters_from_config(source_configs)

        # 启动收集
        await orchestrator.start_collection()

        # 执行收集
        result = await orchestrator.collect_news()

        print(f"收集到 {result.total_count} 篇文章")
        print(f"使用源: {result.sources_used}")
        print(f"执行时间: {result.execution_time:.2f}ms")

        if result.errors:
            print(f"错误: {result.errors}")

        # 显示前几篇文章
        for i, article in enumerate(result.articles[:3]):
            print(f"\n文章 {i+1}:")
            print(f"  标题: {article.title}")
            print(f"  来源: {article.source}")
            print(f"  分类: {article.category.value if article.category else 'Unknown'}")
            print(f"  发布时间: {article.published_at}")

    finally:
        await orchestrator.stop_collection()


async def example_scheduled_collection():
    """定时收集示例"""
    print("\n=== 定时收集示例 ===")

    orchestrator = CollectionOrchestrator()

    try:
        await orchestrator.initialize()

        # 注册适配器
        coindesk_config = NewsSourceConfig(
            name="coindesk",
            adapter_type="coindesk",
            base_url="https://api.coindesk.com/v1",
            priority=9
        )

        adapter = CoinDeskAdapter(coindesk_config)
        orchestrator.register_adapter(adapter)

        await orchestrator.start_collection()

        # 添加定时任务
        orchestrator.add_collection_job(
            job_id="hourly_coindesk",
            strategy_type="incremental",
            strategy_config={"max_articles_per_source": 50},
            schedule_type="interval",
            interval_minutes=60,
            enabled=True
        )

        print("定时任务已设置，每小时执行一次")

        # 获取任务列表
        jobs = orchestrator.get_collection_jobs()
        print(f"当前任务数: {len(jobs)}")

        # 手动执行任务
        result = await orchestrator.execute_scheduled_collection("hourly_coindesk")
        if result:
            print(f"手动执行收集到 {result.total_count} 篇文章")

        # 获取状态
        status = await orchestrator.get_collection_status()
        print(f"收集状态: {status['is_running']}")
        print(f"注册适配器数: {status['registered_adapters']}")

    finally:
        await orchestrator.stop_collection()


async def example_filtered_collection():
    """过滤收集示例"""
    print("\n=== 过滤收集示例 ===")

    orchestrator = CollectionOrchestrator()

    try:
        await orchestrator.initialize()

        # 注册多个适配器
        source_configs = [
            NewsSourceConfig(
                name="coindesk",
                adapter_type="coindesk",
                base_url="https://api.coindesk.com/v1",
                priority=9
            ),
            NewsSourceConfig(
                name="cointelegraph",
                adapter_type="cointelegraph",
                base_url="https://cointelegraph.com/api",
                priority=8
            )
        ]

        orchestrator.register_adapters_from_config(source_configs)
        await orchestrator.start_collection()

        # 创建查询
        query = NewsQuery(
            keywords=["Bitcoin", "Ethereum", "cryptocurrency"],
            categories=[NewsCategory.BREAKING, NewsCategory.MARKET_ANALYSIS],
            limit=100
        )

        # 执行带查询的收集
        result = await orchestrator.collect_news(query=query)

        print(f"查询收集到 {result.total_count} 篇文章")
        print(f"查询关键词: {query.keywords}")
        print(f"查询分类: {[cat.value for cat in query.categories]}")

        # 按来源分组显示
        by_source = {}
        for article in result.articles:
            source = article.source or "Unknown"
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(article)

        for source, articles in by_source.items():
            print(f"\n{source}: {len(articles)} 篇文章")

    finally:
        await orchestrator.stop_collection()


async def example_priority_based_collection():
    """基于优先级的收集示例"""
    print("\n=== 基于优先级的收集示例 ===")

    orchestrator = CollectionOrchestrator()

    try:
        await orchestrator.initialize()

        # 注册不同优先级的适配器
        high_priority_config = NewsSourceConfig(
            name="high_priority_source",
            adapter_type="coindesk",
            base_url="https://api.coindesk.com/v1",
            priority=9,
            rate_limit=120
        )

        low_priority_config = NewsSourceConfig(
            name="low_priority_source",
            adapter_type="decrypt",
            base_url="https://decrypt.co/api",
            priority=5,
            rate_limit=60
        )

        # 创建适配器实例
        high_adapter = CoinDeskAdapter(high_priority_config)
        low_adapter = DecryptAdapter(low_priority_config)

        orchestrator.register_adapter(high_adapter)
        orchestrator.register_adapter(low_adapter)

        await orchestrator.start_collection()

        # 执行基于优先级的收集
        result = await orchestrator.collect_news(strategy_type="priority_based")

        print(f"基于优先级收集到 {result.total_count} 篇文章")
        print(f"使用源: {result.sources_used}")

        # 获取收集状态以查看优先级信息
        status = await orchestrator.get_collection_status()
        if 'load_balancer_stats' in status and 'sources' in status['load_balancer_stats']:
            for source, stats in status['load_balancer_stats']['sources'].items():
                print(f"{source}: 权重={stats.get('weight', 0):.2f}, 当前负载={stats.get('current_load', 0):.2f}")

    finally:
        await orchestrator.stop_collection()


async def example_collection_statistics():
    """收集统计示例"""
    print("\n=== 收集统计示例 ===")

    orchestrator = CollectionOrchestrator()

    try:
        await orchestrator.initialize()

        # 注册适配器
        config = NewsSourceConfig(
            name="coindesk",
            adapter_type="coindesk",
            base_url="https://api.coindesk.com/v1",
            priority=8
        )

        adapter = CoinDeskAdapter(config)
        orchestrator.register_adapter(adapter)

        await orchestrator.start_collection()

        # 执行多次收集以生成统计数据
        for i in range(3):
            result = await orchestrator.collect_news()
            print(f"第{i+1}次收集: {result.total_count} 篇文章")
            await asyncio.sleep(1)  # 避免过于频繁的请求

        # 获取详细统计
        status = await orchestrator.get_collection_status()

        print("\n=== 收集统计 ===")
        print(f"运行状态: {status['is_running']}")
        print(f"注册适配器: {status['registered_adapters']}")

        if 'tracker_stats' in status:
            tracker_stats = status['tracker_stats']
            print(f"跟踪文章数: {tracker_stats.get('total_articles_tracked', 0)}")
            print(f"跟踪源数: {tracker_stats.get('total_sources_tracked', 0)}")

        if 'optimizer_stats' in status:
            optimizer_stats = status['optimizer_stats']
            if 'current_performance' in optimizer_stats:
                perf = optimizer_stats['current_performance']
                print(f"收集速度: {perf.get('collection_speed', 0):.1f} 文章/分钟")
                print(f"平均延迟: {perf.get('latency', 0):.1f}ms")

        if 'scheduler_stats' in status:
            scheduler_stats = status['scheduler_stats']
            print(f"总任务数: {scheduler_stats.get('total_jobs', 0)}")
            print(f"运行中任务: {scheduler_stats.get('running_jobs', 0)}")

    finally:
        await orchestrator.stop_collection()


async def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")

    orchestrator = CollectionOrchestrator()

    try:
        await orchestrator.initialize()

        # 配置无效的源
        invalid_config = NewsSourceConfig(
            name="invalid_source",
            adapter_type="coindesk",
            base_url="https://invalid-url.com/api",
            priority=5
        )

        adapter = CoinDeskAdapter(invalid_config)
        orchestrator.register_adapter(adapter)

        await orchestrator.start_collection()

        # 尝试收集，应该优雅地处理错误
        result = await orchestrator.collect_news()

        print(f"收集结果: {result.total_count} 篇文章")
        print(f"错误数: {len(result.errors)}")

        if result.errors:
            print("错误信息:")
            for error in result.errors:
                print(f"  - {error}")

        # 检查状态
        status = await orchestrator.get_collection_status()
        if 'adapter_status' in status:
            for adapter_id, adapter_status in status['adapter_status'].items():
                print(f"{adapter_id}: 连接状态={adapter_status.get('is_connected', False)}")

    finally:
        await orchestrator.stop_collection()


async def main():
    """主函数 - 运行所有示例"""
    await setup_logging()

    print("多源新闻收集框架示例")
    print("=" * 50)

    try:
        await example_basic_collection()
        await example_scheduled_collection()
        await example_filtered_collection()
        await example_priority_based_collection()
        await example_collection_statistics()
        await example_error_handling()

        print("\n所有示例运行完成！")

    except Exception as e:
        print(f"示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())