"""
Main entry point for the Data Collection Agent.

This module initializes and starts the data collection system.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional
from contextlib import asynccontextmanager

from .core.exchange_manager import ExchangeManager
from .core.data_collector import DataCollector, DataType
from .core.position_manager import PositionManager
from .config.settings import settings, DEFAULT_SYMBOLS
from .utils.metrics import MetricsCollector
from .utils.logger import setup_logger

# Global variables
exchange_manager: Optional[ExchangeManager] = None
data_collector: Optional[DataCollector] = None
position_manager: Optional[PositionManager] = None
metrics: Optional[MetricsCollector] = None
shutdown_event = asyncio.Event()

logger = logging.getLogger(__name__)


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def initialize_system():
    """Initialize all system components."""
    global exchange_manager, data_collector, position_manager, metrics

    logger.info("Initializing Data Collection Agent...")

    # Initialize metrics
    metrics = MetricsCollector()
    await metrics.start()

    # Initialize exchange manager
    if not settings.exchanges:
        logger.error("No exchange configurations found. Please check your environment variables.")
        return False

    exchange_manager = ExchangeManager(settings.exchanges)
    await exchange_manager.initialize()
    logger.info(f"Initialized {len(settings.exchanges)} exchanges")

    # Initialize position manager
    position_manager = PositionManager(exchange_manager)
    await position_manager.start()
    logger.info("Position manager started")

    # Initialize data collector
    data_collector = DataCollector(exchange_manager)

    # Set up data storage callbacks
    data_collector.add_data_callback(DataType.OHLCV, store_ohlcv_data)
    data_collector.add_data_callback(DataType.TICKER, store_ticker_data)
    data_collector.add_data_callback(DataType.ORDERBOOK, store_orderbook_data)
    data_collector.add_data_callback(DataType.TRADES, store_trades_data)

    # Add default collection tasks
    exchange_names = list(settings.exchanges.keys())
    data_collector.add_default_tasks(DEFAULT_SYMBOLS, exchange_names)

    await data_collector.start()
    logger.info("Data collector started")

    return True


async def store_ohlcv_data(data: dict):
    """Store OHLCV data (placeholder - would integrate with database)."""
    logger.debug(f"Storing OHLCV data for {data['symbol']} on {data['exchange']}")
    # TODO: Implement database storage


async def store_ticker_data(data: dict):
    """Store ticker data (placeholder - would integrate with database)."""
    logger.debug(f"Storing ticker data for {data['symbol']} on {data['exchange']}")
    # TODO: Implement database storage


async def store_orderbook_data(data: dict):
    """Store orderbook data (placeholder - would integrate with database)."""
    logger.debug(f"Storing orderbook data for {data['symbol']} on {data['exchange']}")
    # TODO: Implement database storage


async def store_trades_data(data: dict):
    """Store trades data (placeholder - would integrate with database)."""
    logger.debug(f"Storing trades data for {data['symbol']} on {data['exchange']}")
    # TODO: Implement database storage


async def run_system():
    """Main system loop."""
    global shutdown_event

    logger.info("Data Collection Agent is running...")

    try:
        # Main loop
        while not shutdown_event.is_set():
            try:
                # Print periodic status
                await asyncio.sleep(60)  # Status every minute

                if data_collector:
                    stats = data_collector.get_collection_stats()
                    logger.info(f"Collection stats: {stats}")

                if position_manager:
                    pos_stats = position_manager.get_stats()
                    logger.info(f"Position stats: {pos_stats}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)

    finally:
        await cleanup_system()


async def cleanup_system():
    """Cleanup all system components."""
    logger.info("Cleaning up Data Collection Agent...")

    global exchange_manager, data_collector, position_manager, metrics

    if data_collector:
        await data_collector.stop()
        logger.info("Data collector stopped")

    if position_manager:
        await position_manager.stop()
        logger.info("Position manager stopped")

    if exchange_manager:
        await exchange_manager.close_all()
        logger.info("Exchange connections closed")

    if metrics:
        await metrics.stop()
        logger.info("Metrics collector stopped")

    logger.info("Data Collection Agent shutdown complete")


async def main():
    """Main entry point."""
    # Setup logging
    setup_logger(settings.monitoring.log_level, settings.monitoring.log_file)

    # Setup signal handlers
    setup_signal_handlers()

    try:
        # Initialize system
        if await initialize_system():
            # Run system
            await run_system()
        else:
            logger.error("System initialization failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())