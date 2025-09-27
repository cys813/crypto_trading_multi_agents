"""
Main report generator class
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json
import logging

from .models import (
    AnalysisReport,
    ReportConfig,
    AnalysisRequest,
    ReportFormat,
    ReportType,
    MarketDataPoint
)
from .template_engine import TemplateEngine
from .report_analyzer import ReportAnalyzer
from .report_visualizer import ReportVisualizer
from .strategy_advisor import StrategyAdvisor
from .risk_reward_analyzer import RiskRewardAnalyzer

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Main report generator class"""

    def __init__(self, config: ReportConfig = None):
        """
        Initialize report generator

        Args:
            config: Report generation configuration
        """
        self.config = config or ReportConfig()
        self.template_engine = TemplateEngine()
        self.analyzer = ReportAnalyzer()
        self.visualizer = ReportVisualizer()
        self.strategy_advisor = StrategyAdvisor()
        self.risk_reward_analyzer = RiskRewardAnalyzer()

        # Performance tracking
        self.generation_stats = {
            'total_reports': 0,
            'average_generation_time': 0,
            'last_generation_time': None,
            'reports_by_type': {},
            'errors': 0
        }

    async def generate_report(self, analysis_request: AnalysisRequest) -> AnalysisReport:
        """
        Generate a single analysis report

        Args:
            analysis_request: Analysis request parameters

        Returns:
            Generated analysis report
        """
        start_time = datetime.now()
        report_id = str(uuid.uuid4())

        try:
            logger.info(f"Generating report {report_id} for {analysis_request.symbol}")

            # Collect analysis data
            analysis_data = await self._collect_analysis_data(analysis_request)

            # Perform analysis
            analyses = await self._perform_analysis(analysis_data)

            # Generate strategy recommendations
            strategy_recommendation = await self._generate_strategy_recommendation(
                analyses, analysis_request
            )

            # Perform risk-reward analysis
            risk_reward_analysis = await self._perform_risk_reward_analysis(
                strategy_recommendation, analysis_data
            )

            # Generate summary
            summary = self.analyzer.generate_summary(analyses)

            # Generate visualizations if requested
            charts = {}
            if self.config.include_charts:
                charts = await self._generate_charts(analysis_data, analyses)

            # Create report
            report = AnalysisReport(
                report_id=report_id,
                symbol=analysis_request.symbol,
                report_type=analysis_request.report_type,
                generated_at=datetime.now(timezone.utc),
                market_data=analysis_data.get('market_data', []),
                technical_analysis=analyses.get('technical_analysis'),
                fundamental_analysis=analyses.get('fundamental_analysis'),
                sentiment_analysis=analyses.get('sentiment_analysis'),
                strategy_recommendation=strategy_recommendation,
                risk_reward_analysis=risk_reward_analysis,
                summary=summary,
                charts=charts,
                metadata={
                    'request': analysis_request.dict(),
                    'generation_time': (datetime.now() - start_time).total_seconds(),
                    'model_version': '1.0.0'
                }
            )

            # Update performance stats
            self._update_performance_stats(report, start_time)

            logger.info(f"Successfully generated report {report_id}")
            return report

        except Exception as e:
            logger.error(f"Error generating report {report_id}: {e}")
            self.generation_stats['errors'] += 1
            raise

    async def generate_batch_reports(self, analysis_requests: List[AnalysisRequest]) -> List[AnalysisReport]:
        """
        Generate multiple reports in batch

        Args:
            analysis_requests: List of analysis requests

        Returns:
            List of generated reports
        """
        logger.info(f"Generating batch reports for {len(analysis_requests)} symbols")

        # Generate reports concurrently
        tasks = [self.generate_report(request) for request in analysis_requests]
        reports = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        successful_reports = []
        for i, result in enumerate(reports):
            if isinstance(result, Exception):
                logger.error(f"Error generating report for {analysis_requests[i].symbol}: {result}")
            else:
                successful_reports.append(result)

        logger.info(f"Successfully generated {len(successful_reports)} out of {len(analysis_requests)} reports")
        return successful_reports

    async def export_report(self, report: AnalysisReport, format: ReportFormat = None) -> str:
        """
        Export report to specified format

        Args:
            report: Analysis report to export
            format: Output format (uses config default if not specified)

        Returns:
            Exported report content as string
        """
        output_format = format or self.config.output_format

        try:
            if output_format == ReportFormat.JSON:
                return await self._export_to_json(report)
            elif output_format == ReportFormat.HTML:
                return await self._export_to_html(report)
            elif output_format == ReportFormat.MARKDOWN:
                return await self._export_to_markdown(report)
            elif output_format == ReportFormat.PDF:
                return await self._export_to_pdf(report)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

        except Exception as e:
            logger.error(f"Error exporting report {report.report_id} to {output_format}: {e}")
            raise

    async def _collect_analysis_data(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Collect analysis data from various sources"""
        # This would typically involve calling data collection services
        # For now, we'll return mock data structure
        return {
            'market_data': await self._get_market_data(request),
            'technical_data': await self._get_technical_data(request),
            'fundamental_data': await self._get_fundamental_data(request),
            'sentiment_data': await self._get_sentiment_data(request),
            'news_data': await self._get_news_data(request)
        }

    async def _get_market_data(self, request: AnalysisRequest) -> List[MarketDataPoint]:
        """Get market data for analysis"""
        # Mock implementation - would call actual data source
        return []

    async def _get_technical_data(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Get technical indicator data"""
        # Mock implementation - would call technical analysis service
        return {}

    async def _get_fundamental_data(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Get fundamental data"""
        # Mock implementation - would call fundamental analysis service
        return {}

    async def _get_sentiment_data(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Get sentiment analysis data"""
        # Mock implementation - would call sentiment analysis service
        return {}

    async def _get_news_data(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Get news data"""
        # Mock implementation - would call news collection service
        return {}

    async def _perform_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform various types of analysis"""
        analyses = {}

        # Technical analysis
        if analysis_data.get('technical_data'):
            analyses['technical_analysis'] = self.analyzer.analyze_technical_indicators(
                analysis_data['technical_data']
            )

        # Fundamental analysis
        if analysis_data.get('fundamental_data'):
            analyses['fundamental_analysis'] = self.analyzer.analyze_fundamental_data(
                analysis_data['fundamental_data']
            )

        # Sentiment analysis
        if analysis_data.get('sentiment_data'):
            analyses['sentiment_analysis'] = self.analyzer.analyze_sentiment_data(
                analysis_data['sentiment_data']
            )

        return analyses

    async def _generate_strategy_recommendation(self, analyses: Dict[str, Any], request: AnalysisRequest):
        """Generate strategy recommendations"""
        return await self.strategy_advisor.generate_recommendation(
            analyses, request.symbol, request.custom_parameters
        )

    async def _perform_risk_reward_analysis(self, strategy_recommendation, analysis_data: Dict[str, Any]):
        """Perform risk-reward analysis"""
        return await self.risk_reward_analyzer.analyze(
            strategy_recommendation, analysis_data
        )

    async def _generate_charts(self, analysis_data: Dict[str, Any], analyses: Dict[str, Any]) -> Dict[str, str]:
        """Generate visualization charts"""
        charts = {}

        try:
            # Technical analysis charts
            if analyses.get('technical_analysis'):
                charts['technical'] = await self.visualizer.generate_technical_chart(
                    analyses['technical_analysis']
                )

            # Market data charts
            if analysis_data.get('market_data'):
                charts['market_data'] = await self.visualizer.generate_market_data_chart(
                    analysis_data['market_data']
                )

            # Sentiment charts
            if analyses.get('sentiment_analysis'):
                charts['sentiment'] = await self.visualizer.generate_sentiment_chart(
                    analyses['sentiment_analysis']
                )

        except Exception as e:
            logger.error(f"Error generating charts: {e}")

        return charts

    async def _export_to_json(self, report: AnalysisReport) -> str:
        """Export report to JSON format"""
        # Convert report to serializable format
        report_dict = report.dict()

        # Handle datetime objects
        def datetime_converter(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(report_dict, indent=2, default=datetime_converter, ensure_ascii=False)

    async def _export_to_html(self, report: AnalysisReport) -> str:
        """Export report to HTML format"""
        # Prepare template context
        context = {
            'symbol': report.symbol,
            'generated_time': report.generated_at,
            'model_version': report.metadata.get('model_version', '1.0.0'),
            'technical_analysis': report.technical_analysis,
            'fundamental_analysis': report.fundamental_analysis,
            'sentiment_analysis': report.sentiment_analysis,
            'strategy_recommendation': report.strategy_recommendation,
            'risk_reward_analysis': report.risk_reward_analysis,
            'summary': report.summary,
            'charts': report.charts
        }

        # Render template
        template_name = self.config.template_name
        return self.template_engine.render_template(template_name, context)

    async def _export_to_markdown(self, report: AnalysisReport) -> str:
        """Export report to Markdown format"""
        markdown_lines = [
            f"# 做多分析报告 - {report.symbol}",
            "",
            f"**生成时间:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**分析模型版本:** {report.metadata.get('model_version', '1.0.0')}",
            ""
        ]

        # Add summary
        if report.summary:
            markdown_lines.extend([
                "## 执行摘要",
                "",
                f"- **信号强度:** {report.summary.signal_strength.overall_score}/10",
                f"- **置信度:** {report.summary.confidence_score:.1%}",
                ""
            ])

            if report.summary.key_findings:
                markdown_lines.extend([
                    "### 主要发现",
                    ""
                ])
                for finding in report.summary.key_findings:
                    markdown_lines.append(f"- {finding}")
                markdown_lines.append("")

        # Add technical analysis
        if report.technical_analysis:
            markdown_lines.extend([
                "## 技术面分析",
                "",
                f"**趋势:** {report.technical_analysis.trend}",
                f"**动量:** {report.technical_analysis.momentum}",
                f"**波动率:** {report.technical_analysis.volatility:.2%}",
                ""
            ])

            if report.technical_analysis.support_levels:
                markdown_lines.append(f"**支撑位:** {', '.join(map(str, report.technical_analysis.support_levels))}")

            if report.technical_analysis.resistance_levels:
                markdown_lines.append(f"**阻力位:** {', '.join(map(str, report.technical_analysis.resistance_levels))}")

            markdown_lines.append("")

        # Add fundamental analysis
        if report.fundamental_analysis:
            markdown_lines.extend([
                "## 基本面分析",
                "",
                f"- **市值:** ${report.fundamental_analysis.market_cap:,.0f}",
                f"- **24小时成交量:** ${report.fundamental_analysis.volume_24h:,.0f}",
                f"- **24小时涨跌:** {report.fundamental_analysis.price_change_24h:.2%}",
                f"- **市场占有率:** {report.fundamental_analysis.market_dominance:.2%}",
                ""
            ])

        # Add sentiment analysis
        if report.sentiment_analysis:
            markdown_lines.extend([
                "## 市场情绪分析",
                "",
                f"- **整体情绪:** {report.sentiment_analysis.overall_sentiment}",
                f"- **新闻情绪:** {report.sentiment_analysis.news_sentiment:.2%}",
                f"- **社交媒体情绪:** {report.sentiment_analysis.social_sentiment:.2%}",
                f"- **市场情绪:** {report.sentiment_analysis.market_sentiment:.2%}",
                f"- **置信度:** {report.sentiment_analysis.confidence:.2%}",
                ""
            ])

        # Add strategy recommendation
        if report.strategy_recommendation:
            markdown_lines.extend([
                "## 策略建议",
                "",
                f"**操作建议:** {report.strategy_recommendation.action}",
                "",
                "### 入场建议",
                f"- **建议价格:** ${report.strategy_recommendation.entry_recommendation.price}",
                f"- **入场时机:** {report.strategy_recommendation.entry_recommendation.timing}",
                f"- **置信度:** {report.strategy_recommendation.entry_recommendation.confidence}",
                "",
                "### 风险管理",
                f"- **止损价格:** ${report.strategy_recommendation.risk_management.stop_loss}",
                f"- **止盈目标:** {', '.join(map(str, report.strategy_recommendation.risk_management.take_profit_levels))}",
                f"- **建议仓位:** {report.strategy_recommendation.risk_management.position_size:.1%}",
                f"- **风险收益比:** {report.strategy_recommendation.risk_management.risk_reward_ratio}",
                ""
            ])

            if report.strategy_recommendation.reasoning:
                markdown_lines.extend([
                    "### 主要理由",
                    ""
                ])
                for reason in report.strategy_recommendation.reasoning:
                    markdown_lines.append(f"- {reason}")
                markdown_lines.append("")

        # Add risk-reward analysis
        if report.risk_reward_analysis:
            markdown_lines.extend([
                "## 风险收益分析",
                "",
                f"- **预期收益:** {report.risk_reward_analysis.expected_return:.2%}",
                f"- **最大回撤:** {report.risk_reward_analysis.max_drawdown:.2%}",
                f"- **夏普比率:** {report.risk_reward_analysis.sharpe_ratio:.2f}",
                f"- **胜率概率:** {report.risk_reward_analysis.win_probability:.2%}",
                f"- **风险收益比:** {report.risk_reward_analysis.risk_reward_ratio}",
                ""
            ])

        # Add disclaimer
        markdown_lines.extend([
            "## 免责声明",
            "",
            "本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。"
        ])

        return "\n".join(markdown_lines)

    async def _export_to_pdf(self, report: AnalysisReport) -> str:
        """Export report to PDF format"""
        # For now, we'll return HTML content that can be converted to PDF
        # In a real implementation, this would use a PDF generation library
        html_content = await self._export_to_html(report)
        return f"PDF export not implemented yet. HTML content:\n{html_content}"

    def _update_performance_stats(self, report: AnalysisReport, start_time: datetime):
        """Update performance statistics"""
        generation_time = (datetime.now() - start_time).total_seconds()

        self.generation_stats['total_reports'] += 1
        self.generation_stats['last_generation_time'] = generation_time

        # Update average generation time
        total_time = (self.generation_stats['average_generation_time'] *
                     (self.generation_stats['total_reports'] - 1) + generation_time)
        self.generation_stats['average_generation_time'] = total_time / self.generation_stats['total_reports']

        # Update reports by type
        report_type = report.report_type.value
        if report_type not in self.generation_stats['reports_by_type']:
            self.generation_stats['reports_by_type'][report_type] = 0
        self.generation_stats['reports_by_type'][report_type] += 1

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.generation_stats.copy()

    def reset_performance_stats(self):
        """Reset performance statistics"""
        self.generation_stats = {
            'total_reports': 0,
            'average_generation_time': 0,
            'last_generation_time': None,
            'reports_by_type': {},
            'errors': 0
        }