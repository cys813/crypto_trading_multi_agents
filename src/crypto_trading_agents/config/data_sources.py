"""
数据源配置文件

定义各种数据源的配置和连接参数
"""

# 价格数据源配置
PRICE_DATA_SOURCES = {
    "coingecko": {
        "name": "CoinGecko",
        "api_base": "https://api.coingecko.com/api/v3",
        "api_key_required": False,
        "rate_limit": 50,  # requests per minute
        "endpoints": {
            "price": "/simple/price",
            "market_chart": "/coins/{id}/market_chart",
            "ohlc": "/coins/{id}/ohlc",
            "ticker": "/coins/markets",
        },
        "features": {
            "historical_data": True,
            "real_time_data": False,
            "market_cap": True,
            "volume_data": True,
        },
        "coverage": {
            "cryptocurrencies": 10000+,
            "exchanges": 500+,
            "currencies": 50+,
        }
    },
    "coinmarketcap": {
        "name": "CoinMarketCap",
        "api_base": "https://pro-api.coinmarketcap.com/v1",
        "api_key_required": True,
        "rate_limit": 333,  # requests per day for free tier
        "endpoints": {
            "price": "/cryptocurrency/listings/latest",
            "market_chart": "/cryptocurrency/quotes/historical",
            "ohlc": "/cryptocurrency/ohlcv/historical",
            "ticker": "/cryptocurrency/listings/latest",
        },
        "features": {
            "historical_data": True,
            "real_time_data": True,
            "market_cap": True,
            "volume_data": True,
        },
        "coverage": {
            "cryptocurrencies": 8000+,
            "exchanges": 400+,
            "currencies": 50+,
        }
    },
    "binance": {
        "name": "Binance",
        "api_base": "https://api.binance.com/api/v3",
        "api_key_required": False,
        "rate_limit": 1200,
        "endpoints": {
            "price": "/ticker/price",
            "market_chart": "/klines",
            "ohlc": "/klines",
            "ticker": "/ticker/24hr",
        },
        "features": {
            "historical_data": True,
            "real_time_data": True,
            "market_cap": False,
            "volume_data": True,
        },
        "coverage": {
            "cryptocurrencies": 300+,
            "exchanges": 1,
            "currencies": 10+,
        }
    }
}

# 链上数据源配置
ONCHAIN_DATA_SOURCES = {
    "glassnode": {
        "name": "Glassnode",
        "api_base": "https://api.glassnode.com/api/v1",
        "api_key_required": True,
        "rate_limit": 100,
        "endpoints": {
            "active_addresses": "/metrics/addresses/active_count",
            "hash_rate": "/metrics/mining/hash_rate_mean",
            "exchange_flows": "/metrics/transactions/transfers_to_exchanges_sum",
            "whale_activity": "/metrics/entities/miner_to_exchanges_flow",
        },
        "features": {
            "btc_data": True,
            "eth_data": True,
            "defi_data": True,
            "exchange_data": True,
        },
        "coverage": {
            "cryptocurrencies": ["BTC", "ETH"],
            "metrics": 200+,
            "historical_depth": "2010+",
        }
    },
    "intotheblock": {
        "name": "IntoTheBlock",
        "api_base": "https://api.intotheblock.com",
        "api_key_required": True,
        "rate_limit": 100,
        "endpoints": {
            "in_out_money": "/inOutMoney",
            "concentration": "/concentration",
            "holdings_distribution": "/holdingsDistribution",
            "network_growth": "/networkGrowth",
        },
        "features": {
            "btc_data": True,
            "eth_data": True,
            "defi_data": True,
            "prediction_models": True,
        },
        "coverage": {
            "cryptocurrencies": 50+,
            "metrics": 100+,
            "historical_depth": "2017+",
        }
    },
    "nansen": {
        "name": "Nansen",
        "api_base": "https://api.nansen.ai",
        "api_key_required": True,
        "rate_limit": 60,
        "endpoints": {
            "wallet_profiling": "/wallet/profiling",
            "token_flows": "/token/flows",
            "smart_money": "/smart_money",
            "defi_positions": "/defi/positions",
        },
        "features": {
            "wallet_tracking": True,
            "token_flows": True,
            "defi_data": True,
            "nft_data": True,
        },
        "coverage": {
            "cryptocurrencies": ["ETH", "BSC", "POLYGON"],
            "wallets": 100M+,
            "protocols": 500+,
        }
    }
}

# DeFi数据源配置
DEFI_DATA_SOURCES = {
    "defillama": {
        "name": "DeFiLlama",
        "api_base": "https://api.llama.fi",
        "api_key_required": False,
        "rate_limit": 300,
        "endpoints": {
            "tvl": "/tvl",
            "protocols": "/protocols",
            "yields": "/yields",
            "pools": "/pools",
        },
        "features": {
            "tvl_tracking": True,
            "protocol_data": True,
            "yield_farming": True,
            "pool_data": True,
        },
        "coverage": {
            "protocols": 2000+,
            "chains": 100+,
            "pools": 10000+,
        }
    },
    "defipulse": {
        "name": "DeFiPulse",
        "api_base": "https://data.defipulse.com/api",
        "api_key_required": True,
        "rate_limit": 100,
        "endpoints": {
            "tvl": "/GetHistoricalTvl",
            "dominance": "/GetDominance",
            "protocols": "/GetProtocols",
            "eth_gas": "/GetEthGas",
        },
        "features": {
            "tvl_tracking": True,
            "dominance_data": True,
            "protocol_data": True,
            "gas_data": True,
        },
        "coverage": {
            "protocols": 100+,
            "chains": 10+,
            "historical_depth": "2018+",
        }
    }
}

# 情绪数据源配置
SENTIMENT_DATA_SOURCES = {
    "lunarcrush": {
        "name": "LunarCrush",
        "api_base": "https://api.lunarcrush.com/v2",
        "api_key_required": True,
        "rate_limit": 30,
        "endpoints": {
            "social_metrics": "/data",
            "galaxy_score": "/assets",
            "news": "/news",
            "influencers": "/influencers",
        },
        "features": {
            "social_volume": True,
            "sentiment_analysis": True,
            "news_analysis": True,
            "influencer_tracking": True,
        },
        "coverage": {
            "cryptocurrencies": 2000+,
            "social_platforms": 10+,
            "news_sources": 100+,
        }
    },
    "santiment": {
        "name": "Santiment",
        "api_base": "https://api.santiment.net/graphql",
        "api_key_required": True,
        "rate_limit": 100,
        "endpoints": {
            "social_volume": "/socialVolume",
            "sentiment": "/sentiment",
            "dev_activity": "/devActivity",
            "onchain_metrics": "/onchainMetrics",
        },
        "features": {
            "social_volume": True,
            "sentiment_analysis": True,
            "dev_activity": True,
            "onchain_metrics": True,
        },
        "coverage": {
            "cryptocurrencies": 2000+,
            "social_platforms": 20+,
            "github_repos": 10000+,
        }
    },
    "fear_greed_index": {
        "name": "Fear & Greed Index",
        "api_base": "https://api.alternative.me",
        "api_key_required": False,
        "rate_limit": 60,
        "endpoints": {
            "fear_greed": "/fng/",
            "historical": "/fng/history/",
        },
        "features": {
            "market_sentiment": True,
            "historical_data": True,
            "daily_updates": True,
        },
        "coverage": {
            "markets": ["Crypto"],
            "update_frequency": "daily",
            "historical_depth": "2018+",
        }
    }
}

# 新闻数据源配置
NEWS_DATA_SOURCES = {
    "cryptopanic": {
        "name": "CryptoPanic",
        "api_base": "https://cryptopanic.com/api/v1",
        "api_key_required": True,
        "rate_limit": 100,
        "endpoints": {
            "news": "/posts/",
            "categories": "/categories/",
            "currencies": "/currencies/",
        },
        "features": {
            "real_time_news": True,
            "categorization": True,
            "sentiment_analysis": True,
            "filtering": True,
        },
        "coverage": {
            "news_sources": 100+,
            "languages": 10+,
            "update_frequency": "real-time",
        }
    },
    "coindesk": {
        "name": "CoinDesk",
        "api_base": "https://api.coindesk.com/v1",
        "api_key_required": True,
        "rate_limit": 60,
        "endpoints": {
            "articles": "/articles",
            "headlines": "/headlines",
            "markets": "/markets",
        },
        "features": {
            "news_articles": True,
            "market_analysis": True,
            "price_data": True,
        },
        "coverage": {
            "news_categories": 10+,
            "update_frequency": "hourly",
            "historical_depth": "2013+",
        }
    }
}

# 数据源优先级配置
DATA_SOURCE_PRIORITY = {
    "price_data": ["binance", "coingecko", "coinmarketcap"],
    "onchain_data": ["glassnode", "intotheblock", "nansen"],
    "defi_data": ["defillama", "defipulse"],
    "sentiment_data": ["lunarcrush", "santiment", "fear_greed_index"],
    "news_data": ["cryptopanic", "coindesk"],
}

# 数据源错误处理配置
DATA_ERROR_HANDLING = {
    "retry_codes": [429, 500, 502, 503, 504],
    "max_retries": 3,
    "retry_delay": 1,
    "timeout": 30,
    "fallback_sources": {
        "price_data": ["coingecko", "coinmarketcap"],
        "onchain_data": ["glassnode", "intotheblock"],
        "defi_data": ["defillama"],
        "sentiment_data": ["fear_greed_index"],
        "news_data": ["cryptopanic"],
    }
}

# 数据缓存配置
DATA_CACHE_CONFIG = {
    "price_data": {
        "cache_duration": 60,  # 秒
        "max_cache_size": 1000,
        "compress": True,
    },
    "onchain_data": {
        "cache_duration": 300,  # 秒
        "max_cache_size": 500,
        "compress": True,
    },
    "defi_data": {
        "cache_duration": 600,  # 秒
        "max_cache_size": 200,
        "compress": True,
    },
    "sentiment_data": {
        "cache_duration": 1800,  # 秒
        "max_cache_size": 100,
        "compress": True,
    },
    "news_data": {
        "cache_duration": 3600,  # 秒
        "max_cache_size": 500,
        "compress": True,
    }
}

# 数据验证配置
DATA_VALIDATION_CONFIG = {
    "price_data": {
        "min_price": 0.000001,
        "max_price": 1000000,
        "max_change_percent": 50,  # 单次最大变化百分比
        "required_fields": ["price", "timestamp", "symbol"],
    },
    "onchain_data": {
        "min_value": 0,
        "max_value": 1e18,
        "required_fields": ["timestamp", "value", "metric"],
    },
    "defi_data": {
        "min_tvl": 0,
        "max_tvl": 1e12,
        "required_fields": ["tvl", "timestamp", "protocol"],
    },
    "sentiment_data": {
        "min_score": -1,
        "max_score": 1,
        "required_fields": ["score", "timestamp", "source"],
    }
}

# 数据源API密钥配置（示例）
API_KEYS_CONFIG = {
    "coingecko": {
        "demo_key": "CG-demo-api-key",
        "api_key_env": "COINGECKO_API_KEY",
        "free_tier": True,
        "rate_limits": {"requests_per_minute": 50, "requests_per_month": 10000},
    },
    "coinmarketcap": {
        "demo_key": "CMC-demo-api-key",
        "api_key_env": "COINMARKETCAP_API_KEY",
        "free_tier": True,
        "rate_limits": {"requests_per_minute": 333, "requests_per_day": 333},
    },
    "glassnode": {
        "demo_key": "GN-demo-api-key",
        "api_key_env": "GLASSNODE_API_KEY",
        "free_tier": False,
        "rate_limits": {"requests_per_minute": 100, "requests_per_month": 10000},
    },
    "intotheblock": {
        "demo_key": "ITB-demo-api-key",
        "api_key_env": "INTOTHEBLOCK_API_KEY",
        "free_tier": False,
        "rate_limits": {"requests_per_minute": 100, "requests_per_month": 5000},
    },
    "nansen": {
        "demo_key": "NANSEN-demo-api-key",
        "api_key_env": "NANSEN_API_KEY",
        "free_tier": False,
        "rate_limits": {"requests_per_minute": 60, "requests_per_month": 10000},
    },
    "lunarcrush": {
        "demo_key": "LC-demo-api-key",
        "api_key_env": "LUNARCRUSH_API_KEY",
        "free_tier": True,
        "rate_limits": {"requests_per_minute": 30, "requests_per_month": 5000},
    },
    "santiment": {
        "demo_key": "SAN-demo-api-key",
        "api_key_env": "SANTIMENT_API_KEY",
        "free_tier": False,
        "rate_limits": {"requests_per_minute": 100, "requests_per_month": 10000},
    },
    "cryptopanic": {
        "demo_key": "CP-demo-api-key",
        "api_key_env": "CRYPTOPANIC_API_KEY",
        "free_tier": True,
        "rate_limits": {"requests_per_minute": 100, "requests_per_month": 10000},
    },
    "coindesk": {
        "demo_key": "CD-demo-api-key",
        "api_key_env": "COINDESK_API_KEY",
        "free_tier": False,
        "rate_limits": {"requests_per_minute": 60, "requests_per_month": 10000},
    }
}