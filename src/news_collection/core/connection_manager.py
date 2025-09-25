import asyncio
import logging
from typing import Dict, List, Optional, Type
from datetime import datetime, timedelta
import weakref

from ..adapters.base_adapter import BaseNewsAdapter
from ..models import NewsSource, NewsSourceType, ConnectionStatus, HealthMetrics


class ConnectionManager:
    """Manages connections to multiple news sources."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._adapters: Dict[str, BaseNewsAdapter] = {}
        self._connection_statuses: Dict[str, ConnectionStatus] = {}
        self._adapter_classes: Dict[NewsSourceType, Type[BaseNewsAdapter]] = {}
        self._health_check_interval = 30  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._max_connections = 10
        self._active_connections = 0

    def register_adapter_class(self, source_type: NewsSourceType, adapter_class: Type[BaseNewsAdapter]) -> None:
        """
        Register an adapter class for a news source type.

        Args:
            source_type: News source type
            adapter_class: Adapter class
        """
        self._adapter_classes[source_type] = adapter_class
        self.logger.info(f"Registered adapter class for {source_type.value}")

    async def create_adapter(self, source_config: NewsSource) -> BaseNewsAdapter:
        """
        Create and initialize an adapter for a news source.

        Args:
            source_config: News source configuration

        Returns:
            Initialized adapter

        Raises:
            ValueError: If adapter class not found
        """
        if source_config.source_type not in self._adapter_classes:
            raise ValueError(f"No adapter class registered for {source_config.source_type}")

        adapter_class = self._adapter_classes[source_config.source_type]
        adapter = adapter_class(source_config)

        # Check connection limit
        if self._active_connections >= self._max_connections:
            self.logger.warning(f"Connection limit ({self._max_connections}) reached")
            await self._wait_for_connection_slot()

        await adapter.initialize()
        self._adapters[source_config.name] = adapter
        self._active_connections += 1

        # Initialize connection status
        self._connection_statuses[source_config.name] = ConnectionStatus(
            source_name=source_config.name,
            is_connected=True,
            response_time_ms=0,
            last_checked=datetime.now(),
        )

        self.logger.info(f"Created adapter for {source_config.name}")
        return adapter

    async def get_adapter(self, source_name: str) -> Optional[BaseNewsAdapter]:
        """
        Get an adapter by source name.

        Args:
            source_name: Name of the news source

        Returns:
            Adapter if found, None otherwise
        """
        return self._adapters.get(source_name)

    async def get_healthy_adapter(self, source_type: Optional[NewsSourceType] = None) -> Optional[BaseNewsAdapter]:
        """
        Get a healthy adapter, optionally filtered by source type.

        Args:
            source_type: Optional source type filter

        Returns:
            Healthy adapter if available, None otherwise
        """
        candidates = []
        for adapter in self._adapters.values():
            if source_type and adapter.source_config.source_type != source_type:
                continue

            if adapter.is_healthy():
                candidates.append(adapter)

        if not candidates:
            return None

        # Return adapter with highest priority (lowest priority number)
        return min(candidates, key=lambda a: a.source_config.priority)

    async def get_connection_status(self, source_name: str) -> Optional[ConnectionStatus]:
        """
        Get connection status for a source.

        Args:
            source_name: Name of the news source

        Returns:
            Connection status if found, None otherwise
        """
        return self._connection_statuses.get(source_name)

    async def get_all_connection_statuses(self) -> Dict[str, ConnectionStatus]:
        """Get connection statuses for all sources."""
        return self._connection_statuses.copy()

    async def test_all_connections(self) -> Dict[str, ConnectionStatus]:
        """Test connections for all adapters."""
        results = {}
        tasks = []

        for adapter in self._adapters.values():
            task = asyncio.create_task(self._test_single_connection(adapter))
            tasks.append((adapter.source_config.name, task))

        for name, task in tasks:
            try:
                status = await task
                results[name] = status
            except Exception as e:
                self.logger.error(f"Connection test failed for {name}: {str(e)}")
                results[name] = ConnectionStatus(
                    source_name=name,
                    is_connected=False,
                    response_time_ms=0,
                    last_checked=datetime.now(),
                    error_message=str(e),
                )

        return results

    async def _test_single_connection(self, adapter: BaseNewsAdapter) -> ConnectionStatus:
        """Test connection for a single adapter."""
        start_time = datetime.now()
        try:
            status = await adapter.test_connection()
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            # Update connection status
            status.response_time_ms = response_time
            status.last_checked = datetime.now()

            self._connection_statuses[adapter.source_config.name] = status
            return status

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            status = ConnectionStatus(
                source_name=adapter.source_config.name,
                is_connected=False,
                response_time_ms=response_time,
                last_checked=datetime.now(),
                error_message=str(e),
                consecutive_failures=adapter.get_failure_count(),
            )
            self._connection_statuses[adapter.source_config.name] = status
            return status

    async def start_health_monitoring(self) -> None:
        """Start health monitoring for all connections."""
        if self._health_check_task and not self._health_check_task.done():
            return

        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self.logger.info("Started health monitoring")

    async def stop_health_monitoring(self) -> None:
        """Stop health monitoring."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self.logger.info("Stopped health monitoring")

    async def _health_check_loop(self) -> None:
        """Health check loop."""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self.test_all_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {str(e)}")

    async def remove_adapter(self, source_name: str) -> None:
        """
        Remove an adapter and clean up resources.

        Args:
            source_name: Name of the news source
        """
        adapter = self._adapters.get(source_name)
        if adapter:
            await adapter.close()
            del self._adapters[source_name]
            if source_name in self._connection_statuses:
                del self._connection_statuses[source_name]
            self._active_connections -= 1
            self.logger.info(f"Removed adapter for {source_name}")

    async def _wait_for_connection_slot(self) -> None:
        """Wait for a connection slot to become available."""
        while self._active_connections >= self._max_connections:
            await asyncio.sleep(1)

    async def get_health_metrics(self) -> Dict[str, HealthMetrics]:
        """
        Get health metrics for all sources.

        Returns:
            Dictionary of health metrics by source name
        """
        metrics = {}
        for name, status in self._connection_statuses.items():
            # Calculate metrics (simplified version)
            uptime = 100.0 if status.is_connected else 0.0
            avg_response = status.response_time_ms
            success_rate = 100.0 if status.is_connected else 0.0

            metrics[name] = HealthMetrics(
                source_name=name,
                uptime_percentage=uptime,
                average_response_time_ms=avg_response,
                success_rate=success_rate,
                requests_per_minute=0,  # Would need request tracking
                error_count_24h=status.consecutive_failures,
                last_updated=datetime.now(),
            )

        return metrics

    async def close_all(self) -> None:
        """Close all adapters and clean up resources."""
        await self.stop_health_monitoring()

        tasks = []
        for adapter in self._adapters.values():
            task = asyncio.create_task(adapter.close())
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        self._adapters.clear()
        self._connection_statuses.clear()
        self._active_connections = 0
        self.logger.info("Closed all connections")