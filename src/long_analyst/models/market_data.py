"""
Market data models for the Long Analyst Agent.

Defines structures for handling various types of market data including
price data, volume data, and metadata from different sources.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np


class Timeframe(Enum):
    """Timeframe enumeration for market data."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN1 = "1M"


class DataSource(Enum):
    """Data source enumeration."""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    COINGECKO = "coingecko"
    DEFI_PULSE = "defipulse"
    GLASSNODE = "glassnode"
    CRYPTO_QUANT = "cryptoquant"
    CUSTOM = "custom"


class MarketDataType(Enum):
    """Types of market data."""
    OHLCV = "ohlcv"  # Open, High, Low, Close, Volume
    TICKER = "ticker"  # Current price and 24h stats
    ORDER_BOOK = "order_book"  # Order book data
    TRADES = "trades"  # Recent trades
    FUNDING_RATE = "funding_rate"  # Funding rates for perpetual futures
    OPEN_INTEREST = "open_interest"  # Open interest data
    LIQUIDATIONS = "liquidations"  # Liquidation data


@dataclass
class OHLCVData:
    """OHLCV (Open, High, Low, Close, Volume) data point."""
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: Timeframe
    symbol: str
    source: DataSource

    @property
    def datetime(self) -> datetime:
        """Get timestamp as datetime object."""
        return datetime.fromtimestamp(self.timestamp)

    @property
    def price_range(self) -> float:
        """Get price range (high - low)."""
        return self.high - self.low

    @property
    def body_size(self) -> float:
        """Get candle body size (|close - open|)."""
        return abs(self.close - self.open)

    @property
    def upper_shadow(self) -> float:
        """Get upper shadow size (high - max(open, close))."""
        return self.high - max(self.open, self.close)

    @property
    def lower_shadow(self) -> float:
        """Get lower shadow size (min(open, close) - low)."""
        return min(self.open, self.close) - self.low

    @property
    def is_bullish(self) -> bool:
        """Check if candle is bullish (close > open)."""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Check if candle is bearish (close < open)."""
        return self.close < self.open

    @property
    def volume_weighted_price(self) -> float:
        """Get volume-weighted average price (typical price)."""
        return (self.high + self.low + self.close) / 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timeframe": self.timeframe.value,
            "symbol": self.symbol,
            "source": self.source.value
        }


@dataclass
class TickerData:
    """Ticker data for current market state."""
    symbol: str
    last_price: float
    bid_price: float
    ask_price: float
    volume_24h: float
    price_change_24h: float
    price_change_percent_24h: float
    high_24h: float
    low_24h: float
    market_cap: Optional[float] = None
    source: DataSource = DataSource.BINANCE
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

    @property
    def spread(self) -> float:
        """Get bid-ask spread."""
        return self.ask_price - self.bid_price

    @property
    def spread_percent(self) -> float:
        """Get bid-ask spread as percentage of last price."""
        return (self.spread / self.last_price) * 100

    @property
    def mid_price(self) -> float:
        """Get mid-price (average of bid and ask)."""
        return (self.bid_price + self.ask_price) / 2

    @property
    def volatility_24h(self) -> float:
        """Get 24-hour volatility as percentage."""
        if self.high_24h == self.low_24h:
            return 0.0
        return ((self.high_24h - self.low_24h) / self.low_24h) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "last_price": self.last_price,
            "bid_price": self.bid_price,
            "ask_price": self.ask_price,
            "volume_24h": self.volume_24h,
            "price_change_24h": self.price_change_24h,
            "price_change_percent_24h": self.price_change_percent_24h,
            "high_24h": self.high_24h,
            "low_24h": self.low_24h,
            "market_cap": self.market_cap,
            "source": self.source.value,
            "timestamp": self.timestamp
        }


@dataclass
class OrderBookData:
    """Order book data."""
    symbol: str
    bids: List[tuple]  # List of (price, quantity) tuples
    asks: List[tuple]  # List of (price, quantity) tuples
    timestamp: float
    source: DataSource = DataSource.BINANCE

    @property
    def best_bid(self) -> Optional[float]:
        """Get best bid price."""
        return self.bids[0][0] if self.bids else None

    @property
    def best_ask(self) -> Optional[float]:
        """Get best ask price."""
        return self.asks[0][0] if self.asks else None

    @property
    def spread(self) -> Optional[float]:
        """Get bid-ask spread."""
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None

    @property
    def total_bid_volume(self) -> float:
        """Get total bid volume."""
        return sum(quantity for _, quantity in self.bids)

    @property
    def total_ask_volume(self) -> float:
        """Get total ask volume."""
        return sum(quantity for _, quantity in self.asks)

    @property
    def bid_ask_imbalance(self) -> float:
        """Get bid-ask imbalance ratio."""
        total_ask = self.total_ask_volume
        if total_ask == 0:
            return float('inf')
        return self.total_bid_volume / total_ask

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "bids": self.bids[:10],  # Top 10 levels
            "asks": self.asks[:10],  # Top 10 levels
            "timestamp": self.timestamp,
            "source": self.source.value
        }


@dataclass
class MarketData:
    """
    Comprehensive market data container.

    This class can hold different types of market data and provides
    unified access methods.
    """
    symbol: str
    data_type: MarketDataType
    timestamp: float
    source: DataSource
    timeframe: Optional[Timeframe] = None

    # Data containers
    ohlcv_data: Optional[List[OHLCVData]] = None
    ticker_data: Optional[TickerData] = None
    order_book_data: Optional[OrderBookData] = None
    trades_data: Optional[List[Dict[str, Any]]] = None
    funding_rate_data: Optional[Dict[str, Any]] = None
    open_interest_data: Optional[Dict[str, Any]] = None
    liquidations_data: Optional[Dict[str, Any]] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 1.0  # 0.0 to 1.0
    is_complete: bool = True

    def __post_init__(self):
        """Validate market data."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")

        if self.data_type == MarketDataType.OHLCV and not self.ohlcv_data:
            raise ValueError("OHLCV data required for OHLCV data type")

        if self.data_type == MarketDataType.TICKER and not self.ticker_data:
            raise ValueError("Ticker data required for TICKER data type")

        if self.data_type == MarketDataType.ORDER_BOOK and not self.order_book_data:
            raise ValueError("Order book data required for ORDER_BOOK data type")

    @property
    def age_seconds(self) -> float:
        """Get data age in seconds."""
        return datetime.now().timestamp() - self.timestamp

    @property
    def is_fresh(self) -> bool:
        """Check if data is fresh (less than 5 minutes old)."""
        return self.age_seconds < 300

    def get_price(self) -> Optional[float]:
        """Get current price from available data."""
        if self.ticker_data:
            return self.ticker_data.last_price
        elif self.ohlcv_data:
            return self.ohlcv_data[-1].close
        return None

    def get_volume(self) -> Optional[float]:
        """Get current volume from available data."""
        if self.ticker_data:
            return self.ticker_data.volume_24h
        elif self.ohlcv_data:
            return self.ohlcv_data[-1].volume
        return None

    def to_dataframe(self) -> Optional[pd.DataFrame]:
        """Convert OHLCV data to pandas DataFrame."""
        if not self.ohlcv_data:
            return None

        data = []
        for ohlcv in self.ohlcv_data:
            data.append({
                'timestamp': ohlcv.timestamp,
                'open': ohlcv.open,
                'high': ohlcv.high,
                'low': ohlcv.low,
                'close': ohlcv.close,
                'volume': ohlcv.volume
            })

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        return df

    def calculate_returns(self, periods: int = 1) -> Optional[np.ndarray]:
        """Calculate price returns."""
        df = self.to_dataframe()
        if df is None:
            return None
        return df['close'].pct_change(periods).dropna().values

    def calculate_volatility(self, window: int = 20) -> Optional[float]:
        """Calculate volatility (standard deviation of returns)."""
        returns = self.calculate_returns()
        if returns is None or len(returns) < window:
            return None
        return np.std(returns[-window:]) * np.sqrt(252)  # Annualized

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "symbol": self.symbol,
            "data_type": self.data_type.value,
            "timestamp": self.timestamp,
            "source": self.source.value,
            "timeframe": self.timeframe.value if self.timeframe else None,
            "metadata": self.metadata,
            "quality_score": self.quality_score,
            "is_complete": self.is_complete
        }

        if self.ohlcv_data:
            result["ohlcv_data"] = [ohlcv.to_dict() for ohlcv in self.ohlcv_data]

        if self.ticker_data:
            result["ticker_data"] = self.ticker_data.to_dict()

        if self.order_book_data:
            result["order_book_data"] = self.order_book_data.to_dict()

        if self.trades_data:
            result["trades_data"] = self.trades_data[:10]  # Last 10 trades

        if self.funding_rate_data:
            result["funding_rate_data"] = self.funding_rate_data

        if self.open_interest_data:
            result["open_interest_data"] = self.open_interest_data

        if self.liquidations_data:
            result["liquidations_data"] = self.liquidations_data

        return result

    @classmethod
    def from_ohlcv_list(cls, symbol: str, ohlcv_data: List[OHLCVData],
                       source: DataSource = DataSource.BINANCE) -> "MarketData":
        """Create MarketData from OHLCV list."""
        return cls(
            symbol=symbol,
            data_type=MarketDataType.OHLCV,
            timestamp=ohlcv_data[-1].timestamp if ohlcv_data else datetime.now().timestamp(),
            source=source,
            timeframe=ohlcv_data[0].timeframe if ohlcv_data else None,
            ohlcv_data=ohlcv_data
        )

    @classmethod
    def from_ticker(cls, ticker_data: TickerData) -> "MarketData":
        """Create MarketData from ticker data."""
        return cls(
            symbol=ticker_data.symbol,
            data_type=MarketDataType.TICKER,
            timestamp=ticker_data.timestamp,
            source=ticker_data.source,
            ticker_data=ticker_data
        )

    def __str__(self) -> str:
        """String representation."""
        price = self.get_price()
        return f"MarketData({self.symbol}, {self.data_type.value}, price={price})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"MarketData(symbol={self.symbol}, type={self.data_type.value}, "
                f"source={self.source.value}, age={self.age_seconds:.1f}s)")