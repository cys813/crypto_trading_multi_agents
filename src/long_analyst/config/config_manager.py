"""
Configuration Management System.

Provides unified configuration management with hot-reload,
validation, version control, and environment-specific settings.
"""

import os
import json
import yaml
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import shutil
from enum import Enum
import copy
from concurrent.futures import ThreadPoolExecutor

from .schemas import ConfigSchema, ConfigType, ValidationResult
from .validators import ConfigValidator
from .watchers import ConfigWatcher


class ConfigEnvironment(Enum):
    """Configuration environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ConfigEntry:
    """Individual configuration entry."""
    config_type: ConfigType
    data: Dict[str, Any]
    version: str
    timestamp: datetime
    environment: ConfigEnvironment
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_type": self.config_type.value,
            "data": self.data,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "environment": self.environment.value,
            "checksum": self.checksum,
            "metadata": self.metadata
        }


@dataclass
class ConfigHistory:
    """Configuration version history."""
    config_type: ConfigType
    versions: List[ConfigEntry] = field(default_factory=list)
    current_version: Optional[str] = None

    def add_version(self, entry: ConfigEntry):
        """Add new version to history."""
        self.versions.append(entry)
        self.versions.sort(key=lambda x: x.timestamp, reverse=True)
        self.current_version = entry.version

    def get_version(self, version: str) -> Optional[ConfigEntry]:
        """Get specific version."""
        for entry in self.versions:
            if entry.version == version:
                return entry
        return None

    def rollback_to(self, version: str) -> Optional[ConfigEntry]:
        """Rollback to specific version."""
        target_entry = self.get_version(version)
        if target_entry:
            self.current_version = version
            return target_entry
        return None


class ConfigurationManager:
    """
    Advanced configuration management system.

    Features:
    - Environment-specific configurations
    - Hot-reload capability
    - Version control with rollback
    - Schema validation
    - Configuration caching
    - File watching
    - Backup and restore
    """

    def __init__(self, config_dir: str = "config", environment: ConfigEnvironment = ConfigEnvironment.DEVELOPMENT):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory containing configuration files
            environment: Current environment
        """
        self.config_dir = Path(config_dir)
        self.environment = environment
        self.logger = logging.getLogger(__name__)

        # Configuration storage
        self.configs: Dict[ConfigType, ConfigHistory] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_lock = asyncio.Lock()

        # Validation
        self.validator = ConfigValidator()
        self.schemas = self._load_schemas()

        # File watching
        self.watcher = ConfigWatcher(self)
        self.watching: Dict[ConfigType, bool] = {}

        # Callbacks
        self.change_callbacks: Dict[ConfigType, List[Callable]] = {}

        # Performance
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Metrics
        self.load_count = 0
        self.update_count = 0
        self.validation_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

        # Initialize
        self._initialize()

    def _initialize(self):
        """Initialize configuration manager."""
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)

        # Load environment-specific configurations
        self._load_environment_configs()

        # Start file watcher
        self.watcher.start()

        self.logger.info(f"Configuration manager initialized for {self.environment.value} environment")

    def _load_schemas(self) -> Dict[ConfigType, ConfigSchema]:
        """Load configuration schemas."""
        schemas = {}

        # Built-in schemas
        schemas[ConfigType.TECHNICAL_INDICATORS] = ConfigSchema(
            config_type=ConfigType.TECHNICAL_INDICATORS,
            schema=self._get_technical_indicators_schema(),
            required_fields=["trend", "momentum", "volatility"]
        )

        schemas[ConfigType.LLM] = ConfigSchema(
            config_type=ConfigType.LLM,
            schema=self._get_llm_schema(),
            required_fields=["providers", "cost_control"]
        )

        schemas[ConfigType.SIGNALS] = ConfigSchema(
            config_type=ConfigType.SIGNALS,
            schema=self._get_signals_schema(),
            required_fields=["thresholds", "risk_management"]
        )

        schemas[ConfigType.OUTPUT] = ConfigSchema(
            config_type=ConfigType.OUTPUT,
            schema=self._get_output_schema(),
            required_fields=["format", "channels"]
        )

        return schemas

    def _load_environment_configs(self):
        """Load configurations for current environment."""
        env_config_file = self.config_dir / f"{self.environment.value}.yaml"
        if env_config_file.exists():
            try:
                with open(env_config_file, 'r') as f:
                    env_config = yaml.safe_load(f)

                for config_type_name, config_data in env_config.items():
                    try:
                        config_type = ConfigType(config_type_name)
                        self.load_config(config_type, config_data)
                    except ValueError:
                        self.logger.warning(f"Unknown config type: {config_type_name}")

            except Exception as e:
                self.logger.error(f"Failed to load environment config: {e}")

    async def load_config(self, config_type: ConfigType, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration.

        Args:
            config_type: Type of configuration to load
            data: Configuration data (if None, loads from file)

        Returns:
            Loaded configuration data
        """
        self.load_count += 1

        # Check cache first
        cache_key = f"{config_type.value}_{self.environment.value}"
        cached_config = await self._get_cached_config(cache_key)
        if cached_config:
            self.cache_hits += 1
            return cached_config

        self.cache_misses += 1

        # Load configuration data
        if data is None:
            data = await self._load_config_from_file(config_type)

        # Validate configuration
        validation_result = self.validator.validate_config(data, config_type)
        self.validation_count += 1

        if not validation_result.is_valid:
            raise ValueError(f"Configuration validation failed: {validation_result.errors}")

        # Create configuration entry
        version = self._generate_version()
        checksum = self._calculate_checksum(data)

        entry = ConfigEntry(
            config_type=config_type,
            data=data,
            version=version,
            timestamp=datetime.utcnow(),
            environment=self.environment,
            checksum=checksum,
            metadata={"loaded_from": "file" if data is None else "data"}
        )

        # Store configuration
        if config_type not in self.configs:
            self.configs[config_type] = ConfigHistory(config_type)

        self.configs[config_type].add_version(entry)

        # Cache configuration
        await self._cache_config(cache_key, data)

        # Start watching file if not already watching
        if not self.watching.get(config_type):
            await self._start_watching(config_type)

        self.logger.info(f"Loaded {config_type.value} configuration (version: {version})")
        return data

    async def update_config(self, config_type: ConfigType, new_data: Dict[str, Any], comment: str = "") -> bool:
        """
        Update configuration.

        Args:
            config_type: Type of configuration to update
            new_data: New configuration data
            comment: Update comment

        Returns:
            True if update successful
        """
        self.update_count += 1

        # Validate new configuration
        validation_result = self.validator.validate_config(new_data, config_type)
        if not validation_result.is_valid:
            self.logger.error(f"Configuration update validation failed: {validation_result.errors}")
            return False

        # Create new version
        version = self._generate_version()
        checksum = self._calculate_checksum(new_data)

        entry = ConfigEntry(
            config_type=config_type,
            data=new_data,
            version=version,
            timestamp=datetime.utcnow(),
            environment=self.environment,
            checksum=checksum,
            metadata={"comment": comment, "update_source": "api"}
        )

        # Update configuration
        if config_type not in self.configs:
            self.configs[config_type] = ConfigHistory(config_type)

        old_version = self.configs[config_type].current_version
        self.configs[config_type].add_version(entry)

        # Save to file
        await self._save_config_to_file(config_type, new_data)

        # Update cache
        cache_key = f"{config_type.value}_{self.environment.value}"
        await self._cache_config(cache_key, new_data)

        # Notify callbacks
        await self._notify_change_callbacks(config_type, old_version, version)

        self.logger.info(f"Updated {config_type.value} configuration (version: {version})")
        return True

    async def get_config(self, config_type: ConfigType, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get configuration.

        Args:
            config_type: Type of configuration to get
            version: Specific version (if None, gets current)

        Returns:
            Configuration data or None
        """
        if config_type not in self.configs:
            return None

        if version:
            entry = self.configs[config_type].get_version(version)
        else:
            entry = self.configs[config_type].versions[0] if self.configs[config_type].versions else None

        return entry.data if entry else None

    async def watch_config(self, config_type: ConfigType, callback: Callable):
        """
        Watch configuration for changes.

        Args:
            config_type: Type of configuration to watch
            callback: Callback function to call on changes
        """
        if config_type not in self.change_callbacks:
            self.change_callbacks[config_type] = []

        self.change_callbacks[config_type].append(callback)

        # Start watching if not already watching
        if not self.watching.get(config_type):
            await self._start_watching(config_type)

        self.logger.debug(f"Watching {config_type.value} configuration for changes")

    async def rollback_config(self, config_type: ConfigType, target_version: str) -> bool:
        """
        Rollback configuration to specific version.

        Args:
            config_type: Type of configuration to rollback
            target_version: Target version to rollback to

        Returns:
            True if rollback successful
        """
        if config_type not in self.configs:
            return False

        history = self.configs[config_type]
        target_entry = history.get_version(target_version)

        if not target_entry:
            self.logger.error(f"Version {target_version} not found for {config_type.value}")
            return False

        # Perform rollback
        old_version = history.current_version
        success = await self.update_config(
            config_type,
            target_entry.data,
            comment=f"Rollback from {old_version} to {target_version}"
        )

        if success:
            self.logger.info(f"Rolled back {config_type.value} to version {target_version}")
        else:
            self.logger.error(f"Failed to rollback {config_type.value} to version {target_version}")

        return success

    async def list_versions(self, config_type: ConfigType) -> List[Dict[str, Any]]:
        """
        List configuration versions.

        Args:
            config_type: Type of configuration

        Returns:
            List of version information
        """
        if config_type not in self.configs:
            return []

        return [
            {
                "version": entry.version,
                "timestamp": entry.timestamp.isoformat(),
                "environment": entry.environment.value,
                "checksum": entry.checksum,
                "metadata": entry.metadata,
                "is_current": entry.version == self.configs[config_type].current_version
            }
            for entry in self.configs[config_type].versions
        ]

    async def compare_versions(self, config_type: ConfigType, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two configuration versions.

        Args:
            config_type: Type of configuration
            version1: First version
            version2: Second version

        Returns:
            Comparison result
        """
        if config_type not in self.configs:
            return {"error": "Configuration not found"}

        history = self.configs[config_type]
        entry1 = history.get_version(version1)
        entry2 = history.get_version(version2)

        if not entry1 or not entry2:
            return {"error": "One or both versions not found"}

        # Compare configurations
        diff = self._compare_configs(entry1.data, entry2.data)

        return {
            "version1": {
                "version": version1,
                "timestamp": entry1.timestamp.isoformat(),
                "checksum": entry1.checksum
            },
            "version2": {
                "version": version2,
                "timestamp": entry2.timestamp.isoformat(),
                "checksum": entry2.checksum
            },
            "differences": diff
        }

    async def export_config(self, config_type: ConfigType, file_path: str, include_metadata: bool = True):
        """
        Export configuration to file.

        Args:
            config_type: Type of configuration to export
            file_path: Export file path
            include_metadata: Whether to include metadata
        """
        if config_type not in self.configs:
            raise ValueError(f"Configuration {config_type.value} not found")

        current_config = await self.get_config(config_type)
        if not current_config:
            raise ValueError(f"No current configuration for {config_type.value}")

        export_data = {"config": current_config}
        if include_metadata:
            history = self.configs[config_type]
            export_data["metadata"] = {
                "config_type": config_type.value,
                "current_version": history.current_version,
                "environment": self.environment.value,
                "export_timestamp": datetime.utcnow().isoformat(),
                "total_versions": len(history.versions)
            }

        with open(file_path, 'w') as f:
            yaml.dump(export_data, f, default_flow_style=False)

        self.logger.info(f"Exported {config_type.value} configuration to {file_path}")

    async def import_config(self, file_path: str, config_type: Optional[ConfigType] = None) -> bool:
        """
        Import configuration from file.

        Args:
            file_path: Import file path
            config_type: Type of configuration (if None, inferred from file)

        Returns:
            True if import successful
        """
        try:
            with open(file_path, 'r') as f:
                import_data = yaml.safe_load(f)

            if "config" not in import_data:
                raise ValueError("Invalid configuration file format")

            config_data = import_data["config"]

            # Infer config type if not provided
            if config_type is None:
                if "config_type" in import_data.get("metadata", {}):
                    config_type = ConfigType(import_data["metadata"]["config_type"])
                else:
                    # Try to infer from content
                    config_type = self._infer_config_type(config_data)

            if not config_type:
                raise ValueError("Cannot determine configuration type")

            # Import configuration
            comment = import_data.get("metadata", {}).get("import_comment", f"Imported from {file_path}")
            return await self.update_config(config_type, config_data, comment)

        except Exception as e:
            self.logger.error(f"Failed to import configuration from {file_path}: {e}")
            return False

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get configuration management metrics.

        Returns:
            Metrics dictionary
        """
        total_cache_requests = self.cache_hits + self.cache_misses

        return {
            "loads": self.load_count,
            "updates": self.update_count,
            "validations": self.validation_count,
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.cache_hits / total_cache_requests if total_cache_requests > 0 else 0,
                "size": len(self.cache)
            },
            "configs": {
                "total": len(self.configs),
                "watched": len([w for w in self.watching.values() if w]),
                "callbacks": {ct.value: len(cbs) for ct, cbs in self.change_callbacks.items()}
            },
            "versions": {
                "total_versions": sum(len(h.versions) for h in self.configs.values()),
                "average_versions_per_config": sum(len(h.versions) for h in self.configs.values()) / len(self.configs) if self.configs else 0
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.

        Returns:
            Health check results
        """
        # Check all configurations are valid
        invalid_configs = []
        for config_type, history in self.configs.items():
            if history.versions:
                current = history.versions[0]
                validation = self.validator.validate_config(current.data, config_type)
                if not validation.is_valid:
                    invalid_configs.append({
                        "config_type": config_type.value,
                        "version": current.version,
                        "errors": validation.errors
                    })

        return {
            "status": "healthy" if not invalid_configs else "degraded",
            "total_configs": len(self.configs),
            "invalid_configs": invalid_configs,
            "watcher_status": self.watcher.get_status(),
            "cache_status": "normal" if len(self.cache) < 1000 else "warning",
            "environment": self.environment.value
        }

    async def shutdown(self):
        """Shutdown configuration manager."""
        self.logger.info("Shutting down configuration manager")

        # Stop file watcher
        self.watcher.stop()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        # Clear cache
        self.cache.clear()

        self.logger.info("Configuration manager shutdown complete")

    # Helper methods
    async def _load_config_from_file(self, config_type: ConfigType) -> Dict[str, Any]:
        """Load configuration from file."""
        config_file = self.config_dir / f"{config_type.value}.yaml"
        env_config_file = self.config_dir / f"{self.environment.value}_{config_type.value}.yaml"

        # Try environment-specific file first
        if env_config_file.exists():
            with open(env_config_file, 'r') as f:
                return yaml.safe_load(f)

        # Fall back to default file
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)

        # Return empty config if no file exists
        return {}

    async def _save_config_to_file(self, config_type: ConfigType, data: Dict[str, Any]):
        """Save configuration to file."""
        config_file = self.config_dir / f"{self.environment.value}_{config_type.value}.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    async def _start_watching(self, config_type: ConfigType):
        """Start watching configuration file."""
        config_file = self.config_dir / f"{config_type.value}.yaml"
        env_config_file = self.config_dir / f"{self.environment.value}_{config_type.value}.yaml"

        if env_config_file.exists():
            self.watcher.watch_file(env_config_file, config_type)
        elif config_file.exists():
            self.watcher.watch_file(config_file, config_type)

        self.watching[config_type] = True

    async def _notify_change_callbacks(self, config_type: ConfigType, old_version: str, new_version: str):
        """Notify change callbacks."""
        if config_type in self.change_callbacks:
            current_config = await self.get_config(config_type)
            for callback in self.change_callbacks[config_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(config_type, current_config, old_version, new_version)
                    else:
                        callback(config_type, current_config, old_version, new_version)
                except Exception as e:
                    self.logger.error(f"Error in change callback for {config_type.value}: {e}")

    async def _get_cached_config(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached configuration."""
        async with self.cache_lock:
            return self.cache.get(cache_key)

    async def _cache_config(self, cache_key: str, data: Dict[str, Any]):
        """Cache configuration."""
        async with self.cache_lock:
            self.cache[cache_key] = data

    def _generate_version(self) -> str:
        """Generate version identifier."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_part = os.urandom(3).hex()
        return f"v{timestamp}_{random_part}"

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate configuration checksum."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _compare_configs(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two configurations."""
        # This is a simple comparison - in production, use more sophisticated diff
        differences = []

        def _compare_recursive(path: str, obj1: Any, obj2: Any):
            if type(obj1) != type(obj2):
                differences.append({
                    "path": path,
                    "type": "type_change",
                    "old_value": str(obj1),
                    "new_value": str(obj2)
                })
            elif isinstance(obj1, dict):
                for key in set(obj1.keys()) | set(obj2.keys()):
                    new_path = f"{path}.{key}" if path else key
                    if key not in obj1:
                        differences.append({
                            "path": new_path,
                            "type": "added",
                            "value": obj2[key]
                        })
                    elif key not in obj2:
                        differences.append({
                            "path": new_path,
                            "type": "removed",
                            "value": obj1[key]
                        })
                    else:
                        _compare_recursive(new_path, obj1[key], obj2[key])
            elif obj1 != obj2:
                differences.append({
                    "path": path,
                    "type": "value_change",
                    "old_value": obj1,
                    "new_value": obj2
                })

        _compare_recursive("", config1, config2)
        return differences

    def _infer_config_type(self, data: Dict[str, Any]) -> Optional[ConfigType]:
        """Infer configuration type from data."""
        # Simple inference based on top-level keys
        if "providers" in data:
            return ConfigType.LLM
        elif "indicators" in data:
            return ConfigType.TECHNICAL_INDICATORS
        elif "signals" in data:
            return ConfigType.SIGNALS
        elif "output" in data:
            return ConfigType.OUTPUT
        return None

    # Schema definitions
    def _get_technical_indicators_schema(self) -> Dict[str, Any]:
        """Get technical indicators schema."""
        return {
            "type": "object",
            "properties": {
                "trend": {
                    "type": "object",
                    "properties": {
                        "sma": {"type": "object"},
                        "ema": {"type": "object"},
                        "macd": {"type": "object"}
                    }
                },
                "momentum": {
                    "type": "object",
                    "properties": {
                        "rsi": {"type": "object"},
                        "stochastic": {"type": "object"}
                    }
                },
                "volatility": {
                    "type": "object",
                    "properties": {
                        "bollinger_bands": {"type": "object"},
                        "atr": {"type": "object"}
                    }
                }
            }
        }

    def _get_llm_schema(self) -> Dict[str, Any]:
        """Get LLM configuration schema."""
        return {
            "type": "object",
            "properties": {
                "providers": {"type": "object"},
                "cost_control": {"type": "object"},
                "templates": {"type": "object"}
            },
            "required": ["providers", "cost_control"]
        }

    def _get_signals_schema(self) -> Dict[str, Any]:
        """Get signals configuration schema."""
        return {
            "type": "object",
            "properties": {
                "thresholds": {"type": "object"},
                "risk_management": {"type": "object"}
            },
            "required": ["thresholds", "risk_management"]
        }

    def _get_output_schema(self) -> Dict[str, Any]:
        """Get output configuration schema."""
        return {
            "type": "object",
            "properties": {
                "format": {"type": "string"},
                "channels": {"type": "array"}
            },
            "required": ["format", "channels"]
        }