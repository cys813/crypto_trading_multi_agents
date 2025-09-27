"""
Configuration Validators.

Provides comprehensive configuration validation with type checking,
range validation, dependency validation, and custom rules.
"""

import re
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from enum import Enum
import logging

from .schemas import ValidationResult, ConfigType


class ValidationRule:
    """Base validation rule."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def validate(self, value: Any, path: str = "") -> ValidationResult:
        """Validate value against rule."""
        raise NotImplementedError


class TypeRule(ValidationRule):
    """Type validation rule."""
    def __init__(self, expected_type: type, description: str = ""):
        super().__init__("type_check", description or f"Must be {expected_type.__name__}")
        self.expected_type = expected_type

    def validate(self, value: Any, path: str = "") -> ValidationResult:
        """Validate type."""
        if not isinstance(value, self.expected_type):
            return ValidationResult(
                is_valid=False,
                errors=[f"{path}: Expected {self.expected_type.__name__}, got {type(value).__name__}"],
                warnings=[],
                metadata={"rule": self.name, "expected": self.expected_type.__name__, "actual": type(value).__name__}
            )
        return ValidationResult(is_valid=True, errors=[], warnings=[], metadata={"rule": self.name})


class RangeRule(ValidationRule):
    """Range validation rule for numeric values."""
    def __init__(self, min_val: Optional[Union[int, float]] = None, max_val: Optional[Union[int, float]] = None):
        super().__init__("range_check", f"Must be between {min_val} and {max_val}")
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, value: Any, path: str = "") -> ValidationResult:
        """Validate range."""
        if not isinstance(value, (int, float)):
            return ValidationResult(
                is_valid=False,
                errors=[f"{path}: Expected numeric value, got {type(value).__name__}"],
                warnings=[],
                metadata={"rule": self.name, "expected": "numeric", "actual": type(value).__name__}
            )

        errors = []
        if self.min_val is not None and value < self.min_val:
            errors.append(f"{path}: Value {value} is below minimum {self.min_val}")

        if self.max_val is not None and value > self.max_val:
            errors.append(f"{path}: Value {value} is above maximum {self.max_val}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[],
            metadata={"rule": self.name, "value": value, "min": self.min_val, "max": self.max_val}
        )


class ListRule(ValidationRule):
    """List validation rule."""
    def __init__(self, min_length: Optional[int] = None, max_length: Optional[int] = None, element_rule: Optional[ValidationRule] = None):
        super().__init__("list_check", f"List validation with length and element rules")
        self.min_length = min_length
        self.max_length = max_length
        self.element_rule = element_rule

    def validate(self, value: Any, path: str = "") -> ValidationResult:
        """Validate list."""
        if not isinstance(value, list):
            return ValidationResult(
                is_valid=False,
                errors=[f"{path}: Expected list, got {type(value).__name__}"],
                warnings=[],
                metadata={"rule": self.name, "expected": "list", "actual": type(value).__name__}
            )

        errors = []
        warnings = []

        # Check length
        if self.min_length is not None and len(value) < self.min_length:
            errors.append(f"{path}: List length {len(value)} is below minimum {self.min_length}")

        if self.max_length is not None and len(value) > self.max_length:
            errors.append(f"{path}: List length {len(value)} is above maximum {self.max_length}")

        # Validate elements if element rule is provided
        if self.element_rule and value:
            for i, element in enumerate(value):
                element_path = f"{path}[{i}]"
                result = self.element_rule.validate(element, element_path)
                errors.extend(result.errors)
                warnings.extend(result.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={"rule": self.name, "length": len(value), "min_length": self.min_length, "max_length": self.max_length}
        )


class RegexRule(ValidationRule):
    """Regular expression validation rule."""
    def __init__(self, pattern: str, description: str = ""):
        super().__init__("regex_check", description or f"Must match pattern: {pattern}")
        self.pattern = re.compile(pattern)

    def validate(self, value: Any, path: str = "") -> ValidationResult:
        """Validate against regex."""
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                errors=[f"{path}: Expected string, got {type(value).__name__}"],
                warnings=[],
                metadata={"rule": self.name, "expected": "string", "actual": type(value).__name__}
            )

        if not self.pattern.match(value):
            return ValidationResult(
                is_valid=False,
                errors=[f"{path}: Value '{value}' does not match pattern {self.pattern.pattern}"],
                warnings=[],
                metadata={"rule": self.name, "value": value, "pattern": self.pattern.pattern}
            )

        return ValidationResult(is_valid=True, errors=[], warnings=[], metadata={"rule": self.name, "value": value})


class EnumRule(ValidationRule):
    """Enum validation rule."""
    def __init__(self, enum_values: List[Any], description: str = ""):
        super().__init__("enum_check", description or f"Must be one of: {enum_values}")
        self.enum_values = enum_values

    def validate(self, value: Any, path: str = "") -> ValidationResult:
        """Validate enum value."""
        if value not in self.enum_values:
            return ValidationResult(
                is_valid=False,
                errors=[f"{path}: Value '{value}' is not one of allowed values: {self.enum_values}"],
                warnings=[],
                metadata={"rule": self.name, "value": value, "allowed": self.enum_values}
            )

        return ValidationResult(is_valid=True, errors=[], warnings=[], metadata={"rule": self.name, "value": value})


class CustomRule(ValidationRule):
    """Custom validation rule with user-defined function."""
    def __init__(self, validation_func: Callable[[Any], Union[bool, tuple]], description: str = ""):
        super().__init__("custom_check", description or "Custom validation")
        self.validation_func = validation_func

    def validate(self, value: Any, path: str = "") -> ValidationResult:
        """Validate using custom function."""
        try:
            result = self.validation_func(value)
            if isinstance(result, tuple):
                is_valid, message = result
            else:
                is_valid, message = result, ""

            if not is_valid:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"{path}: {message}"],
                    warnings=[],
                    metadata={"rule": self.name, "value": value}
                )

            return ValidationResult(is_valid=True, errors=[], warnings=[], metadata={"rule": self.name, "value": value})

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"{path}: Custom validation error: {e}"],
                warnings=[],
                metadata={"rule": self.name, "value": value, "error": str(e)}
            )


class ConfigValidator:
    """
    Comprehensive configuration validator.

    Provides type checking, range validation, dependency validation,
    and custom validation rules for all configuration types.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_rules = self._initialize_validation_rules()

    def _initialize_validation_rules(self) -> Dict[ConfigType, Dict[str, ValidationRule]]:
        """Initialize validation rules for all configuration types."""
        return {
            ConfigType.TECHNICAL_INDICATORS: self._get_technical_indicators_rules(),
            ConfigType.LLM: self._get_llm_rules(),
            ConfigType.SIGNALS: self._get_signals_rules(),
            ConfigType.OUTPUT: self._get_output_rules(),
            ConfigType.TRADING: self._get_trading_rules(),
            ConfigType.RISK_MANAGEMENT: self._get_risk_management_rules(),
            ConfigType.NOTIFICATIONS: self._get_notifications_rules(),
            ConfigType.LOGGING: self._get_logging_rules()
        }

    def validate_config(self, config: Dict[str, Any], config_type: ConfigType) -> ValidationResult:
        """
        Validate configuration against type-specific rules.

        Args:
            config: Configuration data to validate
            config_type: Type of configuration

        Returns:
            Validation result
        """
        self.logger.debug(f"Validating {config_type.value} configuration")

        if config_type not in self.validation_rules:
            return ValidationResult(
                is_valid=False,
                errors=[f"No validation rules defined for {config_type.value}"],
                warnings=[],
                metadata={"config_type": config_type.value}
            )

        rules = self.validation_rules[config_type]
        return self._validate_with_rules(config, rules, config_type.value)

    def _validate_with_rules(self, config: Dict[str, Any], rules: Dict[str, ValidationRule], config_path: str) -> ValidationResult:
        """Validate configuration with given rules."""
        errors = []
        warnings = []

        for field_path, rule in rules.items():
            field_value = self._get_nested_value(config, field_path)

            if field_value is None:
                # Skip validation for optional fields
                continue

            result = rule.validate(field_value, f"{config_path}.{field_path}")
            errors.extend(result.errors)
            warnings.extend(result.warnings)

        # Additional cross-field validation
        cross_validation_result = self._validate_cross_field_dependencies(config, config_path)
        errors.extend(cross_validation_result.errors)
        warnings.extend(cross_validation_result.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={"config_path": config_path, "fields_validated": len(rules)}
        )

    def _get_nested_value(self, config: Dict[str, Any], path: str) -> Any:
        """Get nested value from configuration using dot notation."""
        keys = path.split('.')
        value = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def _validate_cross_field_dependencies(self, config: Dict[str, Any], config_path: str) -> ValidationResult:
        """Validate cross-field dependencies."""
        errors = []
        warnings = []

        # Example: Validate that if email notifications are enabled, SMTP settings are provided
        if config_path.endswith("notifications"):
            if config.get("email", {}).get("enabled", False):
                smtp = config.get("email", {}).get("smtp_server")
                if not smtp:
                    errors.append(f"{config_path}.email: SMTP server required when email notifications are enabled")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _get_technical_indicators_rules(self) -> Dict[str, ValidationRule]:
        """Get technical indicators validation rules."""
        return {
            "trend.sma.periods": ListRule(
                min_length=1,
                element_rule=RangeRule(min_val=1, max_val=500)
            ),
            "trend.sma.weight": RangeRule(min_val=0.0, max_val=1.0),
            "trend.ema.periods": ListRule(
                min_length=1,
                element_rule=RangeRule(min_val=1, max_val=200)
            ),
            "trend.ema.weight": RangeRule(min_val=0.0, max_val=1.0),
            "trend.macd.fast_period": RangeRule(min_val=1, max_val=50),
            "trend.macd.slow_period": RangeRule(min_val=1, max_val=50),
            "trend.macd.signal_period": RangeRule(min_val=1, max_val=20),
            "momentum.rsi.period": RangeRule(min_val=2, max_val=100),
            "momentum.rsi.oversold": RangeRule(min_val=0.0, max_val=100.0),
            "momentum.rsi.overbought": RangeRule(min_val=0.0, max_val=100.0),
            "momentum.stochastic.k_period": RangeRule(min_val=1, max_val=50),
            "momentum.stochastic.d_period": RangeRule(min_val=1, max_val=20),
            "volatility.bollinger_bands.period": RangeRule(min_val=5, max_val=50),
            "volatility.bollinger_bands.std_dev": RangeRule(min_val=0.1, max_val=5.0),
            "volatility.atr.period": RangeRule(min_val=1, max_val=50)
        }

    def _get_llm_rules(self) -> Dict[str, ValidationRule]:
        """Get LLM configuration validation rules."""
        return {
            "providers.openai.max_tokens": RangeRule(min_val=1, max_val=8000),
            "providers.openai.temperature": RangeRule(min_val=0.0, max_val=2.0),
            "providers.openai.timeout": RangeRule(min_val=1, max_val=300),
            "providers.openai.retry_count": RangeRule(min_val=0, max_val=10),
            "providers.anthropic.max_tokens": RangeRule(min_val=1, max_val=200000),
            "providers.anthropic.temperature": RangeRule(min_val=0.0, max_val=1.0),
            "cost_control.daily_budget": RangeRule(min_val=0.0, max_val=10000.0),
            "cost_control.monthly_budget": RangeRule(min_val=0.0, max_val=100000.0),
            "cost_control.alert_threshold": RangeRule(min_val=0.0, max_val=1.0)
        }

    def _get_signals_rules(self) -> Dict[str, ValidationRule]:
        """Get signals configuration validation rules."""
        return {
            "thresholds.strong_signal": RangeRule(min_val=0.0, max_val=1.0),
            "thresholds.medium_signal": RangeRule(min_val=0.0, max_val=1.0),
            "thresholds.weak_signal": RangeRule(min_val=0.0, max_val=1.0),
            "trend_detection.min_trend_strength": RangeRule(min_val=0.0, max_val=1.0),
            "trend_detection.confirmation_periods": RangeRule(min_val=1, max_val=10),
            "breakout_detection.breakout_volume_multiplier": RangeRule(min_val=1.0, max_val=10.0),
            "breakout_detection.breakout_confirmation_candles": RangeRule(min_val=1, max_val=10),
            "pullback_detection.max_pullback_depth": RangeRule(min_val=0.0, max_val=1.0),
            "pullback_detection.min_pullback_volume": RangeRule(min_val=0.0, max_val=2.0),
            "risk_management.max_risk_per_trade": RangeRule(min_val=0.0, max_val=1.0),
            "risk_management.min_risk_reward_ratio": RangeRule(min_val=1.0, max_val=10.0),
            "risk_management.max_position_size": RangeRule(min_val=0.0, max_val=1.0)
        }

    def _get_output_rules(self) -> Dict[str, ValidationRule]:
        """Get output configuration validation rules."""
        return {
            "format.type": EnumRule(["json", "yaml", "csv", "xml"]),
            "channels": ListRule(
                max_length=10,
                element_rule=TypeRule(dict)
            ),
            "channels.0.type": EnumRule(["file", "console", "webhook", "database"]),
            "notification.enabled": TypeRule(bool),
            "notification.channels": ListRule(
                element_rule=EnumRule(["email", "slack", "discord", "telegram"])
            )
        }

    def _get_trading_rules(self) -> Dict[str, ValidationRule]:
        """Get trading configuration validation rules."""
        return {
            "execution.broker": TypeRule(str),
            "execution.test_mode": TypeRule(bool),
            "execution.max_slippage": RangeRule(min_val=0.0, max_val=0.1),
            "position_management.max_positions": RangeRule(min_val=1, max_val=100),
            "position_management.max_portfolio_risk": RangeRule(min_val=0.0, max_val=1.0),
            "position_management.default_position_size": RangeRule(min_val=0.0, max_val=1.0),
            "order_types.default": EnumRule(["market", "limit", "stop", "stop_limit"]),
            "order_types.allow_market": TypeRule(bool),
            "order_types.post_only": TypeRule(bool),
            "order_types.reduce_only": TypeRule(bool)
        }

    def _get_risk_management_rules(self) -> Dict[str, ValidationRule]:
        """Get risk management configuration validation rules."""
        return {
            "stop_loss.enabled": TypeRule(bool),
            "stop_loss.method": EnumRule(["percentage", "atr", "volatility"]),
            "stop_loss.percentage": RangeRule(min_val=0.0, max_val=0.5),
            "stop_loss.trailing.enabled": TypeRule(bool),
            "stop_loss.trailing.distance": RangeRule(min_val=0.0, max_val=0.5),
            "take_profit.enabled": TypeRule(bool),
            "take_profit.method": EnumRule(["percentage", "multiple_targets", "trailing"]),
            "portfolio_limits.max_drawdown": RangeRule(min_val=0.0, max_val=1.0),
            "portfolio_limits.daily_loss_limit": RangeRule(min_val=0.0, max_val=1.0),
            "portfolio_limits.max_correlation": RangeRule(min_val=0.0, max_val=1.0),
            "portfolio_limits.max_leverage": RangeRule(min_val=1.0, max_val=100.0)
        }

    def _get_notifications_rules(self) -> Dict[str, ValidationRule]:
        """Get notifications configuration validation rules."""
        return {
            "email.enabled": TypeRule(bool),
            "email.smtp_port": RangeRule(min_val=1, max_val=65535),
            "email.recipients": ListRule(
                element_rule=RegexRule(r"[^@]+@[^@]+\.[^@]+", "Valid email address")
            ),
            "slack.enabled": TypeRule(bool),
            "slack.channel": TypeRule(str),
            "discord.enabled": TypeRule(bool),
            "discord.channel": TypeRule(str),
            "telegram.enabled": TypeRule(bool)
        }

    def _get_logging_rules(self) -> Dict[str, ValidationRule]:
        """Get logging configuration validation rules."""
        return {
            "level": EnumRule(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
            "format.type": EnumRule(["structured", "simple", "json"]),
            "format.include_timestamp": TypeRule(bool),
            "format.include_level": TypeRule(bool),
            "handlers.file.enabled": TypeRule(bool),
            "handlers.file.level": EnumRule(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
            "handlers.console.enabled": TypeRule(bool),
            "handlers.console.level": EnumRule(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        }

    def add_custom_rule(self, config_type: ConfigType, field_path: str, rule: ValidationRule):
        """
        Add custom validation rule.

        Args:
            config_type: Configuration type
            field_path: Field path (dot notation)
            rule: Validation rule to add
        """
        if config_type not in self.validation_rules:
            self.validation_rules[config_type] = {}

        self.validation_rules[config_type][field_path] = rule
        self.logger.info(f"Added custom rule for {config_type.value}.{field_path}")

    def remove_rule(self, config_type: ConfigType, field_path: str):
        """
        Remove validation rule.

        Args:
            config_type: Configuration type
            field_path: Field path to remove rule for
        """
        if config_type in self.validation_rules and field_path in self.validation_rules[config_type]:
            del self.validation_rules[config_type][field_path]
            self.logger.info(f"Removed rule for {config_type.value}.{field_path}")

    def get_rules_summary(self) -> Dict[str, Any]:
        """Get summary of all validation rules."""
        summary = {}
        for config_type, rules in self.validation_rules.items():
            summary[config_type.value] = {
                "rule_count": len(rules),
                "fields": list(rules.keys()),
                "rule_types": [rule.name for rule in rules.values()]
            }
        return summary