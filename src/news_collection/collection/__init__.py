"""
Multi-source news collection strategies and optimization components

This module provides intelligent news collection capabilities including:
- Multiple collection strategies (incremental, full, priority-based)
- Intelligent scheduling with load balancing
- Time-based deduplication and rolling window management
- Cryptocurrency relevance filtering and scoring
- Priority-based collection optimization
- Performance optimization and adaptive tuning
"""

from .strategies import (
    CollectionStrategy,
    CollectionStrategyFactory,
    IncrementalCollectionStrategy,
    FullCollectionStrategy,
    PriorityBasedCollectionStrategy,
    CollectionResult,
    CollectionWindow
)

from .scheduler import (
    CollectionScheduler,
    ScheduleConfig,
    ScheduleType,
    CollectionJob
)

from .incremental_tracker import (
    IncrementalTracker,
    ArticleFingerprint,
    SourceTrackingInfo
)

from .relevance_filter import (
    RelevanceFilter,
    RelevanceLevel,
    RelevanceScore,
    CryptocurrencyInfo
)

from .priority_engine import (
    PriorityEngine,
    CollectionPriority,
    PriorityLevel,
    PriorityFactors
)

from .load_balancer import (
    LoadBalancer,
    LoadBalancingStrategy,
    LoadMetrics,
    SourceWeight
)

from .optimizer import (
    CollectionOptimizer,
    OptimizationTarget,
    PerformanceMetrics,
    OptimizationParameters,
    OptimizationResult
)

__all__ = [
    # Strategies
    'CollectionStrategy',
    'CollectionStrategyFactory',
    'IncrementalCollectionStrategy',
    'FullCollectionStrategy',
    'PriorityBasedCollectionStrategy',
    'CollectionResult',
    'CollectionWindow',

    # Scheduler
    'CollectionScheduler',
    'ScheduleConfig',
    'ScheduleType',
    'CollectionJob',

    # Incremental Tracker
    'IncrementalTracker',
    'ArticleFingerprint',
    'SourceTrackingInfo',

    # Relevance Filter
    'RelevanceFilter',
    'RelevanceLevel',
    'RelevanceScore',
    'CryptocurrencyInfo',

    # Priority Engine
    'PriorityEngine',
    'CollectionPriority',
    'PriorityLevel',
    'PriorityFactors',

    # Load Balancer
    'LoadBalancer',
    'LoadBalancingStrategy',
    'LoadMetrics',
    'SourceWeight',

    # Optimizer
    'CollectionOptimizer',
    'OptimizationTarget',
    'PerformanceMetrics',
    'OptimizationParameters',
    'OptimizationResult',
]