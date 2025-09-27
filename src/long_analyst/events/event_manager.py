"""
Event Manager for the Long Analyst Agent.

Provides event-driven architecture for real-time processing,
component communication, and system coordination.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass
from datetime import datetime
import weakref
from collections import defaultdict, deque

from .event_types import Event, EventType, EventPriority, EventStatus, create_error_event
from ..utils.performance_monitor import PerformanceMonitor


@dataclass
class EventSubscription:
    """Event subscription information."""
    event_type: EventType
    handler: Callable
    priority: int = 0
    filter_func: Optional[Callable[[Event], bool]] = None
    is_active: bool = True


class EventManager:
    """
    Central event management system.

    Handles event creation, routing, subscription management,
    and provides event-driven communication between components.
    """

    def __init__(self, max_queue_size: int = 10000, max_concurrent_handlers: int = 100):
        """Initialize the event manager."""
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()

        # Event queue and processing
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.max_concurrent_handlers = max_concurrent_handlers
        self.is_running = False

        # Subscription management
        self.subscriptions: Dict[EventType, List[EventSubscription]] = defaultdict(list)
        self.wildcard_subscriptions: List[EventSubscription] = []

        # Event processing metrics
        self.events_processed = 0
        self.events_failed = 0
        self.average_processing_time = 0.0

        # Event history for debugging
        self.event_history: deque = deque(maxlen=1000)
        self.failed_events: deque = deque(maxlen=100)

        # Background tasks
        self.processing_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the event manager."""
        if self.is_running:
            self.logger.warning("Event manager is already running")
            return

        self.logger.info("Starting event manager")
        self.is_running = True

        # Start event processing task
        self.processing_task = asyncio.create_task(self._process_events())

        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_events())

        self.logger.info("Event manager started successfully")

    async def stop(self):
        """Stop the event manager."""
        if not self.is_running:
            self.logger.warning("Event manager is not running")
            return

        self.logger.info("Stopping event manager")
        self.is_running = False

        # Cancel background tasks
        if self.processing_task:
            self.processing_task.cancel()

        if self.cleanup_task:
            self.cleanup_task.cancel()

        # Wait for tasks to complete
        if self.processing_task:
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

        if self.cleanup_task:
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Event manager stopped successfully")

    def subscribe(self, event_type: EventType, handler: Callable,
                  priority: int = 0, filter_func: Optional[Callable[[Event], bool]] = None) -> str:
        """
        Subscribe to events.

        Args:
            event_type: Type of events to subscribe to
            handler: Function to call when event occurs
            priority: Handler priority (higher = called first)
            filter_func: Optional function to filter events

        Returns:
            Subscription ID
        """
        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
            priority=priority,
            filter_func=filter_func
        )

        if event_type == EventType.SYSTEM_ERROR:  # Wildcard for all events
            self.wildcard_subscriptions.append(subscription)
        else:
            self.subscriptions[event_type].append(subscription)

        # Sort subscriptions by priority
        self.subscriptions[event_type].sort(key=lambda x: x.priority, reverse=True)

        subscription_id = f"{event_type.value}_{len(self.subscriptions[event_type])}"
        self.logger.debug(f"Added subscription: {subscription_id}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.

        Args:
            subscription_id: Subscription ID to remove

        Returns:
            True if subscription was removed, False if not found
        """
        # Search in specific subscriptions
        for event_type, subscriptions in self.subscriptions.items():
            for i, subscription in enumerate(subscriptions):
                if f"{event_type.value}_{i}" == subscription_id:
                    subscription.is_active = False
                    subscriptions.remove(subscription)
                    self.logger.debug(f"Removed subscription: {subscription_id}")
                    return True

        # Search in wildcard subscriptions
        for i, subscription in enumerate(self.wildcard_subscriptions):
            if f"wildcard_{i}" == subscription_id:
                subscription.is_active = False
                self.wildcard_subscriptions.remove(subscription)
                self.logger.debug(f"Removed wildcard subscription: {subscription_id}")
                return True

        self.logger.warning(f"Subscription not found: {subscription_id}")
        return False

    async def emit(self, event_type: EventType, data: Dict[str, Any] = None,
                   source: str = "system", target: Optional[str] = None,
                   priority: EventPriority = EventPriority.NORMAL,
                   correlation_id: Optional[str] = None) -> Event:
        """
        Emit an event.

        Args:
            event_type: Type of event to emit
            data: Event data payload
            source: Event source
            target: Event target (optional)
            priority: Event priority
            correlation_id: Correlation ID for tracing

        Returns:
            Created event
        """
        if not self.is_running:
            self.logger.warning(f"Event manager not running, cannot emit event: {event_type.value}")
            # Create event but don't queue it
            return Event(
                event_type=event_type,
                data=data or {},
                source=source,
                target=target,
                priority=priority,
                correlation_id=correlation_id
            )

        event = Event(
            event_type=event_type,
            data=data or {},
            source=source,
            target=target,
            priority=priority,
            correlation_id=correlation_id
        )

        try:
            # Add to queue
            await self.event_queue.put(event)
            self.logger.debug(f"Event queued: {event.event_type.value} from {event.source}")

            # Add to history
            self.event_history.append(event)

            return event

        except asyncio.QueueFull:
            self.logger.error(f"Event queue full, dropping event: {event.event_type.value}")
            failed_event = event.copy()
            failed_event.fail_processing("Event queue full")
            self.failed_events.append(failed_event)
            return event

    async def emit_event(self, event: Event) -> bool:
        """
        Emit a pre-created event.

        Args:
            event: Event to emit

        Returns:
            True if event was queued successfully
        """
        if not self.is_running:
            self.logger.warning(f"Event manager not running, cannot emit event: {event.event_type.value}")
            return False

        try:
            await self.event_queue.put(event)
            self.logger.debug(f"Event queued: {event.event_type.value} from {event.source}")
            self.event_history.append(event)
            return True

        except asyncio.QueueFull:
            self.logger.error(f"Event queue full, dropping event: {event.event_type.value}")
            failed_event = event.copy()
            failed_event.fail_processing("Event queue full")
            self.failed_events.append(failed_event)
            return False

    async def _process_events(self):
        """Process events from the queue."""
        self.logger.info("Starting event processing loop")

        handlers = []

        while self.is_running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                # Start processing
                event.start_processing()

                # Find handlers for this event
                event_handlers = self._find_handlers(event)

                # Create handler tasks
                handler_tasks = []
                for subscription in event_handlers:
                    if subscription.is_active:
                        task = asyncio.create_task(
                            self._execute_handler(subscription, event)
                        )
                        handler_tasks.append(task)

                # Execute handlers concurrently
                if handler_tasks:
                    await asyncio.gather(*handler_tasks, return_exceptions=True)

                # Complete event processing
                event.complete_processing()

                # Update metrics
                self.events_processed += 1
                processing_time = event.processing_duration or 0
                self.average_processing_time = (
                    (self.average_processing_time * (self.events_processed - 1) + processing_time) /
                    self.events_processed
                )

                # Record performance metric
                self.performance_monitor.record_metric("event_processing_time", processing_time)
                self.performance_monitor.record_metric("events_handled", 1)

                # Mark task as done
                self.event_queue.task_done()

            except asyncio.TimeoutError:
                # No events in queue, continue loop
                continue

            except Exception as e:
                self.logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(1)  # Prevent rapid error loops

        self.logger.info("Event processing loop stopped")

    def _find_handlers(self, event: Event) -> List[EventSubscription]:
        """Find all handlers that should process this event."""
        handlers = []

        # Add specific handlers for this event type
        if event.event_type in self.subscriptions:
            for subscription in self.subscriptions[event.event_type]:
                if subscription.is_active:
                    if subscription.filter_func is None or subscription.filter_func(event):
                        handlers.append(subscription)

        # Add wildcard handlers
        for subscription in self.wildcard_subscriptions:
            if subscription.is_active:
                if subscription.filter_func is None or subscription.filter_func(event):
                    handlers.append(subscription)

        return handlers

    async def _execute_handler(self, subscription: EventSubscription, event: Event):
        """Execute a single event handler."""
        try:
            # Call the handler
            if asyncio.iscoroutinefunction(subscription.handler):
                await subscription.handler(event)
            else:
                subscription.handler(event)

        except Exception as e:
            self.logger.error(f"Error in event handler for {event.event_type.value}: {e}")
            # Create error event
            error_event = create_error_event(
                error_message=f"Handler error: {str(e)}",
                source="event_manager",
                correlation_id=event.correlation_id
            )
            await self.emit_event(error_event)

    async def _cleanup_events(self):
        """Cleanup old events and failed events."""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes

                # Clean up old history events (keep only last 1000)
                while len(self.event_history) > 1000:
                    self.event_history.popleft()

                # Clean up old failed events (keep only last 100)
                while len(self.failed_events) > 100:
                    self.failed_events.popleft()

                self.logger.debug("Event cleanup completed")

            except Exception as e:
                self.logger.error(f"Error in event cleanup: {e}")
                await asyncio.sleep(60)

    def get_metrics(self) -> Dict[str, Any]:
        """Get event manager metrics."""
        return {
            "is_running": self.is_running,
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "average_processing_time": self.average_processing_time,
            "queue_size": self.event_queue.qsize(),
            "active_subscriptions": sum(len(subs) for subs in self.subscriptions.values()),
            "wildcard_subscriptions": len(self.wildcard_subscriptions),
            "history_size": len(self.event_history),
            "failed_events_size": len(self.failed_events)
        }

    def get_event_history(self, event_type: Optional[EventType] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history, optionally filtered by type."""
        events = list(self.event_history)

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        events.reverse()  # Most recent first
        return [e.to_dict() for e in events[:limit]]

    def get_failed_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent failed events."""
        failed = list(self.failed_events)
        failed.reverse()
        return [e.to_dict() for e in failed[:limit]]

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the event manager."""
        health_status = {
            "status": "healthy",
            "metrics": self.get_metrics(),
            "queue_health": "normal",
            "processing_health": "normal"
        }

        # Check queue health
        queue_size = self.event_queue.qsize()
        if queue_size > 5000:
            health_status["queue_health"] = "warning"
        elif queue_size > 8000:
            health_status["queue_health"] = "critical"
            health_status["status"] = "degraded"

        # Check processing health
        if self.events_processed > 0:
            failure_rate = self.events_failed / self.events_processed
            if failure_rate > 0.1:  # 10% failure rate
                health_status["processing_health"] = "warning"
            elif failure_rate > 0.2:  # 20% failure rate
                health_status["processing_health"] = "critical"
                health_status["status"] = "degraded"

        return health_status

    def __str__(self) -> str:
        """String representation."""
        return f"EventManager(running={self.is_running}, processed={self.events_processed})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"EventManager(running={self.is_running}, "
                f"processed={self.events_processed}, failed={self.events_failed}, "
                f"queue_size={self.event_queue.qsize()})")