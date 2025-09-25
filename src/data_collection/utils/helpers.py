"""
Helper functions for the data collection agent.

This module contains various utility functions for data processing,
formatting, and common operations.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timezone
import re
import pandas as pd
import numpy as np


def format_timestamp(timestamp: Union[int, float, str, datetime],
                    timezone_str: str = 'UTC') -> datetime:
    """
    Format timestamp to datetime object with timezone.

    Args:
        timestamp: Input timestamp (milliseconds, seconds, or datetime)
        timezone_str: Timezone string

    Returns:
        Formatted datetime object
    """
    if timestamp is None:
        return datetime.now(timezone.utc)

    if isinstance(timestamp, datetime):
        return timestamp

    if isinstance(timestamp, str):
        # Try to parse ISO format
        try:
            return pd.to_datetime(timestamp).to_pydatetime()
        except ValueError:
            pass

        # Try to parse numeric string
        try:
            timestamp = float(timestamp)
        except ValueError:
            raise ValueError(f"Invalid timestamp string: {timestamp}")

    # Handle numeric timestamps
    if isinstance(timestamp, (int, float)):
        # Check if timestamp is in milliseconds or seconds
        if timestamp > 1e12:  # Milliseconds
            return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        else:  # Seconds
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    raise ValueError(f"Unsupported timestamp format: {timestamp}")


def normalize_symbol(symbol: str, exchange: str = 'binance') -> str:
    """
    Normalize symbol format across different exchanges.

    Args:
        symbol: Original symbol
        exchange: Exchange name

    Returns:
        Normalized symbol
    """
    if not symbol:
        return ''

    # Remove whitespace and convert to uppercase
    symbol = symbol.strip().upper()

    # Exchange-specific normalization
    if exchange == 'binance':
        # Binance format: BTCUSDT, ETHBTC
        if '/' in symbol:
            symbol = symbol.replace('/', '')
        elif '-' in symbol:
            symbol = symbol.replace('-', '')

    elif exchange == 'okx':
        # OKX format: BTC-USDT, ETH-BTC
        if '/' in symbol:
            symbol = symbol.replace('/', '-')
        elif not '-' in symbol and len(symbol) > 6:  # Likely needs separator
            # Try to insert separator (e.g., BTCUSDT -> BTC-USDT)
            if symbol.endswith('USDT'):
                symbol = symbol[:-4] + '-' + symbol[-4:]
            elif symbol.endswith('BTC'):
                symbol = symbol[:-3] + '-' + symbol[-3:]

    elif exchange == 'huobi':
        # Huobi format: btcusdt, ethbtc
        if '/' in symbol:
            symbol = symbol.replace('/', '').lower()
        elif '-' in symbol:
            symbol = symbol.replace('-', '').lower()
        else:
            symbol = symbol.lower()

    return symbol


def calculate_pnl(entry_price: float, exit_price: float, quantity: float,
                fees: float = 0, side: str = 'long') -> Dict[str, float]:
    """
    Calculate profit and loss for a trade.

    Args:
        entry_price: Entry price
        exit_price: Exit price
        quantity: Trade quantity
        fees: Total fees paid
        side: Trade side ('long' or 'short')

    Returns:
        Dictionary with PnL metrics
    """
    if side.lower() == 'long':
        gross_pnl = (exit_price - entry_price) * quantity
    elif side.lower() == 'short':
        gross_pnl = (entry_price - exit_price) * quantity
    else:
        raise ValueError("Side must be 'long' or 'short'")

    net_pnl = gross_pnl - fees
    roi = (net_pnl / (entry_price * quantity)) * 100 if entry_price * quantity > 0 else 0

    return {
        'gross_pnl': gross_pnl,
        'net_pnl': net_pnl,
        'fees': fees,
        'roi_percent': roi,
        'is_profitable': net_pnl > 0
    }


def calculate_position_metrics(positions: List[Dict]) -> Dict[str, Any]:
    """
    Calculate overall portfolio metrics from positions.

    Args:
        positions: List of position dictionaries

    Returns:
        Dictionary with portfolio metrics
    """
    if not positions:
        return {
            'total_value': 0,
            'total_pnl': 0,
            'total_unrealized_pnl': 0,
            'total_realized_pnl': 0,
            'position_count': 0,
            'largest_position': None,
            'best_performer': None,
            'worst_performer': None
        }

    total_value = sum(pos.get('value', 0) for pos in positions)
    total_pnl = sum(pos.get('pnl', 0) for pos in positions)
    total_unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions)
    total_realized_pnl = sum(pos.get('realized_pnl', 0) for pos in positions)

    # Find largest position
    largest_position = max(positions, key=lambda x: x.get('value', 0))

    # Find best and worst performers
    best_performer = max(positions, key=lambda x: x.get('pnl_percent', 0))
    worst_performer = min(positions, key=lambda x: x.get('pnl_percent', 0))

    return {
        'total_value': total_value,
        'total_pnl': total_pnl,
        'total_unrealized_pnl': total_unrealized_pnl,
        'total_realized_pnl': total_realized_pnl,
        'position_count': len(positions),
        'largest_position': largest_position,
        'best_performer': best_performer,
        'worst_performer': worst_performer
    }


def calculate_order_metrics(orders: List[Dict]) -> Dict[str, Any]:
    """
    Calculate order execution metrics.

    Args:
        orders: List of order dictionaries

    Returns:
        Dictionary with order metrics
    """
    if not orders:
        return {
            'total_orders': 0,
            'filled_orders': 0,
            'cancelled_orders': 0,
            'fill_rate': 0,
            'avg_fill_time': 0,
            'total_volume': 0,
            'total_fees': 0
        }

    total_orders = len(orders)
    filled_orders = sum(1 for order in orders if order.get('status') == 'filled')
    cancelled_orders = sum(1 for order in orders if order.get('status') == 'cancelled')

    fill_rate = filled_orders / total_orders if total_orders > 0 else 0

    # Calculate average fill time
    filled_orders_with_time = [
        order for order in orders
        if order.get('status') == 'filled' and
        'filled_at' in order and
        'created_at' in order
    ]

    if filled_orders_with_time:
        fill_times = []
        for order in filled_orders_with_time:
            created = format_timestamp(order['created_at'])
            filled = format_timestamp(order['filled_at'])
            fill_times.append((filled - created).total_seconds())

        avg_fill_time = sum(fill_times) / len(fill_times)
    else:
        avg_fill_time = 0

    # Calculate total volume and fees
    total_volume = sum(order.get('filled_quantity', 0) for order in orders)
    total_fees = sum(order.get('fees', 0) for order in orders)

    return {
        'total_orders': total_orders,
        'filled_orders': filled_orders,
        'cancelled_orders': cancelled_orders,
        'fill_rate': fill_rate,
        'avg_fill_time': avg_fill_time,
        'total_volume': total_volume,
        'total_fees': total_fees
    }


def calculate_volatility(prices: List[float], window: int = 20) -> float:
    """
    Calculate price volatility using standard deviation.

    Args:
        prices: List of prices
        window: Rolling window size

    Returns:
        Volatility as percentage
    """
    if len(prices) < 2:
        return 0.0

    # Calculate returns
    returns = []
    for i in range(1, len(prices)):
        if prices[i-1] != 0:
            returns.append((prices[i] - prices[i-1]) / prices[i-1])

    if not returns:
        return 0.0

    # Calculate standard deviation of returns
    volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility
    return volatility * 100  # Convert to percentage


def calculate_spread(bid: float, ask: float) -> Dict[str, float]:
    """
    Calculate bid-ask spread metrics.

    Args:
        bid: Bid price
        ask: Ask price

    Returns:
        Dictionary with spread metrics
    """
    if bid <= 0 or ask <= 0:
        return {
            'spread': 0,
            'spread_percent': 0,
            'mid_price': 0
        }

    spread = ask - bid
    mid_price = (bid + ask) / 2
    spread_percent = (spread / mid_price) * 100 if mid_price > 0 else 0

    return {
        'spread': spread,
        'spread_percent': spread_percent,
        'mid_price': mid_price
    }


def detect_anomalies(data: List[float], threshold: float = 2.0) -> List[int]:
    """
    Detect anomalies in time series data using Z-score method.

    Args:
        data: List of data points
        threshold: Z-score threshold for anomaly detection

    Returns:
        List of indices where anomalies were detected
    """
    if len(data) < 3:
        return []

    mean = np.mean(data)
    std = np.std(data)

    if std == 0:
        return []

    anomalies = []
    for i, value in enumerate(data):
        z_score = abs(value - mean) / std
        if z_score > threshold:
            anomalies.append(i)

    return anomalies


def resample_ohlcv(ohlcv_data: List[List], timeframe: str = '1h') -> List[List]:
    """
    Resample OHLCV data to a different timeframe.

    Args:
        ohlcv_data: List of OHLCV data [timestamp, open, high, low, close, volume]
        timeframe: Target timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)

    Returns:
        Resampled OHLCV data
    """
    if not ohlcv_data:
        return []

    # Convert to DataFrame
    df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # Map timeframe to pandas resample string
    timeframe_map = {
        '1m': '1T',
        '5m': '5T',
        '15m': '15T',
        '30m': '30T',
        '1h': '1H',
        '4h': '4H',
        '1d': '1D'
    }

    resample_string = timeframe_map.get(timeframe, '1H')

    # Resample
    resampled = df.resample(resample_string).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })

    # Remove NaN values
    resampled = resampled.dropna()

    # Convert back to list format
    result = []
    for timestamp, row in resampled.iterrows():
        result.append([
            int(timestamp.timestamp() * 1000),  # Convert to milliseconds
            row['open'],
            row['high'],
            row['low'],
            row['close'],
            row['volume']
        ])

    return result


def validate_api_key_format(api_key: str, exchange: str) -> bool:
    """
    Validate API key format for different exchanges.

    Args:
        api_key: API key string
        exchange: Exchange name

    Returns:
        True if format is valid, False otherwise
    """
    if not api_key:
        return False

    # Exchange-specific validation
    if exchange == 'binance':
        # Binance API keys are typically 64 characters alphanumeric
        return bool(re.match(r'^[A-Za-z0-9]{64}$', api_key))

    elif exchange == 'okx':
        # OKX API keys are typically UUID format
        return bool(re.match(r'^[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}$', api_key))

    elif exchange == 'huobi':
        # Huobi API keys vary in format but are typically alphanumeric
        return bool(re.match(r'^[A-Za-z0-9]{20,40}$', api_key))

    # Generic validation - alphanumeric with reasonable length
    return bool(re.match(r'^[A-Za-z0-9]{10,100}$', api_key))


def format_currency_value(value: float, currency: str = 'USDT', decimals: int = 8) -> str:
    """
    Format currency value for display.

    Args:
        value: Currency value
        currency: Currency symbol
        decimals: Number of decimal places

    Returns:
        Formatted currency string
    """
    if value == 0:
        return f"0.00 {currency}"

    # Format based on value magnitude
    if abs(value) >= 1e6:
        formatted = f"{value/1e6:.{decimals}f}M {currency}"
    elif abs(value) >= 1e3:
        formatted = f"{value/1e3:.{decimals}f}K {currency}"
    else:
        formatted = f"{value:.{decimals}f} {currency}"

    return formatted


def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value
    """
    if value is None:
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def merge_order_books(book1: Dict, book2: Dict, max_depth: int = 20) -> Dict:
    """
    Merge two order books.

    Args:
        book1: First order book
        book2: Second order book
        max_depth: Maximum depth of merged book

    Returns:
        Merged order book
    """
    merged = {'bids': [], 'asks': []}

    # Merge bids (sorted by price descending)
    all_bids = []
    if 'bids' in book1:
        all_bids.extend(book1['bids'])
    if 'bids' in book2:
        all_bids.extend(book2['bids'])

    # Sort bids by price descending and merge same prices
    all_bids.sort(key=lambda x: float(x[0]), reverse=True)
    merged_bids = []

    for price, amount in all_bids:
        price = float(price)
        amount = float(amount)

        if merged_bids and abs(merged_bids[-1][0] - price) < 1e-8:
            # Merge same price levels
            merged_bids[-1] = (price, merged_bids[-1][1] + amount)
        else:
            merged_bids.append([price, amount])

    merged['bids'] = merged_bids[:max_depth]

    # Merge asks (sorted by price ascending)
    all_asks = []
    if 'asks' in book1:
        all_asks.extend(book1['asks'])
    if 'asks' in book2:
        all_asks.extend(book2['asks'])

    # Sort asks by price ascending and merge same prices
    all_asks.sort(key=lambda x: float(x[0]))
    merged_asks = []

    for price, amount in all_asks:
        price = float(price)
        amount = float(amount)

        if merged_asks and abs(merged_asks[-1][0] - price) < 1e-8:
            # Merge same price levels
            merged_asks[-1] = (price, merged_asks[-1][1] + amount)
        else:
            merged_asks.append([price, amount])

    merged['asks'] = merged_asks[:max_depth]

    return merged


def get_timeframe_seconds(timeframe: str) -> int:
    """
    Convert timeframe string to seconds.

    Args:
        timeframe: Timeframe string (1m, 5m, 15m, 30m, 1h, 4h, 1d)

    Returns:
        Timeframe in seconds
    """
    timeframe_map = {
        '1m': 60,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '4h': 14400,
        '1d': 86400
    }

    return timeframe_map.get(timeframe, 3600)