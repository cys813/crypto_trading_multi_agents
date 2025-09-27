"""
LLM integration modules for news collection and analysis
"""

from .llm_connector import (
    LLMConnector,
    LLMConfig,
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMError,
    CacheManager
)

from .summarizer import (
    NewsSummarizer,
    SummaryConfig,
    SummaryResult,
    SummaryStats,
    SummaryLength,
    SummaryFocus
)

from .sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentConfig,
    SentimentAnalysisResult,
    SentimentStats,
    SentimentCategory,
    SentimentAspect,
    SentimentScore
)

from .content_segmenter import (
    ContentSegmenter,
    SectionConfig,
    SegmentationResult,
    SegmentationStats,
    ContentSection,
    SectionType
)

from .entity_extractor import (
    EntityExtractor,
    EntityConfig,
    EntityExtractionResult,
    EntityExtractionStats,
    Entity,
    EntityRelationship,
    EntityType
)

from .market_impact import (
    MarketImpactAssessor,
    MarketImpactConfig,
    MarketImpactResult,
    MarketImpactStats,
    ImpactScore,
    ImpactType,
    ImpactTimeframe,
    ImpactMagnitude
)

from .batch_processor import (
    BatchProcessor,
    BatchConfig,
    BatchResult,
    BatchStats,
    BatchTask,
    BatchPriority,
    BatchStrategy
)

from .cache_manager import (
    CacheManager,
    CacheConfig,
    CacheStats,
    CacheEntry,
    CacheLevel,
    CacheStrategy
)

__all__ = [
    # LLM Connector
    'LLMConnector',
    'LLMConfig',
    'LLMProvider',
    'LLMMessage',
    'LLMResponse',
    'LLMError',
    'CacheManager',

    # Summarization
    'NewsSummarizer',
    'SummaryConfig',
    'SummaryResult',
    'SummaryStats',
    'SummaryLength',
    'SummaryFocus',

    # Sentiment Analysis
    'SentimentAnalyzer',
    'SentimentConfig',
    'SentimentAnalysisResult',
    'SentimentStats',
    'SentimentCategory',
    'SentimentAspect',
    'SentimentScore',

    # Content Segmentation
    'ContentSegmenter',
    'SectionConfig',
    'SegmentationResult',
    'SegmentationStats',
    'ContentSection',
    'SectionType',

    # Entity Extraction
    'EntityExtractor',
    'EntityConfig',
    'EntityExtractionResult',
    'EntityExtractionStats',
    'Entity',
    'EntityRelationship',
    'EntityType',

    # Market Impact
    'MarketImpactAssessor',
    'MarketImpactConfig',
    'MarketImpactResult',
    'MarketImpactStats',
    'ImpactScore',
    'ImpactType',
    'ImpactTimeframe',
    'ImpactMagnitude',

    # Batch Processing
    'BatchProcessor',
    'BatchConfig',
    'BatchResult',
    'BatchStats',
    'BatchTask',
    'BatchPriority',
    'BatchStrategy',

    # Cache Management
    'CacheManager',
    'CacheConfig',
    'CacheStats',
    'CacheEntry',
    'CacheLevel',
    'CacheStrategy'
]