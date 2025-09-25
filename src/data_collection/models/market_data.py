"""
Market data models for the data collection agent.

This module defines database models for storing market data including
OHLCV data, order book data, and trade data in TimescaleDB.
"""

import logging
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid

from .database import TimescaleBase, TimeSeriesBaseModel
from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class MarketData(TimescaleBase):
    """Base market data table for metadata and tracking."""

    __tablename__ = 'market_data'

    id = UUID(as_uuid=True, primary_key=True, default=uuid.uuid4)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    data_type = Column(String(20), nullable=False)  # 'ohlcv', 'orderbook', 'trade', 'ticker'
    timestamp = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), default=func.now())
    processed_at = Column(DateTime(timezone=True))
    quality_score = Column(Float)
    validation_report = Column(JSON)
    raw_data = Column(JSON)
    processing_time_ms = Column(Float)
    status = Column(String(20), default='pending')  # 'pending', 'processed', 'failed'
    error_message = Column(Text)

    # Indexes
    __table_args__ = (
        Index('idx_market_data_exchange_symbol', 'exchange', 'symbol'),
        Index('idx_market_data_timestamp', 'timestamp'),
        Index('idx_market_data_type_timestamp', 'data_type', 'timestamp'),
    )

    def __repr__(self):
        return f"<MarketData(exchange='{self.exchange}', symbol='{self.symbol}', type='{self.data_type}', timestamp='{self.timestamp}')>"


class OHLCVData(TimescaleBase, TimeSeriesBaseModel):
    """OHLCV (Open, High, Low, Close, Volume) data model."""

    __tablename__ = 'ohlcv_data'

    id = UUID(as_uuid=True, primary_key=True, default=uuid.uuid4)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)  # '1m', '5m', '15m', '30m', '1h', '4h', '1d'
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    quote_volume = Column(Float)  # Volume in quote currency
    trades_count = Column(Integer)  # Number of trades in this candle
    buy_volume = Column(Float)  # Buy volume
    sell_volume = Column(Float)  # Sell volume
    vwap = Column(Float)  # Volume Weighted Average Price
    received_at = Column(DateTime(timezone=True), default=func.now())
    quality_score = Column(Float)
    is_complete = Column(Boolean, default=True)
    last_update = Column(DateTime(timezone=True), default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_ohlcv_exchange_symbol_timeframe', 'exchange', 'symbol', 'timeframe'),
        Index('idx_ohlcv_timestamp', 'timestamp'),
        Index('idx_ohlcv_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
        # TimescaleDB hypertable will be created on timestamp
    )

    def __repr__(self):
        return f"<OHLCVData(exchange='{self.exchange}', symbol='{self.symbol}', timeframe='{self.timeframe}', timestamp='{self.timestamp}')>"

    @property
    def is_valid(self):
        """Check if OHLCV data is valid."""
        return (
            self.open > 0 and
            self.high > 0 and
            self.low > 0 and
            self.close > 0 and
            self.volume >= 0 and
            self.high >= self.low >= self.close >= self.open
        )

    @property
    def price_range(self):
        """Calculate price range (high - low)."""
        return self.high - self.low

    @property
    def price_change(self):
        """Calculate price change (close - open)."""
        return self.close - self.open

    @property
    def price_change_percent(self):
        """Calculate price change percentage."""
        if self.open > 0:
            return (self.price_change / self.open) * 100
        return 0

    @property
    def is_green_candle(self):
        """Check if this is a green candle (close > open)."""
        return self.close > self.open

    @property
    def is_red_candle(self):
        """Check if this is a red candle (close < open)."""
        return self.close < self.open

    @property
    def body_size(self):
        """Calculate candle body size."""
        return abs(self.close - self.open)

    @property
    def upper_shadow(self):
        """Calculate upper shadow size."""
        return self.high - max(self.open, self.close)

    @property
    def lower_shadow(self):
        """Calculate lower shadow size."""
        return min(self.open, self.close) - self.low

    @property
    def total_range(self):
        """Calculate total candle range."""
        return self.high - self.low

    def to_dict(self, include_metadata: bool = True):
        """Convert to dictionary."""
        data = {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
        }

        if include_metadata:
            data.update({
                'exchange': self.exchange,
                'symbol': self.symbol,
                'timeframe': self.timeframe,
                'quote_volume': self.quote_volume,
                'trades_count': self.trades_count,
                'buy_volume': self.buy_volume,
                'sell_volume': self.sell_volume,
                'vwap': self.vwap,
                'quality_score': self.quality_score,
                'is_complete': self.is_complete,
                'price_range': self.price_range,
                'price_change': self.price_change,
                'price_change_percent': self.price_change_percent,
                'is_green_candle': self.is_green_candle,
                'is_red_candle': self.is_red_candle,
                'body_size': self.body_size,
                'upper_shadow': self.upper_shadow,
                'lower_shadow': self.lower_shadow,
                'total_range': self.total_range,
            })

        return data


class OrderBookData(TimescaleBase, TimeSeriesBaseModel):
    """Order book data model."""

    __tablename__ = 'orderbook_data'

    id = UUID(as_uuid=True, primary_key=True, default=uuid.uuid4)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    bids = Column(JSON, nullable=False)  # Array of [price, amount] pairs
    asks = Column(JSON, nullable=False)  # Array of [price, amount] pairs
    received_at = Column(DateTime(timezone=True), default=func.now())
    quality_score = Column(Float)
    last_update = Column(DateTime(timezone=True), default=func.now())

    # Calculated fields
    best_bid = Column(Float)
    best_ask = Column(Float)
    bid_volume = Column(Float)
    ask_volume = Column(Float)
    spread = Column(Float)
    spread_percent = Column(Float)
    mid_price = Column(Float)
    depth_levels = Column(Integer, default=20)
    total_bid_value = Column(Float)  # Total value of bids
    total_ask_value = Column(Float)  # Total value of asks
    imbalance = Column(Float)  # (bid_volume - ask_volume) / (bid_volume + ask_volume)

    # Indexes
    __table_args__ = (
        Index('idx_orderbook_exchange_symbol', 'exchange', 'symbol'),
        Index('idx_orderbook_timestamp', 'timestamp'),
        # TimescaleDB hypertable will be created on timestamp
    )

    def __repr__(self):
        return f"<OrderBookData(exchange='{self.exchange}', symbol='{self.symbol}', timestamp='{self.timestamp}')>"

    def calculate_metrics(self):
        """Calculate order book metrics."""
        if not self.bids or not self.asks:
            return

        # Best bid and ask
        if self.bids:
            self.best_bid = float(self.bids[0][0])
        if self.asks:
            self.best_ask = float(self.asks[0][1])

        # Spread and mid price
        if self.best_bid and self.best_ask:
            self.spread = self.best_ask - self.best_bid
            self.mid_price = (self.best_bid + self.best_ask) / 2
            if self.mid_price > 0:
                self.spread_percent = (self.spread / self.mid_price) * 100

        # Calculate volumes
        self.bid_volume = sum(float(bid[1]) for bid in self.bids)
        self.ask_volume = sum(float(ask[1]) for ask in self.asks)

        # Calculate total values
        self.total_bid_value = sum(float(bid[0]) * float(bid[1]) for bid in self.bids)
        self.total_ask_value = sum(float(ask[0]) * float(ask[1]) for ask in self.asks)

        # Calculate imbalance
        total_volume = self.bid_volume + self.ask_volume
        if total_volume > 0:
            self.imbalance = (self.bid_volume - self.ask_volume) / total_volume

        # Set depth levels
        self.depth_levels = min(len(self.bids), len(self.asks))

    def to_dict(self, include_metadata: bool = True):
        """Convert to dictionary."""
        data = {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'bids': self.bids,
            'asks': self.asks,
        }

        if include_metadata:
            data.update({
                'exchange': self.exchange,
                'symbol': self.symbol,
                'best_bid': self.best_bid,
                'best_ask': self.best_ask,
                'bid_volume': self.bid_volume,
                'ask_volume': self.ask_volume,
                'spread': self.spread,
                'spread_percent': self.spread_percent,
                'mid_price': self.mid_price,
                'depth_levels': self.depth_levels,
                'total_bid_value': self.total_bid_value,
                'total_ask_value': self.total_ask_value,
                'imbalance': self.imbalance,
                'quality_score': self.quality_score,
            })

        return data


class TradeData(TimescaleBase, TimeSeriesBaseModel):
    """Trade data model."""

    __tablename__ = 'trade_data'

    id = UUID(as_uuid=True, primary_key=True, default=uuid.uuid4)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    trade_id = Column(String(100))  # Exchange-specific trade ID
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    side = Column(String(10), nullable=False)  # 'buy', 'sell'
    type = Column(String(20))  # 'limit', 'market', etc.
    taker_or_maker = Column(String(10))  # 'taker', 'maker'
    received_at = Column(DateTime(timezone=True), default=func.now())
    quality_score = Column(Float)
    last_update = Column(DateTime(timezone=True), default=func.now())

    # Calculated fields
    value = Column(Float)  # price * amount
    is_buyer_maker = Column(Boolean)
    is_large_trade = Column(Boolean, default=False)
    large_trade_threshold = Column(Float, default=10000)  # Value threshold for large trades

    # Indexes
    __table_args__ = (
        Index('idx_trade_exchange_symbol', 'exchange', 'symbol'),
        Index('idx_trade_timestamp', 'timestamp'),
        Index('idx_trade_trade_id', 'trade_id'),
        Index('idx_trade_side', 'side'),
        # TimescaleDB hypertable will be created on timestamp
    )

    def __repr__(self):
        return f"<TradeData(exchange='{self.exchange}', symbol='{self.symbol}', price={self.price}, amount={self.amount}, side='{self.side}')>"

    def calculate_metrics(self):
        """Calculate trade metrics."""
        # Calculate trade value
        self.value = self.price * self.amount

        # Determine if buyer is maker
        if self.taker_or_maker:
            self.is_buyer_maker = (self.taker_or_maker == 'maker') and (self.side == 'buy')

        # Check if it's a large trade
        if self.large_trade_threshold:
            self.is_large_trade = self.value >= self.large_trade_threshold

    def to_dict(self, include_metadata: bool = True):
        """Convert to dictionary."""
        data = {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'price': self.price,
            'amount': self.amount,
            'side': self.side,
        }

        if include_metadata:
            data.update({
                'exchange': self.exchange,
                'symbol': self.symbol,
                'trade_id': self.trade_id,
                'type': self.type,
                'taker_or_maker': self.taker_or_maker,
                'value': self.value,
                'is_buyer_maker': self.is_buyer_maker,
                'is_large_trade': self.is_large_trade,
                'quality_score': self.quality_score,
            })

        return data


class TickerData(TimescaleBase, TimeSeriesBaseModel):
    """Ticker data model."""

    __tablename__ = 'ticker_data'

    id = UUID(as_uuid=True, primary_key=True, default=uuid.uuid4)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    last = Column(Float, nullable=False)
    bid = Column(Float)
    ask = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    quote_volume = Column(Float)
    open = Column(Float)
    close = Column(Float)
    previous_close = Column(Float)
    change = Column(Float)
    change_percent = Column(Float)
    average = Column(Float)
    vwap = Column(Float)
    received_at = Column(DateTime(timezone=True), default=func.now())
    quality_score = Column(Float)
    last_update = Column(DateTime(timezone=True), default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_ticker_exchange_symbol', 'exchange', 'symbol'),
        Index('idx_ticker_timestamp', 'timestamp'),
        # TimescaleDB hypertable will be created on timestamp
    )

    def __repr__(self):
        return f"<TickerData(exchange='{self.exchange}', symbol='{self.symbol}', last={self.last}, timestamp='{self.timestamp}')>"

    def to_dict(self, include_metadata: bool = True):
        """Convert to dictionary."""
        data = {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'last': self.last,
            'bid': self.bid,
            'ask': self.ask,
            'volume': self.volume,
        }

        if include_metadata:
            data.update({
                'exchange': self.exchange,
                'symbol': self.symbol,
                'high': self.high,
                'low': self.low,
                'quote_volume': self.quote_volume,
                'open': self.open,
                'close': self.close,
                'previous_close': self.previous_close,
                'change': self.change,
                'change_percent': self.change_percent,
                'average': self.average,
                'vwap': self.vwap,
                'quality_score': self.quality_score,
            })

        return data


# Create TimescaleDB hypertables
def create_hypertables():
    """Create TimescaleDB hypertables for time-series data."""
    # This would typically be executed with TimescaleDB-specific SQL commands
    # For now, we'll define the function structure
    pass


# Register models for import
__all__ = [
    'MarketData',
    'OHLCVData',
    'OrderBookData',
    'TradeData',
    'TickerData',
    'create_hypertables'
]