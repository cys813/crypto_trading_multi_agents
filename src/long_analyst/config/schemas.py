"""
Configuration Schemas and Types.

Defines configuration types, schemas, and validation structures.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class ConfigType(Enum):
    """Configuration types."""
    TECHNICAL_INDICATORS = "technical_indicators"
    LLM = "llm"
    SIGNALS = "signals"
    OUTPUT = "output"
    TRADING = "trading"
    RISK_MANAGEMENT = "risk_management"
    NOTIFICATIONS = "notifications"
    LOGGING = "logging"


@dataclass
class ValidationResult:
    """Configuration validation result."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

    def __post_init__(self):
        """Initialize with empty lists if not provided."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ConfigSchema:
    """Configuration schema definition."""
    config_type: ConfigType
    schema: Dict[str, Any]
    required_fields: List[str]
    optional_fields: List[str] = None
    validation_rules: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize optional fields."""
        if self.optional_fields is None:
            self.optional_fields = []
        if self.validation_rules is None:
            self.validation_rules = {}


@dataclass
class VersionInfo:
    """Configuration version information."""
    version: str
    timestamp: str
    author: str
    comment: str
    checksum: str
    changes: List[str]


@dataclass
class ConfigDiff:
    """Configuration difference information."""
    type: str  # "added", "removed", "modified", "type_change"
    path: str
    old_value: Any
    new_value: Any


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration."""
    environment: str
    overrides: Dict[str, Any]
    defaults: Dict[str, Any]
    is_default: bool = False


# Built-in configuration templates
TECHNICAL_INDICATORS_TEMPLATE = {
    "trend": {
        "sma": {
            "periods": [5, 10, 20, 50, 100, 200],
            "weight": 0.3
        },
        "ema": {
            "periods": [12, 26],
            "weight": 0.4
        },
        "macd": {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
            "weight": 0.5
        }
    },
    "momentum": {
        "rsi": {
            "period": 14,
            "oversold": 30,
            "overbought": 70,
            "weight": 0.4
        },
        "stochastic": {
            "k_period": 14,
            "d_period": 3,
            "weight": 0.3
        }
    },
    "volatility": {
        "bollinger_bands": {
            "period": 20,
            "std_dev": 2,
            "weight": 0.4
        },
        "atr": {
            "period": 14,
            "weight": 0.3
        }
    }
}

LLM_CONFIG_TEMPLATE = {
    "providers": {
        "openai": {
            "api_key": "${OPENAI_API_KEY}",
            "model": "gpt-4",
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 30,
            "retry_count": 3
        },
        "azure_openai": {
            "endpoint": "${AZURE_OPENAI_ENDPOINT}",
            "api_key": "${AZURE_OPENAI_API_KEY}",
            "deployment": "gpt-4",
            "api_version": "2024-02-15-preview"
        },
        "anthropic": {
            "api_key": "${ANTHROPIC_API_KEY}",
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 4000,
            "temperature": 0.5
        }
    },
    "cost_control": {
        "daily_budget": 100.0,
        "monthly_budget": 2000.0,
        "alert_threshold": 0.8
    },
    "templates": {
        "long_analysis": "templates/long_analysis.txt",
        "quick_decision": "templates/quick_decision.txt",
        "risk_assessment": "templates/risk_assessment.txt"
    }
}

SIGNALS_CONFIG_TEMPLATE = {
    "thresholds": {
        "strong_signal": 0.8,
        "medium_signal": 0.6,
        "weak_signal": 0.4
    },
    "trend_detection": {
        "min_trend_strength": 0.6,
        "confirmation_periods": 3
    },
    "breakout_detection": {
        "breakout_volume_multiplier": 1.5,
        "breakout_confirmation_candles": 2
    },
    "pullback_detection": {
        "max_pullback_depth": 0.382,  # Fibonacci 38.2%
        "min_pullback_volume": 0.8
    },
    "risk_management": {
        "max_risk_per_trade": 0.02,
        "min_risk_reward_ratio": 2.0,
        "max_position_size": 0.1
    }
}

OUTPUT_CONFIG_TEMPLATE = {
    "format": {
        "type": "json",
        "pretty_print": True,
        "include_metadata": True,
        "include_timestamps": True
    },
    "channels": [
        {
            "type": "file",
            "path": "logs/analysis_results.log",
            "format": "json"
        },
        {
            "type": "console",
            "level": "INFO",
            "format": "structured"
        },
        {
            "type": "webhook",
            "url": "${WEBHOOK_URL}",
            "timeout": 30,
            "retry_count": 3
        }
    ],
    "notification": {
        "enabled": True,
        "channels": ["email", "slack"],
        "urgency_levels": ["low", "medium", "high", "critical"]
    }
}

TRADING_CONFIG_TEMPLATE = {
    "execution": {
        "broker": "binance",
        "api_key": "${EXCHANGE_API_KEY}",
        "api_secret": "${EXCHANGE_API_SECRET}",
        "test_mode": True,
        "max_slippage": 0.001
    },
    "position_management": {
        "max_positions": 5,
        "max_portfolio_risk": 0.1,
        "position_sizing_method": "fixed_percentage",
        "default_position_size": 0.02
    },
    "order_types": {
        "default": "limit",
        "allow_market": False,
        "post_only": False,
        "reduce_only": False
    }
}

RISK_MANAGEMENT_CONFIG_TEMPLATE = {
    "stop_loss": {
        "enabled": True,
        "method": "percentage",
        "percentage": 0.02,
        "trailing": {
            "enabled": True,
            "distance": 0.01,
            "activation_threshold": 0.01
        }
    },
    "take_profit": {
        "enabled": True,
        "method": "multiple_targets",
        "targets": [
            {"percentage": 0.5, "profit": 0.02},
            {"percentage": 0.3, "profit": 0.04},
            {"percentage": 0.2, "profit": 0.06}
        ]
    },
    "portfolio_limits": {
        "max_drawdown": 0.2,
        "daily_loss_limit": 0.05,
        "max_correlation": 0.7,
        "max_leverage": 3.0
    }
}

NOTIFICATIONS_CONFIG_TEMPLATE = {
    "email": {
        "enabled": False,
        "smtp_server": "${SMTP_SERVER}",
        "smtp_port": 587,
        "username": "${SMTP_USERNAME}",
        "password": "${SMTP_PASSWORD}",
        "recipients": []
    },
    "slack": {
        "enabled": False,
        "webhook_url": "${SLACK_WEBHOOK_URL}",
        "channel": "#trading-alerts",
        "username": "Trading Bot"
    },
    "discord": {
        "enabled": False,
        "webhook_url": "${DISCORD_WEBHOOK_URL}",
        "channel": "trading-alerts"
    },
    "telegram": {
        "enabled": False,
        "bot_token": "${TELEGRAM_BOT_TOKEN}",
        "chat_id": "${TELEGRAM_CHAT_ID}"
    }
}

LOGGING_CONFIG_TEMPLATE = {
    "level": "INFO",
    "format": {
        "type": "structured",
        "include_timestamp": True,
        "include_level": True,
        "include_logger": True,
        "json": True
    },
    "handlers": {
        "file": {
            "enabled": True,
            "filename": "logs/long_analyst.log",
            "max_size": "10MB",
            "backup_count": 5,
            "level": "DEBUG"
        },
        "console": {
            "enabled": True,
            "level": "INFO"
        }
    },
    "loggers": {
        "long_analyst": {
            "level": "DEBUG",
            "handlers": ["file", "console"]
        },
        "llm_service": {
            "level": "INFO",
            "handlers": ["file"]
        }
    }
}


def get_config_template(config_type: ConfigType) -> Dict[str, Any]:
    """Get configuration template for type."""
    templates = {
        ConfigType.TECHNICAL_INDICATORS: TECHNICAL_INDICATORS_TEMPLATE,
        ConfigType.LLM: LLM_CONFIG_TEMPLATE,
        ConfigType.SIGNALS: SIGNALS_CONFIG_TEMPLATE,
        ConfigType.OUTPUT: OUTPUT_CONFIG_TEMPLATE,
        ConfigType.TRADING: TRADING_CONFIG_TEMPLATE,
        ConfigType.RISK_MANAGEMENT: RISK_MANAGEMENT_CONFIG_TEMPLATE,
        ConfigType.NOTIFICATIONS: NOTIFICATIONS_CONFIG_TEMPLATE,
        ConfigType.LOGGING: LOGGING_CONFIG_TEMPLATE
    }

    if config_type not in templates:
        raise ValueError(f"No template available for {config_type.value}")

    return templates[config_type].copy()


def get_default_config_environments() -> List[EnvironmentConfig]:
    """Get default environment configurations."""
    return [
        EnvironmentConfig(
            environment="development",
            overrides={
                "llm": {"providers": {"default": "mock"}},
                "logging": {"level": "DEBUG"},
                "trading": {"execution": {"test_mode": True}}
            },
            defaults={},
            is_default=True
        ),
        EnvironmentConfig(
            environment="testing",
            overrides={
                "llm": {"providers": {"default": "mock"}},
                "logging": {"level": "INFO"},
                "trading": {"execution": {"test_mode": True}}
            },
            defaults={},
            is_default=False
        ),
        EnvironmentConfig(
            environment="staging",
            overrides={
                "logging": {"level": "INFO"},
                "trading": {"execution": {"test_mode": False}}
            },
            defaults={},
            is_default=False
        ),
        EnvironmentConfig(
            environment="production",
            overrides={
                "logging": {"level": "WARNING"},
                "trading": {"execution": {"test_mode": False}}
            },
            defaults={},
            is_default=False
        )
    ]