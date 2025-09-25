"""
Configuration settings for the data collection agent.
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseSettings, Field
from dataclasses import dataclass

from ..core.exchange_manager import ExchangeConfig


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="crypto_trading", env="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="password", env="POSTGRES_PASSWORD")

    timescaledb_host: str = Field(default="localhost", env="TIMESCALEDB_HOST")
    timescaledb_port: int = Field(default=5432, env="TIMESCALEDB_PORT")
    timescaledb_db: str = Field(default="crypto_timeseries", env="TIMESCALEDB_DB")
    timescaledb_user: str = Field(default="postgres", env="TIMESCALEDB_USER")
    timescaledb_password: str = Field(default="password", env="TIMESCALEDB_PASSWORD")

    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")


class APISettings(BaseSettings):
    """API server configuration."""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="API_DEBUG")
    cors_origins: List[str] = Field(default=["*"], env="API_CORS_ORIGINS")


class MonitoringSettings(BaseSettings):
    """Monitoring and logging configuration."""
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/data_collection.log", env="LOG_FILE")
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")


class DataCollectionSettings(BaseSettings):
    """Data collection specific settings."""
    collection_interval: int = Field(default=60, env="COLLECTION_INTERVAL")
    batch_size: int = Field(default=100, env="BATCH_SIZE")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay: int = Field(default=5, env="RETRY_DELAY")
    enable_real_time: bool = Field(default=True, env="ENABLE_REAL_TIME")


class Settings(BaseSettings):
    """Main settings class."""
    database: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    data_collection: DataCollectionSettings = DataCollectionSettings()

    # Exchange configurations
    exchanges: Dict[str, ExchangeConfig] = {}

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_exchange_configs()

    def _load_exchange_configs(self):
        """Load exchange configurations from environment variables."""
        exchange_configs = {
            "binance": ExchangeConfig(
                name="binance",
                api_key=os.getenv("BINANCE_API_KEY"),
                secret=os.getenv("BINANCE_API_SECRET"),
                sandbox=os.getenv("BINANCE_SANDBOX", "false").lower() == "true",
                rate_limit=int(os.getenv("BINANCE_RATE_LIMIT", "120"))
            ),
            "okx": ExchangeConfig(
                name="okx",
                api_key=os.getenv("OKX_API_KEY"),
                secret=os.getenv("OKX_API_SECRET"),
                passphrase=os.getenv("OKX_API_PASSPHRASE"),
                sandbox=os.getenv("OKX_SANDBOX", "false").lower() == "true",
                rate_limit=int(os.getenv("OKX_RATE_LIMIT", "120"))
            ),
            "huobi": ExchangeConfig(
                name="huobi",
                api_key=os.getenv("HUOBI_API_KEY"),
                secret=os.getenv("HUOBI_API_SECRET"),
                sandbox=os.getenv("HUOBI_SANDBOX", "false").lower() == "true",
                rate_limit=int(os.getenv("HUOBI_RATE_LIMIT", "120"))
            ),
            "coinbase": ExchangeConfig(
                name="coinbase",
                api_key=os.getenv("COINBASE_API_KEY"),
                secret=os.getenv("COINBASE_API_SECRET"),
                passphrase=os.getenv("COINBASE_API_PASSPHRASE"),
                sandbox=os.getenv("COINBASE_SANDBOX", "false").lower() == "true",
                rate_limit=int(os.getenv("COINBASE_RATE_LIMIT", "120"))
            ),
            "kraken": ExchangeConfig(
                name="kraken",
                api_key=os.getenv("KRAKEN_API_KEY"),
                secret=os.getenv("KRAKEN_API_SECRET"),
                sandbox=os.getenv("KRAKEN_SANDBOX", "false").lower() == "true",
                rate_limit=int(os.getenv("KRAKEN_RATE_LIMIT", "120"))
            )
        }

        # Only add exchanges that have API keys configured
        for name, config in exchange_configs.items():
            if config.api_key and config.secret:
                self.exchanges[name] = config
                print(f"Loaded configuration for {name} exchange")
            else:
                print(f"No API credentials found for {name} exchange - skipping")


# Global settings instance
settings = Settings()


# Default trading symbols
DEFAULT_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "DOGE/USDT",
    "DOT/USDT",
    "AVAX/USDT",
    "MATIC/USDT"
]


# Default timeframes for OHLCV data
DEFAULT_TIMEFRAMES = [
    "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"
]


# Data collection priorities
PRIORITY_LEVELS = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4,
    "BACKGROUND": 5
}