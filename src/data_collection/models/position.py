"""
Position data models for the data collection agent.

This module defines database models for storing position information,
including current positions and position history in PostgreSQL.
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


class PositionType(enum.Enum):
    """Position type enumeration."""
    LONG = "long"
    SHORT = "short"
    BOTH = "both"


class PositionStatus(enum.Enum):
    """Position status enumeration."""
    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"
    PARTIALLY_CLOSED = "partially_closed"


class Position(Base, BaseModel):
    """Position data model for tracking trading positions."""

    __tablename__ = 'positions'

    # Basic position information
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    position_id = Column(String(100), unique=True)  # Exchange-specific position ID
    user_id = Column(String(100))  # User identifier
    strategy_id = Column(String(100))  # Strategy identifier

    # Position details
    position_type = Column(Enum(PositionType), nullable=False)
    status = Column(Enum(PositionStatus), default=PositionStatus.OPEN)
    leverage = Column(Float, default=1.0)
    margin_type = Column(String(20), default='isolated')  # 'isolated', 'cross'
    margin_mode = Column(String(20), default='regular')  # 'regular', 'portfolio'

    # Position quantities
    size = Column(Float, nullable=False)  # Position size in base currency
    entry_price = Column(Float, nullable=False)  # Average entry price
    mark_price = Column(Float)  # Current mark price
    last_price = Column(Float)  # Last traded price
    bankruptcy_price = Column(Float)  # Bankruptcy price

    # Financial metrics
    margin = Column(Float)  # Used margin
    initial_margin = Column(Float)  # Initial margin
    maintenance_margin = Column(Float)  # Maintenance margin
    margin_ratio = Column(Float)  # Margin ratio
    pnl = Column(Float, default=0.0)  # Unrealized PnL
    roi = Column(Float, default=0.0)  # Return on Investment
    roe = Column(Float, default=0.0)  # Return on Equity
    funding_rate = Column(Float)  # Funding rate for futures
    funding_cost = Column(Float, default=0.0)  # Cumulative funding cost

    # Risk metrics
    liquidation_price = Column(Float)  # Liquidation price
    mark_to_market_pnl = Column(Float)  # Mark-to-market PnL
    unrealized_pnl = Column(Float, default=0.0)  # Unrealized PnL
    realized_pnl = Column(Float, default=0.0)  # Realized PnL
    cumulative_pnl = Column(Float, default=0.0)  # Cumulative PnL

    # Position timing
    opened_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True))
    duration = Column(String(50))  # Position duration (calculated)

    # Fees and costs
    trading_fees = Column(Float, default=0.0)  # Trading fees
    funding_fees = Column(Float, default=0.0)  # Funding fees
    total_fees = Column(Float, default=0.0)  # Total fees

    # Additional data
    contracts = Column(Float)  # Number of contracts (for futures)
    contract_size = Column(Float)  # Contract size
    settlement_type = Column(String(20))  # 'linear', 'inverse', 'spot'
    is_hedged = Column(Boolean, default=False)  # Is position hedged
    hedge_ratio = Column(Float)  # Hedge ratio
    collateral = Column(JSON)  # Collateral information
    risk_parameters = Column(JSON)  # Risk parameters
    metadata = Column(JSON)  # Additional metadata

    # Timestamps
    last_updated = Column(DateTime(timezone=True), default=func.now())
    last_sync = Column(DateTime(timezone=True))  # Last sync with exchange

    # Relationships
    history = relationship("PositionHistory", back_populates="position", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<Position(exchange='{self.exchange}', symbol='{self.symbol}', size={self.size}, entry_price={self.entry_price}, status='{self.status}')>"

    def update_pnl(self, current_price: float):
        """Update PnL based on current price."""
        if self.position_type == PositionType.LONG:
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
        elif self.position_type == PositionType.SHORT:
            self.unrealized_pnl = (self.entry_price - current_price) * self.size
        else:
            self.unrealized_pnl = 0

        # Update ROI
        if self.initial_margin > 0:
            self.roi = (self.unrealized_pnl / self.initial_margin) * 100

        # Update total PnL
        self.pnl = self.unrealized_pnl + self.realized_pnl

        self.last_updated = func.now()

    def calculate_duration(self):
        """Calculate position duration."""
        if self.opened_at:
            end_time = self.closed_at or func.now()
            duration = end_time - self.opened_at

            # Format duration
            days = duration.days
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60

            if days > 0:
                self.duration = f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                self.duration = f"{hours}h {minutes}m"
            else:
                self.duration = f"{minutes}m"

    def get_risk_metrics(self) -> dict:
        """Get risk metrics for the position."""
        risk_metrics = {
            'position_size': self.size,
            'entry_price': self.entry_price,
            'current_price': self.mark_price or self.last_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'total_pnl': self.pnl,
            'roi': self.roi,
            'leverage': self.leverage,
            'margin_ratio': self.margin_ratio,
            'liquidation_price': self.liquidation_price,
            'bankruptcy_price': self.bankruptcy_price,
        }

        # Calculate additional risk metrics
        if self.entry_price > 0 and self.mark_price:
            price_change_pct = ((self.mark_price - self.entry_price) / self.entry_price) * 100
            risk_metrics['price_change_percent'] = price_change_pct

        # Calculate distance to liquidation
        if self.liquidation_price and self.mark_price:
            if self.position_type == PositionType.LONG:
                distance_to_liq = ((self.mark_price - self.liquidation_price) / self.mark_price) * 100
            else:
                distance_to_liq = ((self.liquidation_price - self.mark_price) / self.mark_price) * 100
            risk_metrics['distance_to_liquidation_percent'] = distance_to_liq

        return risk_metrics

    def to_dict(self, include_risk_metrics: bool = True) -> dict:
        """Convert position to dictionary."""
        position_dict = {
            'id': str(self.id),
            'exchange': self.exchange,
            'symbol': self.symbol,
            'position_id': self.position_id,
            'position_type': self.position_type.value if self.position_type else None,
            'status': self.status.value if self.status else None,
            'size': self.size,
            'entry_price': self.entry_price,
            'mark_price': self.mark_price,
            'last_price': self.last_price,
            'leverage': self.leverage,
            'margin_type': self.margin_type,
            'pnl': self.pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'roi': self.roe,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'duration': self.duration,
            'total_fees': self.total_fees,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_risk_metrics:
            position_dict['risk_metrics'] = self.get_risk_metrics()

        return position_dict


class PositionHistory(Base, BaseModel):
    """Position history model for tracking position changes."""

    __tablename__ = 'position_history'

    # Reference to position
    position_id = Column(UUID(as_uuid=True), nullable=False)
    position = relationship("Position", back_populates="history")

    # Event information
    event_type = Column(String(50), nullable=False)  # 'open', 'close', 'update', 'partial_close', 'liquidation'
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    event_id = Column(String(100))  # Event identifier

    # Position state at event time
    size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    mark_price = Column(Float)
    pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    cumulative_pnl = Column(Float, default=0.0)

    # Change details
    size_change = Column(Float, default=0.0)  # Change in position size
    price_change = Column(Float, default=0.0)  # Change in price
    pnl_change = Column(Float, default=0.0)  # Change in PnL

    # Additional information
    reason = Column(Text)  # Reason for the event
    trigger = Column(String(100))  # Event trigger
    notes = Column(Text)  # Additional notes
    metadata = Column(JSON)  # Event metadata

    # Fees and costs
    fees_incurred = Column(Float, default=0.0)
    funding_costs = Column(Float, default=0.0)

    # Indexes
    __table_args__ = (
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<PositionHistory(position_id='{self.position_id}', event_type='{self.event_type}', event_timestamp='{self.event_timestamp}')>"

    def to_dict(self) -> dict:
        """Convert position history to dictionary."""
        return {
            'id': str(self.id),
            'position_id': str(self.position_id),
            'event_type': self.event_type,
            'event_timestamp': self.event_timestamp.isoformat() if self.event_timestamp else None,
            'size': self.size,
            'entry_price': self.entry_price,
            'mark_price': self.mark_price,
            'pnl': self.pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'cumulative_pnl': self.cumulative_pnl,
            'size_change': self.size_change,
            'price_change': self.price_change,
            'pnl_change': self.pnl_change,
            'reason': self.reason,
            'trigger': self.trigger,
            'notes': self.notes,
            'fees_incurred': self.fees_incurred,
            'funding_costs': self.funding_costs,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PositionMetrics(Base, BaseModel):
    """Position metrics model for storing aggregated position statistics."""

    __tablename__ = 'position_metrics'

    # Aggregation key
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    user_id = Column(String(100))
    strategy_id = Column(String(100))
    date = Column(DateTime(timezone=True), nullable=False)  # Daily aggregation

    # Position counts
    total_positions = Column(Integer, default=0)
    open_positions = Column(Integer, default=0)
    closed_positions = Column(Integer, default=0)
    liquidated_positions = Column(Integer, default=0)

    # Financial metrics
    total_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    total_fees = Column(Float, default=0.0)

    # Performance metrics
    winning_positions = Column(Integer, default=0)
    losing_positions = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float)

    # Position metrics
    avg_position_size = Column(Float, default=0.0)
    avg_position_duration = Column(String(50))
    max_position_size = Column(Float, default=0.0)
    min_position_size = Column(Float, default=0.0)

    # Risk metrics
    max_leverage_used = Column(Float, default=0.0)
    avg_leverage = Column(Float, default=0.0)
    margin_call_count = Column(Integer, default=0)
    liquidation_count = Column(Integer, default=0)

    # Additional data
    metadata = Column(JSON)

    # Indexes
    __table_args__ = (
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<PositionMetrics(exchange='{self.exchange}', symbol='{self.symbol}', date='{self.date}')>"

    def to_dict(self) -> dict:
        """Convert position metrics to dictionary."""
        return {
            'id': str(self.id),
            'exchange': self.exchange,
            'symbol': self.symbol,
            'user_id': self.user_id,
            'strategy_id': self.strategy_id,
            'date': self.date.isoformat() if self.date else None,
            'total_positions': self.total_positions,
            'open_positions': self.open_positions,
            'closed_positions': self.closed_positions,
            'liquidated_positions': self.liquidated_positions,
            'total_pnl': self.total_pnl,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'total_fees': self.total_fees,
            'winning_positions': self.winning_positions,
            'losing_positions': self.losing_positions,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'avg_position_size': self.avg_position_size,
            'avg_position_duration': self.avg_position_duration,
            'max_position_size': self.max_position_size,
            'min_position_size': self.min_position_size,
            'max_leverage_used': self.max_leverage_used,
            'avg_leverage': self.avg_leverage,
            'margin_call_count': self.margin_call_count,
            'liquidation_count': self.liquidation_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# Register models for import
__all__ = [
    'Position',
    'PositionHistory',
    'PositionMetrics',
    'PositionType',
    'PositionStatus'
]