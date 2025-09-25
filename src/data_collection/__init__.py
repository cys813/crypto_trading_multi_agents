"""
Data Collection Agent for Cryptocurrency Multi-Agent Trading System

This package provides comprehensive data collection capabilities across multiple
cryptocurrency exchanges using the CCXT library.
"""

__version__ = "1.0.0"
__author__ = "Crypto Trading Multi-Agents Team"

from .core.exchange_manager import ExchangeManager
from .core.data_collector import DataCollector
from .core.position_manager import PositionManager
from .core.order_manager import OrderManager
from .core.data_processor import DataProcessor

__all__ = [
    "ExchangeManager",
    "DataCollector",
    "PositionManager",
    "OrderManager",
    "DataProcessor"
]