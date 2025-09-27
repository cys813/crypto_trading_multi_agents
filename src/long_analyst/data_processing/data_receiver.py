"""
Data Receiver and Processing Module for Long Analyst Agent.

This module provides unified data interface for receiving, validating, and processing
market data from multiple sources including trading data, news, and social media.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import time
import aiohttp
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod

from ..models.market_data import MarketData, DataSource, Timeframe
from ..events.event_manager import EventManager
from ..utils.performance_monitor import PerformanceMonitor


class DataFormat(Enum):
    """Supported data formats."""
    JSON = "json"
    CSV = "csv"
    PROTOBUF = "protobuf"
    WEBSOCKET = "websocket"
    REST_API = "rest_api"


class DataType(Enum):
    """Types of data supported."""
    MARKET_DATA = "market_data"
    NEWS_DATA = "news_data"
    SOCIAL_MEDIA = "social_media"
    FUNDAMENTAL_DATA = "fundamental_data"


class DataQuality(Enum):
    """Data quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


@dataclass
class DataReceiverConfig:
    """Configuration for data receiver."""

    # Performance settings
    max_concurrent_requests: int = 100
    request_timeout_seconds: int = 30
    batch_size: int = 1000

    # Quality settings
    min_data_quality: DataQuality = DataQuality.GOOD
    enable_data_validation: bool = True
    enable_data_preprocessing: bool = True

    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    backoff_factor: float = 2.0

    # Cache settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 300

    # Data sources
    enabled_sources: List[DataSource] = None
    enabled_formats: List[DataFormat] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.enabled_sources is None:
            self.enabled_sources = [DataSource.BINANCE, DataSource.COINBASE, DataSource.KRAKEN]
        if self.enabled_formats is None:
            self.enabled_formats = [DataFormat.JSON, DataFormat.REST_API]


@dataclass
class ProcessedData:
    """Container for processed data."""

    source: DataSource
    data_type: DataType
    format: DataFormat
    timestamp: float
    quality: DataQuality
    data: Any
    metadata: Dict[str, Any]
    processing_time_ms: float
    validation_errors: List[str] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.validation_errors is None:
            self.validation_errors = []


class DataValidator(ABC):
    """Abstract base class for data validators."""

    @abstractmethod
    async def validate(self, data: Any) -> Dict[str, Any]:
        """Validate data and return validation results."""
        pass

    @abstractmethod
    def get_quality_score(self, data: Any) -> float:
        """Calculate quality score for data."""
        pass


class MarketDataValidator(DataValidator):
    """Validator for market data."""

    def __init__(self):
        """Initialize market data validator."""
        self.logger = logging.getLogger(__name__)
        self.required_fields = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
        self.min_data_points = 100

    async def validate(self, data: Any) -> Dict[str, Any]:
        """Validate market data."""
        results = {
            'is_valid': True,
            'quality_score': 1.0,
            'errors': [],
            'warnings': [],
            'completeness': 1.0,
            'accuracy': 1.0,
            'timeliness': 1.0
        }

        try:
            # Check if data is pandas DataFrame
            if not isinstance(data, pd.DataFrame):
                results['is_valid'] = False
                results['errors'].append("Data must be a pandas DataFrame")
                return results

            # Check required fields
            missing_fields = [field for field in self.required_fields if field not in data.columns]
            if missing_fields:
                results['is_valid'] = False
                results['errors'].append(f"Missing required fields: {missing_fields}")
                results['completeness'] = 1.0 - (len(missing_fields) / len(self.required_fields))

            # Check data size
            if len(data) < self.min_data_points:
                results['warnings'].append(f"Data has only {len(data)} points, minimum {self.min_data_points} recommended")
                results['completeness'] *= len(data) / self.min_data_points

            # Check for missing values
            missing_values = data.isnull().sum()
            total_missing = missing_values.sum()
            if total_missing > 0:
                results['warnings'].append(f"Found {total_missing} missing values")
                results['completeness'] *= (len(data) * len(data.columns) - total_missing) / (len(data) * len(data.columns))

            # Check data consistency
            if not self._check_data_consistency(data):
                results['warnings'].append("Data consistency issues detected")
                results['accuracy'] *= 0.9

            # Check data freshness
            timeliness = self._check_data_freshness(data)
            results['timeliness'] = timeliness

            # Calculate overall quality score
            results['quality_score'] = (results['completeness'] + results['accuracy'] + results['timeliness']) / 3

            return results

        except Exception as e:
            self.logger.error(f"Error validating market data: {e}")
            results['is_valid'] = False
            results['errors'].append(f"Validation error: {str(e)}")
            results['quality_score'] = 0.0
            return results

    def get_quality_score(self, data: Any) -> float:
        """Get quality score for market data."""
        try:
            if isinstance(data, pd.DataFrame):
                # Simple quality heuristic based on completeness
                completeness = 1.0 - (data.isnull().sum().sum() / (len(data) * len(data.columns)))
                return min(1.0, max(0.0, completeness))
            return 0.5
        except Exception:
            return 0.0

    def _check_data_consistency(self, data: pd.DataFrame) -> bool:
        """Check data consistency."""
        try:
            # Check if high >= low >= open/close
            inconsistent_rows = data[
                (data['high'] < data['low']) |
                (data['high'] < data['open']) |
                (data['high'] < data['close']) |
                (data['low'] > data['open']) |
                (data['low'] > data['close'])
            ]
            return len(inconsistent_rows) == 0
        except Exception:
            return False

    def _check_data_freshness(self, data: pd.DataFrame) -> float:
        """Check data freshness and return timeliness score."""
        try:
            if 'timestamp' in data.columns:
                latest_timestamp = data['timestamp'].max()
                current_time = time.time()
                age_hours = (current_time - latest_timestamp) / 3600

                if age_hours < 1:
                    return 1.0
                elif age_hours < 6:
                    return 0.8
                elif age_hours < 24:
                    return 0.6
                else:
                    return 0.3
            return 0.5
        except Exception:
            return 0.5


class DataProcessor:
    """Data processor for cleaning and standardizing data."""

    def __init__(self, config: DataReceiverConfig):
        """Initialize data processor."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()

    async def process_data(self, raw_data: Any, source: DataSource, data_type: DataType) -> ProcessedData:
        """Process raw data and return standardized result."""
        start_time = time.time()

        try:
            # Convert to standard format
            standardized_data = await self._standardize_format(raw_data, data_type)

            # Clean data
            cleaned_data = await self._clean_data(standardized_data, data_type)

            # Validate data
            validation_result = await self._validate_data(cleaned_data, data_type)

            # Calculate quality score
            quality_score = validation_result.get('quality_score', 0.5)
            quality = self._score_to_quality(quality_score)

            # Create processed data container
            processed_data = ProcessedData(
                source=source,
                data_type=data_type,
                format=DataFormat.JSON,  # Standardized to JSON
                timestamp=time.time(),
                quality=quality,
                data=cleaned_data,
                metadata={
                    'original_size': len(raw_data) if hasattr(raw_data, '__len__') else 'unknown',
                    'processed_size': len(cleaned_data) if hasattr(cleaned_data, '__len__') else 'unknown',
                    'quality_score': quality_score,
                    'validation_result': validation_result
                },
                processing_time_ms=(time.time() - start_time) * 1000,
                validation_errors=validation_result.get('errors', [])
            )

            return processed_data

        except Exception as e:
            self.logger.error(f"Error processing data from {source}: {e}")
            return ProcessedData(
                source=source,
                data_type=data_type,
                format=DataFormat.JSON,
                timestamp=time.time(),
                quality=DataQuality.INVALID,
                data=None,
                metadata={'error': str(e)},
                processing_time_ms=(time.time() - start_time) * 1000,
                validation_errors=[f"Processing error: {str(e)}"]
            )

    async def _standardize_format(self, raw_data: Any, data_type: DataType) -> Any:
        """Standardize data format."""
        if data_type == DataType.MARKET_DATA:
            if isinstance(raw_data, pd.DataFrame):
                return raw_data
            elif isinstance(raw_data, list):
                return pd.DataFrame(raw_data)
            elif isinstance(raw_data, dict):
                return pd.DataFrame([raw_data])
            else:
                raise ValueError(f"Unsupported market data format: {type(raw_data)}")
        else:
            # For other data types, return as-is for now
            return raw_data

    async def _clean_data(self, data: Any, data_type: DataType) -> Any:
        """Clean and preprocess data."""
        if data_type == DataType.MARKET_DATA and isinstance(data, pd.DataFrame):
            return self._clean_market_data(data)
        else:
            return data

    def _clean_market_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean market data DataFrame."""
        # Make a copy to avoid modifying original
        cleaned = df.copy()

        # Convert timestamp if needed
        if 'timestamp' in cleaned.columns:
            cleaned['timestamp'] = pd.to_numeric(cleaned['timestamp'])

        # Sort by timestamp
        if 'timestamp' in cleaned.columns:
            cleaned = cleaned.sort_values('timestamp')

        # Handle missing values
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in cleaned.columns:
                cleaned[col] = pd.to_numeric(cleaned[col], errors='coerce')
                # Forward fill missing values
                cleaned[col] = cleaned[col].fillna(method='ffill')
                # Drop remaining NaN values
                cleaned = cleaned.dropna(subset=[col])

        # Remove outliers (values beyond 5 standard deviations)
        for col in numeric_columns:
            if col in cleaned.columns:
                mean = cleaned[col].mean()
                std = cleaned[col].std()
                if std > 0:
                    cleaned = cleaned[
                        (cleaned[col] >= mean - 5 * std) &
                        (cleaned[col] <= mean + 5 * std)
                    ]

        # Reset index
        cleaned = cleaned.reset_index(drop=True)

        return cleaned

    async def _validate_data(self, data: Any, data_type: DataType) -> Dict[str, Any]:
        """Validate processed data."""
        if data_type == DataType.MARKET_DATA:
            validator = MarketDataValidator()
            return await validator.validate(data)
        else:
            return {
                'is_valid': True,
                'quality_score': 0.8,
                'errors': [],
                'warnings': [],
                'completeness': 1.0,
                'accuracy': 1.0,
                'timeliness': 1.0
            }

    def _score_to_quality(self, score: float) -> DataQuality:
        """Convert quality score to DataQuality enum."""
        if score >= 0.9:
            return DataQuality.EXCELLENT
        elif score >= 0.7:
            return DataQuality.GOOD
        elif score >= 0.5:
            return DataQuality.FAIR
        elif score > 0.0:
            return DataQuality.POOR
        else:
            return DataQuality.INVALID


class DataReceiver:
    """
    Unified data receiver for multi-source data ingestion.

    This class provides a unified interface for receiving data from various
    sources including market data feeds, news APIs, and social media streams.
    """

    def __init__(self, config: DataReceiverConfig):
        """Initialize the data receiver."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()
        self.event_manager = EventManager()

        # Initialize data processor
        self.processor = DataProcessor(config)

        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_requests)

        # Session management
        self.session = None
        self.active_connections = 0

        # Metrics
        self.total_received = 0
        self.total_processed = 0
        self.error_count = 0
        self.average_processing_time = 0.0

        self.logger.info("Data receiver initialized")

    async def start(self):
        """Start the data receiver."""
        self.logger.info("Starting data receiver")

        # Create HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.request_timeout_seconds)
        )

        self.logger.info("Data receiver started")

    async def stop(self):
        """Stop the data receiver."""
        self.logger.info("Stopping data receiver")

        # Close HTTP session
        if self.session:
            await self.session.close()

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        self.logger.info("Data receiver stopped")

    async def receive_data(self, source: DataSource, data_type: DataType,
                          data: Any, format: DataFormat = DataFormat.JSON) -> Optional[ProcessedData]:
        """
        Receive and process data from a source.

        Args:
            source: Data source
            data_type: Type of data
            data: Raw data
            format: Data format

        Returns:
            Processed data or None if processing failed
        """
        start_time = time.time()

        try:
            self.total_received += 1

            # Emit receive event
            await self.event_manager.emit("data_received", {
                "source": source.value,
                "data_type": data_type.value,
                "format": format.value,
                "timestamp": time.time()
            })

            # Process data
            processed_data = await self.processor.process_data(data, source, data_type)

            # Update metrics
            self.total_processed += 1
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time)

            # Emit processed event
            await self.event_manager.emit("data_processed", {
                "source": source.value,
                "data_type": data_type.value,
                "quality": processed_data.quality.value,
                "processing_time_ms": processing_time,
                "success": processed_data.quality != DataQuality.INVALID
            })

            return processed_data

        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error receiving data from {source}: {e}")

            # Emit error event
            await self.event_manager.emit("data_error", {
                "source": source.value,
                "data_type": data_type.value,
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000
            })

            return None

    async def fetch_market_data(self, symbol: str, timeframe: Timeframe,
                              source: DataSource = DataSource.BINANCE,
                              limit: int = 1000) -> Optional[ProcessedData]:
        """
        Fetch market data from a source.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            source: Data source
            limit: Number of data points to fetch

        Returns:
            Processed market data
        """
        if not self.session:
            raise RuntimeError("Data receiver not started")

        try:
            # Construct API URL based on source
            url = self._get_api_url(source, symbol, timeframe, limit)

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self.receive_data(source, DataType.MARKET_DATA, data)
                else:
                    self.logger.error(f"API request failed: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Error fetching market data: {e}")
            return None

    async def batch_receive(self, data_items: List[Dict[str, Any]]) -> List[ProcessedData]:
        """
        Receive multiple data items concurrently.

        Args:
            data_items: List of data items to process

        Returns:
            List of processed data
        """
        tasks = []
        for item in data_items:
            task = self.receive_data(
                source=item['source'],
                data_type=item['data_type'],
                data=item['data'],
                format=item.get('format', DataFormat.JSON)
            )
            tasks.append(task)

        # Process concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and None results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Batch processing error: {result}")
                self.error_count += 1
            elif result is not None:
                processed_results.append(result)

        return processed_results

    def _get_api_url(self, source: DataSource, symbol: str, timeframe: Timeframe, limit: int) -> str:
        """Get API URL for data source."""
        # This is a simplified implementation - in production, you'd have proper API endpoints
        base_urls = {
            DataSource.BINANCE: "https://api.binance.com/api/v3/klines",
            DataSource.COINBASE: "https://api.pro.coinbase.com/products",
            DataSource.KRAKEN: "https://api.kraken.com/0/public/OHLC"
        }

        # Convert timeframe to API format
        timeframe_map = {
            Timeframe.M1: "1m",
            Timeframe.M5: "5m",
            Timeframe.M15: "15m",
            Timeframe.H1: "1h",
            Timeframe.H4: "4h",
            Timeframe.D1: "1d"
        }

        if source in base_urls:
            return f"{base_urls[source]}?symbol={symbol}&interval={timeframe_map.get(timeframe, '1h')}&limit={limit}"
        else:
            raise ValueError(f"Unsupported data source: {source}")

    def _update_performance_metrics(self, processing_time: float):
        """Update performance metrics."""
        self.total_processed += 1

        # Update average processing time
        if self.total_processed > 0:
            self.average_processing_time = (
                (self.average_processing_time * (self.total_processed - 1) + processing_time) /
                self.total_processed
            )

        # Record metrics
        self.performance_monitor.record_metric("processing_time", processing_time)
        self.performance_monitor.record_metric("total_processed", self.total_processed)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "total_received": self.total_received,
            "total_processed": self.total_processed,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(1, self.total_received),
            "average_processing_time_ms": self.average_processing_time,
            "active_connections": self.active_connections,
            "throughput_per_second": self.total_processed / max(1, time.time() - self.performance_monitor.start_time)
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "status": "healthy",
            "session_active": self.session is not None,
            "active_connections": self.active_connections,
            "metrics": await self.get_metrics()
        }