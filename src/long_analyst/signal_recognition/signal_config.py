"""
Configuration classes for Signal Recognition Algorithms.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class DetectionMode(Enum):
    """Signal detection modes."""
    REAL_TIME = "real_time"
    BATCH = "batch"
    BACKTEST = "backtest"


class SignalPriority(Enum):
    """Signal priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SignalConfig:
    """Configuration for signal recognition algorithms."""

    # Performance settings
    max_concurrent_detections: int = 100
    detection_timeout_ms: int = 1000
    enable_caching: bool = True
    cache_ttl_seconds: int = 300

    # Detection settings
    min_signal_strength: float = 0.6
    min_confidence: float = 0.7
    enable_multi_timeframe: bool = True
    timeframes: List[str] = field(default_factory=lambda: ["1m", "5m", "15m", "1h", "4h"])

    # Algorithm settings
    enable_trend_detection: bool = True
    enable_breakout_detection: bool = True
    enable_pullback_detection: bool = True
    enable_pattern_recognition: bool = True

    # Trend detection settings
    trend_min_period: int = 20
    trend_strength_threshold: float = 0.6
    require_volume_confirmation: bool = True
    min_volume_ratio: float = 1.2

    # Breakout detection settings
    breakout_lookback_periods: int = 50
    breakout_confirmation_periods: int = 3
    breakout_volume_multiplier: float = 1.5
    false_breakout_filter: bool = True

    # Pullback detection settings
    pullback_fibonacci_levels: List[float] = field(default_factory=lambda: [0.382, 0.5, 0.618])
    pullback_ma_periods: List[int] = field(default_factory=lambda: [20, 50])
    max_pullback_depth: float = 0.3  # 30% max pullback

    # Pattern recognition settings
    pattern_min_confidence: float = 0.8
    pattern_lookback_periods: int = 100
    enable_neckline_breakout: bool = True

    # Multi-timeframe settings
    timeframe_weights: Dict[str, float] = field(default_factory=lambda: {
        "1m": 0.1, "5m": 0.15, "15m": 0.2, "1h": 0.3, "4h": 0.25
    })
    require_timeframe_consistency: bool = True
    min_consistent_timeframes: int = 2

    # Risk management
    max_risk_per_signal: float = 0.02
    min_risk_reward_ratio: float = 2.0
    enable_dynamic_stops: bool = True

    # Output settings
    max_signals_per_symbol: int = 5
    signal_expiry_hours: int = 24
    enable_signal_ranking: bool = True
    detailed_output: bool = True

    # Debug and logging
    enable_debug_logging: bool = False
    log_signal_details: bool = True
    save_detection_history: bool = True

    def __post_init__(self):
        """Validate configuration."""
        # Validate strength and confidence thresholds
        if not (0.0 <= self.min_signal_strength <= 1.0):
            raise ValueError("min_signal_strength must be between 0.0 and 1.0")

        if not (0.0 <= self.min_confidence <= 1.0):
            raise ValueError("min_confidence must be between 0.0 and 1.0")

        # Validate timeframe weights sum to 1.0
        total_weight = sum(self.timeframe_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            # Normalize weights
            for timeframe in self.timeframe_weights:
                self.timeframe_weights[timeframe] /= total_weight

        # Validate periods
        if self.trend_min_period < 5:
            raise ValueError("trend_min_period must be at least 5")

        if self.breakout_lookback_periods < 10:
            raise ValueError("breakout_lookback_periods must be at least 10")


@dataclass
class DetectorConfig:
    """Configuration for individual signal detectors."""

    name: str
    enabled: bool = True
    priority: SignalPriority = SignalPriority.MEDIUM
    weight: float = 1.0
    min_confidence: float = 0.6
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate detector configuration."""
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError("weight must be between 0.0 and 1.0")

        if not (0.0 <= self.min_confidence <= 1.0):
            raise ValueError("min_confidence must be between 0.0 and 1.0")