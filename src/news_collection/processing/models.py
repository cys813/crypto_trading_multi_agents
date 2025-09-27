"""
Processing pipeline data models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from enum import Enum

from ..models.base import NewsArticle


class ProcessingStage(Enum):
    """处理阶段枚举"""
    PREPROCESSING = "preprocessing"
    DEDUPLICATION = "deduplication"
    NOISE_FILTERING = "noise_filtering"
    STRUCTURING = "structuring"
    QUALITY_SCORING = "quality_scoring"
    LLM_ANALYSIS = "llm_analysis"


class ProcessingStatus(Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ContentFingerprint:
    """内容指纹"""
    fingerprint_id: str
    content_hash: str
    semantic_hash: str
    source_fingerprint: str
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class ProcessingResult:
    """处理结果"""
    article: NewsArticle
    status: ProcessingStatus
    processing_time: float
    stages_completed: List[ProcessingStage]
    errors: List[str]
    metadata: Dict[str, Any]
    quality_score: Optional[float] = None
    is_duplicate: bool = False
    duplicate_group_id: Optional[str] = None

    def __post_init__(self):
        if self.stages_completed is None:
            self.stages_completed = []
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DeduplicationResult:
    """去重结果"""
    is_duplicate: bool
    duplicate_group_id: Optional[str]
    similarity_score: float
    matched_articles: List[str]
    fingerprint: ContentFingerprint
    confidence: float


@dataclass
class QualityMetrics:
    """质量指标"""
    content_length_score: float
    readability_score: float
    source_credibility_score: float
    timeliness_score: float
    completeness_score: float
    overall_score: float
    factors: Dict[str, Any]


@dataclass
class ProcessingConfig:
    """处理配置"""
    enable_preprocessing: bool = True
    enable_deduplication: bool = True
    enable_noise_filtering: bool = True
    enable_structuring: bool = True
    enable_quality_scoring: bool = True
    enable_llm_analysis: bool = True

    # 预处理配置
    min_content_length: int = 100
    max_content_length: int = 10000
    normalize_whitespace: bool = True
    remove_html_tags: bool = True
    remove_urls: bool = True

    # 去重配置
    similarity_threshold: float = 0.85
    semantic_threshold: float = 0.75
    cross_source_detection: bool = True
    time_window_hours: int = 24

    # 噪声过滤配置
    remove_ads: bool = True
    remove_boilerplate: bool = True
    min_word_count: int = 50
    max_repetition_ratio: float = 0.3

    # 质量评分配置
    quality_threshold: float = 0.6
    readability_weights: Dict[str, float] = None
    credibility_weights: Dict[str, float] = None

    # LLM分析配置
    llm_analysis_types: List[str] = None
    llm_min_quality_threshold: float = 0.5
    llm_max_processing_time: float = 60.0
    llm_enable_caching: bool = True
    llm_confidence_threshold: float = 0.4

    # 性能配置
    max_batch_size: int = 100
    processing_timeout: float = 30.0
    enable_parallel_processing: bool = True

    def __post_init__(self):
        if self.readability_weights is None:
            self.readability_weights = {
                'content_length': 0.3,
                'sentence_structure': 0.2,
                'vocabulary': 0.2,
                'coherence': 0.3
            }
        if self.credibility_weights is None:
            self.credibility_weights = {
                'source_reputation': 0.4,
                'author_credibility': 0.3,
                'fact_checking': 0.3
            }
        if self.llm_analysis_types is None:
            self.llm_analysis_types = ['summarization', 'sentiment', 'entities']