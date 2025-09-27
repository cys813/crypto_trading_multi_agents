"""
Performance metrics and win rate calculation for the Long Analyst Agent.

Provides comprehensive performance tracking and analysis capabilities
 for evaluating signal quality and system effectiveness.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import statistics
import numpy as np
from .signal import Signal, SignalType, SignalStrength
from .analysis_result import AnalysisResult


class PerformanceMetric(Enum):
    """Types of performance metrics."""
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    AVERAGE_RETURN = "average_return"
    TOTAL_RETURN = "total_return"
    SIGNAL_ACCURACY = "signal_accuracy"
    RISK_ADJUSTED_RETURN = "risk_adjusted_return"
    EXPECTED_VALUE = "expected_value"


class TimeWindow(Enum):
    """Time windows for performance analysis."""
    HOUR_1 = "1h"
    HOUR_24 = "24h"
    DAY_7 = "7d"
    DAY_30 = "30d"
    DAY_90 = "90d"
    YEAR_1 = "1y"
    ALL_TIME = "all"


@dataclass
class SignalPerformance:
    """Performance data for a single signal."""
    signal_id: str
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: float = field(default_factory=lambda: datetime.now().timestamp())
    exit_time: Optional[float] = None
    holding_period_hours: Optional[float] = None
    return_percentage: Optional[float] = None
    outcome: Optional[str] = None  # "win", "loss", "breakeven"
    fees: float = 0.0
    slippage: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_closed(self) -> bool:
        """Check if signal performance is complete."""
        return self.exit_price is not None and self.exit_time is not None

    @property
    def holding_period(self) -> Optional[timedelta]:
        """Get holding period as timedelta."""
        if self.exit_time is None:
            return None
        return timedelta(seconds=self.exit_time - self.entry_time)

    def close_position(self, exit_price: float, exit_time: float, fees: float = 0.0):
        """Close the position and calculate performance."""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.holding_period_hours = (exit_time - self.entry_time) / 3600
        self.fees = fees

        # Calculate return percentage
        if self.signal_type in [SignalType.BUY, SignalType.MODERATE_BUY, SignalType.STRONG_BUY]:
            self.return_percentage = ((exit_price - self.entry_price) / self.entry_price) * 100
        else:
            self.return_percentage = ((self.entry_price - exit_price) / self.entry_price) * 100

        # Determine outcome
        if self.return_percentage > 0.1:  # Small threshold for wins
            self.outcome = "win"
        elif self.return_percentage < -0.1:
            self.outcome = "loss"
        else:
            self.outcome = "breakeven"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "strength": self.strength.value,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "holding_period_hours": self.holding_period_hours,
            "return_percentage": self.return_percentage,
            "outcome": self.outcome,
            "fees": self.fees,
            "slippage": self.slippage,
            "metadata": self.metadata
        }


@dataclass
class PerformanceSnapshot:
    """Performance snapshot at a specific point in time."""
    timestamp: float
    total_signals: int
    active_signals: int
    closed_signals: int
    winning_signals: int
    losing_signals: int
    breakeven_signals: int
    win_rate: float
    average_return: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    risk_adjusted_return: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "total_signals": self.total_signals,
            "active_signals": self.active_signals,
            "closed_signals": self.closed_signals,
            "winning_signals": self.winning_signals,
            "losing_signals": self.losing_signals,
            "breakeven_signals": self.breakeven_signals,
            "win_rate": self.win_rate,
            "average_return": self.average_return,
            "total_return": self.total_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "profit_factor": self.profit_factor,
            "risk_adjusted_return": self.risk_adjusted_return
        }


class WinRateCalculator:
    """Calculator for win rate and performance metrics."""

    def __init__(self):
        """Initialize the win rate calculator."""
        self.signal_performances: List[SignalPerformance] = []
        self.performance_history: List[PerformanceSnapshot] = []
        self.baseline_win_rate: float = 0.5

    def add_signal_performance(self, signal: Signal, entry_price: float, entry_time: float) -> SignalPerformance:
        """Add a new signal for performance tracking."""
        performance = SignalPerformance(
            signal_id=signal.id,
            symbol=signal.symbol,
            signal_type=signal.signal_type,
            strength=signal.strength,
            entry_price=entry_price,
            entry_time=entry_time,
            metadata={
                "signal_strength": signal.strength.value,
                "signal_confidence": signal.confidence,
                "expected_return": signal.expected_return
            }
        )
        self.signal_performances.append(performance)
        return performance

    def close_signal(self, signal_id: str, exit_price: float, exit_time: float, fees: float = 0.0) -> Optional[SignalPerformance]:
        """Close a signal and update performance metrics."""
        for performance in self.signal_performances:
            if performance.signal_id == signal_id and not performance.is_closed:
                performance.close_position(exit_price, exit_time, fees)
                return performance
        return None

    def calculate_win_rate(self, window: TimeWindow = TimeWindow.ALL_TIME) -> float:
        """Calculate win rate for the specified time window."""
        closed_signals = self._get_closed_signals_in_window(window)
        if not closed_signals:
            return 0.0

        winning_signals = [s for s in closed_signals if s.outcome == "win"]
        return len(winning_signals) / len(closed_signals)

    def calculate_average_return(self, window: TimeWindow = TimeWindow.ALL_TIME) -> float:
        """Calculate average return for the specified time window."""
        closed_signals = self._get_closed_signals_in_window(window)
        if not closed_signals:
            return 0.0

        returns = [s.return_percentage for s in closed_signals if s.return_percentage is not None]
        return statistics.mean(returns) if returns else 0.0

    def calculate_total_return(self, window: TimeWindow = TimeWindow.ALL_TIME) -> float:
        """Calculate total return for the specified time window."""
        closed_signals = self._get_closed_signals_in_window(window)
        if not closed_signals:
            return 0.0

        total_return = sum(s.return_percentage for s in closed_signals if s.return_percentage is not None)
        return total_return

    def calculate_profit_factor(self, window: TimeWindow = TimeWindow.ALL_TIME) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        closed_signals = self._get_closed_signals_in_window(window)
        if not closed_signals:
            return 0.0

        gross_profit = sum(s.return_percentage for s in closed_signals if s.return_percentage and s.return_percentage > 0)
        gross_loss = sum(abs(s.return_percentage) for s in closed_signals if s.return_percentage and s.return_percentage < 0)

        return gross_profit / gross_loss if gross_loss > 0 else float('inf')

    def calculate_max_drawdown(self, window: TimeWindow = TimeWindow.ALL_TIME) -> float:
        """Calculate maximum drawdown."""
        closed_signals = self._get_closed_signals_in_window(window)
        if not closed_signals:
            return 0.0

        # Sort signals by entry time
        sorted_signals = sorted(closed_signals, key=lambda x: x.entry_time)

        # Calculate cumulative returns
        cumulative_returns = []
        cumulative_sum = 0.0

        for signal in sorted_signals:
            if signal.return_percentage is not None:
                cumulative_sum += signal.return_percentage
                cumulative_returns.append(cumulative_sum)

        if not cumulative_returns:
            return 0.0

        # Calculate drawdown
        peak = cumulative_returns[0]
        max_drawdown = 0.0

        for value in cumulative_returns[1:]:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def calculate_sharpe_ratio(self, window: TimeWindow = TimeWindow.ALL_TIME, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        closed_signals = self._get_closed_signals_in_window(window)
        if len(closed_signals) < 2:
            return 0.0

        returns = [s.return_percentage for s in closed_signals if s.return_percentage is not None]
        if not returns:
            return 0.0

        # Convert to annualized returns
        avg_return = statistics.mean(returns) * 252  # Assuming daily returns
        std_dev = statistics.stdev(returns) * np.sqrt(252)  # Annualized standard deviation

        return (avg_return - risk_free_rate) / std_dev if std_dev > 0 else 0.0

    def calculate_risk_adjusted_return(self, window: TimeWindow = TimeWindow.ALL_TIME) -> float:
        """Calculate risk-adjusted return (return / max_drawdown)."""
        avg_return = self.calculate_average_return(window)
        max_drawdown = self.calculate_max_drawdown(window)

        return avg_return / max_drawdown if max_drawdown > 0 else 0.0

    def calculate_signal_accuracy(self, signal_type: SignalType, window: TimeWindow = TimeWindow.ALL_TIME) -> float:
        """Calculate accuracy for a specific signal type."""
        closed_signals = self._get_closed_signals_in_window(window)
        type_signals = [s for s in closed_signals if s.signal_type == signal_type]

        if not type_signals:
            return 0.0

        winning_signals = [s for s in type_signals if s.outcome == "win"]
        return len(winning_signals) / len(type_signals)

    def get_performance_summary(self, window: TimeWindow = TimeWindow.ALL_TIME) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        closed_signals = self._get_closed_signals_in_window(window)
        active_signals = [s for s in self.signal_performances if not s.is_closed]

        total_signals = len(closed_signals) + len(active_signals)
        winning_signals = [s for s in closed_signals if s.outcome == "win"]
        losing_signals = [s for s in closed_signals if s.outcome == "loss"]
        breakeven_signals = [s for s in closed_signals if s.outcome == "breakeven"]

        win_rate = len(winning_signals) / len(closed_signals) if closed_signals else 0.0

        return {
            "window": window.value,
            "total_signals": total_signals,
            "active_signals": len(active_signals),
            "closed_signals": len(closed_signals),
            "winning_signals": len(winning_signals),
            "losing_signals": len(losing_signals),
            "breakeven_signals": len(breakeven_signals),
            "win_rate": win_rate,
            "average_return": self.calculate_average_return(window),
            "total_return": self.calculate_total_return(window),
            "profit_factor": self.calculate_profit_factor(window),
            "max_drawdown": self.calculate_max_drawdown(window),
            "sharpe_ratio": self.calculate_sharpe_ratio(window),
            "risk_adjusted_return": self.calculate_risk_adjusted_return(window),
            "signal_accuracy_by_type": {
                signal_type.value: self.calculate_signal_accuracy(signal_type, window)
                for signal_type in SignalType
            }
        }

    def get_performance_by_strength(self, window: TimeWindow = TimeWindow.ALL_TIME) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics grouped by signal strength."""
        closed_signals = self._get_closed_signals_in_window(window)
        strength_groups = {}

        for strength in SignalStrength:
            strength_signals = [s for s in closed_signals if s.strength == strength]
            winning_signals = [s for s in strength_signals if s.outcome == "win"]

            strength_groups[strength.value] = {
                "total_signals": len(strength_signals),
                "winning_signals": len(winning_signals),
                "win_rate": len(winning_signals) / len(strength_signals) if strength_signals else 0.0,
                "average_return": statistics.mean([s.return_percentage for s in strength_signals if s.return_percentage]) if strength_signals else 0.0
            }

        return strength_groups

    def create_performance_snapshot(self) -> PerformanceSnapshot:
        """Create a performance snapshot at current time."""
        closed_signals = [s for s in self.signal_performances if s.is_closed]
        active_signals = [s for s in self.signal_performances if not s.is_closed]

        winning_signals = [s for s in closed_signals if s.outcome == "win"]
        losing_signals = [s for s in closed_signals if s.outcome == "loss"]
        breakeven_signals = [s for s in closed_signals if s.outcome == "breakeven"]

        win_rate = len(winning_signals) / len(closed_signals) if closed_signals else 0.0

        return PerformanceSnapshot(
            timestamp=datetime.now().timestamp(),
            total_signals=len(self.signal_performances),
            active_signals=len(active_signals),
            closed_signals=len(closed_signals),
            winning_signals=len(winning_signals),
            losing_signals=len(losing_signals),
            breakeven_signals=len(breakeven_signals),
            win_rate=win_rate,
            average_return=self.calculate_average_return(),
            total_return=self.calculate_total_return(),
            max_drawdown=self.calculate_max_drawdown(),
            sharpe_ratio=self.calculate_sharpe_ratio(),
            profit_factor=self.calculate_profit_factor(),
            risk_adjusted_return=self.calculate_risk_adjusted_return()
        )

    def _get_closed_signals_in_window(self, window: TimeWindow) -> List[SignalPerformance]:
        """Get closed signals within the specified time window."""
        if window == TimeWindow.ALL_TIME:
            return [s for s in self.signal_performances if s.is_closed]

        cutoff_time = self._get_cutoff_time(window)
        return [s for s in self.signal_performances if s.is_closed and s.entry_time >= cutoff_time]

    def _get_cutoff_time(self, window: TimeWindow) -> float:
        """Get cutoff time for the specified window."""
        now = datetime.now()

        if window == TimeWindow.HOUR_1:
            return (now - timedelta(hours=1)).timestamp()
        elif window == TimeWindow.HOUR_24:
            return (now - timedelta(hours=24)).timestamp()
        elif window == TimeWindow.DAY_7:
            return (now - timedelta(days=7)).timestamp()
        elif window == TimeWindow.DAY_30:
            return (now - timedelta(days=30)).timestamp()
        elif window == TimeWindow.DAY_90:
            return (now - timedelta(days=90)).timestamp()
        elif window == TimeWindow.YEAR_1:
            return (now - timedelta(days=365)).timestamp()
        else:
            return 0.0

    def export_performance_data(self) -> Dict[str, Any]:
        """Export all performance data for external analysis."""
        return {
            "signal_performances": [s.to_dict() for s in self.signal_performances],
            "performance_history": [s.to_dict() for s in self.performance_history],
            "current_summary": self.get_performance_summary(),
            "performance_by_strength": self.get_performance_by_strength()
        }

    def reset(self):
        """Reset all performance data."""
        self.signal_performances.clear()
        self.performance_history.clear()


class PerformanceMetrics:
    """Comprehensive performance metrics tracking system."""

    def __init__(self):
        """Initialize performance metrics."""
        self.win_rate_calculator = WinRateCalculator()
        self.metrics_history: List[Dict[str, Any]] = []
        self.benchmark_data: Dict[str, float] = {}

    def track_signal(self, signal: Signal, entry_price: float, entry_time: float):
        """Track a new signal for performance analysis."""
        return self.win_rate_calculator.add_signal_performance(signal, entry_price, entry_time)

    def close_signal(self, signal_id: str, exit_price: float, exit_time: float, fees: float = 0.0):
        """Close a signal and update metrics."""
        return self.win_rate_calculator.close_signal(signal_id, exit_price, exit_time, fees)

    def get_current_metrics(self, window: TimeWindow = TimeWindow.ALL_TIME) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.win_rate_calculator.get_performance_summary(window)

    def get_signal_quality_metrics(self) -> Dict[str, Any]:
        """Get signal quality analysis metrics."""
        closed_signals = [s for s in self.win_rate_calculator.signal_performances if s.is_closed]

        if not closed_signals:
            return {}

        # Calculate correlation between signal strength and returns
        strengths = [s.strength.value for s in closed_signals]
        returns = [s.return_percentage for s in closed_signals if s.return_percentage is not None]

        if len(strengths) != len(returns):
            return {}

        correlation = np.corrcoef(strengths, returns)[0, 1] if len(strengths) > 1 else 0.0

        return {
            "strength_return_correlation": correlation,
            "average_strength": statistics.mean(strengths),
            "strength_distribution": {
                strength.value: len([s for s in closed_signals if s.strength.value == strength.value])
                for strength in SignalStrength
            },
            "confidence_accuracy_correlation": self._calculate_confidence_correlation(closed_signals)
        }

    def _calculate_confidence_correlation(self, signals: List[SignalPerformance]) -> float:
        """Calculate correlation between signal confidence and actual returns."""
        confidences = [s.metadata.get("signal_confidence", 0.5) for s in signals]
        returns = [s.return_percentage for s in signals if s.return_percentage is not None]

        if len(confidences) != len(returns) or len(confidences) < 2:
            return 0.0

        return np.corrcoef(confidences, returns)[0, 1]

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        return {
            "overall_performance": self.get_current_metrics(),
            "signal_quality": self.get_signal_quality_metrics(),
            "time_window_analysis": {
                window.value: self.get_current_metrics(window)
                for window in TimeWindow
            },
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        current_metrics = self.get_current_metrics()

        if current_metrics.get("win_rate", 0) < 0.5:
            recommendations.append("Consider improving signal quality or filtering criteria")

        if current_metrics.get("max_drawdown", 0) > 20:
            recommendations.append("Implement better risk management to reduce drawdowns")

        if current_metrics.get("sharpe_ratio", 0) < 1.0:
            recommendations.append("Focus on risk-adjusted returns rather than absolute returns")

        if current_metrics.get("profit_factor", 0) < 1.5:
            recommendations.append("Improve profit factor by better position sizing or entry timing")

        return recommendations