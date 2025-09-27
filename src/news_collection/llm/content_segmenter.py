"""
Content segmentation module for breaking news articles into logical sections
"""

import asyncio
import logging
import time
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..models.base import NewsArticle
from .llm_connector import LLMConnector, LLMMessage, LLMConfig, LLMResponse


class SectionType(Enum):
    """段落类型枚举"""
    INTRODUCTION = "introduction"
    BACKGROUND = "background"
    MAIN_CONTENT = "main_content"
    TECHNICAL_DETAILS = "technical_details"
    MARKET_ANALYSIS = "market_analysis"
    REGULATORY_ASPECTS = "regulatory_aspects"
    SECURITY_CONCERNS = "security_concerns"
    ADOPTION_NEWS = "adoption_news"
    QUOTES = "quotes"
    OPINION = "opinion"
    CONCLUSION = "conclusion"
    CALL_TO_ACTION = "call_to_action"
    OTHER = "other"


@dataclass
class SectionConfig:
    """段落配置"""
    enable_hierarchical_segmentation: bool = True
    enable_content_categorization: bool = True
    enable_key_point_extraction: bool = True
    enable_section_summarization: bool = True
    max_section_length: int = 1000  # characters
    min_section_length: int = 100  # characters
    prioritize_section_types: List[SectionType] = field(default_factory=lambda: [
        SectionType.INTRODUCTION,
        SectionType.MAIN_CONTENT,
        SectionType.CONCLUSION
    ])
    language: str = "en"
    output_format: str = "structured"  # structured, simple
    include_section_stats: bool = True


@dataclass
class ContentSection:
    """内容段落"""
    id: str
    type: SectionType
    title: str
    content: str
    start_position: int
    end_position: int
    word_count: int
    key_points: List[str] = None
    summary: Optional[str] = None
    importance_score: float = 0.5  # 0.0 to 1.0
    sentiment: Dict[str, Any] = None
    entities: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.key_points is None:
            self.key_points = []
        if self.sentiment is None:
            self.sentiment = {}
        if self.entities is None:
            self.entities = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SegmentationResult:
    """分段结果"""
    sections: List[ContentSection]
    overall_structure: Dict[str, Any]
    section_hierarchy: Dict[str, List[str]]
    processing_time: float
    metadata: Dict[str, Any]


@dataclass
class SegmentationStats:
    """分段统计"""
    total_articles: int = 0
    successful_segmentations: int = 0
    failed_segmentations: int = 0
    average_processing_time: float = 0.0
    average_sections_per_article: float = 0.0
    section_type_distribution: Dict[str, int] = field(default_factory=dict)
    average_section_length: float = 0.0


class ContentSegmenter:
    """内容分段器"""

    def __init__(self, llm_connector: LLMConnector, config: SectionConfig):
        self.llm_connector = llm_connector
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats = SegmentationStats()

        # 初始化段落类型分布
        for section_type in SectionType:
            self.stats.section_type_distribution[section_type.value] = 0

        # 预编译正则表达式
        self.sentence_pattern = re.compile(r'[.!?]+')
        self.word_pattern = re.compile(r'\b\w+\b')

    def _create_system_prompt(self) -> str:
        """创建系统提示"""
        system_prompt = """You are an expert content analyst specializing in news article structure and segmentation.

Your task is to analyze news articles and break them into logical, coherent sections.

Segmentation Requirements:

1. Identify Natural Sections:
   - Look for paragraph breaks, headings, and topic transitions
   - Identify distinct themes and subject areas
   - Recognize changes in focus or perspective

2. Section Classification:
   - Introduction: Opening paragraphs that set the context
   - Background: Historical or contextual information
   - Main Content: Core information and developments
   - Technical Details: Technical specifications or explanations
   - Market Analysis: Market trends, price movements, trading data
   - Regulatory Aspects: Legal, regulatory, or compliance information
   - Security Concerns: Security issues, vulnerabilities, or threats
   - Adoption News: Partnership, integration, or adoption developments
   - Quotes: Direct quotes from experts or officials
   - Opinion: Editorial or opinion content
   - Conclusion: Summary or final thoughts
   - Call to Action: Recommendations or next steps

3. Section Characteristics:
   - Logical coherence within sections
   - Clear transitions between sections
   - Appropriate length (100-1000 characters recommended)
   - Distinct focus and purpose

4. Additional Analysis:
   - Extract key points from each section
   - Provide brief section summaries if requested
   - Identify section importance and relevance
   - Note any structural patterns

Section Identification Guidelines:
- Use paragraph breaks as primary indicators
- Look for topic shifts or subject changes
- Consider headings, subheadings, and formatting
- Account for quoted content and expert commentary
- Identify technical vs. general content sections

Output format: structured JSON

Respond with JSON containing:
- sections: array of section objects with type, title, content, position
- overall_structure: object describing the article's general structure
- section_hierarchy: object showing parent-child relationships between sections
- key_points: array of main points from each section
- section_stats: object with section count, average length, etc.

Ensure your segmentation:
- Maintains content flow and readability
- Preserves important information
- Creates meaningful, useful sections
- Handles various article structures and formats"""

        return system_prompt

    def _create_user_prompt(self, article: NewsArticle) -> str:
        """创建用户提示"""
        prompt = f"""Please segment the following news article into logical sections:

Title: {article.title}
Source: {article.source or 'Unknown'}
Published: {article.published_at or 'Unknown date'}
Category: {article.category.value if article.category else 'General'}
Author: {article.author or 'Unknown'}

Content:
{article.content}

"""

        if article.tags:
            prompt += f"Tags: {', '.join(article.tags)}\n"

        # 添加配置说明
        config_details = []
        if self.config.enable_hierarchical_segmentation:
            config_details.append("hierarchical segmentation")
        if self.config.enable_content_categorization:
            config_details.append("content categorization")
        if self.config.enable_key_point_extraction:
            config_details.append("key point extraction")
        if self.config.enable_section_summarization:
            config_details.append("section summarization")

        if config_details:
            prompt += f"\nPlease include: {', '.join(config_details)}\n"

        # 添加优先段落类型
        priority_types = [section_type.value for section_type in self.config.prioritize_section_types]
        prompt += f"\nPrioritize these section types: {', '.join(priority_types)}\n"

        prompt += f"\nTarget section length: {self.config.min_section_length}-{self.config.max_section_length} characters\n"

        prompt += "\nProvide a comprehensive segmentation following the requirements specified."

        return prompt

    def _parse_segmentation_response(self, response: str) -> Dict[str, Any]:
        """解析分段响应"""
        try:
            # 尝试解析JSON
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            # 如果不是有效的JSON，执行基本分段
            self.logger.warning("Failed to parse JSON segmentation response, using basic segmentation")
            return self._basic_segmentation(response)

    def _basic_segmentation(self, content: str) -> Dict[str, Any]:
        """基础分段逻辑"""
        # 按段落分割
        paragraphs = content.split('\n\n')
        sections = []
        current_pos = 0

        for i, paragraph in enumerate(paragraphs):
            if len(paragraph.strip()) < self.config.min_section_length:
                continue

            section = {
                "id": f"section_{i+1}",
                "type": "main_content",
                "title": f"Section {i+1}",
                "content": paragraph.strip(),
                "start_position": current_pos,
                "end_position": current_pos + len(paragraph),
                "importance_score": 0.5,
                "key_points": []
            }
            sections.append(section)
            current_pos += len(paragraph) + 2  # +2 for \n\n

        return {
            "sections": sections,
            "overall_structure": {"type": "linear", "sections_count": len(sections)},
            "section_hierarchy": {},
            "key_points": []
        }

    def _create_content_section(self, section_data: Dict[str, Any], section_id: str) -> ContentSection:
        """创建内容段落对象"""
        section_type_map = {
            "introduction": SectionType.INTRODUCTION,
            "background": SectionType.BACKGROUND,
            "main_content": SectionType.MAIN_CONTENT,
            "technical_details": SectionType.TECHNICAL_DETAILS,
            "market_analysis": SectionType.MARKET_ANALYSIS,
            "regulatory_aspects": SectionType.REGULATORY_ASPECTS,
            "security_concerns": SectionType.SECURITY_CONCERNS,
            "adoption_news": SectionType.ADOPTION_NEWS,
            "quotes": SectionType.QUOTES,
            "opinion": SectionType.OPINION,
            "conclusion": SectionType.CONCLUSION,
            "call_to_action": SectionType.CALL_TO_ACTION,
            "other": SectionType.OTHER
        }

        word_count = len(self.word_pattern.findall(section_data.get("content", "")))

        return ContentSection(
            id=section_id,
            type=section_type_map.get(section_data.get("type", "other"), SectionType.OTHER),
            title=section_data.get("title", "Untitled Section"),
            content=section_data.get("content", ""),
            start_position=section_data.get("start_position", 0),
            end_position=section_data.get("end_position", 0),
            word_count=word_count,
            key_points=section_data.get("key_points", []),
            summary=section_data.get("summary"),
            importance_score=section_data.get("importance_score", 0.5),
            sentiment=section_data.get("sentiment", {}),
            entities=section_data.get("entities", []),
            metadata=section_data.get("metadata", {})
        )

    async def segment_content(self, article: NewsArticle) -> SegmentationResult:
        """分段文章内容"""
        start_time = time.time()
        self.stats.total_articles += 1

        try:
            # 创建消息
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(article)

            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ]

            # 调用LLM
            response = await self.llm_connector.generate_response(messages)

            # 解析响应
            segmentation_data = self._parse_segmentation_response(response.content)

            # 创建段落对象
            sections = []
            for i, section_data in enumerate(segmentation_data.get("sections", [])):
                section_id = section_data.get("id", f"section_{i+1}")
                section = self._create_content_section(section_data, section_id)
                sections.append(section)

            # 创建结果
            result = SegmentationResult(
                sections=sections,
                overall_structure=segmentation_data.get("overall_structure", {}),
                section_hierarchy=segmentation_data.get("section_hierarchy", {}),
                processing_time=time.time() - start_time,
                metadata={
                    "llm_provider": response.provider.value,
                    "llm_model": response.model,
                    "response_time": response.response_time,
                    "tokens_used": response.usage.get("total_tokens", 0),
                    "cached": response.cached
                }
            )

            # 更新统计
            self.stats.successful_segmentations += 1
            self._update_stats(result)

            self.logger.info(f"Successfully segmented article {article.id} into {len(sections)} sections")
            return result

        except Exception as e:
            self.stats.failed_segmentations += 1
            self.logger.error(f"Failed to segment article {article.id}: {str(e)}")

            # 返回默认结果（单个段落）
            default_section = ContentSection(
                id="section_1",
                type=SectionType.MAIN_CONTENT,
                title="Full Content",
                content=article.content,
                start_position=0,
                end_position=len(article.content),
                word_count=len(self.word_pattern.findall(article.content)),
                key_points=[],
                importance_score=0.5
            )

            return SegmentationResult(
                sections=[default_section],
                overall_structure={"type": "single_section", "error": "Segmentation failed"},
                section_hierarchy={},
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )

    async def segment_batch_content(self, articles: List[NewsArticle]) -> List[SegmentationResult]:
        """批量内容分段"""
        self.logger.info(f"Starting batch content segmentation of {len(articles)} articles")

        tasks = []
        for article in articles:
            task = self.segment_content(article)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        segmentation_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch segmentation failed for article {articles[i].id}: {str(result)}")
                # 创建失败结果
                default_section = ContentSection(
                    id="section_1",
                    type=SectionType.MAIN_CONTENT,
                    title="Full Content",
                    content=articles[i].content,
                    start_position=0,
                    end_position=len(articles[i].content),
                    word_count=len(self.word_pattern.findall(articles[i].content)),
                    key_points=[],
                    importance_score=0.5
                )

                segmentation_results.append(SegmentationResult(
                    sections=[default_section],
                    overall_structure={"type": "single_section", "error": "Batch processing failed"},
                    section_hierarchy={},
                    processing_time=0.0,
                    metadata={"error": str(result), "batch_failed": True}
                ))
            else:
                segmentation_results.append(result)

        self.logger.info(f"Batch segmentation completed: {len(segmentation_results)} articles processed")
        return segmentation_results

    def _update_stats(self, result: SegmentationResult):
        """更新统计信息"""
        # 更新平均处理时间
        total_time = self.stats.average_processing_time * (self.stats.successful_segmentations - 1)
        total_time += result.processing_time
        self.stats.average_processing_time = total_time / self.stats.successful_segmentations

        # 更新平均段落数量
        total_sections = self.stats.average_sections_per_article * (self.stats.successful_segmentations - 1)
        total_sections += len(result.sections)
        self.stats.average_sections_per_article = total_sections / self.stats.successful_segmentations

        # 更新段落类型分布
        for section in result.sections:
            self.stats.section_type_distribution[section.type.value] += 1

        # 更新平均段落长度
        if result.sections:
            total_length = self.stats.average_section_length * (self.stats.successful_segmentations - 1)
            avg_article_length = sum(section.word_count for section in result.sections) / len(result.sections)
            total_length += avg_article_length
            self.stats.average_section_length = total_length / self.stats.successful_segmentations

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = self.stats.successful_segmentations / max(1, self.stats.total_articles)
        return {
            "total_articles": self.stats.total_articles,
            "successful_segmentations": self.stats.successful_segmentations,
            "failed_segmentations": self.stats.failed_segmentations,
            "success_rate": success_rate,
            "average_processing_time": self.stats.average_processing_time,
            "average_sections_per_article": self.stats.average_sections_per_article,
            "average_section_length": self.stats.average_section_length,
            "section_type_distribution": self.stats.section_type_distribution,
            "config": {
                "enable_hierarchical_segmentation": self.config.enable_hierarchical_segmentation,
                "enable_content_categorization": self.config.enable_content_categorization,
                "enable_key_point_extraction": self.config.enable_key_point_extraction,
                "enable_section_summarization": self.config.enable_section_summarization,
                "max_section_length": self.config.max_section_length,
                "min_section_length": self.config.min_section_length
            }
        }

    def update_config(self, config: SectionConfig):
        """更新配置"""
        self.config = config
        self.logger.info("Content segmenter configuration updated")

    def get_section_summary(self, sections: List[ContentSection]) -> Dict[str, Any]:
        """获取段落摘要"""
        if not sections:
            return {"error": "No sections to summarize"}

        section_summary = {
            "total_sections": len(sections),
            "total_words": sum(section.word_count for section in sections),
            "average_section_length": sum(section.word_count for section in sections) / len(sections),
            "section_types": {},
            "most_important_sections": [],
            "longest_sections": [],
            "key_points_count": sum(len(section.key_points) for section in sections)
        }

        # 统计段落类型
        type_counts = {}
        for section in sections:
            section_type = section.type.value
            type_counts[section_type] = type_counts.get(section_type, 0) + 1
        section_summary["section_types"] = type_counts

        # 最重要的段落
        important_sections = sorted(sections, key=lambda x: x.importance_score, reverse=True)
        section_summary["most_important_sections"] = [
            {
                "id": section.id,
                "type": section.type.value,
                "title": section.title,
                "importance_score": section.importance_score,
                "word_count": section.word_count
            }
            for section in important_sections[:3]
        ]

        # 最长的段落
        longest_sections = sorted(sections, key=lambda x: x.word_count, reverse=True)
        section_summary["longest_sections"] = [
            {
                "id": section.id,
                "type": section.type.value,
                "title": section.title,
                "word_count": section.word_count
            }
            for section in longest_sections[:3]
        ]

        return section_summary

    def merge_sections(self, sections: List[ContentSection], merge_strategy: str = "similarity") -> List[ContentSection]:
        """合并段落"""
        if len(sections) <= 1:
            return sections

        if merge_strategy == "similarity":
            # 基于类型相似性合并
            type_groups = {}
            for section in sections:
                section_type = section.type.value
                if section_type not in type_groups:
                    type_groups[section_type] = []
                type_groups[section_type].append(section)

            merged_sections = []
            for section_type, type_sections in type_groups.items():
                if len(type_sections) == 1:
                    merged_sections.extend(type_sections)
                else:
                    # 合并相同类型的段落
                    merged_content = " ".join(section.content for section in type_sections)
                    merged_key_points = []
                    for section in type_sections:
                        merged_key_points.extend(section.key_points)

                    merged_section = ContentSection(
                        id=f"merged_{section_type}",
                        type=type_sections[0].type,
                        title=f"Merged {section_type}",
                        content=merged_content,
                        start_position=min(section.start_position for section in type_sections),
                        end_position=max(section.end_position for section in type_sections),
                        word_count=sum(section.word_count for section in type_sections),
                        key_points=merged_key_points[:10],  # 限制要点数量
                        importance_score=max(section.importance_score for section in type_sections)
                    )
                    merged_sections.append(merged_section)

            return merged_sections

        elif merge_strategy == "length":
            # 基于长度合并短段落
            merged_sections = []
            current_section = None

            for section in sections:
                if current_section is None:
                    current_section = section
                else:
                    # 如果当前段落太短，与下一个段落合并
                    if current_section.word_count < self.config.min_section_length:
                        current_section.content += " " + section.content
                        current_section.word_count += section.word_count
                        current_section.end_position = section.end_position
                        current_section.key_points.extend(section.key_points)
                    else:
                        merged_sections.append(current_section)
                        current_section = section

            if current_section:
                merged_sections.append(current_section)

            return merged_sections

        else:
            return sections

    def validate_article(self, article: NewsArticle) -> bool:
        """验证文章是否适合分段"""
        if not article.content or len(article.content.strip()) < self.config.min_section_length:
            self.logger.warning(f"Article {article.id} has insufficient content for segmentation")
            return False

        # 如果文章已经很短，不需要分段
        if len(article.content) < self.config.max_section_length * 1.5:
            self.logger.info(f"Article {article.id} is too short for meaningful segmentation")
            return False

        return True