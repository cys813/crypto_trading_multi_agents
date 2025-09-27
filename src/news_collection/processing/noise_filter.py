"""
Noise filtering system for removing irrelevant and low-quality content
"""

import re
import logging
from typing import List, Dict, Any, Set, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
from collections import Counter

from ..models.base import NewsArticle
from .models import ProcessingConfig


@dataclass
class NoiseFilterStats:
    """噪声过滤统计信息"""
    original_length: int
    filtered_length: int
    removed_ads: int
    removed_boilerplate: int
    removed_spam: int
    removed_irrelevant: int
    processing_time: float


class NoiseFilter:
    """噪声过滤器 - 移除不相关和低质量内容"""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 广告模式
        self.ad_patterns = [
            re.compile(r'点击购买', re.IGNORECASE),
            re.compile(r'限时优惠', re.IGNORECASE),
            re.compile(r'立即购买', re.IGNORECASE),
            re.compile(r'打折', re.IGNORECASE),
            re.compile(r'促销', re.IGNORECASE),
            re.compile(r'优惠券', re.IGNORECASE),
            re.compile(r'免费领取', re.IGNORECASE),
            re.compile(r'特价', re.IGNORECASE),
            re.compile(r'广告', re.IGNORECASE),
            re.compile(r'sponsored', re.IGNORECASE),
            re.compile(r'advertisement', re.IGNORECASE),
        ]

        # 垃圾内容模式
        self.spam_patterns = [
            re.compile(r'点击这里', re.IGNORECASE),
            re.compile(r'点击查看', re.IGNORECASE),
            re.compile(r'点击阅读', re.IGNORECASE),
            re.compile(r'关注我们', re.IGNORECASE),
            re.compile(r'订阅新闻', re.IGNORECASE),
            re.compile(r'关注公众号', re.IGNORECASE),
            re.compile(r'添加微信', re.IGNORECASE),
            re.compile(r'联系我们', re.IGNORECASE),
            re.compile(r'商业合作', re.IGNORECASE),
        ]

        # 样板文本模式
        self.boilerplate_patterns = [
            re.compile(r'免责声明：.*?(?=\n\n|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'风险提示：.*?(?=\n\n|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'本文不代表.*?观点。', re.IGNORECASE),
            re.compile(r'投资有风险，入市需谨慎。', re.IGNORECASE),
            re.compile(r'以上内容仅供参考。', re.IGNORECASE),
            re.compile(r'文章来源：.*?(?=\n\n|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'作者声明：.*?(?=\n\n|$)', re.IGNORECASE | re.DOTALL),
        ]

        # 重复内容模式
        self.repetition_patterns = [
            re.compile(r'(.{20,}?)\1{2,}', re.DOTALL),  # 重复20个字符以上2次以上
            re.compile(r'(.)\1{5,}'),  # 重复单个字符5次以上
        ]

        # 不相关关键词
        self.irrelevant_keywords = {
            '彩票', '赌博', '色情', '成人', '美女', '帅哥', '交友',
            '贷款', '信用卡', '理财', '保险', '投资', '股票', '基金',
            '教育', '培训', '考试', '学习', '留学', '移民', '签证',
            '医疗', '健康', '养生', '减肥', '美容', '健身', '瑜伽',
        }

        # 低质量指示词
        self.low_quality_indicators = {
            '震惊', '惊人', '吓人', '恐怖', '可怕', '不敢相信',
            '揭秘', '内幕', '黑幕', '真相', '你不知道', '终于知道',
            '紧急通知', '重要提醒', '速看', '马上删除', '内部消息',
        }

    async def filter_noise(self, article: NewsArticle) -> Tuple[NewsArticle, NoiseFilterStats]:
        """过滤噪声内容"""
        start_time = datetime.now()
        original_content = article.content

        try:
            # 初始化统计
            stats = NoiseFilterStats(
                original_length=len(original_content),
                filtered_length=0,
                removed_ads=0,
                removed_boilerplate=0,
                removed_spam=0,
                removed_irrelevant=0,
                processing_time=0.0
            )

            # 检查内容质量
            quality_check = await self._check_content_quality(article.content)
            if not quality_check['is_quality']:
                self.logger.warning(f"内容质量过低: {quality_check['reason']}")
                return article, stats

            # 过滤噪声
            filtered_content = original_content

            # 移除广告
            if self.config.remove_ads:
                filtered_content, ads_removed = self._remove_ads(filtered_content)
                stats.removed_ads = ads_removed

            # 移除样板文本
            if self.config.remove_boilerplate:
                filtered_content, boilerplate_removed = self._remove_boilerplate(filtered_content)
                stats.removed_boilerplate = boilerplate_removed

            # 移除垃圾内容
            filtered_content, spam_removed = self._remove_spam(filtered_content)
            stats.removed_spam = spam_removed

            # 移除重复内容
            filtered_content, repetition_removed = self._remove_repetition(filtered_content)
            stats.removed_spam += repetition_removed

            # 检查不相关内容
            relevance_check = await self._check_content_relevance(filtered_content, article.category)
            if not relevance_check['is_relevant']:
                self.logger.warning(f"内容不相关: {relevance_check['reason']}")
                stats.removed_irrelevant = 1
                return article, stats

            # 标准化内容
            filtered_content = self._normalize_content(filtered_content)

            # 检查处理后内容长度
            if len(filtered_content) < self.config.min_content_length:
                self.logger.warning(f"过滤后内容过短: {len(filtered_content)} 字符")
                return article, stats

            # 创建过滤后的文章
            filtered_article = NewsArticle(
                id=article.id,
                title=article.title,
                content=filtered_content,
                summary=article.summary,
                author=article.author,
                published_at=article.published_at,
                source=article.source,
                url=article.url,
                category=article.category,
                tags=article.tags.copy() if article.tags else [],
                metadata={
                    **(article.metadata or {}),
                    'noise_filtered': True,
                    'noise_filtering_time': datetime.now().isoformat(),
                    'original_length': len(original_content),
                    'filtered_length': len(filtered_content),
                    'noise_removal_stats': {
                        'ads_removed': stats.removed_ads,
                        'boilerplate_removed': stats.removed_boilerplate,
                        'spam_removed': stats.removed_spam,
                        'irrelevant_removed': stats.removed_irrelevant
                    }
                }
            )

            # 更新统计
            stats.filtered_length = len(filtered_content)
            stats.processing_time = (datetime.now() - start_time).total_seconds()

            self.logger.info(f"噪声过滤完成: {len(original_content)} -> {len(filtered_content)} 字符")

            return filtered_article, stats

        except Exception as e:
            self.logger.error(f"噪声过滤失败: {str(e)}", exc_info=True)
            stats.processing_time = (datetime.now() - start_time).total_seconds()
            return article, stats

    async def batch_filter_noise(self, articles: List[NewsArticle]) -> List[Tuple[NewsArticle, NoiseFilterStats]]:
        """批量过滤噪声"""
        self.logger.info(f"开始批量噪声过滤 {len(articles)} 篇文章")

        results = []
        for article in articles:
            try:
                filtered_article, stats = await self.filter_noise(article)
                results.append((filtered_article, stats))
            except Exception as e:
                self.logger.error(f"批量噪声过滤失败: {str(e)}", exc_info=True)
                # 返回原始文章和空统计
                stats = NoiseFilterStats(
                    original_length=len(article.content),
                    filtered_length=len(article.content),
                    removed_ads=0,
                    removed_boilerplate=0,
                    removed_spam=0,
                    removed_irrelevant=0,
                    processing_time=0.0
                )
                results.append((article, stats))

        self.logger.info(f"批量噪声过滤完成，处理了 {len(results)} 篇文章")
        return results

    async def _check_content_quality(self, content: str) -> Dict[str, Any]:
        """检查内容质量"""
        if not content or len(content.strip()) < self.config.min_content_length:
            return {'is_quality': False, 'reason': '内容过短'}

        # 检查词数
        words = content.split()
        if len(words) < self.config.min_word_count:
            return {'is_quality': False, 'reason': '词数过少'}

        # 检查重复率
        unique_chars = len(set(content))
        total_chars = len(content)
        if total_chars > 0 and unique_chars / total_chars < 0.3:
            return {'is_quality': False, 'reason': '重复率过高'}

        # 检查低质量指示词
        low_quality_count = sum(1 for indicator in self.low_quality_indicators if indicator in content)
        if low_quality_count > 2:  # 超过2个低质量指示词
            return {'is_quality': False, 'reason': '包含过多低质量指示词'}

        return {'is_quality': True, 'reason': ''}

    async def _check_content_relevance(self, content: str, category) -> Dict[str, Any]:
        """检查内容相关性"""
        # 检查不相关关键词
        irrelevant_count = sum(1 for keyword in self.irrelevant_keywords if keyword in content)
        if irrelevant_count > 3:  # 超过3个不相关关键词
            return {'is_relevant': False, 'reason': '包含过多不相关关键词'}

        # 检查是否主要是广告
        ad_count = sum(1 for pattern in self.ad_patterns if pattern.search(content))
        if ad_count > 5:  # 超过5个广告模式
            return {'is_relevant': False, 'reason': '广告内容过多'}

        # 检查是否主要是垃圾内容
        spam_count = sum(1 for pattern in self.spam_patterns if pattern.search(content))
        if spam_count > 3:  # 超过3个垃圾模式
            return {'is_relevant': False, 'reason': '垃圾内容过多'}

        return {'is_relevant': True, 'reason': ''}

    def _remove_ads(self, content: str) -> Tuple[str, int]:
        """移除广告内容"""
        removed_count = 0
        filtered_content = content

        for pattern in self.ad_patterns:
            matches = pattern.findall(filtered_content)
            if matches:
                filtered_content = pattern.sub('', filtered_content)
                removed_count += len(matches)

        return filtered_content, removed_count

    def _remove_boilerplate(self, content: str) -> Tuple[str, int]:
        """移除样板文本"""
        removed_count = 0
        filtered_content = content

        for pattern in self.boilerplate_patterns:
            matches = pattern.findall(filtered_content)
            if matches:
                filtered_content = pattern.sub('', filtered_content)
                removed_count += len(matches)

        return filtered_content, removed_count

    def _remove_spam(self, content: str) -> Tuple[str, int]:
        """移除垃圾内容"""
        removed_count = 0
        filtered_content = content

        for pattern in self.spam_patterns:
            matches = pattern.findall(filtered_content)
            if matches:
                filtered_content = pattern.sub('', filtered_content)
                removed_count += len(matches)

        return filtered_content, removed_count

    def _remove_repetition(self, content: str) -> Tuple[str, int]:
        """移除重复内容"""
        removed_count = 0
        filtered_content = content

        for pattern in self.repetition_patterns:
            matches = pattern.findall(filtered_content)
            if matches:
                filtered_content = pattern.sub(r'\1', filtered_content)  # 保留一个副本
                removed_count += len(matches)

        return filtered_content, removed_count

    def _normalize_content(self, content: str) -> str:
        """标准化内容"""
        # 标准化空白字符
        content = re.sub(r'\s+', ' ', content)

        # 移除多余空行
        content = re.sub(r'\n\s*\n', '\n\n', content)

        # 移除首尾空白
        content = content.strip()

        return content

    def calculate_noise_score(self, content: str) -> float:
        """计算噪声分数（0-1，分数越高噪声越多）"""
        if not content:
            return 1.0

        score = 0.0
        max_score = 0.0

        # 广告分数
        ad_count = sum(1 for pattern in self.ad_patterns if pattern.search(content))
        score += min(ad_count * 0.1, 0.3)  # 最高0.3分
        max_score += 0.3

        # 垃圾内容分数
        spam_count = sum(1 for pattern in self.spam_patterns if pattern.search(content))
        score += min(spam_count * 0.1, 0.3)  # 最高0.3分
        max_score += 0.3

        # 重复内容分数
        repetition_ratio = self._calculate_repetition_ratio(content)
        score += min(repetition_ratio * 0.4, 0.4)  # 最高0.4分
        max_score += 0.4

        return score / max_score if max_score > 0 else 0.0

    def _calculate_repetition_ratio(self, content: str) -> float:
        """计算重复比例"""
        if not content or len(content) < 50:
            return 0.0

        # 计算字符重复率
        char_counts = Counter(content)
        unique_chars = len(char_counts)
        total_chars = len(content)

        if total_chars == 0:
            return 0.0

        # 计算重复率（1 - 唯一字符率）
        repetition_ratio = 1.0 - (unique_chars / total_chars)

        return min(repetition_ratio, 1.0)

    def get_noise_patterns(self) -> Dict[str, List[str]]:
        """获取噪声模式"""
        return {
            'ads': [pattern.pattern for pattern in self.ad_patterns],
            'spam': [pattern.pattern for pattern in self.spam_patterns],
            'boilerplate': [pattern.pattern for pattern in self.boilerplate_patterns],
            'irrelevant_keywords': list(self.irrelevant_keywords),
            'low_quality_indicators': list(self.low_quality_indicators)
        }

    def add_noise_pattern(self, pattern_type: str, pattern: str):
        """添加噪声模式"""
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)

            if pattern_type == 'ads':
                self.ad_patterns.append(compiled_pattern)
            elif pattern_type == 'spam':
                self.spam_patterns.append(compiled_pattern)
            elif pattern_type == 'boilerplate':
                self.boilerplate_patterns.append(compiled_pattern)
            else:
                raise ValueError(f"不支持的噪声模式类型: {pattern_type}")

            self.logger.info(f"已添加 {pattern_type} 噪声模式: {pattern}")

        except Exception as e:
            self.logger.error(f"添加噪声模式失败: {str(e)}", exc_info=True)