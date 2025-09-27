"""
Context Manager for LLM Integration.

Manages sliding window context for LLM analysis, including
historical data caching and context optimization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from collections import deque
import time

from ..models.market_data import MarketData


@dataclass
class ContextEntry:
    """Single context entry with metadata."""
    data: Dict[str, Any]
    timestamp: datetime
    priority: float = 1.0
    ttl_seconds: int = 3600  # 1 hour default

    def is_expired(self) -> bool:
        """Check if context entry has expired."""
        return datetime.utcnow() - self.timestamp > timedelta(seconds=self.ttl_seconds)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority,
            "ttl_seconds": self.ttl_seconds
        }


class ContextManager:
    """
    Advanced context manager for LLM analysis.

    Maintains a sliding window of relevant context data,
    optimizes context length, and manages priorities.
    """

    def __init__(self, max_context_size: int = 10, max_tokens: int = 4000):
        """
        Initialize context manager.

        Args:
            max_context_size: Maximum number of context entries to maintain
            max_tokens: Maximum tokens for context optimization
        """
        self.max_context_size = max_context_size
        self.max_tokens = max_tokens
        self.logger = logging.getLogger(__name__)

        # Context storage with priority queue
        self.context_queue: deque[ContextEntry] = deque(maxlen=max_context_size)
        self.context_lock = asyncio.Lock()

        # Context compression settings
        self.compression_ratio = 0.7  # Target compression ratio
        self.min_priority = 0.1  # Minimum priority threshold

        # Metrics
        self.total_updates = 0
        self.compression_operations = 0
        self.cache_hits = 0
        self.cache_misses = 0

        self.logger.info(f"Context manager initialized with max_size={max_context_size}, max_tokens={max_tokens}")

    async def update_context(self, market_data: MarketData, additional_context: Optional[Dict[str, Any]] = None):
        """
        Update context with new market data and additional context.

        Args:
            market_data: New market data to add to context
            additional_context: Additional context information
        """
        async with self.context_lock:
            # Create context entry
            context_entry = self._create_context_entry(market_data, additional_context)

            # Add to context queue
            self._add_to_context(context_entry)

            # Cleanup expired entries
            self._cleanup_expired_context()

            # Optimize context if needed
            if self._needs_optimization():
                await self._optimize_context()

            self.total_updates += 1
            self.logger.debug(f"Context updated for {market_data.symbol}, total entries: {len(self.context_queue)}")

    async def get_context(self, max_entries: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get current context data.

        Args:
            max_entries: Maximum number of entries to return

        Returns:
            List of context data entries
        """
        async with self.context_lock:
            # Sort by priority and timestamp
            sorted_context = sorted(
                self.context_queue,
                key=lambda x: (x.priority, x.timestamp),
                reverse=True
            )

            # Limit entries if requested
            if max_entries:
                sorted_context = sorted_context[:max_entries]

            # Convert to list of dictionaries
            context_data = [entry.to_dict() for entry in sorted_context if not entry.is_expired()]

            return context_data

    async def get_optimized_context(self, target_tokens: Optional[int] = None) -> str:
        """
        Get optimized context as formatted string for LLM.

        Args:
            target_tokens: Target token count for optimization

        Returns:
            Optimized context string
        """
        target_tokens = target_tokens or self.max_tokens
        context_entries = await self.get_context()

        if not context_entries:
            return "No historical context available."

        # Convert to formatted context
        context_parts = []
        current_tokens = 0

        for entry in context_entries:
            entry_str = self._format_context_entry(entry)
            estimated_tokens = len(entry_str.split()) * 1.3  # Rough token estimation

            if current_tokens + estimated_tokens <= target_tokens:
                context_parts.append(entry_str)
                current_tokens += estimated_tokens
            else:
                break

        optimized_context = "\n\n".join(context_parts)
        self.logger.debug(f"Optimized context generated: ~{current_tokens:.0f} tokens")
        return optimized_context

    async def add_manual_context(self, context_data: Dict[str, Any], priority: float = 1.0):
        """
        Add manual context entry.

        Args:
            context_data: Context data to add
            priority: Priority level (0.0 to 1.0)
        """
        async with self.context_lock:
            context_entry = ContextEntry(
                data=context_data,
                timestamp=datetime.utcnow(),
                priority=max(0.0, min(1.0, priority))
            )

            self._add_to_context(context_entry)
            self.logger.debug("Manual context entry added")

    async def clear_context(self):
        """Clear all context entries."""
        async with self.context_lock:
            self.context_queue.clear()
            self.logger.info("Context cleared")

    async def get_context_summary(self) -> Dict[str, Any]:
        """Get context summary statistics."""
        async with self.context_lock:
            active_entries = [entry for entry in self.context_queue if not entry.is_expired()]
            expired_entries = [entry for entry in self.context_queue if entry.is_expired()]

            return {
                "total_entries": len(self.context_queue),
                "active_entries": len(active_entries),
                "expired_entries": len(expired_entries),
                "max_size": self.max_context_size,
                "utilization_rate": len(self.context_queue) / self.max_context_size,
                "average_priority": sum(entry.priority for entry in active_entries) / len(active_entries) if active_entries else 0,
                "oldest_entry_age": (datetime.utcnow() - min(entry.timestamp for entry in active_entries)).total_seconds() if active_entries else 0,
                "total_updates": self.total_updates,
                "compression_operations": self.compression_operations,
                "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
            }

    def _create_context_entry(self, market_data: MarketData, additional_context: Optional[Dict[str, Any]]) -> ContextEntry:
        """Create context entry from market data."""
        # Extract key market data
        context_data = {
            "symbol": market_data.symbol,
            "timestamp": market_data.timestamp.isoformat(),
            "price": market_data.get_price(),
            "volume": market_data.get_volume(),
            "data_type": market_data.data_type.value,
            "source": market_data.source.value,
            "timeframe": market_data.timeframe.value if market_data.timeframe else None,
            "age_seconds": market_data.age_seconds
        }

        # Add OHLCV data if available
        if market_data.ohlcv_data and len(market_data.ohlcv_data) > 0:
            latest_ohlcv = market_data.ohlcv_data[-1]
            context_data["latest_ohlcv"] = {
                "open": latest_ohlcv.open,
                "high": latest_ohlcv.high,
                "low": latest_ohlcv.low,
                "close": latest_ohlcv.close,
                "volume": latest_ohlcv.volume
            }

        # Add additional context if provided
        if additional_context:
            context_data.update(additional_context)

        # Calculate priority based on data freshness and relevance
        priority = self._calculate_priority(market_data)

        return ContextEntry(
            data=context_data,
            timestamp=datetime.utcnow(),
            priority=priority,
            ttl_seconds=3600  # 1 hour TTL
        )

    def _calculate_priority(self, market_data: MarketData) -> float:
        """Calculate priority for context entry."""
        priority = 0.5  # Base priority

        # Higher priority for fresher data
        if market_data.age_seconds < 60:  # Less than 1 minute
            priority += 0.3
        elif market_data.age_seconds < 300:  # Less than 5 minutes
            priority += 0.2
        elif market_data.age_seconds < 900:  # Less than 15 minutes
            priority += 0.1

        # Higher priority for higher volume
        if market_data.get_volume() > 1000000:  # > 1M volume
            priority += 0.1

        # Higher priority for specific timeframes
        if market_data.timeframe and market_data.timeframe.value in ["1h", "4h", "1d"]:
            priority += 0.1

        return min(1.0, max(0.0, priority))

    def _add_to_context(self, context_entry: ContextEntry):
        """Add context entry to queue with priority-based insertion."""
        # Find insertion position based on priority
        insert_position = 0
        for i, existing_entry in enumerate(self.context_queue):
            if context_entry.priority > existing_entry.priority:
                insert_position = i
                break
            insert_position = i + 1

        # Insert at calculated position
        self.context_queue.insert(insert_position, context_entry)

        # Ensure we don't exceed max size
        while len(self.context_queue) > self.max_context_size:
            self.context_queue.pop()

    def _cleanup_expired_context(self):
        """Remove expired context entries."""
        initial_size = len(self.context_queue)
        self.context_queue = deque(
            [entry for entry in self.context_queue if not entry.is_expired()],
            maxlen=self.max_context_size
        )

        removed_count = initial_size - len(self.context_queue)
        if removed_count > 0:
            self.logger.debug(f"Removed {removed_count} expired context entries")

    def _needs_optimization(self) -> bool:
        """Check if context needs optimization."""
        # Estimate total tokens
        total_tokens = sum(len(str(entry.data)) * 1.3 for entry in self.context_queue)
        return total_tokens > self.max_tokens

    async def _optimize_context(self):
        """Optimize context to fit token limits."""
        self.compression_operations += 1
        self.logger.debug("Starting context optimization")

        # Sort by priority
        sorted_entries = sorted(self.context_queue, key=lambda x: x.priority, reverse=True)

        # Keep highest priority entries
        optimized_entries = []
        current_tokens = 0

        for entry in sorted_entries:
            entry_tokens = len(str(entry.data)) * 1.3
            if current_tokens + entry_tokens <= self.max_tokens * self.compression_ratio:
                optimized_entries.append(entry)
                current_tokens += entry_tokens
            else:
                break

        # Update context queue
        self.context_queue = deque(optimized_entries, maxlen=self.max_context_size)
        self.logger.debug(f"Context optimization completed: {len(optimized_entries)} entries, ~{current_tokens:.0f} tokens")

    def _format_context_entry(self, entry: Dict[str, Any]) -> str:
        """Format context entry for LLM consumption."""
        timestamp = datetime.fromisoformat(entry["timestamp"])
        data = entry["data"]

        formatted = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {data['symbol']} - Price: ${data['price']:.2f}, Volume: {data['volume']:,.0f}"

        if data.get('latest_ohlcv'):
            ohlcv = data['latest_ohlcv']
            formatted += f" (OHLC: ${ohlcv['open']:.2f}/${ohlcv['high']:.2f}/${ohlcv['low']:.2f}/${ohlcv['close']:.2f})"

        if data.get('timeframe'):
            formatted += f" [{data['timeframe']}]"

        return formatted

    async def search_context(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search context entries for specific criteria.

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            Matching context entries
        """
        async with self.context_lock:
            results = []
            query_lower = query.lower()

            for entry in self.context_queue:
                if entry.is_expired():
                    continue

                # Search in data fields
                entry_str = json.dumps(entry.data).lower()
                if query_lower in entry_str:
                    results.append(entry.to_dict())

                    if len(results) >= max_results:
                        break

            return results

    async def export_context(self, file_path: str):
        """Export context to file for backup/analysis."""
        async with self.context_lock:
            context_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "context_entries": [entry.to_dict() for entry in self.context_queue],
                "summary": await self.get_context_summary()
            }

            with open(file_path, 'w') as f:
                json.dump(context_data, f, indent=2)

            self.logger.info(f"Context exported to {file_path}")

    async def import_context(self, file_path: str):
        """Import context from file."""
        try:
            with open(file_path, 'r') as f:
                context_data = json.load(f)

            async with self.context_lock:
                self.context_queue.clear()

                for entry_data in context_data.get("context_entries", []):
                    context_entry = ContextEntry(
                        data=entry_data["data"],
                        timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                        priority=entry_data["priority"],
                        ttl_seconds=entry_data["ttl_seconds"]
                    )
                    self.context_queue.append(context_entry)

            self.logger.info(f"Context imported from {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to import context from {file_path}: {e}")
            raise