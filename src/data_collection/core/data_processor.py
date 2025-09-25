"""
Data Processor for processing and cleaning collected market data.

This module provides functionality for processing raw market data from exchanges,
including data cleaning, validation, normalization, and quality control.
"""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from dataclasses import dataclass

from ..config.settings import get_settings
from ..models.market_data import OHLCVData, OrderBookData, TradeData, TickerData
from ..utils.helpers import format_timestamp, normalize_symbol, safe_float_conversion
from ..utils.validation import DataValidator


@dataclass
class ProcessingResult:
    """Result of data processing operation."""
    success: bool
    processed_count: int
    error_count: int
    warnings: List[str]
    errors: List[str]
    processing_time_ms: float


class DataProcessor:
    """Processes and cleans market data."""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.validator = DataValidator()

        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'successful_processes': 0,
            'failed_processes': 0,
            'data_points_processed': 0,
            'anomalies_detected': 0,
            'outliers_corrected': 0,
            'last_processing_time': None
        }

    async def process_ohlcv(self, raw_data: List[List], exchange: str, symbol: str,
                           timeframe: str) -> List[OHLCVData]:
        """Process OHLCV data."""
        start_time = datetime.now()
        warnings = []
        errors = []

        try:
            if not raw_data:
                errors.append("Empty OHLCV data")
                return []

            processed_data = []

            # Process each OHLCV record
            for i, record in enumerate(raw_data):
                try:
                    ohlcv = await self._process_single_ohlcv(record, exchange, symbol, timeframe)
                    if ohlcv:
                        processed_data.append(ohlcv)
                except Exception as e:
                    errors.append(f"Error processing OHLCV record {i}: {str(e)}")

            # Additional validation and processing
            processed_data = await self._validate_ohlcv_sequence(processed_data, warnings)

            # Update statistics
            self._update_stats(True, len(processed_data), len(errors), start_time)

            return processed_data

        except Exception as e:
            errors.append(f"OHLCV processing failed: {str(e)}")
            self._update_stats(False, 0, len(errors), start_time)
            return []

    async def process_orderbook(self, raw_data: Dict, exchange: str, symbol: str) -> OrderBookData:
        """Process order book data."""
        start_time = datetime.now()
        warnings = []
        errors = []

        try:
            if not raw_data:
                errors.append("Empty order book data")
                return None

            # Create OrderBookData instance
            orderbook = OrderBookData(
                exchange=exchange,
                symbol=symbol,
                timestamp=datetime.now(timezone.utc),
                bids=raw_data.get('bids', []),
                asks=raw_data.get('asks', [])
            )

            # Calculate metrics
            orderbook.calculate_metrics()

            # Validate order book structure
            if not orderbook.bids or not orderbook.asks:
                errors.append("Order book missing bids or asks")
                return None

            # Check for anomalies
            anomalies = await self._detect_orderbook_anomalies(orderbook)
            if anomalies:
                warnings.extend(anomalies)

            # Update statistics
            self._update_stats(True, 1, len(errors), start_time)

            return orderbook

        except Exception as e:
            errors.append(f"Order book processing failed: {str(e)}")
            self._update_stats(False, 0, len(errors), start_time)
            return None

    async def process_trades(self, raw_data: List[Dict], exchange: str, symbol: str) -> List[TradeData]:
        """Process trades data."""
        start_time = datetime.now()
        warnings = []
        errors = []

        try:
            if not raw_data:
                errors.append("Empty trades data")
                return []

            processed_data = []

            # Process each trade record
            for i, trade in enumerate(raw_data):
                try:
                    trade_data = await self._process_single_trade(trade, exchange, symbol)
                    if trade_data:
                        processed_data.append(trade_data)
                except Exception as e:
                    errors.append(f"Error processing trade record {i}: {str(e)}")

            # Sort trades by timestamp
            processed_data.sort(key=lambda x: x.timestamp)

            # Detect trade anomalies
            anomalies = await self._detect_trade_anomalies(processed_data)
            if anomalies:
                warnings.extend(anomalies)

            # Update statistics
            self._update_stats(True, len(processed_data), len(errors), start_time)

            return processed_data

        except Exception as e:
            errors.append(f"Trades processing failed: {str(e)}")
            self._update_stats(False, 0, len(errors), start_time)
            return []

    async def process_ticker(self, raw_data: Dict, exchange: str, symbol: str) -> TickerData:
        """Process ticker data."""
        start_time = datetime.now()
        warnings = []
        errors = []

        try:
            if not raw_data:
                errors.append("Empty ticker data")
                return None

            # Normalize symbol
            normalized_symbol = normalize_symbol(symbol, exchange)

            # Create TickerData instance
            ticker = TickerData(
                exchange=exchange,
                symbol=normalized_symbol,
                timestamp=datetime.now(timezone.utc),
                last=safe_float_conversion(raw_data.get('last')),
                bid=safe_float_conversion(raw_data.get('bid')),
                ask=safe_float_conversion(raw_data.get('ask')),
                high=safe_float_conversion(raw_data.get('high')),
                low=safe_float_conversion(raw_data.get('low')),
                volume=safe_float_conversion(raw_data.get('volume')),
                quote_volume=safe_float_conversion(raw_data.get('quoteVolume')),
                open=safe_float_conversion(raw_data.get('open')),
                close=safe_float_conversion(raw_data.get('close')),
                previous_close=safe_float_conversion(raw_data.get('previousClose')),
                change=safe_float_conversion(raw_data.get('change')),
                change_percent=safe_float_conversion(raw_data.get('percentage')),
                average=safe_float_conversion(raw_data.get('averagePrice')),
                vwap=safe_float_conversion(raw_data.get('vwap'))
            )

            # Calculate derived metrics
            if ticker.open and ticker.close:
                ticker.change = ticker.close - ticker.open
                ticker.change_percent = (ticker.change / ticker.open) * 100 if ticker.open > 0 else 0

            # Validate ticker data
            if ticker.last <= 0:
                errors.append("Invalid last price in ticker")
                return None

            # Update statistics
            self._update_stats(True, 1, len(errors), start_time)

            return ticker

        except Exception as e:
            errors.append(f"Ticker processing failed: {str(e)}")
            self._update_stats(False, 0, len(errors), start_time)
            return None

    async def _process_single_ohlcv(self, record: List, exchange: str, symbol: str,
                                 timeframe: str) -> Optional[OHLCVData]:
        """Process a single OHLCV record."""
        try:
            # Ensure record has all required fields
            if len(record) < 6:
                self.logger.warning(f"Incomplete OHLCV record: {record}")
                return None

            # Extract fields
            timestamp, open_price, high, low, close, volume = record[:6]

            # Convert and validate fields
            timestamp = format_timestamp(timestamp)
            open_price = safe_float_conversion(open_price)
            high = safe_float_conversion(high)
            low = safe_float_conversion(low)
            close = safe_float_conversion(close)
            volume = safe_float_conversion(volume)

            # Validate numeric values
            if any(x is None or x < 0 for x in [open_price, high, low, close]):
                return None

            if volume < 0:
                return None

            # Validate price relationships
            if not (high >= low and high >= open_price and high >= close_price and
                   low <= open_price and low <= close_price):
                return None

            # Normalize symbol
            normalized_symbol = normalize_symbol(symbol, exchange)

            # Create OHLCVData instance
            ohlcv = OHLCVData(
                exchange=exchange,
                symbol=normalized_symbol,
                timeframe=timeframe,
                timestamp=timestamp,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                received_at=datetime.now(timezone.utc)
            )

            return ohlcv

        except Exception as e:
            self.logger.error(f"Error processing single OHLCV record: {e}")
            return None

    async def _process_single_trade(self, trade: Dict, exchange: str, symbol: str) -> Optional[TradeData]:
        """Process a single trade record."""
        try:
            # Extract required fields
            timestamp = trade.get('timestamp')
            price = trade.get('price')
            amount = trade.get('amount')
            side = trade.get('side')

            # Validate required fields
            if None in [timestamp, price, amount, side]:
                return None

            # Convert and validate fields
            timestamp = format_timestamp(timestamp)
            price = safe_float_conversion(price)
            amount = safe_float_conversion(amount)

            if price <= 0 or amount <= 0:
                return None

            # Validate side
            if side.lower() not in ['buy', 'sell']:
                return None

            # Normalize symbol
            normalized_symbol = normalize_symbol(symbol, exchange)

            # Create TradeData instance
            trade_data = TradeData(
                exchange=exchange,
                symbol=normalized_symbol,
                timestamp=timestamp,
                trade_id=trade.get('id'),
                price=price,
                amount=amount,
                side=side.lower(),
                type=trade.get('type'),
                taker_or_maker=trade.get('takerOrMaker'),
                received_at=datetime.now(timezone.utc)
            )

            # Calculate metrics
            trade_data.calculate_metrics()

            return trade_data

        except Exception as e:
            self.logger.error(f"Error processing single trade record: {e}")
            return None

    async def _validate_ohlcv_sequence(self, ohlcv_data: List[OHLCVData],
                                     warnings: List[str]) -> List[OHLCVData]:
        """Validate OHLCV sequence and detect anomalies."""
        if len(ohlcv_data) < 2:
            return ohlcv_data

        # Sort by timestamp
        ohlcv_data.sort(key=lambda x: x.timestamp)

        # Detect gaps
        expected_interval = 60  # Default to 1 minute, should be calculated from timeframe
        for i in range(1, len(ohlcv_data)):
            time_diff = (ohlcv_data[i].timestamp - ohlcv_data[i-1].timestamp).total_seconds()
            if time_diff > expected_interval * 1.5:  # 50% tolerance
                warnings.append(f"Gap detected in OHLCV data: {time_diff}s between candles")

        # Detect price anomalies
        prices = [candle.close for candle in ohlcv_data]
        anomalies = await self._detect_price_anomalies(prices)
        if anomalies:
            self.stats['anomalies_detected'] += len(anomalies)
            warnings.append(f"Price anomalies detected: {len(anomalies)} points")

        # Detect volume anomalies
        volumes = [candle.volume for candle in ohlcv_data]
        volume_anomalies = await self._detect_volume_anomalies(volumes)
        if volume_anomalies:
            self.stats['anomalies_detected'] += len(volume_anomalies)
            warnings.append(f"Volume anomalies detected: {len(volume_anomalies)} points")

        return ohlcv_data

    async def _detect_price_anomalies(self, prices: List[float], threshold: float = 3.0) -> List[int]:
        """Detect price anomalies using statistical methods."""
        if len(prices) < 10:
            return []

        anomalies = []

        # Calculate returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])

        if not returns:
            return []

        # Calculate Z-scores
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return []

        # Detect anomalies
        for i, ret in enumerate(returns):
            z_score = abs(ret - mean_return) / std_return
            if z_score > threshold:
                anomalies.append(i + 1)  # +1 because returns start from index 1

        return anomalies

    async def _detect_volume_anomalies(self, volumes: List[float], threshold: float = 3.0) -> List[int]:
        """Detect volume anomalies using statistical methods."""
        if len(volumes) < 10:
            return []

        anomalies = []

        # Calculate Z-scores
        mean_volume = np.mean(volumes)
        std_volume = np.std(volumes)

        if std_volume == 0:
            return []

        # Detect anomalies
        for i, volume in enumerate(volumes):
            z_score = abs(volume - mean_volume) / std_volume
            if z_score > threshold:
                anomalies.append(i)

        return anomalies

    async def _detect_orderbook_anomalies(self, orderbook: OrderBookData) -> List[str]:
        """Detect order book anomalies."""
        anomalies = []

        # Check bid-ask spread
        if orderbook.spread_percent > 5:  # More than 5% spread
            anomalies.append(f"Large bid-ask spread: {orderbook.spread_percent:.2f}%")

        # Check for inverted spread
        if orderbook.best_bid >= orderbook.best_ask:
            anomalies.append("Inverted bid-ask spread")

        # Check order book depth
        if len(orderbook.bids) < 5 or len(orderbook.asks) < 5:
            anomalies.append("Shallow order book depth")

        # Check for large imbalances
        if abs(orderbook.imbalance) > 0.8:  # More than 80% imbalance
            side = "bid" if orderbook.imbalance > 0 else "ask"
            anomalies.append(f"Large {side} side imbalance: {abs(orderbook.imbalance):.2f}")

        return anomalies

    async def _detect_trade_anomalies(self, trades: List[TradeData]) -> List[str]:
        """Detect trade anomalies."""
        anomalies = []

        if len(trades) < 10:
            return anomalies

        # Check for large trades
        large_trades = [t for t in trades if t.is_large_trade]
        if large_trades:
            anomalies.append(f"Large trades detected: {len(large_trades)} trades")

        # Check for rapid price movements
        prices = [t.price for t in trades]
        if len(prices) >= 2:
            price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            large_changes = [change for change in price_changes if change > 0.05]  # 5% change
            if large_changes:
                anomalies.append(f"Rapid price movements detected: {len(large_changes)} changes")

        # Check for unusual volume patterns
        volumes = [t.amount for t in trades]
        if volumes:
            avg_volume = np.mean(volumes)
            std_volume = np.std(volumes)
            if std_volume > 0:
                unusual_volumes = [v for v in volumes if abs(v - avg_volume) / std_volume > 3]
                if unusual_volumes:
                    anomalies.append(f"Unusual volume patterns detected: {len(unusual_volumes)} trades")

        return anomalies

    def _update_stats(self, success: bool, processed_count: int, error_count: int, start_time: datetime):
        """Update processing statistics."""
        self.stats['total_processed'] += 1
        self.stats['data_points_processed'] += processed_count

        if success:
            self.stats['successful_processes'] += 1
        else:
            self.stats['failed_processes'] += 1

        self.stats['last_processing_time'] = datetime.now()

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.stats.copy()

        # Calculate rates
        if stats['total_processed'] > 0:
            stats['success_rate'] = stats['successful_processes'] / stats['total_processed']
            stats['failure_rate'] = stats['failed_processes'] / stats['total_processed']

        return stats

    def reset_stats(self):
        """Reset processing statistics."""
        self.stats = {
            'total_processed': 0,
            'successful_processes': 0,
            'failed_processes': 0,
            'data_points_processed': 0,
            'anomalies_detected': 0,
            'outliers_corrected': 0,
            'last_processing_time': None
        }

    async def clean_ohlcv_data(self, ohlcv_data: List[OHLCVData]) -> Tuple[List[OHLCVData], List[str]]:
        """Clean OHLCV data by removing or correcting outliers."""
        if len(ohlcv_data) < 10:
            return ohlcv_data, []

        cleaned_data = []
        warnings = []

        # Sort by timestamp
        ohlcv_data.sort(key=lambda x: x.timestamp)

        for i, candle in enumerate(ohlcv_data):
            should_include = True
            issue = None

            # Check for price outliers
            if i > 0 and i < len(ohlcv_data) - 1:
                prev_close = ohlcv_data[i-1].close
                next_close = ohlcv_data[i+1].close
                current_close = candle.close

                # Check if current price is outlier compared to neighbors
                if prev_close > 0 and next_close > 0:
                    expected_price = (prev_close + next_close) / 2
                    deviation = abs(current_close - expected_price) / expected_price

                    if deviation > 0.1:  # 10% deviation threshold
                        issue = f"Price outlier detected: {deviation:.2%} deviation"
                        warnings.append(issue)

                        # Correct the outlier using linear interpolation
                        candle.close = expected_price
                        candle.open = expected_price  # Simplified correction
                        self.stats['outliers_corrected'] += 1

            # Check for volume outliers
            if i > 0:
                volumes = [c.volume for c in ohlcv_data[:i+1]]
                if len(volumes) >= 5:
                    recent_volumes = volumes[-5:]
                    avg_volume = np.mean(recent_volumes)
                    std_volume = np.std(recent_volumes)

                    if std_volume > 0:
                        volume_z_score = abs(candle.volume - avg_volume) / std_volume
                        if volume_z_score > 5:  # Very large volume
                            issue = f"Volume outlier detected: {volume_z_score:.2f} Z-score"
                            warnings.append(issue)

                            # Cap volume at reasonable level
                            candle.volume = avg_volume + 3 * std_volume
                            self.stats['outliers_corrected'] += 1

            if should_include:
                cleaned_data.append(candle)

        return cleaned_data, warnings

    async def aggregate_ohlcv_data(self, ohlcv_data: List[OHLCVData],
                                 target_timeframe: str) -> List[OHLCVData]:
        """Aggregate OHLCV data to a larger timeframe."""
        if not ohlcv_data:
            return []

        # Sort by timestamp
        ohlcv_data.sort(key=lambda x: x.timestamp)

        # Convert to DataFrame for easier aggregation
        df = pd.DataFrame([
            {
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume,
                'quote_volume': candle.quote_volume,
                'trades_count': candle.trades_count
            }
            for candle in ohlcv_data
        ])

        # Set timestamp as index
        df.set_index('timestamp', inplace=True)

        # Map timeframe to pandas resample string
        timeframe_map = {
            '5m': '5T',
            '15m': '15T',
            '30m': '30T',
            '1h': '1H',
            '4h': '4H',
            '1d': '1D'
        }

        resample_string = timeframe_map.get(target_timeframe)
        if not resample_string:
            raise ValueError(f"Unsupported timeframe: {target_timeframe}")

        # Aggregate data
        aggregated = df.resample(resample_string).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'quote_volume': 'sum',
            'trades_count': 'sum'
        })

        # Remove NaN values
        aggregated = aggregated.dropna()

        # Convert back to OHLCVData objects
        result = []
        for timestamp, row in aggregated.iterrows():
            ohlcv = OHLCVData(
                exchange=ohlcv_data[0].exchange,
                symbol=ohlcv_data[0].symbol,
                timeframe=target_timeframe,
                timestamp=timestamp,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                quote_volume=row['quote_volume'],
                trades_count=row['trades_count'] if pd.notna(row['trades_count']) else None
            )
            result.append(ohlcv)

        return result