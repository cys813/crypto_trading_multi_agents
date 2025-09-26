"""
Test script for processing pipeline integration
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from news_collection.processing.pipeline_manager import PipelineManager
from news_collection.processing.models import ProcessingConfig
from news_collection.models.base import NewsArticle, NewsCategory
from news_collection.collection.orchestrator import CollectionOrchestrator


async def test_basic_processing():
    """测试基本处理功能"""
    print("Testing basic processing pipeline...")

    # 创建处理管道
    config = ProcessingConfig()
    pipeline = PipelineManager(config)

    # 创建测试文章
    test_articles = [
        NewsArticle(
            id="test_001",
            title="Bitcoin Price Surges to New High",
            content="""
            Bitcoin, the world's largest cryptocurrency, has reached a new all-time high of $65,000
            as institutional investors continue to adopt digital assets. Major companies including
            Tesla and MicroStrategy have added Bitcoin to their balance sheets.

            The surge comes as regulatory clarity improves and mainstream acceptance grows.
            Analysts predict further growth as more institutions enter the market.
            """,
            summary="Bitcoin reaches new all-time high driven by institutional adoption.",
            author="John Smith",
            published_at=datetime.now(),
            source="coindesk.com",
            category=NewsCategory.GENERAL,
            tags=["bitcoin", "institutional", "adoption"]
        ),
        # 包含噪声的文章
        NewsArticle(
            id="noisy_001",
            title="Crypto News <script>alert('ads')</script>",
            content="""
            <p>Cryptocurrency markets show mixed signals today.</p>
            <div class="ad">Click here for special offers!!!</div>
            Bitcoin trading volume increased while Ethereum remained stable.
            免责声明：投资有风险，入市需谨慎。本文仅供参考，不构成投资建议。
            Visit https://scam-site.com for more info!!! AAAABBBBCCCC repeated characters.
            """,
            published_at=datetime.now(),
            source="unknown-source.com",
            category=NewsCategory.GENERAL
        )
    ]

    # 处理文章
    result = await pipeline.process_articles(test_articles)

    print(f"Processing completed:")
    print(f"  - Total articles: {len(result.articles)}")
    print(f"  - Successful: {result.stats.successful_articles}")
    print(f"  - Failed: {result.stats.failed_articles}")
    print(f"  - Skipped: {result.stats.skipped_articles}")
    print(f"  - Execution time: {result.execution_time:.2f}s")

    # 显示处理结果
    for i, processing_result in enumerate(result.processing_results):
        print(f"\nArticle {i+1} ({processing_result.article.id}):")
        print(f"  - Status: {processing_result.status.value}")
        print(f"  - Processing time: {processing_result.processing_time:.3f}s")
        print(f"  - Stages completed: {[s.value for s in processing_result.stages_completed]}")
        if processing_result.quality_score:
            print(f"  - Quality score: {processing_result.quality_score:.3f}")
        if processing_result.errors:
            print(f"  - Errors: {processing_result.errors}")

    # 检查健康状态
    health = await pipeline.health_check()
    print(f"\nPipeline health: {health['status']}")

    # 获取性能指标
    metrics = pipeline.get_performance_metrics()
    print(f"Performance metrics:")
    print(f"  - Throughput: {metrics['throughput']:.2f} articles/sec")
    print(f"  - Success rate: {metrics['success_rate']:.2%}")

    return True


async def test_orchestrator_integration():
    """测试协调器集成"""
    print("\nTesting orchestrator integration...")

    # 创建协调器
    orchestrator = CollectionOrchestrator()

    try:
        # 初始化协调器
        await orchestrator.initialize()

        # 检查处理管道状态
        status = await orchestrator.get_collection_status()
        if status.get('processing_pipeline_stats'):
            pipeline_stats = status['processing_pipeline_stats']
            print(f"Processing pipeline status: {pipeline_stats['status']}")
        else:
            print("Processing pipeline not initialized")

        # 测试配置处理阶段
        if orchestrator.processing_pipeline:
            print("\nTesting stage configuration...")
            success = orchestrator.enable_processing_stage('preprocessing', True)
            print(f"Enable preprocessing: {success}")

            success = orchestrator.enable_processing_stage('quality_scoring', True)
            print(f"Enable quality scoring: {success}")

        return True

    except Exception as e:
        print(f"Orchestrator test failed: {e}")
        return False

    finally:
        # 清理
        if orchestrator.is_initialized:
            await orchestrator.stop_collection()


async def main():
    """主测试函数"""
    print("Starting processing pipeline integration tests...\n")

    try:
        # 测试基本处理功能
        success1 = await test_basic_processing()

        # 测试协调器集成
        success2 = await test_orchestrator_integration()

        if success1 and success2:
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)