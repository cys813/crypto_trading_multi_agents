"""
默认配置文件 - 加密货币交易专用配置

基于原版TradingAgents配置，针对加密货币市场优化
"""

import os
from typing import Dict, Any

# 默认配置
DEFAULT_CONFIG: Dict[str, Any] = {
    # 基础配置
    "version": "0.1.0",
    "project_name": "Crypto Trading Agents",
    
    # LLM配置
    "llm_provider": "openai",
    "deep_think_llm": "gpt-4o",
    "quick_think_llm": "gpt-4o-mini",
    
    # 交易配置
    "trading_config": {
        "default_symbol": "BTC/USDT",
        "default_timeframe": "1h",
        "risk_per_trade": 0.02,  # 每笔交易风险2%
        "max_position_size": 0.1,  # 最大仓位10%
        "stop_loss": 0.05,  # 5%止损
        "take_profit": 0.15,  # 15%止盈
        "max_leverage": 3,  # 最大杠杆倍数
    },
    
    # 加密货币特定配置
    "crypto_config": {
        "supported_exchanges": ["binance", "coinbase", "ftx", "okx", "huobi"],
        "supported_chains": ["ethereum", "bitcoin", "solana", "polygon", "binance-smart-chain"],
        "defi_protocols": ["uniswap", "aave", "compound", "curve", "sushiswap"],
        "nft_marketplaces": ["opensea", "rarible", "foundation"],
    },
    
    # 分析配置
    "analysis_config": {
        "technical_indicators": [
            "rsi", "macd", "bollinger_bands", "ichimoku", "stochastic", "williams_r"
        ],
        "onchain_metrics": [
            "active_addresses", "transaction_count", "exchange_flows", "whale_transactions"
        ],
        "sentiment_sources": [
            "twitter", "reddit", "telegram", "discord", "news"
        ],
        "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
    },
    
    # 30天分层数据配置
    "layered_data_config": {
        "enabled": True,
        "total_days": 30,
        "layers": {
            "layer_1": {
                "days": 10,
                "timeframe": "4h",
                "description": "前10天 - 4小时K线数据"
            },
            "layer_2": {
                "days": 10,
                "timeframe": "1h",
                "description": "中间10天 - 1小时K线数据"
            },
            "layer_3": {
                "days": 10,
                "timeframe": "15m",
                "description": "最近10天 - 15分钟K线数据"
            }
        },
        "cache_settings": {
            "ttl_minutes": 60,
            "force_refresh": False,
            "auto_cleanup_days": 7
        },
        "data_quality": {
            "min_completeness": 80.0,
            "max_gap_hours": 4,
            "retry_on_failure": True
        }
    },
    
    # 研究深度配置
    "research_depth": {
        "1": {"time_minutes": 2, "description": "快速分析 - 基础技术指标"},
        "2": {"time_minutes": 3, "description": "基础分析 - 技术+基础情绪"},
        "3": {"time_minutes": 5, "description": "标准分析 - 技术+情绪+基础链上"},
        "4": {"time_minutes": 8, "description": "深度分析 - 全面技术+情绪+链上+DeFi"},
        "5": {"time_minutes": 12, "description": "全面分析 - 全维度+多轮辩论"},
    },
    
    # 数据源配置
    "data_sources": {
        "price_data": ["binance", "coinbase", "coingecko", "coinmarketcap"],
        "onchain_data": ["glassnode", "intotheblock", "nansen"],
        "defi_data": ["defillama", "debank", "zapper"],
        "news_data": ["cryptopanic", "coindesk", "cointelegraph"],
        "social_data": ["lunarcrush", "santiment"],
    },
    
    # 风险管理配置
    "risk_management": {
        "max_drawdown": 0.2,  # 最大回撤20%
        "max_concurrent_trades": 5,  # 最大同时交易数
        "correlation_limit": 0.7,  # 相关性限制
        "blacklist_symbols": [],  # 黑名单币种
        "circuit_breaker": {
            "enabled": True,
            "threshold": 0.1,  # 10%波动触发熔断
            "cooldown_minutes": 30,
        },
    },
    
    # 输出配置
    "output_config": {
        "include_charts": True,
        "include_onchain_data": True,
        "include_sentiment_analysis": True,
        "include_defi_analysis": True,
        "report_format": "markdown",
    },
    
    # 数据库配置
    "database_config": {
        "mongodb": {
            "enabled": os.getenv("MONGODB_ENABLED", "false").lower() == "true",
            "host": os.getenv("MONGODB_HOST", "localhost"),
            "port": int(os.getenv("MONGODB_PORT", 27017)),
            "database": "crypto_trading_agents",
            "username": os.getenv("MONGODB_USERNAME", ""),
            "password": os.getenv("MONGODB_PASSWORD", ""),
        },
        "redis": {
            "enabled": os.getenv("REDIS_ENABLED", "false").lower() == "true",
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", 6379)),
            "password": os.getenv("REDIS_PASSWORD", ""),
            "db": int(os.getenv("REDIS_DB", 0)),
        },
    },
    
    # API配置
    "api_config": {
        "binance": {
            "api_key": os.getenv("BINANCE_API_KEY", ""),
            "api_secret": os.getenv("BINANCE_API_SECRET", ""),
            "testnet": os.getenv("BINANCE_TESTNET", "false").lower() == "true",
        },
        "coingecko": {
            "api_key": os.getenv("COINGECKO_API_KEY", ""),
            "demo_mode": True,
        },
        "glassnode": {
            "api_key": os.getenv("GLASSNODE_API_KEY", ""),
        },
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
        },
        "anthropic": {
            "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        },
    },
    
    # 调试配置
    "debug": False,
    "verbose": False,
    "save_intermediate_results": False,
}

# 不同市场环境的配置预设
MARKET_PRESETS = {
    "bull_market": {
        "trading_config": {
            "risk_per_trade": 0.03,
            "take_profit": 0.25,
            "stop_loss": 0.08,
        },
        "analysis_config": {
            "focus": ["momentum", "sentiment", "onchain_adoption"],
        },
    },
    "bear_market": {
        "trading_config": {
            "risk_per_trade": 0.01,
            "take_profit": 0.08,
            "stop_loss": 0.03,
        },
        "analysis_config": {
            "focus": ["value", "risk_management", "defensive_strategies"],
        },
    },
    "sideways_market": {
        "trading_config": {
            "risk_per_trade": 0.015,
            "take_profit": 0.05,
            "stop_loss": 0.03,
        },
        "analysis_config": {
            "focus": ["range_trading", "mean_reversion", "breakout_patterns"],
        },
    },
    "high_volatility": {
        "trading_config": {
            "risk_per_trade": 0.01,
            "max_leverage": 1,
            "stop_loss": 0.02,
        },
        "risk_management": {
            "max_drawdown": 0.1,
            "circuit_breaker": {
                "threshold": 0.05,
            },
        },
    },
}

def get_config(market_condition: str = "normal") -> Dict[str, Any]:
    """
    获取配置，可以根据市场条件调整
    
    Args:
        market_condition: 市场条件 ('bull_market', 'bear_market', 'sideways_market', 'high_volatility')
    
    Returns:
        配置字典
    """
    config = DEFAULT_CONFIG.copy()
    
    if market_condition in MARKET_PRESETS:
        preset = MARKET_PRESETS[market_condition]
        
        # 深度合并配置
        def deep_merge(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_merge(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_merge(config, preset)
    
    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """
    验证配置的有效性
    
    Args:
        config: 配置字典
    
    Returns:
        是否有效
    """
    required_keys = [
        "llm_provider",
        "deep_think_llm",
        "quick_think_llm",
        "trading_config",
        "crypto_config",
    ]
    
    for key in required_keys:
        if key not in config:
            return False
    
    # 验证交易配置
    trading_config = config.get("trading_config", {})
    if trading_config.get("risk_per_trade", 0) <= 0:
        return False
    if trading_config.get("max_position_size", 0) <= 0:
        return False
    
    return True