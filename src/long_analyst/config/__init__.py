"""
Configuration Management Package.

Provides unified configuration management with hot-reload,
validation, version control, and environment-specific settings.
"""

from .config_manager import ConfigurationManager, ConfigEnvironment
from .schemas import (
    ConfigType, ValidationResult, ConfigSchema, VersionInfo, ConfigDiff,
    EnvironmentConfig, get_config_template, get_default_config_environments
)
from .validators import ConfigValidator
from .watchers import ConfigWatcher

__all__ = [
    "ConfigurationManager",
    "ConfigEnvironment",
    "ConfigType",
    "ValidationResult",
    "ConfigSchema",
    "VersionInfo",
    "ConfigDiff",
    "EnvironmentConfig",
    "ConfigValidator",
    "ConfigWatcher",
    "get_config_template",
    "get_default_config_environments"
]


def create_config_manager(
    config_dir: str = "config",
    environment: str = "development",
    auto_start: bool = True
) -> ConfigurationManager:
    """
    Create and initialize configuration manager.

    Args:
        config_dir: Directory containing configuration files
        environment: Environment name
        auto_start: Whether to auto-start the manager

    Returns:
        Initialized configuration manager
    """
    env = ConfigEnvironment(environment.lower())
    manager = ConfigurationManager(config_dir, env)

    if auto_start:
        # Start background services
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(manager._initialize())

    return manager