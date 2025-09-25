#!/usr/bin/env python3
"""
Example usage of the News Collection Manager.

This script demonstrates how to use the news collection framework
to fetch news from multiple cryptocurrency news sources.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from news_collection.news_manager import NewsCollectionManager
from news_collection.models import NewsCategory, NewsSourceType


async def main():
    """Main example function."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Create news collection manager
    manager = NewsCollectionManager()

    try:
        # Initialize with custom configuration
        config = {
            "sources": [
                {
                    "name": "CoinDesk",
                    "source_type": NewsSourceType.COINDESK,
                    "base_url": "https://api.coindesk.com/v1",
                    "rate_limit_per_minute": 30,
                    "timeout_seconds": 30,
                    "enabled": True,
                    "priority": 1,
                },
                {
                    "name": "CoinTelegraph",
                    "source_type": NewsSourceType.COINTELEGRAPH,
                    "base_url": "https://cointelegraph.com/api/v1",
                    "rate_limit_per_minute": 30,
                    "timeout_seconds": 30,
                    "enabled": True,
                    "priority": 2,
                },
                {
                    "name": "Decrypt",
                    "source_type": NewsSourceType.DECRYPT,
                    "base_url": "https://api.decrypt.co/v1",
                    "rate_limit_per_minute": 30,
                    "timeout_seconds": 30,
                    "enabled": True,
                    "priority": 3,
                },
            ]
        }

        logger.info("Initializing News Collection Manager...")
        await manager.initialize(config)

        # Display available sources
        logger.info(f"Available sources: {manager.available_sources}")

        # Test connections to all sources
        logger.info("Testing connections...")
        connection_status = await manager.get_connection_status()
        for source_name, status in connection_status.items():
            logger.info(f"{source_name}: {'Connected' if status.is_connected else 'Disconnected'} "
                       f"({status.response_time_ms:.2f}ms)")

        # Get health summary
        logger.info("Getting health summary...")
        health_summary = await manager.get_health_summary()
        for source_name, summary in health_summary.items():
            logger.info(f"{source_name}: {summary['uptime_percentage']:.1f}% uptime, "
                       f"{summary['average_response_time_ms']:.1f}ms avg response")

        # Manual news collection
        logger.info("Collecting news from all sources...")
        latest_articles = await manager.fetch_news(limit=10)
        logger.info(f"Collected {len(latest_articles)} latest articles")

        # Display some articles
        for i, article in enumerate(latest_articles[:3]):
            logger.info(f"\nArticle {i+1}:")
            logger.info(f"  Title: {article.title}")
            logger.info(f"  Source: {article.source.value}")
            logger.info(f"  Category: {article.category.value}")
            logger.info(f"  Published: {article.published_at}")
            logger.info(f"  URL: {article.url}")
            if article.summary:
                logger.info(f"  Summary: {article.summary}")

        # Filter by category
        logger.info("\nFetching market news only...")
        market_news = await manager.fetch_news(
            limit=5,
            categories=[NewsCategory.MARKET_NEWS]
        )
        logger.info(f"Found {len(market_news)} market news articles")

        # Search for specific topics
        logger.info("\nSearching for Bitcoin-related news...")
        bitcoin_news = await manager.search_news("bitcoin", limit=5)
        logger.info(f"Found {len(bitcoin_news)} Bitcoin-related articles")

        # Start automated collection
        logger.info("Starting automated news collection...")
        await manager.start_collection(interval_seconds=60)  # Collect every minute

        # Let it run for a few minutes
        logger.info("Running for 2 minutes...")
        await asyncio.sleep(120)

        # Stop collection
        logger.info("Stopping automated collection...")
        await manager.stop_collection()

        # Show final statistics
        logger.info(f"\nFinal Statistics:")
        logger.info(f"Total articles collected: {manager.total_articles_collected}")
        logger.info(f"Current latest articles: {len(manager.latest_articles)}")

        # Check for any health alerts
        alerts = manager.get_active_alerts()
        if alerts:
            logger.warning(f"Active alerts: {len(alerts)}")
            for alert in alerts:
                logger.warning(f"  {alert.severity}: {alert.source_name} - {alert.message}")
        else:
            logger.info("No active health alerts")

    except Exception as e:
        logger.error(f"Error in example: {str(e)}")
        raise

    finally:
        # Clean up
        logger.info("Cleaning up...")
        await manager.close()


async def demo_adapter_usage():
    """Demonstrate direct adapter usage."""
    logger = logging.getLogger(__name__)

    from news_collection.models import NewsSource, NewsSourceType
    from news_collection.adapters import CoinDeskAdapter

    # Create a source configuration
    source_config = NewsSource(
        name="CoinDesk Demo",
        source_type=NewsSourceType.COINDESK,
        base_url="https://api.coindesk.com/v1",
        rate_limit_per_minute=30,
        timeout_seconds=30
    )

    # Create adapter
    adapter = CoinDeskAdapter(source_config)

    try:
        # Initialize adapter
        await adapter.initialize()

        # Test connection
        logger.info("Testing CoinDesk connection...")
        status = await adapter.test_connection()
        logger.info(f"Connection status: {'Connected' if status.is_connected else 'Disconnected'}")

        if status.is_connected:
            # Fetch news
            logger.info("Fetching latest news...")
            articles = await adapter.fetch_news(limit=5)
            logger.info(f"Fetched {len(articles)} articles")

            # Display articles
            for i, article in enumerate(articles[:2]):
                logger.info(f"\nArticle {i+1}:")
                logger.info(f"  Title: {article.title}")
                logger.info(f"  Published: {article.published_at}")
                logger.info(f"  Category: {article.category.value}")

    finally:
        # Clean up
        await adapter.close()


if __name__ == "__main__":
    print("News Collection Framework Example")
    print("=" * 40)

    # Run main example
    asyncio.run(main())

    print("\n" + "=" * 40)
    print("Direct Adapter Usage Example")
    print("=" * 40)

    # Run adapter demo
    asyncio.run(demo_adapter_usage())