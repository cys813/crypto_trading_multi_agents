"""
Tests for content segmenter module
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock

from ..content_segmenter import (
    ContentSegmenter, SectionConfig, SegmentationResult, ContentSection,
    SectionType, SegmentationStats
)
from ..llm_connector import LLMConnector, LLMConfig, LLMMessage, LLMResponse
from ...models.base import NewsArticle


class TestSectionConfig:
    """测试段落配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = SectionConfig()
        assert config.enable_hierarchical_segmentation is True
        assert config.enable_content_categorization is True
        assert config.enable_key_point_extraction is True
        assert config.enable_section_summarization is True
        assert config.max_section_length == 1000
        assert config.min_section_length == 100
        assert len(config.prioritize_section_types) == 3
        assert SectionType.INTRODUCTION in config.prioritize_section_types
        assert SectionType.MAIN_CONTENT in config.prioritize_section_types
        assert config.language == "en"
        assert config.output_format == "structured"
        assert config.include_section_stats is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = SectionConfig(
            enable_hierarchical_segmentation=False,
            enable_content_categorization=False,
            max_section_length=500,
            min_section_length=50,
            prioritize_section_types=[SectionType.INTRODUCTION],
            language="zh"
        )
        assert config.enable_hierarchical_segmentation is False
        assert config.enable_content_categorization is False
        assert config.max_section_length == 500
        assert config.min_section_length == 50
        assert len(config.prioritize_section_types) == 1
        assert SectionType.INTRODUCTION in config.prioritize_section_types
        assert config.language == "zh"


class TestContentSection:
    """测试内容段落类"""

    def test_section_creation(self):
        """测试段落创建"""
        section = ContentSection(
            id="section-1",
            type=SectionType.INTRODUCTION,
            title="Introduction",
            content="This is the introduction content.",
            start_position=0,
            end_position=35,
            word_count=7
        )
        assert section.id == "section-1"
        assert section.type == SectionType.INTRODUCTION
        assert section.title == "Introduction"
        assert section.content == "This is the introduction content."
        assert section.start_position == 0
        assert section.end_position == 35
        assert section.word_count == 7
        assert section.importance_score == 0.5
        assert section.key_points == []
        assert section.sentiment == {}
        assert section.entities == []
        assert section.metadata == {}

    def test_section_with_additional_data(self):
        """测试带额外数据的段落"""
        section = ContentSection(
            id="section-2",
            type=SectionType.MAIN_CONTENT,
            title="Main Content",
            content="This is the main content with additional details.",
            start_position=40,
            end_position=90,
            word_count=12,
            key_points=["Important point 1", "Important point 2"],
            summary="Brief summary of main content",
            importance_score=0.8,
            sentiment={"positive": 0.7, "neutral": 0.3},
            entities=[{"name": "Bitcoin", "type": "cryptocurrency"}],
            metadata={"section_priority": "high"}
        )
        assert len(section.key_points) == 2
        assert section.summary == "Brief summary of main content"
        assert section.importance_score == 0.8
        assert section.sentiment["positive"] == 0.7
        assert len(section.entities) == 1
        assert section.metadata["section_priority"] == "high"


class TestSegmentationResult:
    """测试分段结果类"""

    def test_result_creation(self):
        """测试结果创建"""
        sections = [
            ContentSection(
                id="section-1",
                type=SectionType.INTRODUCTION,
                title="Introduction",
                content="Intro content",
                start_position=0,
                end_position=20,
                word_count=4
            ),
            ContentSection(
                id="section-2",
                type=SectionType.MAIN_CONTENT,
                title="Main Content",
                content="Main content",
                start_position=25,
                end_position=45,
                word_count=4
            )
        ]

        result = SegmentationResult(
            sections=sections,
            overall_structure={"type": "linear", "sections": 2},
            section_hierarchy={"section-1": [], "section-2": []},
            processing_time=1.5,
            metadata={"test": "data"}
        )

        assert len(result.sections) == 2
        assert result.overall_structure["type"] == "linear"
        assert len(result.section_hierarchy) == 2
        assert result.processing_time == 1.5
        assert result.metadata["test"] == "data"


class TestContentSegmenter:
    """测试内容分段器"""

    @pytest.fixture
    def mock_llm_connector(self):
        """模拟LLM连接器"""
        connector = Mock(spec=LLMConnector)

        # 模拟生成响应
        async def mock_generate_response(messages, config=None):
            return LLMResponse(
                content='''{
                    "sections": [
                        {
                            "id": "intro",
                            "type": "introduction",
                            "title": "Introduction",
                            "content": "This article discusses the latest developments in cryptocurrency markets.",
                            "start_position": 0,
                            "end_position": 80,
                            "importance_score": 0.9,
                            "key_points": ["Cryptocurrency market developments", "Latest trends"]
                        },
                        {
                            "id": "main",
                            "type": "main_content",
                            "title": "Main Analysis",
                            "content": "Bitcoin has shown significant growth over the past week, with institutional investors showing increased interest.",
                            "start_position": 85,
                            "end_position": 200,
                            "importance_score": 0.8,
                            "key_points": ["Bitcoin growth", "Institutional investment"]
                        },
                        {
                            "id": "conclusion",
                            "type": "conclusion",
                            "title": "Conclusion",
                            "content": "In conclusion, the cryptocurrency market continues to evolve with new opportunities emerging.",
                            "start_position": 205,
                            "end_position": 290,
                            "importance_score": 0.7,
                            "key_points": ["Market evolution", "New opportunities"]
                        }
                    ],
                    "overall_structure": {
                        "type": "standard_news",
                        "sections": 3,
                        "has_introduction": true,
                        "has_conclusion": true
                    },
                    "section_hierarchy": {
                        "intro": [],
                        "main": [],
                        "conclusion": []
                    },
                    "key_points": ["Market developments", "Bitcoin growth", "Future opportunities"]
                }''',
                usage={"total_tokens": 150},
                model="test-model",
                provider="mock",
                response_time=0.8
            )

        connector.generate_response = AsyncMock(side_effect=mock_generate_response)
        return connector

    @pytest.fixture
    def sample_article(self):
        """示例文章"""
        return NewsArticle(
            id="test-article-1",
            title="Cryptocurrency Market Analysis",
            content="This article discusses the latest developments in cryptocurrency markets. Bitcoin has shown significant growth over the past week, with institutional investors showing increased interest. In conclusion, the cryptocurrency market continues to evolve with new opportunities emerging.",
            source="Crypto News",
            category="market_analysis",
            author="Jane Doe",
            tags=["bitcoin", "cryptocurrency", "market", "analysis"]
        )

    def test_init(self, mock_llm_connector):
        """测试初始化"""
        config = SectionConfig()
        segmenter = ContentSegmenter(mock_llm_connector, config)

        assert segmenter.llm_connector == mock_llm_connector
        assert segmenter.config == config
        assert segmenter.stats.total_articles == 0
        assert segmenter.stats.successful_segmentations == 0
        assert segmenter.stats.failed_segmentations == 0

        # 检查统计初始化
        for section_type in SectionType:
            assert segmenter.stats.section_type_distribution[section_type.value] == 0

        # 检查正则表达式
        assert segmenter.sentence_pattern is not None
        assert segmenter.word_pattern is not None

    def test_create_system_prompt(self):
        """测试系统提示创建"""
        config = SectionConfig()
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        prompt = segmenter._create_system_prompt()
        assert "content analyst" in prompt.lower()
        assert "news article structure" in prompt.lower()
        assert "segmentation requirements" in prompt.lower()
        assert "section identification" in prompt.lower()

    def test_create_user_prompt(self, sample_article):
        """测试用户提示创建"""
        config = SectionConfig()
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        prompt = segmenter._create_user_prompt(sample_article)
        assert sample_article.title in prompt
        assert sample_article.content in prompt
        assert sample_article.source in prompt
        assert sample_article.category.value in prompt
        assert "bitcoin, cryptocurrency, market, analysis" in prompt

    def test_parse_segmentation_response_json(self):
        """测试JSON响应解析"""
        config = SectionConfig()
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        json_response = '''{
            "sections": [
                {
                    "id": "section-1",
                    "type": "introduction",
                    "title": "Introduction",
                    "content": "This is the introduction."
                }
            ],
            "overall_structure": {"type": "simple"},
            "section_hierarchy": {}
        }'''

        result = segmenter._parse_segmentation_response(json_response)
        assert len(result["sections"]) == 1
        assert result["sections"][0]["type"] == "introduction"
        assert result["overall_structure"]["type"] == "simple"

    def test_basic_segmentation(self):
        """测试基础分段"""
        config = SectionConfig()
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        content = """This is the first paragraph. It contains multiple sentences and should be long enough for segmentation.

This is the second paragraph. It discusses different topics and provides additional information.

This is the third paragraph. It concludes the article with final thoughts."""

        result = segmenter._basic_segmentation(content)

        assert "sections" in result
        assert len(result["sections"]) >= 2  # 至少应该有2个段落
        assert result["overall_structure"]["type"] == "linear"

        # 检查段落内容
        for section in result["sections"]:
            assert "id" in section
            assert "type" in section
            assert "title" in section
            assert "content" in section
            assert len(section["content"]) >= config.min_section_length

    def test_create_content_section(self):
        """测试创建内容段落对象"""
        config = SectionConfig()
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        section_data = {
            "id": "test-section",
            "type": "introduction",
            "title": "Test Introduction",
            "content": "This is a test introduction section with multiple words for counting.",
            "start_position": 0,
            "end_position": 70,
            "importance_score": 0.8,
            "key_points": ["Test point", "Another point"],
            "summary": "Test summary",
            "sentiment": {"positive": 0.6},
            "entities": [{"name": "Test Entity"}],
            "metadata": {"priority": "high"}
        }

        section = segmenter._create_content_section(section_data, "custom-id")

        assert section.id == "custom-id"
        assert section.type == SectionType.INTRODUCTION
        assert section.title == "Test Introduction"
        assert section.word_count == 14  # 实际单词数
        assert section.importance_score == 0.8
        assert len(section.key_points) == 2
        assert section.summary == "Test summary"
        assert section.sentiment["positive"] == 0.6
        assert len(section.entities) == 1
        assert section.metadata["priority"] == "high"

    @pytest.mark.asyncio
    async def test_segment_content(self, mock_llm_connector, sample_article):
        """测试内容分段"""
        config = SectionConfig()
        segmenter = ContentSegmenter(mock_llm_connector, config)

        result = await segmenter.segment_content(sample_article)

        assert isinstance(result, SegmentationResult)
        assert len(result.sections) > 0
        assert result.processing_time > 0
        assert "overall_structure" in result.overall_structure
        assert "section_hierarchy" in result.section_hierarchy

        # 检查段落详情
        intro_section = next((s for s in result.sections if s.type == SectionType.INTRODUCTION), None)
        assert intro_section is not None
        assert intro_section.importance_score > 0

    @pytest.mark.asyncio
    async def test_segment_content_error_handling(self, mock_llm_connector, sample_article):
        """测试内容分段错误处理"""
        config = SectionConfig()
        segmenter = ContentSegmenter(mock_llm_connector, config)

        # 模拟LLM错误
        mock_llm_connector.generate_response.side_effect = Exception("API Error")

        result = await segmenter.segment_content(sample_article)

        assert isinstance(result, SegmentationResult)
        assert len(result.sections) == 1  # 应该返回默认的单个段落
        assert result.sections[0].type == SectionType.MAIN_CONTENT
        assert result.sections[0].content == sample_article.content
        assert "API Error" in result.metadata.get("error", "")

    @pytest.mark.asyncio
    async def test_segment_batch_content(self, mock_llm_connector):
        """测试批量内容分段"""
        config = SectionConfig()
        segmenter = ContentSegmenter(mock_llm_connector, config)

        articles = [
            NewsArticle(
                id="article-1",
                title="Article 1",
                content="Content for article 1 with sufficient length for segmentation.",
                source="Test"
            ),
            NewsArticle(
                id="article-2",
                title="Article 2",
                content="Content for article 2 with enough details to be segmented properly.",
                source="Test"
            )
        ]

        results = await segmenter.segment_batch_content(articles)

        assert len(results) == 2
        for result in results:
            assert isinstance(result, SegmentationResult)
            assert result.sections is not None

    def test_update_stats(self):
        """测试统计更新"""
        config = SectionConfig()
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        # 创建测试结果
        sections = [
            ContentSection(
                id="section-1",
                type=SectionType.INTRODUCTION,
                title="Introduction",
                content="Intro content",
                start_position=0,
                end_position=20,
                word_count=4
            ),
            ContentSection(
                id="section-2",
                type=SectionType.MAIN_CONTENT,
                title="Main Content",
                content="Main content with more words",
                start_position=25,
                end_position=55,
                word_count=7
            )
        ]

        result = SegmentationResult(
            sections=sections,
            overall_structure={},
            section_hierarchy={},
            processing_time=1.0,
            metadata={}
        )

        segmenter._update_stats(result)

        assert segmenter.stats.section_type_distribution["introduction"] == 1
        assert segmenter.stats.section_type_distribution["main_content"] == 1
        assert segmenter.stats.average_sections_per_article == 2.0
        assert segmenter.stats.average_section_length == 5.5  # (4 + 7) / 2

    def test_get_stats(self):
        """测试获取统计信息"""
        config = SectionConfig()
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        stats = segmenter.get_stats()
        assert "total_articles" in stats
        assert "successful_segmentations" in stats
        assert "failed_segmentations" in stats
        assert "success_rate" in stats
        assert "average_processing_time" in stats
        assert "average_sections_per_article" in stats
        assert "average_section_length" in stats
        assert "section_type_distribution" in stats
        assert "config" in stats

    def test_get_section_summary(self):
        """测试获取段落摘要"""
        config = SectionConfig()
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        sections = [
            ContentSection(
                id="section-1",
                type=SectionType.INTRODUCTION,
                title="Introduction",
                content="This is the introduction content.",
                start_position=0,
                end_position=35,
                word_count=7,
                importance_score=0.6,
                key_points=["Intro point"]
            ),
            ContentSection(
                id="section-2",
                type=SectionType.MAIN_CONTENT,
                title="Main Content",
                content="This is the main content with more details and important information.",
                start_position=40,
                end_position=100,
                word_count=15,
                importance_score=0.9,
                key_points=["Main point 1", "Main point 2"]
            )
        ]

        summary = segmenter.get_section_summary(sections)
        assert summary["total_sections"] == 2
        assert summary["total_words"] == 22
        assert summary["average_section_length"] == 11.0
        assert "section_types" in summary
        assert summary["section_types"]["introduction"] == 1
        assert summary["section_types"]["main_content"] == 1
        assert "most_important_sections" in summary
        assert "longest_sections" in summary
        assert summary["key_points_count"] == 3

        # 检查最重要的段落
        most_important = summary["most_important_sections"][0]
        assert most_important["id"] == "section-2"
        assert most_important["importance_score"] == 0.9

    def test_merge_sections_similarity(self):
        """测试基于相似性合并段落"""
        config = SectionConfig()
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        sections = [
            ContentSection(
                id="intro-1",
                type=SectionType.INTRODUCTION,
                title="Introduction 1",
                content="First intro part.",
                start_position=0,
                end_position=20,
                word_count=4
            ),
            ContentSection(
                id="intro-2",
                type=SectionType.INTRODUCTION,
                title="Introduction 2",
                content="Second intro part.",
                start_position=25,
                end_position=45,
                word_count=4
            ),
            ContentSection(
                id="main",
                type=SectionType.MAIN_CONTENT,
                title="Main Content",
                content="Main content section.",
                start_position=50,
                end_position=75,
                word_count=4
            )
        ]

        merged = segmenter.merge_sections(sections, merge_strategy="similarity")

        # 应该合并两个介绍段落，保留主要内容段落
        assert len(merged) == 2
        assert any(s.id.startswith("merged") for s in merged)
        assert any(s.type == SectionType.MAIN_CONTENT for s in merged)

        # 检查合并的段落内容
        merged_intro = next(s for s in merged if s.type == SectionType.INTRODUCTION)
        assert "First intro part." in merged_intro.content
        assert "Second intro part." in merged_intro.content

    def test_merge_sections_length(self):
        """测试基于长度合并段落"""
        config = SectionConfig(min_section_length=20)
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        sections = [
            ContentSection(
                id="short-1",
                type=SectionType.INTRODUCTION,
                title="Short Intro",
                content="Short",
                start_position=0,
                end_position=5,
                word_count=1  # 低于最小长度
            ),
            ContentSection(
                id="short-2",
                type=SectionType.MAIN_CONTENT,
                title="Short Main",
                content="Content",
                start_position=10,
                end_position=20,
                word_count=1  # 低于最小长度
            ),
            ContentSection(
                id="long",
                type=SectionType.CONCLUSION,
                title="Long Conclusion",
                content="This is a long conclusion that meets the minimum length requirement.",
                start_position=25,
                end_position=85,
                word_count=12  # 高于最小长度
            )
        ]

        merged = segmenter.merge_sections(sections, merge_strategy="length")

        # 短段落应该被合并，长段落保持不变
        assert len(merged) == 2  # 两个短段落合并 + 一个长段落

        # 检查合并的段落
        merged_short = next(s for s in merged if s.word_count > 1 and s.word_count < 10)
        assert merged_short.content == "Short Content"  # 合并后的内容

    def test_validate_article(self):
        """测试文章验证"""
        config = SectionConfig(min_section_length=50, max_section_length=200)
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        # 有效文章
        valid_article = NewsArticle(
            id="valid-article",
            title="Valid Article",
            content="This is a valid article content with sufficient length for proper segmentation. It contains multiple sentences and enough text to be divided into meaningful sections that meet the minimum length requirements while also being long enough to justify segmentation.",
            source="Test"
        )
        assert segmenter.validate_article(valid_article) is True

        # 内容太短的文章
        short_content_article = NewsArticle(
            id="short-content",
            title="Short Content",
            content="Short content",
            source="Test"
        )
        assert segmenter.validate_article(short_content_article) is False

        # 文章长度接近最大段落长度
        short_article = NewsArticle(
            id="short-article",
            title="Short Article",
            content="This article is not much longer than the maximum section length.",
            source="Test"
        )
        assert segmenter.validate_article(short_article) is False

    def test_update_config(self):
        """测试配置更新"""
        config = SectionConfig()
        llm_connector = Mock(spec=LLMConnector)
        segmenter = ContentSegmenter(llm_connector, config)

        new_config = SectionConfig(
            enable_hierarchical_segmentation=False,
            max_section_length=500,
            min_section_length=75
        )

        segmenter.update_config(new_config)
        assert segmenter.config.enable_hierarchical_segmentation is False
        assert segmenter.config.max_section_length == 500
        assert segmenter.config.min_section_length == 75


if __name__ == "__main__":
    pytest.main([__file__])