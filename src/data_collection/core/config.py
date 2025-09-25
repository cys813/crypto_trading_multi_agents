"""
Enhanced configuration management system for the data collection agent.

This module provides a comprehensive configuration management system with:
- Multi-environment support (development, testing, production)
- Environment variable substitution
- Configuration validation with Pydantic
- Hot-reload capability
- Sensitive data encryption
- Structured configuration loading from YAML/JSON files
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from pydantic import BaseModel, Field, validator, root_validator
from cryptography.fernet import Fernet
import logging
from datetime import datetime
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading


class DatabaseConfig(BaseModel):
    """Database configuration model."""
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 10
    max_overflow: int = 5
    connect_timeout: int = 30
    command_timeout: int = 30


class ExchangeConfig(BaseModel):
    """Exchange configuration model."""
    enabled: bool = True
    sandbox: bool = False
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    passphrase: Optional[str] = None
    rate_limit: int = 100
    timeout: int = 10000
    enable_rate_limit: bool = True
    options: Dict[str, Any] = Field(default_factory=dict)


class MonitoringConfig(BaseModel):
    """Monitoring configuration model."""
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    prometheus_path: str = "/metrics"
    grafana_enabled: bool = True
    grafana_host: str = "localhost"
    grafana_port: int = 3000

    @validator('prometheus_port')
    def validate_prometheus_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Prometheus port must be between 1 and 65535')
        return v


class LoggingConfig(BaseModel):
    """Logging configuration model."""
    level: str = "INFO"
    format: str = "json"
    output: List[str] = Field(default_factory=lambda: ["console"])
    file_path: str = "logs/app.log"
    max_file_size: str = "100MB"
    backup_count: int = 10
    structured_logging: bool = True

    @validator('level')
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()

    @validator('format')
    def validate_log_format(cls, v):
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f'Log format must be one of {valid_formats}')
        return v.lower()


class CollectorConfig(BaseModel):
    """Data collector configuration model."""
    market_data_enabled: bool = True
    positions_enabled: bool = True
    orders_enabled: bool = True
    symbols: List[str] = Field(default_factory=lambda: ["BTC/USDT", "ETH/USDT", "BNB/USDT"])
    timeframes: List[str] = Field(default_factory=lambda: ["1m", "5m", "15m", "1h", "4h", "1d"])
    sync_interval: int = 5
    order_book_depth: int = 20
    trade_limit: int = 1000


class AppConfig(BaseModel):
    """Main application configuration model."""
    app_name: str = "data_collection_agent"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"

    # Database configurations
    timescaledb: DatabaseConfig
    postgresql: DatabaseConfig
    redis: DatabaseConfig

    # Exchange configurations
    exchanges: Dict[str, ExchangeConfig]

    # Monitoring configuration
    monitoring: MonitoringConfig

    # Logging configuration
    logging: LoggingConfig

    # Collector configuration
    collector: CollectorConfig

    # Performance settings
    max_concurrent_connections: int = 1000
    request_timeout: int = 100
    cache_ttl: int = 300

    # Quality control
    data_quality_threshold: float = 0.999
    max_retries: int = 3
    retry_delay: int = 1000

    @root_validator
    def validate_environment(cls, values):
        env = values.get('environment', 'development')
        if env not in ['development', 'testing', 'production']:
            raise ValueError('Environment must be development, testing, or production')

        # Adjust settings based on environment
        if env == 'production':
            values['debug'] = False
            if values['logging'].level == 'DEBUG':
                values['logging'].level = 'INFO'

        return values


class ConfigFileHandler(FileSystemEventHandler):
    """Handler for configuration file changes."""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        super().__init__()

    def on_modified(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith(('.yaml', '.yml', '.json')):
            logging.info(f"Configuration file changed: {event.src_path}")
            # Schedule reload in a separate thread to avoid blocking
            threading.Thread(target=self.config_manager.reload, daemon=True).start()


class ConfigManager:
    """Enhanced configuration manager with hot-reload and encryption support."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.getenv("CONFIG_PATH", "configs/development.yaml")
        self.config: Optional[AppConfig] = None
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        self.cipher = Fernet(self.encryption_key.encode()) if self.encryption_key else None
        self.observers = []
        self.reload_callbacks = []
        self._lock = threading.Lock()

        # Load initial configuration
        self.load_config()

        # Start file watching if enabled
        if os.getenv("CONFIG_WATCH", "true").lower() == "true":
            self.start_file_watching()

    def load_config(self) -> AppConfig:
        """Load and validate configuration from file."""
        with self._lock:
            try:
                config_path = Path(self.config_path)

                if not config_path.exists():
                    raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

                # Load configuration based on file type
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")

                # Replace environment variables
                config_data = self._replace_env_variables(config_data)

                # Decrypt sensitive data
                config_data = self._decrypt_sensitive_data(config_data)

                # Validate and create configuration object
                self.config = AppConfig(**config_data)

                logging.info(f"Configuration loaded successfully from {self.config_path}")
                logging.info(f"Environment: {self.config.environment}")
                logging.info(f"Debug mode: {self.config.debug}")

                return self.config

            except Exception as e:
                logging.error(f"Failed to load configuration: {e}")
                raise

    def _replace_env_variables(self, data: Any) -> Any:
        """Recursively replace environment variables in configuration data."""
        if isinstance(data, str):
            # Handle ${VAR} format
            if data.startswith("${") and data.endswith("}"):
                env_key = data[2:-1]
                default_value = None

                # Handle default values: ${VAR:default}
                if ":" in env_key:
                    env_key, default_value = env_key.split(":", 1)

                return os.getenv(env_key, default_value or data)

            # Handle $VAR format
            elif data.startswith("$") and len(data) > 1:
                env_key = data[1:]
                return os.getenv(env_key, data)

        elif isinstance(data, dict):
            return {k: self._replace_env_variables(v) for k, v in data.items()}

        elif isinstance(data, list):
            return [self._replace_env_variables(item) for item in data]

        return data

    def _decrypt_sensitive_data(self, data: Any) -> Any:
        """Decrypt sensitive data in configuration."""
        if not self.cipher:
            return data

        if isinstance(data, dict):
            return {k: self._decrypt_sensitive_data(v) for k, v in data.items()}

        elif isinstance(data, list):
            return [self._decrypt_sensitive_data(item) for item in data]

        elif isinstance(data, str) and data.startswith("encrypted:"):
            try:
                encrypted_data = data[10:]  # Remove "encrypted:" prefix
                return self.cipher.decrypt(encrypted_data.encode()).decode()
            except Exception as e:
                logging.warning(f"Failed to decrypt data: {e}")
                return data

        return data

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key."""
        if not self.config:
            raise ValueError("Configuration not loaded")

        keys = key.split('.')
        value = self.config.dict()

        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        except (KeyError, TypeError):
            return default

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.get(section, {})

    def reload(self) -> AppConfig:
        """Reload configuration from file."""
        try:
            old_config = self.config
            new_config = self.load_config()

            # Call reload callbacks
            for callback in self.reload_callbacks:
                try:
                    callback(old_config, new_config)
                except Exception as e:
                    logging.error(f"Error in reload callback: {e}")

            logging.info("Configuration reloaded successfully")
            return new_config

        except Exception as e:
            logging.error(f"Failed to reload configuration: {e}")
            raise

    def add_reload_callback(self, callback):
        """Add a callback to be called when configuration is reloaded."""
        self.reload_callbacks.append(callback)

    def start_file_watching(self):
        """Start watching configuration file for changes."""
        try:
            config_dir = Path(self.config_path).parent
            observer = Observer()
            observer.schedule(ConfigFileHandler(self), str(config_dir), recursive=False)
            observer.start()
            self.observers.append(observer)
            logging.info(f"Started watching configuration directory: {config_dir}")
        except Exception as e:
            logging.error(f"Failed to start file watching: {e}")

    def stop_file_watching(self):
        """Stop watching configuration files."""
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers.clear()
        logging.info("Stopped watching configuration files")

    def encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value."""
        if not self.cipher:
            raise ValueError("Encryption key not configured")

        encrypted = self.cipher.encrypt(value.encode()).decode()
        return f"encrypted:{encrypted}"

    def save_config(self, config_path: str = None):
        """Save current configuration to file."""
        if not self.config:
            raise ValueError("No configuration loaded")

        save_path = config_path or self.config_path
        config_data = self.config.dict()

        # Encrypt sensitive fields before saving
        config_data = self._encrypt_sensitive_fields(config_data)

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                if save_path.endswith('.json'):
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

            logging.info(f"Configuration saved to {save_path}")

        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            raise

    def _encrypt_sensitive_fields(self, data: Any) -> Any:
        """Encrypt sensitive fields in configuration data."""
        sensitive_keys = ['password', 'api_key', 'api_secret', 'passphrase']

        if isinstance(data, dict):
            return {k: self._encrypt_sensitive_fields(v) if k not in sensitive_keys else
                   (self.encrypt_value(v) if isinstance(v, str) else v)
                   for k, v in data.items()}

        elif isinstance(data, list):
            return [self._encrypt_sensitive_fields(item) for item in data]

        return data

    def validate_config(self) -> List[str]:
        """Validate current configuration and return list of errors."""
        errors = []

        if not self.config:
            errors.append("Configuration not loaded")
            return errors

        try:
            # Validate database connections
            for db_name, db_config in [('timescaledb', self.config.timescaledb),
                                      ('postgresql', self.config.postgresql),
                                      ('redis', self.config.redis)]:
                if not db_config.host:
                    errors.append(f"{db_name} host is required")
                if not db_config.database:
                    errors.append(f"{db_name} database name is required")
                if not 1 <= db_config.port <= 65535:
                    errors.append(f"{db_name} port must be between 1 and 65535")

            # Validate exchange configurations
            for exchange_name, exchange_config in self.config.exchanges.items():
                if exchange_config.enabled:
                    if not exchange_config.api_key:
                        errors.append(f"{exchange_name} API key is required when enabled")
                    if not exchange_config.api_secret:
                        errors.append(f"{exchange_name} API secret is required when enabled")
                    if 'okx' in exchange_name.lower() and not exchange_config.passphrase:
                        errors.append(f"{exchange_name} passphrase is required when enabled")

            # Validate monitoring configuration
            if self.config.monitoring.prometheus_enabled:
                if not 1 <= self.config.monitoring.prometheus_port <= 65535:
                    errors.append("Prometheus port must be between 1 and 65535")

            # Validate logging configuration
            log_path = Path(self.config.logging.file_path)
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create log directory {log_path.parent}: {e}")

            # Validate collector configuration
            if not self.config.collector.symbols:
                errors.append("At least one symbol must be configured for data collection")
            if not self.config.collector.timeframes:
                errors.append("At least one timeframe must be configured for data collection")

        except Exception as e:
            errors.append(f"Configuration validation error: {e}")

        return errors

    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration summary."""
        if not self.config:
            return {}

        return {
            "environment": self.config.environment,
            "debug": self.config.debug,
            "app_name": self.config.app_name,
            "version": self.config.version,
            "host": self.config.host,
            "port": self.config.port,
            "log_level": self.config.logging.level,
            "exchanges_enabled": [name for name, config in self.config.exchanges.items() if config.enabled],
            "monitoring_enabled": self.config.monitoring.prometheus_enabled,
            "data_collection_enabled": self.config.collector.market_data_enabled
        }

    def __del__(self):
        """Cleanup file watchers when destroyed."""
        self.stop_file_watching()


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """Get global configuration instance."""
    return config_manager.config


def get_settings():
    """Legacy compatibility function."""
    return get_config()


def reload_config():
    """Reload global configuration."""
    return config_manager.reload()