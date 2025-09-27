"""
Configuration classes for Win Rate Calculation Algorithms.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class SimilarityMetric(Enum):
    """Similarity calculation methods."""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    MANHATTAN = "manhattan"
    WEIGHTED = "weighted"
    PATTERN = "pattern"


class ProbabilityMethod(Enum):
    """Probability calculation methods."""
    BAYESIAN = "bayesian"
    MONTE_CARLO = "monte_carlo"
    FREQUENCY = "frequency"
    ENSEMBLE = "ensemble"


@dataclass
class WinRateConfig:
    """Configuration for win rate calculation."""

    # Historical matching settings
    enable_historical_matching: bool = True
    max_historical_cases: int = 1000
    similarity_threshold: float = 0.7
    similarity_metric: SimilarityMetric = SimilarityMetric.WEIGHTED
    min_cases_for_analysis: int = 10

    # Feature extraction settings
    feature_extraction_enabled: bool = True
    technical_features_weight: float = 0.4
    market_features_weight: float = 0.3
    pattern_features_weight: float = 0.3
    normalize_features: bool = True

    # Probability calculation settings
    probability_method: ProbabilityMethod = ProbabilityMethod.ENSEMBLE
    bayesian_prior: float = 0.5
    monte_carlo_iterations: int = 10000
    confidence_interval: float = 0.95

    # Risk assessment settings
    enable_risk_assessment: bool = True
    max_risk_score: float = 0.8
    risk_weight_trend: float = 0.3
    risk_weight_volatility: float = 0.25
    risk_weight_liquidity: float = 0.25
    risk_weight_sentiment: float = 0.2

    # Dynamic adjustment settings
    enable_dynamic_adjustment: bool = True
    learning_rate: float = 0.01
    adaptation_window: int = 100  # Number of trades for adaptation
    performance_threshold: float = 0.65
    min_confidence_for_update: float = 0.8

    # Model validation settings
    enable_cross_validation: bool = True
    cv_folds: int = 5
    test_size_ratio: float = 0.2
    validation_frequency: int = 100  # Validate every N trades

    # Output settings
    detailed_output: bool = True
    include_confidence_intervals: bool = True
    max_recommendations: int = 5
    risk_reward_min_ratio: float = 2.0

    # Cache and performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    max_cache_size: int = 10000
    parallel_processing: bool = True
    max_concurrent_calculations: int = 50

    # Logging and monitoring
    enable_performance_logging: bool = True
    log_prediction_accuracy: bool = True
    save_model_state: bool = True
    model_save_frequency: int = 1000

    def __post_init__(self):
        """Validate configuration."""
        # Validate weights sum to 1.0
        feature_weights = [
            self.technical_features_weight,
            self.market_features_weight,
            self.pattern_features_weight
        ]
        total_weight = sum(feature_weights)
        if abs(total_weight - 1.0) > 0.01:
            # Normalize weights
            self.technical_features_weight /= total_weight
            self.market_features_weight /= total_weight
            self.pattern_features_weight /= total_weight

        # Validate risk weights
        risk_weights = [
            self.risk_weight_trend,
            self.risk_weight_volatility,
            self.risk_weight_liquidity,
            self.risk_weight_sentiment
        ]
        total_risk_weight = sum(risk_weights)
        if abs(total_risk_weight - 1.0) > 0.01:
            # Normalize risk weights
            self.risk_weight_trend /= total_risk_weight
            self.risk_weight_volatility /= total_risk_weight
            self.risk_weight_liquidity /= total_risk_weight
            self.risk_weight_sentiment /= total_risk_weight

        # Validate thresholds
        if not (0.0 <= self.similarity_threshold <= 1.0):
            raise ValueError("similarity_threshold must be between 0.0 and 1.0")

        if not (0.0 <= self.confidence_interval <= 1.0):
            raise ValueError("confidence_interval must be between 0.0 and 1.0")

        if self.monte_carlo_iterations < 100:
            raise ValueError("monte_carlo_iterations must be at least 100")

        if self.cv_folds < 2:
            raise ValueError("cv_folds must be at least 2")


@dataclass
class FeatureConfig:
    """Configuration for feature extraction."""

    # Technical features
    include_trend_features: bool = True
    include_momentum_features: bool = True
    include_volatility_features: bool = True
    include_volume_features: bool = True
    include_pattern_features: bool = True

    # Market features
    include_market_regime: bool = True
    include_liquidity_features: bool = True
    include_sentiment_features: bool = True
    include_correlation_features: bool = True

    # Pattern features
    include_candlestick_patterns: bool = True
    include_chart_patterns: bool = True
    include_support_resistance: bool = True
    include_fibonacci_levels: bool = True

    # Feature engineering
    enable_feature_interaction: bool = True
    enable_polynomial_features: bool = False
    max_polynomial_degree: int = 2
    feature_selection_threshold: float = 0.01

    # Normalization
    normalization_method: str = "standard"  # "standard", "minmax", "robust"
    handle_missing_values: str = "mean"  # "mean", "median", "drop"
    outlier_detection: bool = True
    outlier_method: str = "iqr"  # "iqr", "zscore", "isolation_forest"


@dataclass
class ModelConfig:
    """Configuration for probability models."""

    # Bayesian model
    bayesian_smoothing: float = 1.0  # Laplace smoothing
    enable_prior_learning: bool = True
    prior_update_frequency: int = 50

    # Monte Carlo model
    random_seed: Optional[int] = None
    enable_variance_reduction: bool = True
    variance_reduction_method: str = "antithetic"  # "antithetic", "control_variate"

    # Ensemble model
    ensemble_weights: Dict[str, float] = field(default_factory=lambda: {
        "bayesian": 0.4,
        "monte_carlo": 0.4,
        "frequency": 0.2
    })
    enable_dynamic_ensemble_weights: bool = True
    ensemble_adaptation_rate: float = 0.05

    # Model validation
    enable_backtesting: bool = True
    backtest_window: int = 1000
    forward_test_ratio: float = 0.3

    def __post_init__(self):
        """Validate model configuration."""
        # Validate ensemble weights
        total_weight = sum(self.ensemble_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            # Normalize weights
            for key in self.ensemble_weights:
                self.ensemble_weights[key] /= total_weight