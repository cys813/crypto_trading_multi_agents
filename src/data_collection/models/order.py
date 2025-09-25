"""
Order data models for the data collection agent.

This module defines database models for storing order information,
including current orders and order history in PostgreSQL.
"""

import logging
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, JSON, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from .database import Base, BaseModel
from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class OrderType(enum.Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT = "take_profit"
    TAKE_PROFIT_MARKET = "take_profit_market"
    TRAILING_STOP = "trailing_stop"
    POST_ONLY = "post_only"
    FOK = "fok"  # Fill or Kill
    IOC = "ioc"  # Immediate or Cancel


class OrderSide(enum.Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(enum.Enum):
    """Order status enumeration."""
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"


class TimeInForce(enum.Enum):
    """Time in force enumeration."""
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill
    DAY = "DAY"  # Day Order


class Order(Base, BaseModel):
    """Order data model for tracking trading orders."""

    __tablename__ = 'orders'

    # Basic order information
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    order_id = Column(String(100), unique=True, nullable=False)  # Exchange-specific order ID
    client_order_id = Column(String(100), unique=True)  # Client-side order ID
    user_id = Column(String(100))  # User identifier
    strategy_id = Column(String(100))  # Strategy identifier

    # Order details
    order_type = Column(Enum(OrderType), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.OPEN)
    time_in_force = Column(Enum(TimeInForce), default=TimeInForce.GTC)

    # Price and quantity
    price = Column(Float)  # Limit price
    stop_price = Column(Float)  # Stop price
    amount = Column(Float, nullable=False)  # Order quantity
    filled_amount = Column(Float, default=0.0)  # Filled quantity
    remaining_amount = Column(Float)  # Remaining quantity

    # Financial information
    cost = Column(Float, default=0.0)  # Total cost (price * amount)
    average_price = Column(Float)  # Average fill price
    fee = Column(JSON)  # Fee information
    fee_cost = Column(Float, default=0.0)  # Total fee cost
    fee_currency = Column(String(10))  # Fee currency

    # Order execution
    trades = Column(ARRAY(String(100)))  # Associated trade IDs
    last_trade_timestamp = Column(DateTime(timezone=True))
    trigger_condition = Column(String(50))  # Trigger condition for stop orders
    trailing_distance = Column(Float)  # Trailing stop distance
    trailing_percentage = Column(Float)  # Trailing stop percentage

    # Timing information
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    expired_at = Column(DateTime(timezone=True))  # Expiration time
    cancel_timestamp = Column(DateTime(timezone=True))  # Cancellation time
    fill_timestamp = Column(DateTime(timezone=True))  # Fill time

    # Order properties
    reduce_only = Column(Boolean, default=False)  # Reduce-only order
    post_only = Column(Boolean, default=False)  # Post-only order
    hidden = Column(Boolean, default=False)  # Hidden order
    iceberg = Column(Boolean, default=False)  # Iceberg order
    display_size = Column(Float)  # Display size for iceberg orders

    # Additional information
    leverage = Column(Float, default=1.0)  # Leverage for futures
    margin_mode = Column(String(20))  # Margin mode
    position_side = Column(String(20))  # Position side for futures
    self_trade_prevention = Column(String(20))  # Self-trade prevention mode
    metadata = Column(JSON)  # Additional metadata
    exchange_metadata = Column(JSON)  # Exchange-specific metadata

    # Relationships
    history = relationship("OrderHistory", back_populates="order", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<Order(exchange='{self.exchange}', symbol='{self.symbol}', order_id='{self.order_id}', type='{self.order_type}', side='{self.side}')>"

    def update_fill_status(self):
        """Update fill status based on filled amount."""
        if self.amount > 0:
            fill_percentage = (self.filled_amount / self.amount) * 100

            if fill_percentage >= 100:
                self.status = OrderStatus.FILLED
                self.remaining_amount = 0
                if not self.fill_timestamp:
                    self.fill_timestamp = func.now()
            elif fill_percentage > 0:
                self.status = OrderStatus.PARTIALLY_FILLED
                self.remaining_amount = self.amount - self.filled_amount
            else:
                self.status = OrderStatus.OPEN
                self.remaining_amount = self.amount

    def calculate_average_price(self, trades: list):
        """Calculate average fill price from trades."""
        if not trades:
            return

        total_cost = 0
        total_amount = 0

        for trade in trades:
            trade_amount = trade.get('amount', 0)
            trade_price = trade.get('price', 0)
            total_cost += trade_amount * trade_price
            total_amount += trade_amount

        if total_amount > 0:
            self.average_price = total_cost / total_amount

    def calculate_fees(self, trades: list):
        """Calculate total fees from trades."""
        if not trades:
            return

        total_fees = 0
        fee_currencies = set()

        for trade in trades:
            fee = trade.get('fee', {})
            if fee:
                fee_cost = fee.get('cost', 0)
                fee_currency = fee.get('currency', '')
                total_fees += fee_cost
                fee_currencies.add(fee_currency)

        self.fee_cost = total_fees
        if len(fee_currencies) == 1:
            self.fee_currency = fee_currencies.pop()

    def get_order_age(self) -> float:
        """Get order age in seconds."""
        if not self.created_at:
            return 0

        now = func.now()
        age = (now - self.created_at).total_seconds()
        return max(0, age)

    def get_fill_rate(self) -> float:
        """Get order fill rate as percentage."""
        if self.amount <= 0:
            return 0.0

        return (self.filled_amount / self.amount) * 100

    def is_active(self) -> bool:
        """Check if order is still active."""
        active_statuses = [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED, OrderStatus.PENDING]
        return self.status in active_statuses

    def is_expired(self) -> bool:
        """Check if order has expired."""
        if not self.expired_at:
            return False

        return func.now() > self.expired_at

    def to_dict(self, include_trades: bool = False) -> dict:
        """Convert order to dictionary."""
        order_dict = {
            'id': str(self.id),
            'exchange': self.exchange,
            'symbol': self.symbol,
            'order_id': self.order_id,
            'client_order_id': self.client_order_id,
            'order_type': self.order_type.value if self.order_type else None,
            'side': self.side.value if self.side else None,
            'status': self.status.value if self.status else None,
            'time_in_force': self.time_in_force.value if self.time_in_force else None,
            'price': self.price,
            'stop_price': self.stop_price,
            'amount': self.amount,
            'filled_amount': self.filled_amount,
            'remaining_amount': self.remaining_amount,
            'cost': self.cost,
            'average_price': self.average_price,
            'fee_cost': self.fee_cost,
            'fee_currency': self.fee_currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expired_at': self.expired_at.isoformat() if self.expired_at else None,
            'cancel_timestamp': self.cancel_timestamp.isoformat() if self.cancel_timestamp else None,
            'fill_timestamp': self.fill_timestamp.isoformat() if self.fill_timestamp else None,
            'reduce_only': self.reduce_only,
            'post_only': self.post_only,
            'hidden': self.hidden,
            'iceberg': self.iceberg,
            'display_size': self.display_size,
            'leverage': self.leverage,
            'margin_mode': self.margin_mode,
            'position_side': self.position_side,
        }

        # Add calculated fields
        order_dict['fill_rate'] = self.get_fill_rate()
        order_dict['is_active'] = self.is_active()
        order_dict['is_expired'] = self.is_expired()

        # Add trades if requested
        if include_trades and self.trades:
            order_dict['trades'] = self.trades

        return order_dict


class OrderHistory(Base, BaseModel):
    """Order history model for tracking order state changes."""

    __tablename__ = 'order_history'

    # Reference to order
    order_id = Column(UUID(as_uuid=True), nullable=False)
    order = relationship("Order", back_populates="history")

    # Event information
    event_type = Column(String(50), nullable=False)  # 'create', 'update', 'cancel', 'fill', 'expire'
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    event_id = Column(String(100))  # Event identifier

    # Order state at event time
    status = Column(Enum(OrderStatus))
    filled_amount = Column(Float, default=0.0)
    remaining_amount = Column(Float)
    average_price = Column(Float)
    fee_cost = Column(Float, default=0.0)

    # Change details
    amount_change = Column(Float, default=0.0)  # Change in amount
    price_change = Column(Float, default=0.0)  # Change in price
    status_change = Column(String(50))  # Status change

    # Additional information
    reason = Column(Text)  # Reason for the event
    trigger = Column(String(100))  # Event trigger
    notes = Column(Text)  # Additional notes
    metadata = Column(JSON)  # Event metadata
    exchange_data = Column(JSON)  # Exchange-specific data

    # Indexes
    __table_args__ = (
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<OrderHistory(order_id='{self.order_id}', event_type='{self.event_type}', event_timestamp='{self.event_timestamp}')>"

    def to_dict(self) -> dict:
        """Convert order history to dictionary."""
        return {
            'id': str(self.id),
            'order_id': str(self.order_id),
            'event_type': self.event_type,
            'event_timestamp': self.event_timestamp.isoformat() if self.event_timestamp else None,
            'status': self.status.value if self.status else None,
            'filled_amount': self.filled_amount,
            'remaining_amount': self.remaining_amount,
            'average_price': self.average_price,
            'fee_cost': self.fee_cost,
            'amount_change': self.amount_change,
            'price_change': self.price_change,
            'status_change': self.status_change,
            'reason': self.reason,
            'trigger': self.trigger,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class OrderMetrics(Base, BaseModel):
    """Order metrics model for storing aggregated order statistics."""

    __tablename__ = 'order_metrics'

    # Aggregation key
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    user_id = Column(String(100))
    strategy_id = Column(String(100))
    date = Column(DateTime(timezone=True), nullable=False)  # Daily aggregation

    # Order counts
    total_orders = Column(Integer, default=0)
    successful_orders = Column(Integer, default=0)
    failed_orders = Column(Integer, default=0)
    canceled_orders = Column(Integer, default=0)
    expired_orders = Column(Integer, default=0)

    # Order type distribution
    market_orders = Column(Integer, default=0)
    limit_orders = Column(Integer, default=0)
    stop_orders = Column(Integer, default=0)
    other_orders = Column(Integer, default=0)

    # Side distribution
    buy_orders = Column(Integer, default=0)
    sell_orders = Column(Integer, default=0)

    # Execution metrics
    fill_rate = Column(Float, default=0.0)  # Average fill rate
    avg_fill_time = Column(Float, default=0.0)  # Average fill time in seconds
    avg_execution_price = Column(Float, default=0.0)
    price_slippage = Column(Float, default=0.0)  # Average price slippage

    # Financial metrics
    total_volume = Column(Float, default=0.0)  # Total trading volume
    total_fees = Column(Float, default=0.0)
    avg_order_size = Column(Float, default=0.0)
    max_order_size = Column(Float, default=0.0)
    min_order_size = Column(Float, default=0.0)

    # Performance metrics
    order_accuracy = Column(Float, default=0.0)  # Order execution accuracy
    latency_metrics = Column(JSON)  # Order placement and execution latency
    error_rate = Column(Float, default=0.0)  # Order error rate

    # Additional data
    metadata = Column(JSON)

    # Indexes
    __table_args__ = (
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<OrderMetrics(exchange='{self.exchange}', symbol='{self.symbol}', date='{self.date}')>"

    def to_dict(self) -> dict:
        """Convert order metrics to dictionary."""
        return {
            'id': str(self.id),
            'exchange': self.exchange,
            'symbol': self.symbol,
            'user_id': self.user_id,
            'strategy_id': self.strategy_id,
            'date': self.date.isoformat() if self.date else None,
            'total_orders': self.total_orders,
            'successful_orders': self.successful_orders,
            'failed_orders': self.failed_orders,
            'canceled_orders': self.canceled_orders,
            'expired_orders': self.expired_orders,
            'market_orders': self.market_orders,
            'limit_orders': self.limit_orders,
            'stop_orders': self.stop_orders,
            'other_orders': self.other_orders,
            'buy_orders': self.buy_orders,
            'sell_orders': self.sell_orders,
            'fill_rate': self.fill_rate,
            'avg_fill_time': self.avg_fill_time,
            'avg_execution_price': self.avg_execution_price,
            'price_slippage': self.price_slippage,
            'total_volume': self.total_volume,
            'total_fees': self.total_fees,
            'avg_order_size': self.avg_order_size,
            'max_order_size': self.max_order_size,
            'min_order_size': self.min_order_size,
            'order_accuracy': self.order_accuracy,
            'latency_metrics': self.latency_metrics,
            'error_rate': self.error_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# Register models for import
__all__ = [
    'Order',
    'OrderHistory',
    'OrderMetrics',
    'OrderType',
    'OrderSide',
    'OrderStatus',
    'TimeInForce'
]