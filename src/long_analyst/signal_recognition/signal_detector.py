"""
Base Signal Detector classes for Long Analyst Agent.

Provides the foundation for all signal detection algorithms with
abstraction and common functionality.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np

from ..models.signal import Signal, SignalType, SignalStrength, SignalSource, SignalCategory
from ..models.market_data import MarketData
from .signal_config import DetectorConfig


@dataclass
class DetectionResult:
    """Result of signal detection."""
    signal_type: SignalType
    strength: SignalStrength
    confidence: float
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reasoning: str = ""
    key_indicators: Dict[str, float] = None
    metadata: Dict[str, Any] = None
    detection_time: float = None

    def __post_init__(self):
        """Initialize default values."""
        if self.key_indicators is None:
            self.key_indicators = {}
        if self.metadata is None:
            self.metadata = {}
        if self.detection_time is None:
            self.detection_time = datetime.now().timestamp()


class SignalDetector(ABC):
    """
    Abstract base class for signal detectors.

    All signal detection algorithms inherit from this class and implement
    the required methods for consistent signal generation and evaluation.
    """

    def __init__(self, config: DetectorConfig):
        """Initialize the signal detector."""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Detection statistics
        self.total_detections = 0
        self.successful_detections = 0
        self.average_confidence = 0.0
        self.detection_times = []

    @abstractmethod
    async def detect(self, market_data: MarketData) -> List[DetectionResult]:
        """
        Detect signals from market data.

        Args:
            market_data: Market data to analyze

        Returns:
            List of detection results
        """
        pass

    @abstractmethod
    def get_required_indicators(self) -> List[str]:
        """
        Get list of required technical indicators.

        Returns:
            List of indicator names required by this detector
        """
        pass

    def calculate_confidence(self, detection_result: DetectionResult,
                           market_data: MarketData, indicators: Dict[str, Any]) -> float:
        """
        Calculate confidence score for detection result.

        Args:
            detection_result: The detection result to evaluate
            market_data: Current market data
            indicators: Calculated technical indicators

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence from detection
        confidence = detection_result.confidence

        # Adjust based on market data quality
        if hasattr(market_data, 'quality_score'):
            confidence *= (0.5 + 0.5 * market_data.quality_score)

        # Adjust based on data freshness
        data_age = datetime.now().timestamp() - market_data.timestamp
        if data_age < 60:  # Less than 1 minute
            confidence *= 1.0
        elif data_age < 300:  # Less than 5 minutes
            confidence *= 0.9
        else:  # Older data
            confidence *= 0.8

        return min(1.0, max(0.0, confidence))

    def validate_signal(self, detection_result: DetectionResult,
                       market_data: MarketData) -> bool:
        """
        Validate if a detection result meets minimum criteria.

        Args:
            detection_result: Detection result to validate
            market_data: Current market data

        Returns:
            True if signal is valid
        """
        # Check minimum confidence
        if detection_result.confidence < self.config.min_confidence:
            return False

        # Check if signal is too old
        signal_age = datetime.now().timestamp() - detection_result.detection_time
        if signal_age > 300:  # 5 minutes
            return False

        # Validate price targets if provided
        current_price = market_data.get_price()
        if current_price and detection_result.price_target:
            # For buy signals, target should be above current price
            if detection_result.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                if detection_result.price_target <= current_price:
                    return False

        return True

    def create_signal(self, detection_result: DetectionResult,
                     market_data: MarketData, confidence: float) -> Signal:
        """
        Create a Signal object from detection result.

        Args:
            detection_result: Detection result to convert
            market_data: Current market data
            confidence: Final confidence score

        Returns:
            Complete Signal object
        """
        signal = Signal(
            symbol=market_data.symbol,
            signal_type=detection_result.signal_type,
            strength=detection_result.strength,
            confidence=confidence,
            price_target=detection_result.price_target,
            stop_loss=detection_result.stop_loss,
            take_profit=detection_result.take_profit,
            reasoning=detection_result.reasoning,
            key_indicators=detection_result.key_indicators,
            win_probability=confidence * 0.8  # Initial win probability estimate
        )

        # Add detector as source
        signal.sources.append(SignalSource(
            category=SignalCategory.TECHNICAL,
            name=self.config.name,
            confidence=confidence,
            weight=self.config.weight,
            metadata=detection_result.metadata
        ))

        return signal

    async def detect_and_validate(self, market_data: MarketData,
                                indicators: Dict[str, Any] = None) -> List[Signal]:
        """
        Detect signals and validate them.

        Args:
            market_data: Market data to analyze
            indicators: Pre-calculated technical indicators

        Returns:
            List of validated signals
        """
        if not self.config.enabled:
            return []

        start_time = datetime.now().timestamp()
        self.total_detections += 1

        try:
            # Detect signals
            detection_results = await self.detect(market_data)

            # Validate and convert to signals
            signals = []
            for result in detection_results:
                # Calculate confidence
                confidence = self.calculate_confidence(result, market_data, indicators or {})

                # Validate signal
                if self.validate_signal(result, market_data):
                    # Create signal
                    signal = self.create_signal(result, market_data, confidence)
                    signals.append(signal)
                    self.successful_detections += 1

                # Update statistics
                self.average_confidence = (
                    (self.average_confidence * (self.successful_detections - 1) + confidence) /
                    self.successful_detections if self.successful_detections > 0 else confidence
                )

            # Record detection time
            detection_time = (datetime.now().timestamp() - start_time) * 1000
            self.detection_times.append(detection_time)

            # Keep only recent detection times for average calculation
            if len(self.detection_times) > 100:
                self.detection_times = self.detection_times[-100:]

            return signals

        except Exception as e:
            self.logger.error(f"Error in {self.config.name} detection: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get detection statistics.

        Returns:
            Dictionary with detection statistics
        """
        avg_detection_time = (
            np.mean(self.detection_times) if self.detection_times else 0.0
        )

        success_rate = (
            self.successful_detections / self.total_detections
            if self.total_detections > 0 else 0.0
        )

        return {
            "detector_name": self.config.name,
            "total_detections": self.total_detections,
            "successful_detections": self.successful_detections,
            "success_rate": success_rate,
            "average_confidence": self.average_confidence,
            "average_detection_time_ms": avg_detection_time,
            "enabled": self.config.enabled,
            "priority": self.config.priority.value,
            "weight": self.config.weight
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the detector.

        Returns:
            Health check results
        """
        stats = self.get_statistics()

        health_status = {
            "status": "healthy",
            "statistics": stats,
            "last_check": datetime.now().isoformat()
        }

        # Check for potential issues
        if stats["success_rate"] < 0.1:
            health_status["status"] = "warning"
            health_status["issues"] = ["Low success rate"]

        if stats["average_detection_time_ms"] > 500:
            health_status["status"] = "warning"
            health_status.setdefault("issues", []).append("Slow detection time")

        return health_status


class CompositeDetector(SignalDetector):
    """
    Composite detector that combines multiple detectors.

    This detector manages multiple child detectors and combines their results
    according to configured weights and priorities.
    """

    def __init__(self, config: DetectorConfig, child_detectors: List[SignalDetector]):
        """Initialize composite detector."""
        super().__init__(config)
        self.child_detectors = child_detectors

    async def detect(self, market_data: MarketData) -> List[DetectionResult]:
        """Detect signals using all child detectors."""
        all_results = []

        # Run all child detectors concurrently
        tasks = []
        for detector in self.child_detectors:
            if detector.config.enabled:
                tasks.append(detector.detect(market_data))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Error in child detector: {result}")
                elif result:
                    all_results.extend(result)

        return all_results

    def get_required_indicators(self) -> List[str]:
        """Get combined list of required indicators."""
        indicators = set()
        for detector in self.child_detectors:
            indicators.update(detector.get_required_indicators())
        return list(indicators)