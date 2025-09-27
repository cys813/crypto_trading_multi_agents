"""
Content preprocessing for cleaning and standardization
"""

import re
import html
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass
from hashlib import sha256

from ..models.base import NewsArticle
from .models import ProcessingResult, ProcessingStatus, ProcessingStage, ProcessingConfig


@dataclass
class PreprocessingStats:
    """预处理统计信息"""
    original_length: int
    processed_length: int
    removed_chars: int
    removed_html_tags: int
    removed_urls: int
    normalized_whitespace: int
    processing_time: float


class ContentPreprocessor:
    """内容预处理器 - 清理和标准化新闻内容"""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 预编译正则表达式
        self.html_tag_pattern = re.compile(r'<[^>]+>')
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.whitespace_pattern = re.compile(r'\s+')
        self.special_chars_pattern = re.compile(r'[^\w\s\u4e00-\u9fff.,!?;:\'"()-]')
        self.repeated_chars_pattern = re.compile(r'(.)\1{3,}')
        self.boilerplate_patterns = [
            re.compile(r'点击这里阅读更多', re.IGNORECASE),
            re.compile(r'请订阅我们的新闻通讯', re.IGNORECASE),
            re.compile(r'关注我们的社交媒体', re.IGNORECASE),
            re.compile(r'免责声明：', re.IGNORECASE),
            re.compile(r'投资有风险', re.IGNORECASE),
        ]

    async def preprocess(self, article: NewsArticle) -> Tuple[NewsArticle, PreprocessingStats]:
        """预处理新闻文章"""
        start_time = datetime.now()
        original_content = article.content

        try:
            # 检查内容长度
            if len(original_content) < self.config.min_content_length:
                self.logger.warning(f"文章内容过短: {len(original_content)} 字符")
                return article, PreprocessingStats(
                    original_length=len(original_content),
                    processed_length=len(original_content),
                    removed_chars=0,
                    removed_html_tags=0,
                    removed_urls=0,
                    normalized_whitespace=0,
                    processing_time=0
                )

            # 处理内容
            processed_content = original_content

            # 移除HTML标签
            if self.config.remove_html_tags:
                processed_content, html_tags_removed = self._remove_html_tags(processed_content)
            else:
                html_tags_removed = 0

            # 移除URL
            if self.config.remove_urls:
                processed_content, urls_removed = self._remove_urls(processed_content)
            else:
                urls_removed = 0

            # 标准化空白字符
            if self.config.normalize_whitespace:
                processed_content, whitespace_normalized = self._normalize_whitespace(processed_content)
            else:
                whitespace_normalized = 0

            # 清理特殊字符
            processed_content = self._clean_special_chars(processed_content)

            # 移除重复字符
            processed_content = self._remove_repeated_chars(processed_content)

            # 移除样板文本
            processed_content, boilerplate_removed = self._remove_boilerplate(processed_content)

            # 处理标题
            processed_title = self._preprocess_title(article.title)

            # 处理摘要
            processed_summary = None
            if article.summary:
                processed_summary = self._preprocess_summary(article.summary)

            # 限制内容长度
            if len(processed_content) > self.config.max_content_length:
                processed_content = processed_content[:self.config.max_content_length]
                self.logger.info(f"内容被截断至 {self.config.max_content_length} 字符")

            # 创建处理后的文章
            processed_article = NewsArticle(
                id=article.id,
                title=processed_title,
                content=processed_content,
                summary=processed_summary,
                author=article.author,
                published_at=article.published_at,
                source=article.source,
                url=article.url,
                category=article.category,
                tags=article.tags.copy() if article.tags else [],
                metadata={
                    **(article.metadata or {}),
                    'preprocessed': True,
                    'preprocessing_time': datetime.now().isoformat(),
                    'original_length': len(original_content),
                    'processed_length': len(processed_content)
                }
            )

            # 计算统计信息
            processing_time = (datetime.now() - start_time).total_seconds()
            stats = PreprocessingStats(
                original_length=len(original_content),
                processed_length=len(processed_content),
                removed_chars=len(original_content) - len(processed_content),
                removed_html_tags=html_tags_removed,
                removed_urls=urls_removed,
                normalized_whitespace=whitespace_normalized,
                processing_time=processing_time
            )

            self.logger.info(f"预处理完成: {len(original_content)} -> {len(processed_content)} 字符, "
                           f"耗时 {processing_time:.3f}秒")

            return processed_article, stats

        except Exception as e:
            self.logger.error(f"预处理失败: {str(e)}", exc_info=True)
            processing_time = (datetime.now() - start_time).total_seconds()
            stats = PreprocessingStats(
                original_length=len(original_content),
                processed_length=len(original_content),
                removed_chars=0,
                removed_html_tags=0,
                removed_urls=0,
                normalized_whitespace=0,
                processing_time=processing_time
            )
            return article, stats

    def _remove_html_tags(self, content: str) -> Tuple[str, int]:
        """移除HTML标签"""
        matches = self.html_tag_pattern.findall(content)
        cleaned_content = self.html_tag_pattern.sub('', content)

        # 清理HTML实体
        cleaned_content = html.unescape(cleaned_content)

        return cleaned_content, len(matches)

    def _remove_urls(self, content: str) -> Tuple[str, int]:
        """移除URL"""
        matches = self.url_pattern.findall(content)
        cleaned_content = self.url_pattern.sub('[URL]', content)
        return cleaned_content, len(matches)

    def _normalize_whitespace(self, content: str) -> Tuple[str, int]:
        """标准化空白字符"""
        # 替换多个空白字符为单个空格
        cleaned_content = self.whitespace_pattern.sub(' ', content)

        # 移除首尾空白
        cleaned_content = cleaned_content.strip()

        # 计算标准化操作次数
        original_whitespace = len(self.whitespace_pattern.findall(content))
        normalized_whitespace = len(self.whitespace_pattern.findall(cleaned_content))

        return cleaned_content, max(0, original_whitespace - normalized_whitespace)

    def _clean_special_chars(self, content: str) -> str:
        """清理特殊字符"""
        # 保留基本标点和中文字符
        cleaned_content = self.special_chars_pattern.sub('', content)

        # 清理多余的标点符号
        cleaned_content = re.sub(r'([.,!?;:]){2,}', r'\1', cleaned_content)

        return cleaned_content

    def _remove_repeated_chars(self, content: str) -> str:
        """移除重复字符"""
        # 限制字符重复次数（最多3次）
        cleaned_content = self.repeated_chars_pattern.sub(r'\1\1\1', content)
        return cleaned_content

    def _remove_boilerplate(self, content: str) -> Tuple[str, int]:
        """移除样板文本"""
        original_content = content
        removed_count = 0

        for pattern in self.boilerplate_patterns:
            matches = pattern.findall(content)
            if matches:
                content = pattern.sub('', content)
                removed_count += len(matches)

        return content, removed_count

    def _preprocess_title(self, title: str) -> str:
        """预处理标题"""
        if not title:
            return ""

        # 移除HTML标签
        title = self.html_tag_pattern.sub('', title)

        # 标准化空白字符
        title = self.whitespace_pattern.sub(' ', title).strip()

        # 限制标题长度
        if len(title) > 200:
            title = title[:200]

        return title

    def _preprocess_summary(self, summary: str) -> str:
        """预处理摘要"""
        if not summary:
            return ""

        # 移除HTML标签
        summary = self.html_tag_pattern.sub('', summary)

        # 标准化空白字符
        summary = self.whitespace_pattern.sub(' ', summary).strip()

        # 限制摘要长度
        if len(summary) > 500:
            summary = summary[:500]

        return summary

    def generate_content_hash(self, content: str) -> str:
        """生成内容哈希"""
        # 标准化内容后生成哈希
        normalized_content = content.lower().strip()
        normalized_content = self.whitespace_pattern.sub(' ', normalized_content)

        return sha256(normalized_content.encode('utf-8')).hexdigest()

    def validate_content(self, content: str) -> bool:
        """验证内容质量"""
        if not content or len(content.strip()) < self.config.min_content_length:
            return False

        # 检查是否主要是垃圾内容
        words = content.split()
        if len(words) < self.config.min_word_count:
            return False

        # 检查重复率
        unique_chars = len(set(content))
        total_chars = len(content)
        if total_chars > 0 and unique_chars / total_chars < 0.3:
            return False

        return True

    async def batch_preprocess(self, articles: List[NewsArticle]) -> List[Tuple[NewsArticle, PreprocessingStats]]:
        """批量预处理文章"""
        self.logger.info(f"开始批量预处理 {len(articles)} 篇文章")

        results = []
        for article in articles:
            try:
                processed_article, stats = await self.preprocess(article)
                results.append((processed_article, stats))
            except Exception as e:
                self.logger.error(f"批量预处理失败: {str(e)}", exc_info=True)
                # 返回原始文章和空统计
                stats = PreprocessingStats(
                    original_length=len(article.content),
                    processed_length=len(article.content),
                    removed_chars=0,
                    removed_html_tags=0,
                    removed_urls=0,
                    normalized_whitespace=0,
                    processing_time=0
                )
                results.append((article, stats))

        self.logger.info(f"批量预处理完成，处理了 {len(results)} 篇文章")
        return results