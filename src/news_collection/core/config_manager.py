"""
配置管理系统 - 动态配置和热更新
"""

import json
import yaml
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import asyncio
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..models.base import NewsSourceConfig, NewsCategory


@dataclass
class ConfigWatcherConfig:
    """配置监听器配置"""
    watch_files: bool = True
    watch_interval: int = 30  # seconds
    config_paths: List[str] = None
    backup_enabled: bool = True
    backup_count: int = 5

    def __post_init__(self):
        if self.config_paths is None:
            self.config_paths = []


class ConfigReloadHandler(FileSystemEventHandler):
    """配置文件重载处理器"""

    def __init__(self, callback):
        self.callback = callback
        self.logger = logging.getLogger(__name__)

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix in ['.json', '.yaml', '.yml']:
            self.logger.info(f"配置文件已修改: {file_path}")
            asyncio.create_task(self.callback(file_path))


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[str] = None,
                 watcher_config: Optional[ConfigWatcherConfig] = None):
        self.config_path = config_path or "config/news_sources.yaml"
        self.watcher_config = watcher_config or ConfigWatcherConfig()
        self._sources: Dict[str, NewsSourceConfig] = {}
        self._global_config: Dict[str, Any] = {}
        self._watcher: Optional[Observer] = None
        self._reload_callbacks: List[callable] = []
        self._logger = logging.getLogger(__name__)
        self._last_modified: Optional[datetime] = None
        self._file_hash: Optional[str] = None

    async def initialize(self) -> bool:
        """初始化配置管理器"""
        try:
            # 确保配置目录存在
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)

            # 加载配置
            success = await self.load_config()

            if not success:
                # 创建默认配置
                await self.create_default_config()
                success = await self.load_config()

            # 启动文件监听
            if self.watcher_config.watch_files:
                await self._start_file_watcher()

            return success

        except Exception as e:
            self._logger.error(f"初始化配置管理器失败: {e}")
            return False

    async def shutdown(self):
        """关闭配置管理器"""
        if self._watcher:
            self._watcher.stop()
            self._watcher.join()
            self._watcher = None

    async def load_config(self, config_path: Optional[str] = None) -> bool:
        """加载配置文件"""
        path = config_path or self.config_path

        try:
            if not os.path.exists(path):
                self._logger.error(f"配置文件不存在: {path}")
                return False

            with open(path, 'r', encoding='utf-8') as f:
                if path.endswith('.json'):
                    config_data = json.load(f)
                else:
                    config_data = yaml.safe_load(f)

            # 备份当前配置
            if self.watcher_config.backup_enabled:
                await self._backup_config(path)

            # 解析配置
            await self._parse_config(config_data)

            # 更新文件哈希
            self._update_file_hash(path)

            self._last_modified = datetime.now()
            self._logger.info(f"配置加载成功: {path}")

            # 触发重载回调
            await self._trigger_reload_callbacks()

            return True

        except Exception as e:
            self._logger.error(f"加载配置失败: {path}, 错误: {e}")
            return False

    async def save_config(self, config_path: Optional[str] = None) -> bool:
        """保存配置到文件"""
        path = config_path or self.config_path

        try:
            config_data = {
                'global_config': self._global_config,
                'sources': {name: asdict(config) for name, config in self._sources.items()}
            }

            # 备份现有配置
            if os.path.exists(path) and self.watcher_config.backup_enabled:
                await self._backup_config(path)

            with open(path, 'w', encoding='utf-8') as f:
                if path.endswith('.json'):
                    json.dump(config_data, f, indent=2, ensure_ascii=False, default=str)
                else:
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, default_str_style='|')

            self._update_file_hash(path)
            self._last_modified = datetime.now()
            self._logger.info(f"配置保存成功: {path}")

            return True

        except Exception as e:
            self._logger.error(f"保存配置失败: {path}, 错误: {e}")
            return False

    async def add_source(self, config: NewsSourceConfig) -> bool:
        """添加新闻源配置"""
        try:
            # 验证配置
            if not await self._validate_source_config(config):
                return False

            self._sources[config.name] = config
            self._logger.info(f"添加新闻源配置: {config.name}")

            # 自动保存
            await self.save_config()
            return True

        except Exception as e:
            self._logger.error(f"添加新闻源配置失败: {config.name}, 错误: {e}")
            return False

    async def remove_source(self, source_name: str) -> bool:
        """移除新闻源配置"""
        try:
            if source_name not in self._sources:
                self._logger.warning(f"新闻源配置不存在: {source_name}")
                return False

            del self._sources[source_name]
            self._logger.info(f"移除新闻源配置: {source_name}")

            # 自动保存
            await self.save_config()
            return True

        except Exception as e:
            self._logger.error(f"移除新闻源配置失败: {source_name}, 错误: {e}")
            return False

    async def update_source(self, source_name: str, **kwargs) -> bool:
        """更新新闻源配置"""
        try:
            if source_name not in self._sources:
                self._logger.error(f"新闻源配置不存在: {source_name}")
                return False

            config = self._sources[source_name]

            # 更新字段
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            # 验证更新后的配置
            if not await self._validate_source_config(config):
                return False

            self._logger.info(f"更新新闻源配置: {source_name}")

            # 自动保存
            await self.save_config()
            return True

        except Exception as e:
            self._logger.error(f"更新新闻源配置失败: {source_name}, 错误: {e}")
            return False

    def get_source_config(self, source_name: str) -> Optional[NewsSourceConfig]:
        """获取新闻源配置"""
        return self._sources.get(source_name)

    def get_all_sources(self) -> Dict[str, NewsSourceConfig]:
        """获取所有新闻源配置"""
        return self._sources.copy()

    def get_enabled_sources(self) -> List[NewsSourceConfig]:
        """获取启用的新闻源配置"""
        return [config for config in self._sources.values() if config.enabled]

    def get_global_config(self) -> Dict[str, Any]:
        """获取全局配置"""
        return self._global_config.copy()

    async def update_global_config(self, **kwargs) -> bool:
        """更新全局配置"""
        try:
            self._global_config.update(kwargs)
            self._logger.info("更新全局配置")

            # 自动保存
            await self.save_config()
            return True

        except Exception as e:
            self._logger.error(f"更新全局配置失败: {e}")
            return False

    def add_reload_callback(self, callback: callable):
        """添加配置重载回调"""
        self._reload_callbacks.append(callback)

    def remove_reload_callback(self, callback: callable):
        """移除配置重载回调"""
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)

    async def create_default_config(self):
        """创建默认配置"""
        default_sources = [
            NewsSourceConfig(
                name="coindesk",
                adapter_type="coindesk",
                base_url="https://api.coindesk.com/v1",
                rate_limit=60,
                timeout=30,
                priority=8
            ),
            NewsSourceConfig(
                name="cointelegraph",
                adapter_type="cointelegraph",
                base_url="https://cointelegraph.com/api/v1",
                rate_limit=100,
                timeout=30,
                priority=7
            ),
            NewsSourceConfig(
                name="decrypt",
                adapter_type="decrypt",
                base_url="https://api.decrypt.co/v1",
                rate_limit=50,
                timeout=30,
                priority=6
            )
        ]

        self._sources = {config.name: config for config in default_sources}
        self._global_config = {
            "version": "1.0.0",
            "default_timeout": 30,
            "max_retries": 3,
            "cache_enabled": True,
            "cache_ttl": 300,
            "log_level": "INFO"
        }

        await self.save_config()

    async def _parse_config(self, config_data: Dict[str, Any]):
        """解析配置数据"""
        # 解析全局配置
        if 'global_config' in config_data:
            self._global_config = config_data['global_config']

        # 解析新闻源配置
        sources_data = config_data.get('sources', {})
        self._sources.clear()

        for source_name, source_data in sources_data.items():
            try:
                config = NewsSourceConfig(
                    name=source_name,
                    adapter_type=source_data['adapter_type'],
                    base_url=source_data['base_url'],
                    api_key=source_data.get('api_key'),
                    rate_limit=source_data.get('rate_limit', 100),
                    timeout=source_data.get('timeout', 30),
                    headers=source_data.get('headers', {}),
                    enabled=source_data.get('enabled', True),
                    priority=source_data.get('priority', 1)
                )

                # 验证配置
                if await self._validate_source_config(config):
                    self._sources[source_name] = config
                else:
                    self._logger.warning(f"跳过无效配置: {source_name}")

            except Exception as e:
                self._logger.error(f"解析新闻源配置失败: {source_name}, 错误: {e}")

    async def _validate_source_config(self, config: NewsSourceConfig) -> bool:
        """验证新闻源配置"""
        try:
            # 基本字段验证
            if not config.name or not isinstance(config.name, str):
                self._logger.error(f"无效的名称: {config.name}")
                return False

            if not config.adapter_type or not isinstance(config.adapter_type, str):
                self._logger.error(f"无效的适配器类型: {config.adapter_type}")
                return False

            if not config.base_url or not isinstance(config.base_url, str):
                self._logger.error(f"无效的基础URL: {config.base_url}")
                return False

            # URL格式验证
            if not config.base_url.startswith(('http://', 'https://')):
                self._logger.error(f"无效的URL格式: {config.base_url}")
                return False

            # 数值范围验证
            if config.rate_limit <= 0:
                self._logger.error(f"无效的速率限制: {config.rate_limit}")
                return False

            if config.timeout <= 0:
                self._logger.error(f"无效的超时时间: {config.timeout}")
                return False

            if not (1 <= config.priority <= 10):
                self._logger.error(f"无效的优先级: {config.priority}")
                return False

            return True

        except Exception as e:
            self._logger.error(f"配置验证异常: {e}")
            return False

    async def _start_file_watcher(self):
        """启动文件监听"""
        try:
            config_dir = Path(self.config_path).parent

            self._watcher = Observer()
            handler = ConfigReloadHandler(self._on_file_changed)
            self._watcher.schedule(handler, str(config_dir), recursive=False)
            self._watcher.start()

            self._logger.info(f"启动文件监听: {config_dir}")

        except Exception as e:
            self._logger.error(f"启动文件监听失败: {e}")

    async def _on_file_changed(self, file_path: Path):
        """文件变化处理"""
        try:
            if str(file_path) == self.config_path:
                # 检查文件内容是否真的变化
                if await self._has_file_changed(str(file_path)):
                    await self.load_config(str(file_path))

        except Exception as e:
            self._logger.error(f"文件变化处理异常: {e}")

    async def _has_file_changed(self, file_path: str) -> bool:
        """检查文件内容是否变化"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                current_hash = hashlib.md5(content).hexdigest()

            if self._file_hash is None:
                return True

            return current_hash != self._file_hash

        except Exception:
            return True

    def _update_file_hash(self, file_path: str):
        """更新文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                self._file_hash = hashlib.md5(content).hexdigest()
        except Exception:
            self._file_hash = None

    async def _backup_config(self, file_path: str):
        """备份配置文件"""
        try:
            path = Path(file_path)
            backup_dir = path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{path.stem}_{timestamp}{path.suffix}"

            # 复制文件
            import shutil
            shutil.copy2(file_path, backup_path)

            # 清理旧备份
            backup_files = sorted(backup_dir.glob(f"{path.stem}_*{path.suffix}"), reverse=True)
            for old_backup in backup_files[self.watcher_config.backup_count:]:
                old_backup.unlink()

            self._logger.debug(f"配置备份成功: {backup_path}")

        except Exception as e:
            self._logger.error(f"配置备份失败: {e}")

    async def _trigger_reload_callbacks(self):
        """触发重载回调"""
        for callback in self._reload_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                self._logger.error(f"重载回调异常: {e}")

    def get_config_stats(self) -> Dict[str, Any]:
        """获取配置统计信息"""
        return {
            "total_sources": len(self._sources),
            "enabled_sources": len([s for s in self._sources.values() if s.enabled]),
            "last_modified": self._last_modified,
            "config_path": self.config_path,
            "file_watcher_enabled": self._watcher is not None,
            "reload_callbacks": len(self._reload_callbacks)
        }