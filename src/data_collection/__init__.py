"""
Data Collection Agent Module

This module provides comprehensive data collection functionality for cryptocurrency trading,
including market data, position information, order management, and data processing.
"""

from .core.exchange_manager import ExchangeManager
from .core.data_collector import DataCollector
from .core.position_manager import PositionManager
from .core.order_manager import OrderManager
from .core.data_processor import DataProcessor

__version__ = "1.0.0"
__author__ = "Crypto Trading Multi-Agents System"

__all__ = [
    "ExchangeManager",
    "DataCollector",
    "PositionManager",
    "OrderManager",
    "DataProcessor"
]