"""
Configuration example for the News Collection Framework.

This file shows how to configure the news collection manager with various
settings for different news sources.
"""

from news_collection.models import NewsSourceType, NewsCategory

# Example configuration for the NewsCollectionManager
EXAMPLE_CONFIG = {
    "sources": [
        {
            "name": "CoinDesk",
            "source_type": NewsSourceType.COINDESK,
            "base_url": "https://api.coindesk.com/v1",
            "api_key": "your_coindesk_api_key_here",
            "rate_limit_per_minute": 60,
            "timeout_seconds": 30,
            "enabled": True,
            "priority": 1,
            "config": {
                "endpoint": "/latest headlines",
                "default_limit": 20,
                "include_summary": True
            }
        },
        {
            "name": "CoinTelegraph",
            "source_type": NewsSourceType.COINTELEGRAPH,
            "base_url": "https://cointelegraph.com/api/v1",
            "api_key": "your_cointelegraph_api_key_here",
            "rate_limit_per_minute": 60,
            "timeout_seconds": 30,
            "enabled": True,
            "priority": 2,
            "config": {
                "endpoint": "/news",
                "default_limit": 15,
                "include_author": True
            }
        },
        {
            "name": "Decrypt",
            "source_type": NewsSourceType.DECRYPT,
            "base_url": "https://api.decrypt.co/v1",
            "api_key": "your_decrypt_api_key_here",
            "rate_limit_per_minute": 60,
            "timeout_seconds": 30,
            "enabled": True,
            "priority": 3,
            "config": {
                "endpoint": "/articles",
                "default_limit": 25,
                "include_featured": True
            }
        },
        {
            "name": "CryptoSlate",
            "source_type": NewsSourceType.CRYPTOSLATE,
            "base_url": "https://api.cryptoslate.com/v1",
            "api_key": "your_cryptoslate_api_key_here",
            "rate_limit_per_minute": 30,
            "timeout_seconds": 45,
            "enabled": False,  # Disabled until adapter is implemented
            "priority": 4,
            "config": {
                "endpoint": "/news",
                "default_limit": 10
            }
        },
        {
            "name": "The Block",
            "source_type": NewsSourceType.THE_BLOCK,
            "base_url": "https://api.theblockcrypto.com/v1",
            "api_key": "your_theblock_api_key_here",
            "rate_limit_per_minute": 30,
            "timeout_seconds": 45,
            "enabled": False,  # Disabled until adapter is implemented
            "priority": 5,
            "config": {
                "endpoint": "/posts",
                "default_limit": 10
            }
        }
    ]
}

# Example collection configuration
COLLECTION_CONFIG = {
    "collection_interval": 300,  # 5 minutes
    "max_articles_per_source": 20,
    "max_total_articles": 100,
    "article_retention_days": 30,
    "health_check_interval": 30,  # 30 seconds
    "connection_timeout": 30,
    "max_concurrent_connections": 10,
    "retry_attempts": 3,
    "retry_backoff_factor": 2,
}

# Example filter configuration
FILTER_CONFIG = {
    "default_categories": [
        NewsCategory.MARKET_NEWS,
        NewsCategory.TECHNOLOGY,
        NewsCategory.REGULATION,
        NewsCategory.SECURITY,
    ],
    "excluded_keywords": [
        "spam",
        "scam",
        "clickbait",
    ],
    "min_content_length": 100,
    "max_content_length": 50000,
    "require_author": False,
    "require_summary": True,
}

# Example health monitoring configuration
HEALTH_CONFIG = {
    "response_time_threshold": 5000,  # 5 seconds
    "failure_threshold": 3,  # consecutive failures
    "uptime_threshold": 95.0,  # percentage
    "alert_severity_levels": {
        "slow_response": "medium",
        "connection_failed": "high",
        "consecutive_failures": "high",
        "rate_limit_exceeded": "medium",
    },
    "notification_channels": [
        "log",
        # "email",
        # "slack",
        # "webhook",
    ],
}

# Example rate limiting configuration
RATE_LIMIT_CONFIG = {
    "default_rate_limit": 60,  # requests per minute
    "burst_limit": 10,  # burst requests
    "time_window": 60,  # seconds
    "retry_after": 60,  # seconds
    "respect_api_headers": True,
}

# Example logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "news_collection.log",
    "max_file_size": 10485760,  # 10MB
    "backup_count": 5,
    "console_output": True,
}

# Complete configuration example
COMPLETE_CONFIG = {
    "sources": EXAMPLE_CONFIG["sources"],
    "collection": COLLECTION_CONFIG,
    "filters": FILTER_CONFIG,
    "health": HEALTH_CONFIG,
    "rate_limiting": RATE_LIMIT_CONFIG,
    "logging": LOGGING_CONFIG,
}

def get_config():
    """Get the complete configuration example."""
    return COMPLETE_CONFIG

def get_minimal_config():
    """Get a minimal configuration for testing."""
    return {
        "sources": [
            {
                "name": "CoinDesk",
                "source_type": NewsSourceType.COINDESK,
                "base_url": "https://api.coindesk.com/v1",
                "enabled": True,
                "priority": 1,
            }
        ]
    }

def get_production_config():
    """Get a production-ready configuration."""
    return {
        "sources": [
            {
                "name": "CoinDesk",
                "source_type": NewsSourceType.COINDESK,
                "base_url": "https://api.coindesk.com/v1",
                "api_key": "your_production_api_key",
                "rate_limit_per_minute": 60,
                "timeout_seconds": 30,
                "enabled": True,
                "priority": 1,
            },
            {
                "name": "CoinTelegraph",
                "source_type": NewsSourceType.COINTELEGRAPH,
                "base_url": "https://cointelegraph.com/api/v1",
                "api_key": "your_production_api_key",
                "rate_limit_per_minute": 60,
                "timeout_seconds": 30,
                "enabled": True,
                "priority": 2,
            },
        ],
        "collection": {
            "collection_interval": 300,
            "max_articles_per_source": 20,
            "health_check_interval": 30,
        },
        "health": {
            "response_time_threshold": 5000,
            "failure_threshold": 3,
        },
    }