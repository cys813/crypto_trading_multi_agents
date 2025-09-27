"""
Pipeline manager for orchestrating the entire content processing pipeline
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from ..models.base import NewsArticle
from .models import (
    ProcessingResult,
    ProcessingStatus,
    ProcessingStage,
    ProcessingConfig,
    QualityMetrics
)
from .content_preprocessor import ContentPreprocessor, PreprocessingStats
from .deduplication_engine import DeduplicationEngine, DeduplicationResult
from .noise_filter import NoiseFilter, NoiseFilterStats
from .content_structurer import ContentStructurer, StructuredContent, StructuringStats
from .quality_scorer import QualityScorer, QualityScore
from ..llm import LLMConnector, LLMConfig, BatchProcessor, BatchConfig
from ..llm import NewsSummarizer, SummaryConfig
from ..llm import SentimentAnalyzer, SentimentConfig
from ..llm import EntityExtractor, EntityConfig
from ..llm import MarketImpactAssessor, MarketImpactConfig
from ..llm import CacheManager, CacheConfig


@dataclass
class PipelineStats:
    """管道统计信息"""
    total_articles: int = 0
    successful_articles: int = 0
    failed_articles: int = 0
    skipped_articles: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    stage_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    quality_distribution: Dict[str, int] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """管道处理结果"""
    articles: List[NewsArticle]
    processing_results: List[ProcessingResult]
    stats: PipelineStats
    execution_time: float
    errors: List[str]


class PipelineManager:
    """管道管理器 - 协调整个内容处理管道"""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 初始化处理组件
        self.preprocessor = ContentPreprocessor(config)
        self.deduplication_engine = DeduplicationEngine(config)
        self.noise_filter = NoiseFilter(config)
        self.content_structurer = ContentStructurer(config)
        self.quality_scorer = QualityScorer(config)

        # 初始化LLM分析组件
        if config.enable_llm_analysis:
            # LLM连接器
            llm_config = LLMConfig(provider="mock")  # 默认使用mock提供商
            self.llm_connector = LLMConnector(llm_config)

            # 缓存管理器
            cache_config = CacheConfig()
            self.cache_manager = CacheManager(cache_config)

            # 批处理器
            batch_config = BatchConfig()
            self.batch_processor = BatchProcessor(self.llm_connector, batch_config)

            # 分析组件
            self.summarizer = NewsSummarizer(self.llm_connector, SummaryConfig())
            self.sentiment_analyzer = SentimentAnalyzer(self.llm_connector, SentimentConfig())
            self.entity_extractor = EntityExtractor(self.llm_connector, EntityConfig())
            self.market_impact_assessor = MarketImpactAssessor(self.llm_connector, MarketImpactConfig())

            self.llm_components_initialized = False
        else:
            self.llm_connector = None
            self.cache_manager = None
            self.batch_processor = None
            self.summarizer = None
            self.sentiment_analyzer = None
            self.entity_extractor = None
            self.market_impact_assessor = None
            self.llm_components_initialized = False

        # 管道状态
        self.is_running = False
        self.processed_articles = []
        self.pipeline_stats = PipelineStats()

        # 性能配置
        self.max_workers = min(4, config.max_batch_size // 10)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    async def process_articles(self, articles: List[NewsArticle]) -> PipelineResult:
        """处理文章列表"""
        if not articles:
            return PipelineResult(
                articles=[],
                processing_results=[],
                stats=PipelineStats(),
                execution_time=0.0,
                errors=[]
            )

        start_time = time.time()
        self.logger.info(f"开始处理管道，输入 {len(articles)} 篇文章")

        try:
            self.is_running = True
            processed_articles = []
            processing_results = []
            errors = []

            # 检查是否启用并行处理
            if self.config.enable_parallel_processing and len(articles) > 1:
                # 并行处理
                tasks = []
                for article in articles:
                    task = self._process_single_article(article)
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        error_msg = f"文章 {articles[i].id} 处理失败: {str(result)}"
                        errors.append(error_msg)
                        self.logger.error(error_msg, exc_info=True)

                        # 创建失败结果
                        failed_result = ProcessingResult(
                            article=articles[i],
                            status=ProcessingStatus.FAILED,
                            processing_time=0.0,
                            stages_completed=[],
                            errors=[str(result)],
                            metadata={}
                        )
                        processing_results.append(failed_result)
                    else:
                        processed_article, processing_result = result
                        processed_articles.append(processed_article)
                        processing_results.append(processing_result)
            else:
                # 串行处理
                for article in articles:
                    try:
                        processed_article, processing_result = await self._process_single_article(article)
                        processed_articles.append(processed_article)
                        processing_results.append(processing_result)
                    except Exception as e:
                        error_msg = f"文章 {article.id} 处理失败: {str(e)}"
                        errors.append(error_msg)
                        self.logger.error(error_msg, exc_info=True)

                        # 创建失败结果
                        failed_result = ProcessingResult(
                            article=article,
                            status=ProcessingStatus.FAILED,
                            processing_time=0.0,
                            stages_completed=[],
                            errors=[str(e)],
                            metadata={}
                        )
                        processing_results.append(failed_result)

            # 计算执行时间
            execution_time = time.time() - start_time

            # 更新统计信息
            self._update_pipeline_stats(processing_results, execution_time)

            # 记录处理结果
            self.logger.info(f"管道处理完成: 成功 {len(processed_articles)}, "
                           f"失败 {len([r for r in processing_results if r.status == ProcessingStatus.FAILED])}, "
                           f"跳过 {len([r for r in processing_results if r.status == ProcessingStatus.SKIPPED])}, "
                           f"耗时 {execution_time:.2f}秒")

            return PipelineResult(
                articles=processed_articles,
                processing_results=processing_results,
                stats=self.pipeline_stats,
                execution_time=execution_time,
                errors=errors
            )

        except Exception as e:
            self.logger.error(f"管道处理失败: {str(e)}", exc_info=True)
            execution_time = time.time() - start_time

            return PipelineResult(
                articles=[],
                processing_results=[],
                stats=self.pipeline_stats,
                execution_time=execution_time,
                errors=[str(e)]
            )

        finally:
            self.is_running = False

    async def _process_single_article(self, article: NewsArticle) -> Tuple[NewsArticle, ProcessingResult]:
        """处理单篇文章"""
        start_time = time.time()
        stages_completed = []
        errors = []
        metadata = {}
        current_article = article
        quality_score = None
        is_duplicate = False

        try:
            # 阶段1: 预处理
            if self.config.enable_preprocessing:
                try:
                    current_article, preprocessing_stats = await self.preprocessor.preprocess(current_article)
                    stages_completed.append(ProcessingStage.PREPROCESSING)
                    metadata['preprocessing_stats'] = {
                        'original_length': preprocessing_stats.original_length,
                        'processed_length': preprocessing_stats.processed_length,
                        'processing_time': preprocessing_stats.processing_time
                    }
                    self.logger.debug(f"文章 {article.id} 预处理完成")
                except Exception as e:
                    error_msg = f"预处理失败: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg, exc_info=True)

            # 阶段2: 去重
            if self.config.enable_deduplication and len(errors) == 0:
                try:
                    # 获取已处理的文章用于去重比较
                    existing_articles = [r.article for r in self.processed_articles if r.status == ProcessingStatus.COMPLETED]

                    deduplication_result = await self.deduplication_engine.deduplicate(current_article, existing_articles)
                    stages_completed.append(ProcessingStage.DEDUPLICATION)

                    if deduplication_result.is_duplicate:
                        is_duplicate = True
                        metadata['deduplication_result'] = {
                            'is_duplicate': True,
                            'similarity_score': deduplication_result.similarity_score,
                            'duplicate_group_id': deduplication_result.duplicate_group_id,
                            'confidence': deduplication_result.confidence
                        }
                        self.logger.info(f"文章 {article.id} 检测为重复，相似度: {deduplication_result.similarity_score:.2f}")
                    else:
                        metadata['deduplication_result'] = {
                            'is_duplicate': False,
                            'similarity_score': deduplication_result.similarity_score,
                            'confidence': deduplication_result.confidence
                        }

                except Exception as e:
                    error_msg = f"去重失败: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg, exc_info=True)

            # 阶段3: 噪声过滤
            if self.config.enable_noise_filtering and len(errors) == 0 and not is_duplicate:
                try:
                    current_article, noise_stats = await self.noise_filter.filter_noise(current_article)
                    stages_completed.append(ProcessingStage.NOISE_FILTERING)
                    metadata['noise_filtering_stats'] = {
                        'original_length': noise_stats.original_length,
                        'filtered_length': noise_stats.filtered_length,
                        'removed_ads': noise_stats.removed_ads,
                        'removed_boilerplate': noise_stats.removed_boilerplate,
                        'removed_spam': noise_stats.removed_spam,
                        'processing_time': noise_stats.processing_time
                    }
                    self.logger.debug(f"文章 {article.id} 噪声过滤完成")
                except Exception as e:
                    error_msg = f"噪声过滤失败: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg, exc_info=True)

            # 阶段4: 内容结构化
            if self.config.enable_structuring and len(errors) == 0 and not is_duplicate:
                try:
                    structured_content, structuring_stats = await self.content_structurer.structure_content(current_article)
                    stages_completed.append(ProcessingStage.STRUCTURING)
                    metadata['structuring_stats'] = {
                        'sections_extracted': structuring_stats.sections_extracted,
                        'key_points_extracted': structuring_stats.key_points_extracted,
                        'entities_extracted': structuring_stats.entities_extracted,
                        'sentiment_analyzed': structuring_stats.sentiment_analyzed,
                        'processing_time': structuring_stats.processing_time
                    }

                    # 更新文章元数据
                    current_article = self.content_structurer.structure_to_article(structured_content, current_article)
                    self.logger.debug(f"文章 {article.id} 结构化完成")
                except Exception as e:
                    error_msg = f"结构化失败: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg, exc_info=True)

            # 阶段5: 质量评分
            quality_score = None
            if self.config.enable_quality_scoring and len(errors) == 0 and not is_duplicate:
                try:
                    quality_score = await self.quality_scorer.score_quality(current_article)
                    stages_completed.append(ProcessingStage.QUALITY_SCORING)
                    metadata['quality_score'] = {
                        'overall_score': quality_score.overall_score,
                        'grade': quality_score.grade,
                        'confidence': quality_score.confidence,
                        'recommendation': quality_score.recommendation
                    }

                    # 检查质量阈值
                    if quality_score.overall_score < self.config.quality_threshold:
                        error_msg = f"质量分数过低: {quality_score.overall_score:.2f} < {self.config.quality_threshold}"
                        errors.append(error_msg)
                        self.logger.warning(error_msg)

                    self.logger.debug(f"文章 {article.id} 质量评分完成: {quality_score.grade} ({quality_score.overall_score:.2f})")
                except Exception as e:
                    error_msg = f"质量评分失败: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg, exc_info=True)

            # 阶段6: LLM智能分析
            llm_analysis_results = {}
            if (self.config.enable_llm_analysis and len(errors) == 0 and not is_duplicate and
                quality_score and quality_score.overall_score >= self.config.llm_min_quality_threshold):

                # 确保LLM组件已初始化
                if not self.llm_components_initialized and self.batch_processor:
                    try:
                        await self.batch_processor.start()
                        self.llm_components_initialized = True
                    except Exception as e:
                        self.logger.error(f"Failed to initialize LLM components: {str(e)}")

                if self.llm_components_initialized:
                    try:
                        llm_start_time = time.time()

                        # 检查缓存
                        cache_key = f"llm_analysis_{article.id}"
                        cached_result = None
                        if self.cache_manager and self.config.llm_enable_caching:
                            cached_result = self.cache_manager.get(cache_key)

                        if cached_result:
                            llm_analysis_results = cached_result
                            self.logger.debug(f"文章 {article.id} LLM分析结果来自缓存")
                        else:
                            # 根据配置执行不同的分析类型
                            for analysis_type in self.config.llm_analysis_types:
                                try:
                                    if analysis_type == 'summarization' and self.summarizer:
                                        result = await self.summarizer.summarize_article(current_article)
                                        llm_analysis_results['summarization'] = result.__dict__

                                    elif analysis_type == 'sentiment' and self.sentiment_analyzer:
                                        result = await self.sentiment_analyzer.analyze_sentiment(current_article)
                                        llm_analysis_results['sentiment'] = result.__dict__

                                    elif analysis_type == 'entities' and self.entity_extractor:
                                        result = await self.entity_extractor.extract_entities(current_article)
                                        llm_analysis_results['entities'] = result.__dict__

                                    elif analysis_type == 'market_impact' and self.market_impact_assessor:
                                        result = await self.market_impact_assessor.assess_market_impact(current_article)
                                        llm_analysis_results['market_impact'] = result.__dict__

                                    self.logger.debug(f"文章 {article.id} {analysis_type} 分析完成")

                                except Exception as analysis_error:
                                    error_msg = f"{analysis_type} 分析失败: {str(analysis_error)}"
                                    errors.append(error_msg)
                                    self.logger.warning(error_msg)

                            # 缓存结果
                            if self.cache_manager and self.config.llm_enable_caching and llm_analysis_results:
                                self.cache_manager.set(cache_key, llm_analysis_results, ttl=3600)

                        stages_completed.append(ProcessingStage.LLM_ANALYSIS)
                        metadata['llm_analysis'] = {
                            'analysis_types': self.config.llm_analysis_types,
                            'processing_time': time.time() - llm_start_time,
                            'results_count': len(llm_analysis_results),
                            'from_cache': cached_result is not None
                        }

                        # 验证LLM分析质量
                        llm_confidence = self._validate_llm_analysis_quality(llm_analysis_results)
                        if llm_confidence < self.config.llm_confidence_threshold:
                            error_msg = f"LLM分析置信度过低: {llm_confidence:.2f} < {self.config.llm_confidence_threshold}"
                            errors.append(error_msg)
                            self.logger.warning(error_msg)

                        self.logger.debug(f"文章 {article.id} LLM分析完成，耗时 {time.time() - llm_start_time:.2f}秒")

                    except Exception as e:
                        error_msg = f"LLM分析失败: {str(e)}"
                        errors.append(error_msg)
                        self.logger.error(error_msg, exc_info=True)

            # 确定处理状态
            processing_time = time.time() - start_time

            if errors:
                status = ProcessingStatus.FAILED
            elif is_duplicate:
                status = ProcessingStatus.SKIPPED
            else:
                status = ProcessingStatus.COMPLETED

            # 创建处理结果
            processing_result = ProcessingResult(
                article=current_article,
                status=status,
                processing_time=processing_time,
                stages_completed=stages_completed,
                errors=errors,
                metadata=metadata,
                quality_score=quality_score.overall_score if quality_score else None,
                is_duplicate=is_duplicate
            )

            # 如果成功处理，添加到已处理列表
            if status == ProcessingStatus.COMPLETED:
                self.processed_articles.append(processing_result)

            return current_article, processing_result

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"文章 {article.id} 处理失败: {str(e)}", exc_info=True)

            # 创建失败结果
            processing_result = ProcessingResult(
                article=article,
                status=ProcessingStatus.FAILED,
                processing_time=processing_time,
                stages_completed=stages_completed,
                errors=[str(e)],
                metadata=metadata,
                quality_score=quality_score.overall_score if quality_score else None,
                is_duplicate=is_duplicate
            )

            return article, processing_result

    def _update_pipeline_stats(self, results: List[ProcessingResult], execution_time: float):
        """更新管道统计信息"""
        self.pipeline_stats.total_articles = len(results)
        self.pipeline_stats.successful_articles = len([r for r in results if r.status == ProcessingStatus.COMPLETED])
        self.pipeline_stats.failed_articles = len([r for r in results if r.status == ProcessingStatus.FAILED])
        self.pipeline_stats.skipped_articles = len([r for r in results if r.status == ProcessingStatus.SKIPPED])
        self.pipeline_stats.total_processing_time = execution_time
        self.pipeline_stats.average_processing_time = execution_time / len(results) if results else 0.0

        # 更新阶段统计
        stage_stats = {}
        for result in results:
            for stage in result.stages_completed:
                stage_name = stage.value
                if stage_name not in stage_stats:
                    stage_stats[stage_name] = {'count': 0, 'total_time': 0.0}
                stage_stats[stage_name]['count'] += 1
                stage_stats[stage_name]['total_time'] += result.processing_time

        self.pipeline_stats.stage_stats = stage_stats

        # 更新质量分布
        quality_distribution = {}
        for result in results:
            if result.quality_score is not None:
                grade = self._score_to_grade(result.quality_score)
                quality_distribution[grade] = quality_distribution.get(grade, 0) + 1

        self.pipeline_stats.quality_distribution = quality_distribution

    def _score_to_grade(self, score: float) -> str:
        """将分数转换为等级"""
        if score >= 0.95:
            return 'A+'
        elif score >= 0.85:
            return 'A'
        elif score >= 0.70:
            return 'B'
        elif score >= 0.55:
            return 'C'
        elif score >= 0.40:
            return 'D'
        else:
            return 'F'

    def _validate_llm_analysis_quality(self, llm_results: Dict[str, Any]) -> float:
        """验证LLM分析质量"""
        if not llm_results:
            return 0.0

        confidence_scores = []

        # 检查摘要质量
        if 'summarization' in llm_results:
            summary_data = llm_results['summarization']
            if 'confidence' in summary_data:
                confidence_scores.append(summary_data['confidence'])

            # 检查单词计数比率
            if 'word_count' in summary_data:
                original_words = summary_data['word_count'].get('original', 0)
                summary_words = summary_data['word_count'].get('summary', 0)
                if original_words > 0:
                    ratio = summary_words / original_words
                    # 理想比率是0.2-0.4
                    if 0.2 <= ratio <= 0.4:
                        confidence_scores.append(0.8)
                    elif 0.1 <= ratio <= 0.5:
                        confidence_scores.append(0.6)
                    else:
                        confidence_scores.append(0.3)

        # 检查情感分析质量
        if 'sentiment' in llm_results:
            sentiment_data = llm_results['sentiment']
            if 'overall_sentiment' in sentiment_data:
                overall_sentiment = sentiment_data['overall_sentiment']
                if 'confidence' in overall_sentiment:
                    confidence_scores.append(overall_sentiment['confidence'])

        # 检查实体提取质量
        if 'entities' in llm_results:
            entities_data = llm_results['entities']
            if 'entities' in entities_data:
                entities = entities_data['entities']
                # 检查实体数量和质量
                entity_count = len(entities)
                if 5 <= entity_count <= 20:
                    confidence_scores.append(0.7)
                elif entity_count > 0:
                    confidence_scores.append(0.5)

        # 检查市场影响分析质量
        if 'market_impact' in llm_results:
            market_data = llm_results['market_impact']
            if 'overall_impact' in market_data:
                overall_impact = market_data['overall_impact']
                if 'confidence' in overall_impact:
                    confidence_scores.append(overall_impact['confidence'])

        # 计算平均置信度
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            return 0.5  # 默认中等置信度

    def get_pipeline_status(self) -> Dict[str, Any]:
        """获取管道状态"""
        return {
            'is_running': self.is_running,
            'total_processed': len(self.processed_articles),
            'stats': self.pipeline_stats.__dict__,
            'config': self.config.__dict__
        }

    def get_component_stats(self) -> Dict[str, Any]:
        """获取组件统计信息"""
        return {
            'preprocessor': {},
            'deduplication_engine': self.deduplication_engine.get_stats(),
            'noise_filter': {},
            'content_structurer': {},
            'quality_scorer': {}
        }

    def clear_processed_articles(self):
        """清空已处理文章缓存"""
        self.processed_articles.clear()
        self.deduplication_engine.clear_cache()
        self.logger.info("已清空处理缓存")

    def update_config(self, config: ProcessingConfig):
        """更新配置"""
        self.config = config
        self.logger.info("管道配置已更新")

    async def shutdown(self):
        """关闭管道"""
        self.is_running = False
        self.executor.shutdown(wait=True)

        # 关闭LLM组件
        if self.llm_components_initialized:
            if self.batch_processor:
                await self.batch_processor.stop()
            if self.cache_manager:
                self.cache_manager.shutdown()

        self.logger.info("管道已关闭")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            'throughput': len(self.processed_articles) / max(1, self.pipeline_stats.total_processing_time),
            'success_rate': self.pipeline_stats.successful_articles / max(1, self.pipeline_stats.total_articles),
            'average_processing_time': self.pipeline_stats.average_processing_time,
            'stage_efficiency': self.pipeline_stats.stage_stats,
            'quality_distribution': self.pipeline_stats.quality_distribution
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            'status': 'healthy' if not self.is_running else 'processing',
            'components': {
                'preprocessor': 'healthy',
                'deduplication_engine': 'healthy',
                'noise_filter': 'healthy',
                'content_structurer': 'healthy',
                'quality_scorer': 'healthy'
            },
            'performance': self.get_performance_metrics(),
            'last_updated': datetime.now().isoformat()
        }