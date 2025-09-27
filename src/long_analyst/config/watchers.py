"""
Configuration File Watchers.

Provides file system monitoring for configuration hot-reload capability.
"""

import asyncio
import logging
import time
from typing import Dict, Set, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from threading import Thread, Event
import os

from .schemas import ConfigType


@dataclass
class WatchedFile:
    """Information about a watched file."""
    file_path: Path
    config_type: ConfigType
    last_modified: float
    last_size: int
    callback: Optional[Callable] = None


class FileWatcher:
    """
    File system watcher for configuration files.

    Monitors file changes and triggers callbacks when modifications are detected.
    """

    def __init__(self, check_interval: float = 1.0):
        """
        Initialize file watcher.

        Args:
            check_interval: Interval in seconds to check for file changes
        """
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)

        self.watched_files: Dict[str, WatchedFile] = {}
        self.is_running = False
        self.stop_event = Event()
        self.watcher_thread: Optional[Thread] = None

        # Callbacks for file changes
        self.change_callbacks: Dict[ConfigType, list] = {}

    def start(self):
        """Start the file watcher."""
        if self.is_running:
            self.logger.warning("File watcher is already running")
            return

        self.is_running = True
        self.stop_event.clear()
        self.watcher_thread = Thread(target=self._watch_loop, daemon=True)
        self.watcher_thread.start()

        self.logger.info("File watcher started")

    def stop(self):
        """Stop the file watcher."""
        if not self.is_running:
            return

        self.is_running = False
        self.stop_event.set()

        if self.watcher_thread:
            self.watcher_thread.join(timeout=5.0)

        self.logger.info("File watcher stopped")

    def watch_file(self, file_path: Path, config_type: ConfigType, callback: Optional[Callable] = None):
        """
        Watch a file for changes.

        Args:
            file_path: Path to file to watch
            config_type: Type of configuration
            callback: Optional callback to call on file change
        """
        if not file_path.exists():
            self.logger.warning(f"Cannot watch non-existent file: {file_path}")
            return

        # Get initial file stats
        stat = file_path.stat()
        watched_file = WatchedFile(
            file_path=file_path,
            config_type=config_type,
            last_modified=stat.st_mtime,
            last_size=stat.st_size,
            callback=callback
        )

        file_key = str(file_path.absolute())
        self.watched_files[file_key] = watched_file

        self.logger.info(f"Watching file: {file_path}")

    def unwatch_file(self, file_path: Path):
        """
        Stop watching a file.

        Args:
            file_path: Path to file to unwatch
        """
        file_key = str(file_path.absolute())
        if file_key in self.watched_files:
            del self.watched_files[file_key]
            self.logger.info(f"Stopped watching file: {file_path}")

    def add_change_callback(self, config_type: ConfigType, callback: Callable):
        """
        Add callback for configuration changes.

        Args:
            config_type: Type of configuration
            callback: Callback function
        """
        if config_type not in self.change_callbacks:
            self.change_callbacks[config_type] = []

        self.change_callbacks[config_type].append(callback)

    def remove_change_callback(self, config_type: ConfigType, callback: Callable):
        """
        Remove callback for configuration changes.

        Args:
            config_type: Type of configuration
            callback: Callback function to remove
        """
        if config_type in self.change_callbacks:
            try:
                self.change_callbacks[config_type].remove(callback)
            except ValueError:
                pass

    def _watch_loop(self):
        """Main watcher loop."""
        while not self.stop_event.wait(self.check_interval):
            try:
                self._check_files()
            except Exception as e:
                self.logger.error(f"Error in file watcher loop: {e}")

    def _check_files(self):
        """Check all watched files for changes."""
        changed_files = []

        for file_key, watched_file in self.watched_files.items():
            try:
                if not watched_file.file_path.exists():
                    self.logger.warning(f"Watched file disappeared: {watched_file.file_path}")
                    continue

                stat = watched_file.file_path.stat()

                # Check if file was modified
                if stat.st_mtime != watched_file.last_modified or stat.st_size != watched_file.last_size:
                    self.logger.info(f"File changed: {watched_file.file_path}")

                    # Update watched file info
                    watched_file.last_modified = stat.st_mtime
                    watched_file.last_size = stat.st_size

                    changed_files.append(watched_file)

            except Exception as e:
                self.logger.error(f"Error checking file {watched_file.file_path}: {e}")

        # Process changed files
        for watched_file in changed_files:
            self._handle_file_change(watched_file)

    def _handle_file_change(self, watched_file: WatchedFile):
        """Handle file change event."""
        # Call file-specific callback
        if watched_file.callback:
            try:
                if asyncio.iscoroutinefunction(watched_file.callback):
                    # Create event loop if needed
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    loop.run_until_complete(watched_file.callback(watched_file.config_type))
                else:
                    watched_file.callback(watched_file.config_type)
            except Exception as e:
                self.logger.error(f"Error in file change callback: {e}")

        # Call registered callbacks for this config type
        if watched_file.config_type in self.change_callbacks:
            for callback in self.change_callbacks[watched_file.config_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        # Create event loop if needed
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)

                        loop.run_until_complete(callback(watched_file.config_type, str(watched_file.file_path)))
                    else:
                        callback(watched_file.config_type, str(watched_file.file_path))
                except Exception as e:
                    self.logger.error(f"Error in config change callback: {e}")

    def get_status(self) -> Dict[str, any]:
        """Get watcher status."""
        return {
            "is_running": self.is_running,
            "watched_files_count": len(self.watched_files),
            "watched_files": [str(wf.file_path) for wf in self.watched_files.values()],
            "check_interval": self.check_interval
        }

    def get_watched_files(self) -> Dict[str, Dict[str, any]]:
        """Get information about watched files."""
        return {
            file_key: {
                "file_path": str(wf.file_path),
                "config_type": wf.config_type.value,
                "last_modified": wf.last_modified,
                "last_size": wf.last_size,
                "exists": wf.file_path.exists()
            }
            for file_key, wf in self.watched_files.items()
        }


class ConfigWatcher:
    """
    High-level configuration watcher that integrates with the configuration manager.

    Provides automatic configuration reloading when files change.
    """

    def __init__(self, config_manager):
        """
        Initialize configuration watcher.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

        # File watcher
        self.file_watcher = FileWatcher(check_interval=1.0)

        # Debouncing to prevent rapid reloads
        self.debounce_times: Dict[ConfigType, float] = {}
        self.debounce_delay = 2.0  # seconds

        # Statistics
        self.reload_count = 0
        self.error_count = 0

        # Start watcher
        self.start()

    def start(self):
        """Start configuration watcher."""
        self.file_watcher.start()
        self.logger.info("Configuration watcher started")

    def stop(self):
        """Stop configuration watcher."""
        self.file_watcher.stop()
        self.logger.info("Configuration watcher stopped")

    def watch_file(self, file_path: Path, config_type: ConfigType):
        """
        Watch configuration file for changes.

        Args:
            file_path: Path to configuration file
            config_type: Type of configuration
        """
        callback = self._create_reload_callback(config_type)
        self.file_watcher.watch_file(file_path, config_type, callback)

    def unwatch_file(self, file_path: Path):
        """
        Stop watching configuration file.

        Args:
            file_path: Path to configuration file
        """
        self.file_watcher.unwatch_file(file_path)

    def _create_reload_callback(self, config_type: ConfigType):
        """Create reload callback for configuration type."""
        async def reload_callback(config_type_arg: ConfigType):
            """Reload configuration when file changes."""
            # Debounce rapid changes
            current_time = time.time()
            if config_type in self.debounce_times:
                if current_time - self.debounce_times[config_type] < self.debounce_delay:
                    return

            self.debounce_times[config_type] = current_time

            try:
                self.logger.info(f"Reloading {config_type.value} configuration due to file change")
                await self.config_manager.load_config(config_type)
                self.reload_count += 1

            except Exception as e:
                self.error_count += 1
                self.logger.error(f"Failed to reload {config_type.value} configuration: {e}")

        def sync_callback(config_type_arg: ConfigType):
            """Synchronous wrapper for reload callback."""
            asyncio.create_task(reload_callback(config_type_arg))

        return sync_callback

    def get_status(self) -> Dict[str, any]:
        """Get watcher status."""
        return {
            "file_watcher": self.file_watcher.get_status(),
            "reload_count": self.reload_count,
            "error_count": self.error_count,
            "debounce_delay": self.debounce_delay
        }

    def get_statistics(self) -> Dict[str, any]:
        """Get watcher statistics."""
        return {
            "total_reloads": self.reload_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(1, self.reload_count + self.error_count),
            "debounce_times": {ct.value: lt for ct, lt in self.debounce_times.items()}
        }