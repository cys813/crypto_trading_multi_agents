"""
Advanced deduplication engine with content fingerprinting and semantic analysis
"""

import hashlib
import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

from ..models.base import NewsArticle
from .models import (
    ContentFingerprint,
    DeduplicationResult,
    ProcessingConfig
)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.decomposition import TruncatedSVD
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, using basic text similarity")


@dataclass
class FingerprintCache:
    """指纹缓存"""
    fingerprints: Dict[str, ContentFingerprint] = field(default_factory=dict)
    article_groups: Dict[str, Set[str]] = field(default_factory=dict)
    last_cleanup: datetime = field(default_factory=datetime.now)
    cache_ttl_hours: int = 24


class DeduplicationEngine:
    """高级去重引擎 - 使用内容指纹和语义分析"""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 初始化缓存
        self.cache = FingerprintCache()

        # 初始化文本向量化器
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english' if self._is_english_content() else None,
                ngram_range=(1, 3),
                lowercase=True
            )
            self.svd = TruncatedSVD(n_components=100, random_state=42)
        else:
            self.vectorizer = None
            self.svd = None

        # 去重统计
        self.stats = {
            'total_processed': 0,
            'duplicates_found': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'avg_processing_time': 0.0
        }

    async def deduplicate(self, article: NewsArticle, existing_articles: List[NewsArticle] = None) -> DeduplicationResult:
        """去重单篇文章"""
        start_time = time.time()

        try:
            # 生成内容指纹
            fingerprint = await self._generate_fingerprint(article)

            # 检查缓存中的重复
            cached_duplicate = await self._check_cache_duplicate(fingerprint)
            if cached_duplicate:
                return cached_duplicate

            # 检查与现有文章的重复
            if existing_articles:
                duplicate_result = await self._check_duplicate_with_existing(article, fingerprint, existing_articles)
                if duplicate_result.is_duplicate:
                    # 更新缓存
                    await self._update_cache(fingerprint, duplicate_result.duplicate_group_id)
                    return duplicate_result

            # 无重复，创建新的指纹组
            group_id = await self._create_fingerprint_group(article, fingerprint)
            await self._update_cache(fingerprint, group_id)

            # 更新统计
            processing_time = time.time() - start_time
            self._update_stats(processing_time)

            return DeduplicationResult(
                is_duplicate=False,
                duplicate_group_id=group_id,
                similarity_score=0.0,
                matched_articles=[],
                fingerprint=fingerprint,
                confidence=1.0
            )

        except Exception as e:
            self.logger.error(f"去重处理失败: {str(e)}", exc_info=True)
            return DeduplicationResult(
                is_duplicate=False,
                duplicate_group_id=None,
                similarity_score=0.0,
                matched_articles=[],
                fingerprint=None,
                confidence=0.0
            )

    async def batch_deduplicate(self, articles: List[NewsArticle]) -> List[DeduplicationResult]:
        """批量去重文章"""
        self.logger.info(f"开始批量去重 {len(articles)} 篇文章")

        results = []
        processed_articles = []

        for article in articles:
            try:
                # 检查与已处理文章的重复
                result = await self.deduplicate(article, processed_articles)
                results.append(result)

                # 如果不是重复，添加到已处理列表
                if not result.is_duplicate:
                    processed_articles.append(article)

            except Exception as e:
                self.logger.error(f"批量去重失败: {str(e)}", exc_info=True)
                # 返回非重复结果
                results.append(DeduplicationResult(
                    is_duplicate=False,
                    duplicate_group_id=None,
                    similarity_score=0.0,
                    matched_articles=[],
                    fingerprint=None,
                    confidence=0.0
                ))

        # 清理过期缓存
        await self._cleanup_cache()

        self.logger.info(f"批量去重完成，发现 {sum(1 for r in results if r.is_duplicate)} 个重复")
        return results

    async def _generate_fingerprint(self, article: NewsArticle) -> ContentFingerprint:
        """生成内容指纹"""
        # 内容哈希
        content_hash = self._generate_content_hash(article.content)

        # 语义哈希
        semantic_hash = await self._generate_semantic_hash(article.content)

        # 源指纹
        source_fingerprint = self._generate_source_fingerprint(article)

        return ContentFingerprint(
            fingerprint_id=f"{content_hash[:16]}_{semantic_hash[:16]}",
            content_hash=content_hash,
            semantic_hash=semantic_hash,
            source_fingerprint=source_fingerprint,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=self.config.time_window_hours)
        )

    def _generate_content_hash(self, content: str) -> str:
        """生成内容哈希"""
        # 标准化内容
        normalized_content = content.lower().strip()
        normalized_content = ' '.join(normalized_content.split())  # 标准化空白

        # 使用SHA256生成哈希
        return hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()

    async def _generate_semantic_hash(self, content: str) -> str:
        """生成语义哈希"""
        if not SKLEARN_AVAILABLE or not self.vectorizer:
            # 回退到简单的内容哈希
            return self._generate_content_hash(content)

        try:
            # 使用TF-IDF向量化
            tfidf_matrix = self.vectorizer.fit_transform([content])

            # 使用SVD降维
            if tfidf_matrix.shape[1] > 100:
                reduced_matrix = self.svd.fit_transform(tfidf_matrix)
            else:
                reduced_matrix = tfidf_matrix.toarray()

            # 生成语义哈希
            semantic_vector = reduced_matrix.flatten()
            semantic_hash = hashlib.sha256(semantic_vector.tobytes()).hexdigest()

            return semantic_hash

        except Exception as e:
            self.logger.warning(f"语义哈希生成失败，使用内容哈希: {str(e)}")
            return self._generate_content_hash(content)

    def _generate_source_fingerprint(self, article: NewsArticle) -> str:
        """生成源指纹"""
        # 结合标题、作者和来源
        source_info = f"{article.title}|{article.author or ''}|{article.source or ''}"
        return hashlib.md5(source_info.encode('utf-8')).hexdigest()

    async def _check_cache_duplicate(self, fingerprint: ContentFingerprint) -> Optional[DeduplicationResult]:
        """检查缓存中的重复"""
        # 检查指纹是否存在于缓存中
        existing_fp = self.cache.fingerprints.get(fingerprint.fingerprint_id)
        if existing_fp:
            # 检查是否过期
            if existing_fp.expires_at and existing_fp.expires_at < datetime.now():
                return None

            # 找到重复
            group_id = existing_fp.fingerprint_id
            return DeduplicationResult(
                is_duplicate=True,
                duplicate_group_id=group_id,
                similarity_score=1.0,
                matched_articles=list(self.cache.article_groups.get(group_id, set())),
                fingerprint=fingerprint,
                confidence=0.95
            )

        return None

    async def _check_duplicate_with_existing(self, article: NewsArticle, fingerprint: ContentFingerprint,
                                           existing_articles: List[NewsArticle]) -> DeduplicationResult:
        """检查与现有文章的重复"""
        best_match = None
        best_score = 0.0

        for existing_article in existing_articles:
            # 跳过时间窗口外的文章
            if (existing_article.published_at and article.published_at and
                abs((existing_article.published_at - article.published_at).total_seconds()) >
                self.config.time_window_hours * 3600):
                continue

            # 计算相似度
            similarity = await self._calculate_similarity(article, existing_article)

            if similarity > best_score:
                best_score = similarity
                best_match = existing_article

        # 检查是否超过阈值
        if best_score >= self.config.similarity_threshold:
            return DeduplicationResult(
                is_duplicate=True,
                duplicate_group_id=best_match.id,
                similarity_score=best_score,
                matched_articles=[best_match.id],
                fingerprint=fingerprint,
                confidence=min(0.9, best_score + 0.1)
            )

        return DeduplicationResult(
            is_duplicate=False,
            duplicate_group_id=None,
            similarity_score=best_score,
            matched_articles=[],
            fingerprint=fingerprint,
            confidence=1.0 - best_score
        )

    async def _calculate_similarity(self, article1: NewsArticle, article2: NewsArticle) -> float:
        """计算两篇文章的相似度"""
        try:
            # 内容相似度
            content_similarity = self._calculate_content_similarity(article1.content, article2.content)

            # 标题相似度
            title_similarity = self._calculate_title_similarity(article1.title, article2.title)

            # 语义相似度
            semantic_similarity = await self._calculate_semantic_similarity(article1.content, article2.content)

            # 综合相似度
            weights = {'content': 0.5, 'title': 0.3, 'semantic': 0.2}
            combined_similarity = (
                weights['content'] * content_similarity +
                weights['title'] * title_similarity +
                weights['semantic'] * semantic_similarity
            )

            return combined_similarity

        except Exception as e:
            self.logger.error(f"相似度计算失败: {str(e)}", exc_info=True)
            return 0.0

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似度"""
        if not content1 or not content2:
            return 0.0

        # 使用词袋模型
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 or not words2:
            return 0.0

        # Jaccard相似度
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """计算标题相似度"""
        if not title1 or not title2:
            return 0.0

        # 标准化标题
        title1_norm = title1.lower().strip()
        title2_norm = title2.lower().strip()

        if title1_norm == title2_norm:
            return 1.0

        # 编辑距离相似度
        distance = self._levenshtein_distance(title1_norm, title2_norm)
        max_length = max(len(title1_norm), len(title2_norm))

        return 1.0 - (distance / max_length) if max_length > 0 else 0.0

    async def _calculate_semantic_similarity(self, content1: str, content2: str) -> float:
        """计算语义相似度"""
        if not SKLEARN_AVAILABLE or not self.vectorizer:
            # 回退到内容相似度
            return self._calculate_content_similarity(content1, content2)

        try:
            # 向量化内容
            tfidf_matrix = self.vectorizer.fit_transform([content1, content2])

            # 计算余弦相似度
            similarity_matrix = cosine_similarity(tfidf_matrix)
            return float(similarity_matrix[0, 1])

        except Exception as e:
            self.logger.warning(f"语义相似度计算失败: {str(e)}")
            return self._calculate_content_similarity(content1, content2)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    async def _create_fingerprint_group(self, article: NewsArticle, fingerprint: ContentFingerprint) -> str:
        """创建指纹组"""
        group_id = fingerprint.fingerprint_id

        # 添加到缓存
        self.cache.fingerprints[group_id] = fingerprint
        self.cache.article_groups[group_id] = {article.id}

        return group_id

    async def _update_cache(self, fingerprint: ContentFingerprint, group_id: str):
        """更新缓存"""
        self.cache.fingerprints[fingerprint.fingerprint_id] = fingerprint

        if group_id not in self.cache.article_groups:
            self.cache.article_groups[group_id] = set()
        self.cache.article_groups[group_id].add(fingerprint.fingerprint_id)

    async def _cleanup_cache(self):
        """清理过期缓存"""
        now = datetime.now()
        if (now - self.cache.last_cleanup).total_seconds() < 3600:  # 1小时内不重复清理
            return

        expired_fingerprints = []
        for fp_id, fingerprint in self.cache.fingerprints.items():
            if fingerprint.expires_at and fingerprint.expires_at < now:
                expired_fingerprints.append(fp_id)

        for fp_id in expired_fingerprints:
            del self.cache.fingerprints[fp_id]

        self.cache.last_cleanup = now
        self.logger.info(f"清理了 {len(expired_fingerprints)} 个过期指纹")

    def _update_stats(self, processing_time: float):
        """更新统计信息"""
        self.stats['total_processed'] += 1
        self.stats['avg_processing_time'] = (
            (self.stats['avg_processing_time'] * (self.stats['total_processed'] - 1) + processing_time) /
            self.stats['total_processed']
        )

    def _is_english_content(self) -> bool:
        """检查是否为英文内容"""
        # 简单的英文检测
        return True  # 默认为英文

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def clear_cache(self):
        """清空缓存"""
        self.cache.fingerprints.clear()
        self.cache.article_groups.clear()
        self.cache.last_cleanup = datetime.now()
        self.logger.info("缓存已清空")