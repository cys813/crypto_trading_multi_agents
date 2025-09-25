"""
Order Manager for managing trading order information.

This module provides functionality for collecting, tracking, and analyzing
order data from multiple cryptocurrency exchanges, including real-time order
monitoring, execution analysis, and order lifecycle management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import uuid

from .exchange_manager import ExchangeManager
from ..config.settings import get_settings
from ..models.database import get_session
from ..models.order import Order, OrderHistory, OrderMetrics, OrderType, OrderSide, OrderStatus
from ..utils.metrics import MetricsCollector
from ..utils.helpers import safe_float_conversion, format_timestamp


@dataclass
class OrderUpdate:
    """Represents an order update."""
    order_id: str
    exchange: str
    symbol: str
    update_type: str  # 'create', 'update', 'cancel', 'fill', 'expire'
    old_order: Optional[Dict] = None
    new_order: Optional[Dict] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class OrderManager:
    """Manages order data from multiple exchanges."""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.exchange_manager = ExchangeManager()
        self.metrics = MetricsCollector()

        # Order tracking
        self.orders: Dict[str, Order] = {}  # order_id -> Order
        self.orders_by_exchange: Dict[str, Dict[str, Order]] = {}  # exchange -> symbol -> List[Order]
        self.orders_by_symbol: Dict[str, Dict[str, Order]] = {}  # symbol -> exchange -> List[Order]

        # Order updates queue
        self.update_queue = asyncio.Queue()
        self.order_callbacks = []

        # Monitoring and statistics
        self.stats = {
            'total_orders': 0,
            'active_orders': 0,
            'filled_orders': 0,
            'cancelled_orders': 0,
            'expired_orders': 0,
            'rejected_orders': 0,
            'total_volume': 0.0,
            'total_fees': 0.0,
            'avg_fill_time': 0.0,
            'fill_rate': 0.0,
            'last_update': None,
            'monitored_exchanges': 0,
            'monitored_symbols': 0
        }

        # Background tasks
        self.monitor_task = None
        self.sync_task = None
        self.history_task = None
        self.metrics_task = None

        # Monitoring settings
        self.sync_interval = 15  # seconds
        self.history_interval = 300  # 5 minutes
        self.metrics_interval = 3600  # 1 hour

    async def start(self):
        """Start the order manager."""
        self.logger.info("Starting order manager")

        # Start background tasks
        await self.start_monitoring()
        await self.start_sync()
        await self.start_history_tracking()
        await self.start_metrics_tracking()

        # Initial sync
        await self.sync_all_orders()

        self.logger.info("Order manager started")

    async def stop(self):
        """Stop the order manager."""
        self.logger.info("Stopping order manager")

        # Cancel background tasks
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass

        if self.history_task:
            self.history_task.cancel()
            try:
                await self.history_task
            except asyncio.CancelledError:
                pass

        if self.metrics_task:
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Order manager stopped")

    async def start_monitoring(self):
        """Start order monitoring task."""
        async def monitor():
            while True:
                try:
                    await self.update_orders()
                    await asyncio.sleep(self.sync_interval)
                except Exception as e:
                    self.logger.error(f"Order monitoring error: {e}")
                    await asyncio.sleep(10)  # Wait before retrying

        self.monitor_task = asyncio.create_task(monitor())

    async def start_sync(self):
        """Start order sync task."""
        async def sync():
            while True:
                try:
                    await self.sync_all_orders()
                    await asyncio.sleep(self.sync_interval)
                except Exception as e:
                    self.logger.error(f"Order sync error: {e}")
                    await asyncio.sleep(10)  # Wait before retrying

        self.sync_task = asyncio.create_task(sync())

    async def start_history_tracking(self):
        """Start order history tracking task."""
        async def track_history():
            while True:
                try:
                    await self.record_order_history()
                    await asyncio.sleep(self.history_interval)
                except Exception as e:
                    self.logger.error(f"Order history tracking error: {e}")
                    await asyncio.sleep(30)  # Wait before retrying

        self.history_task = asyncio.create_task(track_history())

    async def start_metrics_tracking(self):
        """Start order metrics tracking task."""
        async def track_metrics():
            while True:
                try:
                    await self.calculate_order_metrics()
                    await asyncio.sleep(self.metrics_interval)
                except Exception as e:
                    self.logger.error(f"Order metrics tracking error: {e}")
                    await asyncio.sleep(60)  # Wait before retrying

        self.metrics_task = asyncio.create_task(track_metrics())

    async def sync_all_orders(self):
        """Sync orders from all exchanges."""
        exchanges = await self.exchange_manager.get_all_exchanges()

        for exchange in exchanges:
            try:
                await self.sync_exchange_orders(exchange)
            except Exception as e:
                self.logger.error(f"Failed to sync orders for {exchange}: {e}")

    async def sync_exchange_orders(self, exchange: str):
        """Sync orders from a specific exchange."""
        try:
            # Get orders from exchange
            raw_orders = await self.exchange_manager.get_orders(exchange)

            if not raw_orders:
                return

            # Process each order
            for raw_order in raw_orders:
                await self.process_order_update(exchange, raw_order)

            # Update statistics
            self.stats['monitored_exchanges'] = len(self.orders_by_exchange)
            self.stats['monitored_symbols'] = sum(len(orders) for orders in self.orders_by_exchange.values())

        except Exception as e:
            self.logger.error(f"Failed to sync orders from {exchange}: {e}")

    async def process_order_update(self, exchange: str, raw_order: Dict):
        """Process a single order update."""
        try:
            # Extract order details
            symbol = raw_order.get('symbol')
            order_id = raw_order.get('id')

            if not symbol or not order_id:
                self.logger.warning(f"Order update missing symbol or ID: {raw_order}")
                return

            # Create or update order
            order = await self._create_or_update_order(exchange, symbol, order_id, raw_order)

            if order:
                # Update tracking
                await self._update_order_tracking(order)

                # Determine update type
                update_type = self._determine_update_type(order)

                # Queue update
                update = OrderUpdate(
                    order_id=order_id,
                    exchange=exchange,
                    symbol=symbol,
                    update_type=update_type,
                    new_order=order.to_dict()
                )
                await self.update_queue.put(update)

                # Notify callbacks
                await self._notify_order_callbacks(update)

        except Exception as e:
            self.logger.error(f"Failed to process order update: {e}")

    async def _create_or_update_order(self, exchange: str, symbol: str, order_id: str,
                                    raw_order: Dict) -> Optional[Order]:
        """Create or update an order in the database."""
        try:
            session = get_session()

            # Check if order exists
            existing_order = session.query(Order).filter(
                Order.order_id == order_id
            ).first()

            # Extract order data
            order_type = self._parse_order_type(raw_order.get('type', 'limit'))
            side = self._parse_order_side(raw_order.get('side'))
            status = self._parse_order_status(raw_order.get('status'))
            price = safe_float_conversion(raw_order.get('price'))
            amount = safe_float_conversion(raw_order.get('amount', raw_order.get('quantity')))
            filled_amount = safe_float_conversion(raw_order.get('filled', raw_order.get('filled_quantity')))
            remaining_amount = amount - filled_amount if amount is not None else None

            # Parse timestamps
            created_at = format_timestamp(raw_order.get('datetime', raw_order.get('created_at')))
            updated_at = format_timestamp(raw_order.get('timestamp'))

            # Parse fees
            fee = raw_order.get('fee')
            fee_cost = 0.0
            fee_currency = None
            if fee:
                fee_cost = safe_float_conversion(fee.get('cost', 0))
                fee_currency = fee.get('currency')

            # Calculate cost and average price
            cost = safe_float_conversion(raw_order.get('cost'))
            average_price = safe_float_conversion(raw_order.get('average'))

            # Determine if order is filled
            if filled_amount >= amount and amount > 0:
                status = OrderStatus.FILLED
                if not existing_order or not existing_order.fill_timestamp:
                    updated_at = datetime.now(timezone.utc)  # Use current time for fill timestamp

            if existing_order:
                # Update existing order
                old_status = existing_order.status
                update_data = {
                    'status': status,
                    'price': price,
                    'amount': amount,
                    'filled_amount': filled_amount,
                    'remaining_amount': remaining_amount,
                    'cost': cost,
                    'average_price': average_price,
                    'fee_cost': fee_cost,
                    'fee_currency': fee_currency,
                    'updated_at': updated_at
                }

                # Update fields
                for key, value in update_data.items():
                    if value is not None:
                        setattr(existing_order, key, value)

                # Update fill status
                existing_order.update_fill_status()

                # Set fill timestamp if order was just filled
                if old_status != OrderStatus.FILLED and status == OrderStatus.FILLED:
                    existing_order.fill_timestamp = updated_at

                session.commit()
                order = existing_order

            else:
                # Create new order
                order = Order(
                    exchange=exchange,
                    symbol=symbol,
                    order_id=order_id,
                    order_type=order_type,
                    side=side,
                    status=status,
                    price=price,
                    amount=amount,
                    filled_amount=filled_amount,
                    remaining_amount=remaining_amount,
                    cost=cost,
                    average_price=average_price,
                    fee_cost=fee_cost,
                    fee_currency=fee_currency,
                    created_at=created_at,
                    updated_at=updated_at
                )

                session.add(order)
                session.commit()

                # Set fill timestamp if already filled
                if status == OrderStatus.FILLED:
                    order.fill_timestamp = created_at

            session.close()
            return order

        except Exception as e:
            self.logger.error(f"Failed to create/update order {order_id}: {e}")
            return None

    def _parse_order_type(self, order_type_str: str) -> OrderType:
        """Parse order type string to enum."""
        type_mapping = {
            'market': OrderType.MARKET,
            'limit': OrderType.LIMIT,
            'stop': OrderType.STOP,
            'stop_market': OrderType.STOP_MARKET,
            'stop_limit': OrderType.STOP_LIMIT,
            'take_profit': OrderType.TAKE_PROFIT,
            'take_profit_market': OrderType.TAKE_PROFIT_MARKET,
            'trailing_stop': OrderType.TRAILING_STOP
        }
        return type_mapping.get(order_type_str.lower(), OrderType.LIMIT)

    def _parse_order_side(self, side_str: str) -> OrderSide:
        """Parse order side string to enum."""
        if side_str and side_str.lower() == 'sell':
            return OrderSide.SELL
        return OrderSide.BUY

    def _parse_order_status(self, status_str: str) -> OrderStatus:
        """Parse order status string to enum."""
        status_mapping = {
            'open': OrderStatus.OPEN,
            'closed': OrderStatus.CLOSED,
            'canceled': OrderStatus.CANCELED,
            'cancelled': OrderStatus.CANCELED,
            'expired': OrderStatus.EXPIRED,
            'rejected': OrderStatus.REJECTED,
            'pending': OrderStatus.PENDING,
            'partially_filled': OrderStatus.PARTIALLY_FILLED,
            'filled': OrderStatus.FILLED
        }
        return status_mapping.get(status_str.lower(), OrderStatus.OPEN)

    def _determine_update_type(self, order: Order) -> str:
        """Determine the type of order update."""
        if order.status == OrderStatus.FILLED:
            return 'fill'
        elif order.status == OrderStatus.CANCELED:
            return 'cancel'
        elif order.status == OrderStatus.EXPIRED:
            return 'expire'
        elif order.status == OrderStatus.REJECTED:
            return 'reject'
        else:
            return 'update'

    async def _update_order_tracking(self, order: Order):
        """Update internal order tracking."""
        order_id = str(order.id)
        exchange = order.exchange
        symbol = order.symbol

        # Update main tracking
        self.orders[order_id] = order

        # Update by exchange
        if exchange not in self.orders_by_exchange:
            self.orders_by_exchange[exchange] = {}
        if symbol not in self.orders_by_exchange[exchange]:
            self.orders_by_exchange[exchange][symbol] = []
        if order not in self.orders_by_exchange[exchange][symbol]:
            self.orders_by_exchange[exchange][symbol].append(order)

        # Update by symbol
        if symbol not in self.orders_by_symbol:
            self.orders_by_symbol[symbol] = {}
        if exchange not in self.orders_by_symbol[symbol]:
            self.orders_by_symbol[symbol][exchange] = []
        if order not in self.orders_by_symbol[symbol][exchange]:
            self.orders_by_symbol[symbol][exchange].append(order)

        # Update statistics
        await self._update_order_stats()

    async def _update_order_stats(self):
        """Update order statistics."""
        all_orders = list(self.orders.values())

        self.stats['total_orders'] = len(all_orders)
        self.stats['active_orders'] = len([o for o in all_orders if o.is_active()])
        self.stats['filled_orders'] = len([o for o in all_orders if o.status == OrderStatus.FILLED])
        self.stats['cancelled_orders'] = len([o for o in all_orders if o.status == OrderStatus.CANCELED])
        self.stats['expired_orders'] = len([o for o in all_orders if o.status == OrderStatus.EXPIRED])
        self.stats['rejected_orders'] = len([o for o in all_orders if o.status == OrderStatus.REJECTED])

        # Calculate volume and fees
        self.stats['total_volume'] = sum(o.filled_amount for o in all_orders)
        self.stats['total_fees'] = sum(o.fee_cost for o in all_orders)

        # Calculate fill rate
        total_completed = self.stats['filled_orders'] + self.stats['cancelled_orders'] + self.stats['expired_orders']
        if total_completed > 0:
            self.stats['fill_rate'] = self.stats['filled_orders'] / total_completed

        # Calculate average fill time
        filled_orders = [o for o in all_orders if o.fill_timestamp and o.created_at]
        if filled_orders:
            fill_times = [(o.fill_timestamp - o.created_at).total_seconds() for o in filled_orders]
            self.stats['avg_fill_time'] = sum(fill_times) / len(fill_times)

        self.stats['last_update'] = datetime.now(timezone.utc)

    async def update_orders(self):
        """Update all active orders with current status."""
        try:
            # Get active orders
            active_orders = [o for o in self.orders.values() if o.is_active()]

            # Group by exchange and symbol
            exchange_symbol_pairs = set()
            for order in active_orders:
                exchange_symbol_pairs.add((order.exchange, order.symbol))

            # Update orders for each exchange-symbol pair
            for exchange, symbol in exchange_symbol_pairs:
                await self._update_exchange_symbol_orders(exchange, symbol)

        except Exception as e:
            self.logger.error(f"Failed to update orders: {e}")

    async def _update_exchange_symbol_orders(self, exchange: str, symbol: str):
        """Update orders for a specific exchange-symbol pair."""
        try:
            # Get current orders from exchange
            raw_orders = await self.exchange_manager.get_orders(exchange, symbol)

            if not raw_orders:
                return

            # Create a mapping of order IDs to raw orders
            current_orders = {order.get('id'): order for order in raw_orders}

            # Update existing orders
            existing_orders = self.orders_by_exchange.get(exchange, {}).get(symbol, [])
            for order in existing_orders:
                if order.order_id in current_orders:
                    # Update with current data
                    await self.process_order_update(exchange, current_orders[order.order_id])
                elif order.is_active():
                    # Order was removed from exchange but still active in our system
                    # Mark as cancelled/expired
                    order.status = OrderStatus.CANCELED
                    order.updated_at = datetime.now(timezone.utc)

                    # Update database
                    session = get_session()
                    try:
                        db_order = session.query(Order).filter(
                            Order.id == order.id
                        ).first()
                        if db_order:
                            db_order.status = OrderStatus.CANCELED
                            db_order.updated_at = datetime.now(timezone.utc)
                            session.commit()
                    except Exception as e:
                        session.rollback()
                        self.logger.error(f"Failed to update cancelled order: {e}")
                    finally:
                        session.close()

        except Exception as e:
            self.logger.error(f"Failed to update orders for {exchange}/{symbol}: {e}")

    async def record_order_history(self):
        """Record order history for all orders."""
        try:
            session = get_session()

            for order in self.orders.values():
                # Create history record for recent changes
                if order.updated_at and (datetime.now(timezone.utc) - order.updated_at) < timedelta(hours=1):
                    history = OrderHistory(
                        order_id=order.id,
                        event_type='update',
                        event_timestamp=order.updated_at,
                        status=order.status,
                        filled_amount=order.filled_amount,
                        remaining_amount=order.remaining_amount,
                        average_price=order.average_price,
                        fee_cost=order.fee_cost,
                        reason='periodic_update'
                    )

                    session.add(history)

            session.commit()
            session.close()

        except Exception as e:
            self.logger.error(f"Failed to record order history: {e}")

    async def calculate_order_metrics(self):
        """Calculate and store order metrics."""
        try:
            # Group orders by date, exchange, and symbol
            from collections import defaultdict
            metrics_data = defaultdict(lambda: defaultdict(list))

            for order in self.orders.values():
                date_key = order.created_at.date()
                metrics_data[date_key][order.exchange].append(order)

            # Calculate metrics for each date and exchange
            session = get_session()

            for date, exchange_orders in metrics_data.items():
                for exchange, orders in exchange_orders.items():
                    # Calculate metrics
                    total_orders = len(orders)
                    filled_orders = len([o for o in orders if o.status == OrderStatus.FILLED])
                    cancelled_orders = len([o for o in orders if o.status == OrderStatus.CANCELED])
                    expired_orders = len([o for o in orders if o.status == OrderStatus.EXPIRED])

                    # Volume metrics
                    total_volume = sum(o.filled_amount for o in orders)
                    total_fees = sum(o.fee_cost for o in orders)

                    # Performance metrics
                    filled_order_objects = [o for o in orders if o.status == OrderStatus.FILLED and o.fill_timestamp]
                    if filled_order_objects:
                        fill_times = [(o.fill_timestamp - o.created_at).total_seconds() for o in filled_order_objects]
                        avg_fill_time = sum(fill_times) / len(fill_times)
                    else:
                        avg_fill_time = 0

                    # Order type distribution
                    market_orders = len([o for o in orders if o.order_type == OrderType.MARKET])
                    limit_orders = len([o for o in orders if o.order_type == OrderType.LIMIT])
                    stop_orders = len([o for o in orders if o.order_type in [OrderType.STOP, OrderType.STOP_MARKET, OrderType.STOP_LIMIT]])

                    # Side distribution
                    buy_orders = len([o for o in orders if o.side == OrderSide.BUY])
                    sell_orders = len([o for o in orders if o.side == OrderSide.SELL])

                    # Create or update metrics record
                    metrics = session.query(OrderMetrics).filter(
                        OrderMetrics.exchange == exchange,
                        OrderMetrics.date == date
                    ).first()

                    if metrics:
                        # Update existing metrics
                        metrics.total_orders = total_orders
                        metrics.filled_orders = filled_orders
                        metrics.cancelled_orders = cancelled_orders
                        metrics.expired_orders = expired_orders
                        metrics.total_volume = total_volume
                        metrics.total_fees = total_fees
                        metrics.avg_fill_time = avg_fill_time
                        metrics.market_orders = market_orders
                        metrics.limit_orders = limit_orders
                        metrics.stop_orders = stop_orders
                        metrics.buy_orders = buy_orders
                        metrics.sell_orders = sell_orders
                    else:
                        # Create new metrics record
                        metrics = OrderMetrics(
                            exchange=exchange,
                            date=date,
                            total_orders=total_orders,
                            filled_orders=filled_orders,
                            cancelled_orders=cancelled_orders,
                            expired_orders=expired_orders,
                            total_volume=total_volume,
                            total_fees=total_fees,
                            avg_fill_time=avg_fill_time,
                            market_orders=market_orders,
                            limit_orders=limit_orders,
                            stop_orders=stop_orders,
                            buy_orders=buy_orders,
                            sell_orders=sell_orders
                        )
                        session.add(metrics)

            session.commit()
            session.close()

        except Exception as e:
            self.logger.error(f"Failed to calculate order metrics: {e}")

    async def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID."""
        order = self.orders.get(order_id)
        return order.to_dict() if order else None

    async def get_orders_by_exchange(self, exchange: str, symbol: Optional[str] = None) -> List[Dict]:
        """Get orders for an exchange, optionally filtered by symbol."""
        if symbol:
            orders = self.orders_by_exchange.get(exchange, {}).get(symbol, [])
        else:
            orders = []
            for symbol_orders in self.orders_by_exchange.get(exchange, {}).values():
                orders.extend(symbol_orders)

        return [order.to_dict() for order in orders]

    async def get_orders_by_symbol(self, symbol: str, exchange: Optional[str] = None) -> List[Dict]:
        """Get orders for a symbol, optionally filtered by exchange."""
        if exchange:
            orders = self.orders_by_symbol.get(symbol, {}).get(exchange, [])
        else:
            orders = []
            for exchange_orders in self.orders_by_symbol.get(symbol, {}).values():
                orders.extend(exchange_orders)

        return [order.to_dict() for order in orders]

    async def get_all_orders(self) -> List[Dict]:
        """Get all orders."""
        return [order.to_dict() for order in self.orders.values()]

    async def get_order_summary(self) -> Dict:
        """Get order summary statistics."""
        return {
            'total_orders': self.stats['total_orders'],
            'active_orders': self.stats['active_orders'],
            'filled_orders': self.stats['filled_orders'],
            'cancelled_orders': self.stats['cancelled_orders'],
            'expired_orders': self.stats['expired_orders'],
            'rejected_orders': self.stats['rejected_orders'],
            'total_volume': self.stats['total_volume'],
            'total_fees': self.stats['total_fees'],
            'avg_fill_time': self.stats['avg_fill_time'],
            'fill_rate': self.stats['fill_rate'],
            'last_update': self.stats['last_update'].isoformat() if self.stats['last_update'] else None,
            'exchanges': list(self.orders_by_exchange.keys()),
            'symbols': list(self.orders_by_symbol.keys())
        }

    async def get_order_performance_metrics(self) -> Dict:
        """Get order performance metrics."""
        all_orders = list(self.orders.values())

        if not all_orders:
            return {
                'execution_speed': 0.0,
                'price_accuracy': 0.0,
                'order_reliability': 0.0,
                'cost_efficiency': 0.0
            }

        # Calculate execution speed (fill time)
        filled_orders = [o for o in all_orders if o.status == OrderStatus.FILLED and o.fill_timestamp]
        if filled_orders:
            fill_times = [(o.fill_timestamp - o.created_at).total_seconds() for o in filled_orders]
            execution_speed = sum(fill_times) / len(fill_times)
        else:
            execution_speed = 0.0

        # Calculate order reliability (success rate)
        completed_orders = len([o for o in all_orders if o.status in [OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.EXPIRED]])
        if completed_orders > 0:
            order_reliability = self.stats['filled_orders'] / completed_orders
        else:
            order_reliability = 0.0

        # Calculate cost efficiency (fees as percentage of volume)
        if self.stats['total_volume'] > 0:
            cost_efficiency = (self.stats['total_fees'] / self.stats['total_volume']) * 100
        else:
            cost_efficiency = 0.0

        return {
            'execution_speed': execution_speed,
            'order_reliability': order_reliability,
            'cost_efficiency': cost_efficiency,
            'avg_order_size': self.stats['total_volume'] / len(all_orders) if all_orders else 0
        }

    def add_order_callback(self, callback):
        """Add a callback for order updates."""
        self.order_callbacks.append(callback)

    def remove_order_callback(self, callback):
        """Remove an order callback."""
        if callback in self.order_callbacks:
            self.order_callbacks.remove(callback)

    async def _notify_order_callbacks(self, update: OrderUpdate):
        """Notify all callbacks of order update."""
        for callback in self.order_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                self.logger.error(f"Order callback error: {e}")

    async def get_order_updates(self, timeout: float = 1.0) -> List[OrderUpdate]:
        """Get order updates from the queue."""
        updates = []
        start_time = asyncio.get_event_loop().time()

        while len(updates) < 100 and (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                update = await asyncio.wait_for(self.update_queue.get(), timeout=0.1)
                updates.append(update)
            except asyncio.TimeoutError:
                break

        return updates