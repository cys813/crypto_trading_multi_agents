"""
Crypto Trading Agents - 专业虚拟货币多智能体量化交易框架

基于TradingAgents-CN架构，专为加密货币市场设计的多智能体AI交易系统。
"""

__version__ = "0.1.0"
__author__ = "Crypto Trading Agents Team"
__email__ = "contact@crypto-trading-agents.com"

from .graph.crypto_trading_graph import CryptoTradingGraph
from .default_config import DEFAULT_CONFIG

__all__ = [
    "CryptoTradingGraph",
    "DEFAULT_CONFIG",
]