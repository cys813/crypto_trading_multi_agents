"""
加密货币交易所配置文件

定义各种加密货币交易所的连接和交易参数
"""

# Binance 配置
BINANCE_CONFIG = {
    "name": "Binance",
    "api_base": "https://api.binance.com/api/v3",
    "futures_api_base": "https://fapi.binance.com/fapi/v1",
    "supports": {
        "spot": True,
        "futures": True,
        "margin": True,
        "staking": True,
        "savings": True,
    },
    "fees": {
        "spot_maker": 0.001,
        "spot_taker": 0.001,
        "futures_maker": 0.0002,
        "futures_taker": 0.0004,
    },
    "limits": {
        "max_leverage": 125,
        "min_order_size": 0.000001,
        "max_order_size": 1000000,
        "rate_limit": 1200,  # requests per minute
    },
    "symbols": [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT",
        "XRP/USDT", "DOT/USDT", "DOGE/USDT", "AVAX/USDT", "MATIC/USDT",
    ],
    "features": {
        "stop_loss": True,
        "take_profit": True,
        "oco_orders": True,
        "trailing_stop": True,
        "margin_trading": True,
    }
}

# Coinbase 配置
COINBASE_CONFIG = {
    "name": "Coinbase",
    "api_base": "https://api.coinbase.com/v2",
    "pro_api_base": "https://api.pro.coinbase.com",
    "supports": {
        "spot": True,
        "futures": False,
        "margin": False,
        "staking": True,
        "savings": False,
    },
    "fees": {
        "spot_maker": 0.004,
        "spot_taker": 0.006,
    },
    "limits": {
        "max_leverage": 1,
        "min_order_size": 0.000001,
        "max_order_size": 1000000,
        "rate_limit": 600,  # requests per minute
    },
    "symbols": [
        "BTC/USD", "ETH/USD", "SOL/USD", "ADA/USD", "DOT/USD",
        "MATIC/USD", "AVAX/USD", "LINK/USD", "UNI/USD", "LTC/USD",
    ],
    "features": {
        "stop_loss": True,
        "take_profit": True,
        "oco_orders": False,
        "trailing_stop": False,
        "margin_trading": False,
    }
}

# OKX 配置
OKX_CONFIG = {
    "name": "OKX",
    "api_base": "https://www.okx.com/api/v5",
    "supports": {
        "spot": True,
        "futures": True,
        "margin": True,
        "staking": True,
        "savings": True,
    },
    "fees": {
        "spot_maker": 0.0008,
        "spot_taker": 0.0015,
        "futures_maker": 0.0002,
        "futures_taker": 0.0005,
    },
    "limits": {
        "max_leverage": 125,
        "min_order_size": 0.000001,
        "max_order_size": 1000000,
        "rate_limit": 600,  # requests per minute
    },
    "symbols": [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "DOT/USDT", "AVAX/USDT",
        "MATIC/USDT", "UNI/USDT", "LINK/USDT", "ATOM/USDT", "ALGO/USDT",
    ],
    "features": {
        "stop_loss": True,
        "take_profit": True,
        "oco_orders": True,
        "trailing_stop": True,
        "margin_trading": True,
    }
}

# Kraken 配置
KRAKEN_CONFIG = {
    "name": "Kraken",
    "api_base": "https://api.kraken.com/0",
    "supports": {
        "spot": True,
        "futures": True,
        "margin": True,
        "staking": True,
        "savings": False,
    },
    "fees": {
        "spot_maker": 0.0016,
        "spot_taker": 0.0026,
        "futures_maker": 0.0002,
        "futures_taker": 0.0005,
    },
    "limits": {
        "max_leverage": 50,
        "min_order_size": 0.0001,
        "max_order_size": 1000000,
        "rate_limit": 300,  # requests per minute
    },
    "symbols": [
        "BTC/USD", "ETH/USD", "SOL/USD", "ADA/USD", "DOT/USD",
        "LINK/USD", "AVAX/USD", "MATIC/USD", "UNI/USD", "LTC/USD",
    ],
    "features": {
        "stop_loss": True,
        "take_profit": True,
        "oco_orders": True,
        "trailing_stop": True,
        "margin_trading": True,
    }
}

# Bybit 配置
BYBIT_CONFIG = {
    "name": "Bybit",
    "api_base": "https://api.bybit.com/v5",
    "supports": {
        "spot": True,
        "futures": True,
        "margin": True,
        "staking": False,
        "savings": False,
    },
    "fees": {
        "spot_maker": 0.001,
        "spot_taker": 0.001,
        "futures_maker": 0.0001,
        "futures_taker": 0.0006,
    },
    "limits": {
        "max_leverage": 100,
        "min_order_size": 0.000001,
        "max_order_size": 1000000,
        "rate_limit": 600,  # requests per minute
    },
    "symbols": [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "DOT/USDT", "AVAX/USDT",
        "MATIC/USDT", "LINK/USDT", "UNI/USDT", "ATOM/USDT", "NEAR/USDT",
    ],
    "features": {
        "stop_loss": True,
        "take_profit": True,
        "oco_orders": True,
        "trailing_stop": True,
        "margin_trading": True,
    }
}

# Gate.io 配置
GATEIO_CONFIG = {
    "name": "Gate.io",
    "api_base": "https://api.gate.io/api/v4",
    "supports": {
        "spot": True,
        "futures": True,
        "margin": True,
        "staking": True,
        "savings": True,
    },
    "fees": {
        "spot_maker": 0.001,
        "spot_taker": 0.001,
        "futures_maker": 0.0002,
        "futures_taker": 0.0005,
    },
    "limits": {
        "max_leverage": 100,
        "min_order_size": 0.000001,
        "max_order_size": 1000000,
        "rate_limit": 600,  # requests per minute
    },
    "symbols": [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "DOT/USDT", "AVAX/USDT",
        "MATIC/USDT", "LINK/USDT", "UNI/USDT", "ATOM/USDT", "ALGO/USDT",
    ],
    "features": {
        "stop_loss": True,
        "take_profit": True,
        "oco_orders": True,
        "trailing_stop": True,
        "margin_trading": True,
    }
}

# Huobi 配置
HUOBI_CONFIG = {
    "name": "Huobi",
    "api_base": "https://api.huobi.pro",
    "supports": {
        "spot": True,
        "futures": True,
        "margin": True,
        "staking": True,
        "savings": True,
    },
    "fees": {
        "spot_maker": 0.001,
        "spot_taker": 0.001,
        "futures_maker": 0.0002,
        "futures_taker": 0.0004,
    },
    "limits": {
        "max_leverage": 125,
        "min_order_size": 0.000001,
        "max_order_size": 1000000,
        "rate_limit": 1200,  # requests per minute
    },
    "symbols": [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "DOT/USDT", "AVAX/USDT",
        "MATIC/USDT", "LINK/USDT", "UNI/USDT", "ATOM/USDT", "ALGO/USDT",
    ],
    "features": {
        "stop_loss": True,
        "take_profit": True,
        "oco_orders": True,
        "trailing_stop": True,
        "margin_trading": True,
    }
}

# KuCoin 配置
KUCOIN_CONFIG = {
    "name": "KuCoin",
    "api_base": "https://api.kucoin.com",
    "supports": {
        "spot": True,
        "futures": True,
        "margin": True,
        "staking": True,
        "savings": True,
    },
    "fees": {
        "spot_maker": 0.001,
        "spot_taker": 0.001,
        "futures_maker": 0.0002,
        "futures_taker": 0.0006,
    },
    "limits": {
        "max_leverage": 100,
        "min_order_size": 0.000001,
        "max_order_size": 1000000,
        "rate_limit": 1800,  # requests per minute
    },
    "symbols": [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "DOT/USDT", "AVAX/USDT",
        "MATIC/USDT", "LINK/USDT", "UNI/USDT", "ATOM/USDT", "ALGO/USDT",
    ],
    "features": {
        "stop_loss": True,
        "take_profit": True,
        "oco_orders": True,
        "trailing_stop": True,
        "margin_trading": True,
    }
}

# 所有交易所配置
EXCHANGE_CONFIGS = {
    "binance": BINANCE_CONFIG,
    "coinbase": COINBASE_CONFIG,
    "okx": OKX_CONFIG,
    "kraken": KRAKEN_CONFIG,
    "bybit": BYBIT_CONFIG,
    "gateio": GATEIO_CONFIG,
    "huobi": HUOBI_CONFIG,
    "kucoin": KUCOIN_CONFIG,
}

# 推荐的交易所优先级
EXCHANGE_PRIORITY = [
    "binance",      # 最大的流动性，最多的交易对
    "okx",          # 良好的衍生品支持
    "bybit",        # 优秀的杠杆交易
    "huobi",        # 亚洲市场领先
    "kucoin",       # 多样化的代币支持
    "kraken",       # 欧美市场，安全性高
    "gateio",       # 新兴项目支持好
    "coinbase",     # 美国合规交易所
]

# 交易所风险评估
EXCHANGE_RISK_PROFILE = {
    "binance": {"risk_level": "low", "regulatory": "moderate", "security": "high"},
    "coinbase": {"risk_level": "low", "regulatory": "high", "security": "high"},
    "okx": {"risk_level": "medium", "regulatory": "moderate", "security": "high"},
    "kraken": {"risk_level": "low", "regulatory": "high", "security": "high"},
    "bybit": {"risk_level": "medium", "regulatory": "low", "security": "high"},
    "gateio": {"risk_level": "medium", "regulatory": "low", "security": "medium"},
    "huobi": {"risk_level": "medium", "regulatory": "moderate", "security": "high"},
    "kucoin": {"risk_level": "medium", "regulatory": "moderate", "security": "high"},
}

# 交易所连接测试配置
CONNECTION_TEST_CONFIG = {
    "timeout": 10,  # 秒
    "retry_attempts": 3,
    "test_symbol": "BTC/USDT",
    "test_amount": 0.001,
    "test_endpoints": [
        "/time",
        "/ticker/24hr",
        "/depth",
        "/trades",
    ]
}

# 交易所错误处理
ERROR_HANDLING_CONFIG = {
    "retry_codes": [429, 500, 502, 503, 504],
    "max_retries": 3,
    "retry_delay": 1,  # 秒
    "rate_limit_codes": [429],
    "rate_limit_delay": 60,  # 秒
    "invalid_symbol_codes": [400, 404],
    "insufficient_funds_codes": [400, 409],
}

# 交易所数据源优先级
DATA_SOURCE_PRIORITY = {
    "binance": 1,
    "okx": 2,
    "huobi": 3,
    "bybit": 4,
    "kraken": 5,
    "kucoin": 6,
    "gateio": 7,
    "coinbase": 8,
}

# 交易所API限制
API_LIMITS = {
    "binance": {"weight_limit": 1200, "minute_limit": 1200},
    "coinbase": {"weight_limit": 600, "minute_limit": 600},
    "okx": {"weight_limit": 600, "minute_limit": 600},
    "kraken": {"weight_limit": 300, "minute_limit": 300},
    "bybit": {"weight_limit": 600, "minute_limit": 600},
    "gateio": {"weight_limit": 600, "minute_limit": 600},
    "huobi": {"weight_limit": 1200, "minute_limit": 1200},
    "kucoin": {"weight_limit": 1800, "minute_limit": 1800},
}