"""
Configuration settings for the data collection agent.

This module contains all configuration settings including database connections,
exchange configurations, and system parameters.
"""

import os
from typing import List, Dict, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Main configuration class for the data collection agent."""

    # Database Configuration
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="password", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="crypto_trading", env="POSTGRES_DB")

    # TimescaleDB Configuration
    TIMESCALEDB_HOST: str = Field(default="localhost", env="TIMESCALEDB_HOST")
    TIMESCALEDB_PORT: int = Field(default=5432, env="TIMESCALEDB_PORT")
    TIMESCALEDB_USER: str = Field(default="postgres", env="TIMESCALEDB_USER")
    TIMESCALEDB_PASSWORD: str = Field(default="password", env="TIMESCALEDB_PASSWORD")
    TIMESCALEDB_DB: str = Field(default="timescaledb_crypto", env="TIMESCALEDB_DB")

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")

    # Exchange Configuration
    EXCHANGE_CONFIGS: Dict[str, Dict] = Field(
        default={
            "binance": {
                "apiKey": "",
                "secret": "",
                "sandbox": False,
                "enableRateLimit": True,
                "rateLimit": 100,
                "timeout": 10000,
                "options": {
                    "defaultType": "spot"
                }
            },
            "okx": {
                "apiKey": "",
                "secret": "",
                "passphrase": "",
                "sandbox": False,
                "enableRateLimit": True,
                "rateLimit": 100,
                "timeout": 10000,
                "options": {
                    "defaultType": "spot"
                }
            },
            "huobi": {
                "apiKey": "",
                "secret": "",
                "sandbox": False,
                "enableRateLimit": True,
                "rateLimit": 100,
                "timeout": 10000,
                "options": {
                    "defaultType": "spot"
                }
            }
        },
        env="EXCHANGE_CONFIGS"
    )

    # Data Collection Settings
    DATA_COLLECTION_INTERVAL: int = Field(default=1000, env="DATA_COLLECTION_INTERVAL")
    OHLCV_TIMEFRAMES: List[str] = Field(
        default=["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        env="OHLCV_TIMEFRAMES"
    )
    ORDER_BOOK_DEPTH: int = Field(default=20, env="ORDER_BOOK_DEPTH")
    TRADE_LIMIT: int = Field(default=1000, env="TRADE_LIMIT")

    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_WORKERS: int = Field(default=4, env="API_WORKERS")

    # Monitoring Configuration
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="data_collection.log", env="LOG_FILE")

    # Performance Settings
    MAX_CONCURRENT_CONNECTIONS: int = Field(default=1000, env="MAX_CONCURRENT_CONNECTIONS")
    REQUEST_TIMEOUT: int = Field(default=100, env="REQUEST_TIMEOUT")
    CACHE_TTL: int = Field(default=300, env="CACHE_TTL")

    # Quality Control
    DATA_QUALITY_THRESHOLD: float = Field(default=0.999, env="DATA_QUALITY_THRESHOLD")
    MAX_RETRIES: int = Field(default=3, env="MAX_RETRIES")
    RETRY_DELAY: int = Field(default=1000, env="RETRY_DELAY")

    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def timescaledb_url(self) -> str:
        """Generate TimescaleDB connection URL."""
        return f"postgresql://{self.TIMESCALEDB_USER}:{self.TIMESCALEDB_PASSWORD}@{self.TIMESCALEDB_HOST}:{self.TIMESCALEDB_PORT}/{self.TIMESCALEDB_DB}"

    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings