"""
配置管理模块

该模块负责做空分析师代理的配置管理，支持动态配置加载和热重载。
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
import threading

from ..core.architecture import ShortAnalystConfig


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "crypto_trading"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 100
    socket_timeout: int = 5


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: str = ""
    base_url: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.3
    timeout: int = 30
    max_retries: int = 3


@dataclass
class ExchangeConfig:
    """交易所配置"""
    api_key: str = ""
    secret: str = ""
    passphrase: Optional[str] = None
    sandbox: bool = True
    rate_limit: int = 100
    timeout: int = 10


@dataclass
class MonitoringConfig:
    """监控配置"""
    enable_metrics: bool = True
    metrics_port: int = 8000
    log_level: str = "INFO"
    log_file: str = "logs/short_analyst.log"
    enable_tracing: bool = True
    tracing_sample_rate: float = 0.1


@dataclass
class ShortAnalystFullConfig:
    """完整配置"""
    # 核心配置
    core: ShortAnalystConfig = field(default_factory=ShortAnalystConfig)

    # 数据库配置
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Redis配置
    redis: RedisConfig = field(default_factory=RedisConfig)

    # LLM配置
    llm: LLMConfig = field(default_factory=LLMConfig)

    # 交易所配置
    exchanges: Dict[str, ExchangeConfig] = field(default_factory=dict)

    # 监控配置
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # 其他配置
    environment: str = "development"
    debug: bool = False
    config_version: str = "1.0.0"
    last_updated: datetime = field(default_factory=datetime.now)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file or self._get_default_config_path()
        self._config: Optional[ShortAnalystFullConfig] = None
        self._config_lock = threading.RLock()
        self._last_modified = 0
        self._watch_thread: Optional[threading.Thread] = None
        self._watching = False

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 按优先级查找配置文件
        possible_paths = [
            os.environ.get("SHORT_ANALYST_CONFIG"),
            os.path.join(os.getcwd(), "config", "short_analyst.yaml"),
            os.path.join(os.path.expanduser("~"), ".short_analyst", "config.yaml"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "short_analyst.yaml")
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                return path

        # 如果没找到，返回默认路径
        return os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "short_analyst.yaml")

    def load_config(self) -> ShortAnalystFullConfig:
        """
        加载配置文件

        Returns:
            ShortAnalystFullConfig: 完整配置对象
        """
        with self._config_lock:
            if self._config is not None:
                return self._config

            try:
                # 如果配置文件不存在，创建默认配置
                if not os.path.exists(self.config_file):
                    self.logger.info(f"配置文件不存在，创建默认配置: {self.config_file}")
                    self._create_default_config()

                # 加载配置文件
                config_data = self._load_config_file(self.config_file)

                # 创建配置对象
                self._config = self._create_config_from_data(config_data)

                # 更新最后修改时间
                self._last_modified = os.path.getmtime(self.config_file)

                self.logger.info(f"配置加载成功: {self.config_file}")
                return self._config

            except Exception as e:
                self.logger.error(f"配置加载失败: {e}")
                # 返回默认配置
                self._config = ShortAnalystFullConfig()
                return self._config

    def _load_config_file(self, file_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f) or {}
            elif file_path.suffix.lower() == '.json':
                return json.load(f) or {}
            else:
                raise ValueError(f"不支持的配置文件格式: {file_path.suffix}")

    def _create_config_from_data(self, data: Dict[str, Any]) -> ShortAnalystFullConfig:
        """从配置数据创建配置对象"""
        try:
            # 创建核心配置
            core_data = data.get("core", {})
            core_config = ShortAnalystConfig(**core_data)

            # 创建数据库配置
            db_data = data.get("database", {})
            db_config = DatabaseConfig(**db_data)

            # 创建Redis配置
            redis_data = data.get("redis", {})
            redis_config = RedisConfig(**redis_data)

            # 创建LLM配置
            llm_data = data.get("llm", {})
            llm_config = LLMConfig(**llm_data)

            # 创建交易所配置
            exchanges_data = data.get("exchanges", {})
            exchanges_config = {
                name: ExchangeConfig(**exchange_data)
                for name, exchange_data in exchanges_data.items()
            }

            # 创建监控配置
            monitoring_data = data.get("monitoring", {})
            monitoring_config = MonitoringConfig(**monitoring_data)

            return ShortAnalystFullConfig(
                core=core_config,
                database=db_config,
                redis=redis_config,
                llm=llm_config,
                exchanges=exchanges_config,
                monitoring=monitoring_config,
                environment=data.get("environment", "development"),
                debug=data.get("debug", False),
                config_version=data.get("config_version", "1.0.0")
            )

        except Exception as e:
            self.logger.error(f"配置数据解析失败: {e}")
            raise ValueError(f"配置数据格式错误: {e}")

    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = ShortAnalystFullConfig()

        # 确保配置目录存在
        config_dir = os.path.dirname(self.config_file)
        os.makedirs(config_dir, exist_ok=True)

        # 保存默认配置
        self.save_config(default_config)

    def save_config(self, config: ShortAnalystFullConfig):
        """保存配置到文件"""
        try:
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, exist_ok=True)

            config_data = asdict(config)

            # 转换datetime对象为字符串
            config_data["last_updated"] = config.last_updated.isoformat()

            # 根据文件扩展名选择格式
            if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            else:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"配置保存成功: {self.config_file}")

        except Exception as e:
            self.logger.error(f"配置保存失败: {e}")
            raise

    def reload_config(self) -> bool:
        """
        重新加载配置文件

        Returns:
            bool: 是否成功重新加载
        """
        try:
            with self._config_lock:
                # 检查文件是否被修改
                current_modified = os.path.getmtime(self.config_file)
                if current_modified <= self._last_modified:
                    return False  # 文件未被修改

                # 重新加载配置
                config_data = self._load_config_file(self.config_file)
                self._config = self._create_config_from_data(config_data)
                self._last_modified = current_modified

                self.logger.info("配置重新加载成功")
                return True

        except Exception as e:
            self.logger.error(f"配置重新加载失败: {e}")
            return False

    def get_config(self) -> ShortAnalystFullConfig:
        """获取当前配置"""
        with self._config_lock:
            if self._config is None:
                self._config = self.load_config()
            return self._config

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        更新配置

        Args:
            updates: 配置更新字典

        Returns:
            bool: 是否成功更新
        """
        try:
            with self._config_lock:
                if self._config is None:
                    self._config = self.load_config()

                # 更新配置
                self._update_config_object(self._config, updates)

                # 保存配置
                self.save_config(self._config)

                self.logger.info("配置更新成功")
                return True

        except Exception as e:
            self.logger.error(f"配置更新失败: {e}")
            return False

    def _update_config_object(self, config: ShortAnalystFullConfig, updates: Dict[str, Any]):
        """递归更新配置对象"""
        for key, value in updates.items():
            if hasattr(config, key):
                if isinstance(value, dict) and hasattr(getattr(config, key), "__dict__"):
                    # 递归更新嵌套对象
                    self._update_config_object(getattr(config, key), value)
                else:
                    setattr(config, key, value)

    def get_core_config(self) -> ShortAnalystConfig:
        """获取核心配置"""
        return self.get_config().core

    def get_database_config(self) -> DatabaseConfig:
        """获取数据库配置"""
        return self.get_config().database

    def get_redis_config(self) -> RedisConfig:
        """获取Redis配置"""
        return self.get_config().redis

    def get_llm_config(self) -> LLMConfig:
        """获取LLM配置"""
        return self.get_config().llm

    def get_exchange_config(self, exchange_name: str) -> Optional[ExchangeConfig]:
        """获取交易所配置"""
        return self.get_config().exchanges.get(exchange_name)

    def get_monitoring_config(self) -> MonitoringConfig:
        """获取监控配置"""
        return self.get_config().monitoring

    def start_config_watcher(self):
        """启动配置文件监控"""
        if self._watching:
            return

        self._watching = True
        self._watch_thread = threading.Thread(target=self._watch_config_file, daemon=True)
        self._watch_thread.start()
        self.logger.info("配置文件监控已启动")

    def stop_config_watcher(self):
        """停止配置文件监控"""
        self._watching = False
        if self._watch_thread:
            self._watch_thread.join(timeout=1)
        self.logger.info("配置文件监控已停止")

    def _watch_config_file(self):
        """监控配置文件变化"""
        while self._watching:
            try:
                # 检查文件修改
                self.reload_config()
                threading.Event().wait(5)  # 每5秒检查一次

            except Exception as e:
                self.logger.error(f"配置文件监控错误: {e}")
                threading.Event().wait(10)  # 出错后等待10秒

    def validate_config(self) -> List[str]:
        """验证配置有效性"""
        errors = []

        config = self.get_config()

        # 验证核心配置
        if config.core.max_concurrent_requests <= 0:
            errors.append("最大并发请求数必须大于0")

        if config.core.target_latency_ms <= 0:
            errors.append("目标延迟必须大于0")

        if config.core.min_signal_strength < 0 or config.core.min_signal_strength > 1:
            errors.append("最小信号强度必须在0-1之间")

        # 验证数据库配置
        if not config.database.host:
            errors.append("数据库主机地址不能为空")

        if config.database.port <= 0:
            errors.append("数据库端口必须大于0")

        # 验证Redis配置
        if not config.redis.host:
            errors.append("Redis主机地址不能为空")

        if config.redis.port <= 0:
            errors.append("Redis端口必须大于0")

        # 验证LLM配置
        if not config.llm.provider:
            errors.append("LLM提供商不能为空")

        if not config.llm.api_key and config.llm.provider != "local":
            errors.append("LLM API密钥不能为空")

        return errors

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        config = self.get_config()

        return {
            "config_file": self.config_file,
            "environment": config.environment,
            "debug": config.debug,
            "config_version": config.config_version,
            "last_updated": config.last_updated.isoformat(),
            "core_config": {
                "max_concurrent_requests": config.core.max_concurrent_requests,
                "target_latency_ms": config.core.target_latency_ms,
                "enable_llm_analysis": config.core.enable_llm_analysis,
                "min_signal_strength": config.core.min_signal_strength
            },
            "exchanges": list(config.exchanges.keys()),
            "monitoring": {
                "enable_metrics": config.monitoring.enable_metrics,
                "log_level": config.monitoring.log_level
            }
        }


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> ShortAnalystFullConfig:
    """获取当前配置"""
    return get_config_manager().get_config()


def get_core_config() -> ShortAnalystConfig:
    """获取核心配置"""
    return get_config_manager().get_core_config()


def reload_config() -> bool:
    """重新加载配置"""
    return get_config_manager().reload_config()


def initialize_config(config_file: Optional[str] = None) -> ConfigManager:
    """初始化配置管理器"""
    global _config_manager
    _config_manager = ConfigManager(config_file)
    return _config_manager