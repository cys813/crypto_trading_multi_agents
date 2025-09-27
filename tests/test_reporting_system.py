"""
Tests for the reporting system
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.long_analyst.reporting import (
    ReportGenerator,
    TemplateEngine,
    ReportAnalyzer,
    ReportVisualizer,
    StrategyAdvisor,
    RiskRewardAnalyzer,
    AnalysisReport,
    ReportConfig,
    AnalysisRequest,
    ReportFormat,
    ReportType,
    StrategyRecommendation,
    RiskRewardAnalysis
)


class TestReportGenerator:
    """Test cases for ReportGenerator"""

    @pytest.fixture
    def report_generator(self):
        """Create a ReportGenerator instance for testing"""
        config = ReportConfig()
        return ReportGenerator(config)

    @pytest.fixture
    def sample_analysis_request(self):
        """Create a sample analysis request"""
        return AnalysisRequest(
            symbol="BTCUSDT",
            report_type=ReportType.STANDARD,
            timeframe="1h",
            lookback_period=100
        )

    @pytest.mark.asyncio
    async def test_generate_report(self, report_generator, sample_analysis_request):
        """Test report generation"""
        # Mock data collection methods
        with patch.object(report_generator, '_collect_analysis_data') as mock_collect:
            with patch.object(report_generator, '_perform_analysis') as mock_analyze:
                with patch.object(report_generator, '_generate_strategy_recommendation') as mock_strategy:
                    with patch.object(report_generator, '_perform_risk_reward_analysis') as mock_risk:
                        with patch.object(report_generator, '_generate_charts') as mock_charts:

                            # Setup mock responses
                            mock_collect.return_value = {
                                'market_data': [],
                                'technical_data': {},
                                'fundamental_data': {},
                                'sentiment_data': {},
                                'news_data': {}
                            }
                            mock_analyze.return_value = {}
                            mock_strategy.return_value = None
                            mock_risk.return_value = None
                            mock_charts.return_value = {}

                            # Generate report
                            report = await report_generator.generate_report(sample_analysis_request)

                            # Assertions
                            assert report.symbol == "BTCUSDT"
                            assert report.report_type == ReportType.STANDARD
                            assert report.generated_at is not None
                            assert report.report_id is not None

    @pytest.mark.asyncio
    async def test_generate_batch_reports(self, report_generator):
        """Test batch report generation"""
        requests = [
            AnalysisRequest(symbol="BTCUSDT", report_type=ReportType.STANDARD),
            AnalysisRequest(symbol="ETHUSDT", report_type=ReportType.QUICK_DECISION)
        ]

        with patch.object(report_generator, 'generate_report') as mock_generate:
            mock_generate.side_effect = [
                AnalysisReport(
                    report_id="1",
                    symbol="BTCUSDT",
                    report_type=ReportType.STANDARD,
                    generated_at=datetime.now()
                ),
                AnalysisReport(
                    report_id="2",
                    symbol="ETHUSDT",
                    report_type=ReportType.QUICK_DECISION,
                    generated_at=datetime.now()
                )
            ]

            reports = await report_generator.generate_batch_reports(requests)

            assert len(reports) == 2
            assert reports[0].symbol == "BTCUSDT"
            assert reports[1].symbol == "ETHUSDT"

    @pytest.mark.asyncio
    async def test_export_report_json(self, report_generator):
        """Test JSON report export"""
        report = AnalysisReport(
            report_id="test",
            symbol="BTCUSDT",
            report_type=ReportType.STANDARD,
            generated_at=datetime.now()
        )

        json_output = await report_generator.export_report(report, ReportFormat.JSON)

        assert '"report_id": "test"' in json_output
        assert '"symbol": "BTCUSDT"' in json_output

    def test_get_performance_stats(self, report_generator):
        """Test performance statistics tracking"""
        stats = report_generator.get_performance_stats()

        assert 'total_reports' in stats
        assert 'average_generation_time' in stats
        assert 'errors' in stats
        assert stats['total_reports'] == 0


class TestTemplateEngine:
    """Test cases for TemplateEngine"""

    @pytest.fixture
    def template_engine(self):
        """Create a TemplateEngine instance"""
        return TemplateEngine()

    def test_list_templates(self, template_engine):
        """Test template listing"""
        templates = template_engine.list_templates()

        assert isinstance(templates, list)
        assert 'standard' in templates
        assert 'quick_decision' in templates

    def test_get_template_config(self, template_engine):
        """Test getting template configuration"""
        config = template_engine.get_template_config('standard')

        assert config.name == 'standard'
        assert config.description is not None
        assert len(config.variables) > 0

    def test_render_template(self, template_engine):
        """Test template rendering"""
        context = {
            'symbol': 'BTCUSDT',
            'generated_time': datetime.now(),
            'model_version': '1.0.0'
        }

        rendered = template_engine.render_template('standard', context)

        assert isinstance(rendered, str)
        assert 'BTCUSDT' in rendered


class TestReportAnalyzer:
    """Test cases for ReportAnalyzer"""

    @pytest.fixture
    def report_analyzer(self):
        """Create a ReportAnalyzer instance"""
        return ReportAnalyzer()

    def test_analyze_technical_indicators(self, report_analyzer):
        """Test technical indicator analysis"""
        technical_data = {
            'rsi': 25.0,
            'macd': {'macd': 0.5, 'signal': 0.3},
            'bollinger': {'position': -0.8},
            'moving_averages': {'spread': 0.03},
            'volume': {'volume_ratio': 1.8},
            'stochastic': {'k': 15, 'd': 20},
            'williams': {'williams_r': -85},
            'volatility': 0.25
        }

        analysis = report_analyzer.analyze_technical_indicators(technical_data)

        assert analysis.trend is not None
        assert len(analysis.key_indicators) > 0
        assert analysis.volatility == 0.25

    def test_analyze_fundamental_data(self, report_analyzer):
        """Test fundamental data analysis"""
        fundamental_data = {
            'market_cap': 1000000000,
            'volume_24h': 50000000,
            'price_change_24h': 0.05,
            'market_dominance': 0.45
        }

        analysis = report_analyzer.analyze_fundamental_data(fundamental_data)

        assert analysis.market_cap == 1000000000
        assert analysis.volume_24h == 50000000
        assert analysis.price_change_24h == 0.05

    def test_analyze_sentiment_data(self, report_analyzer):
        """Test sentiment data analysis"""
        sentiment_data = {
            'news_sentiment': 0.6,
            'social_sentiment': 0.4,
            'market_sentiment': 0.7,
            'confidence': 0.8
        }

        analysis = report_analyzer.analyze_sentiment_data(sentiment_data)

        assert analysis.news_sentiment == 0.6
        assert analysis.social_sentiment == 0.4
        assert analysis.market_sentiment == 0.7
        assert analysis.confidence == 0.8

    def test_generate_summary(self, report_analyzer):
        """Test summary generation"""
        analyses = {
            'technical_analysis': Mock(key_indicators=[Mock(signal="BUY", confidence=0.8)]),
            'sentiment_analysis': Mock(overall_sentiment="BULLISH", news_sentiment=0.6)
        }

        with patch.object(report_analyzer, '_calculate_signal_strength') as mock_signal:
            with patch.object(report_analyzer, '_extract_key_findings') as mock_findings:
                with patch.object(report_analyzer, '_generate_main_recommendations') as mock_recs:
                    with patch.object(report_analyzer, '_identify_primary_risks') as mock_risks:
                        with patch.object(report_analyzer, '_generate_overall_assessment') as mock_assessment:
                            with patch.object(report_analyzer, '_calculate_confidence_score') as mock_confidence:

                                mock_signal.return_value = Mock(overall_score=7.5)
                                mock_findings.return_value = ["Finding 1"]
                                mock_recs.return_value = ["Recommendation 1"]
                                mock_risks.return_value = ["Risk 1"]
                                mock_assessment.return_value = "Good"
                                mock_confidence.return_value = 0.85

                                summary = report_analyzer.generate_summary(analyses)

                                assert summary is not None
                                assert len(summary.key_findings) == 1


class TestStrategyAdvisor:
    """Test cases for StrategyAdvisor"""

    @pytest.fixture
    def strategy_advisor(self):
        """Create a StrategyAdvisor instance"""
        return StrategyAdvisor()

    @pytest.mark.asyncio
    async def test_generate_recommendation(self, strategy_advisor):
        """Test strategy recommendation generation"""
        analyses = {
            'technical_analysis': Mock(key_indicators=[Mock(signal="BUY", confidence=0.8)]),
            'sentiment_analysis': Mock(overall_sentiment="BULLISH"),
            'fundamental_analysis': Mock(price_change_24h=0.05)
        }

        with patch.object(strategy_advisor, '_generate_entry_recommendation') as mock_entry:
            with patch.object(strategy_advisor, '_generate_risk_management') as mock_risk:
                with patch.object(strategy_advisor, '_generate_reasoning') as mock_reasoning:

                    mock_entry.return_value = Mock(price=50000, confidence="HIGH")
                    mock_risk.return_value = Mock(stop_loss=45000, take_profit_levels=[55000])
                    mock_reasoning.return_value = ["Technical trend is bullish"]

                    recommendation = await strategy_advisor.generate_recommendation(analyses, "BTCUSDT")

                    assert recommendation.symbol == "BTCUSDT"
                    assert recommendation.action in ["BUY", "SELL", "HOLD"]

    def test_determine_action(self, strategy_advisor):
        """Test action determination"""
        analyses = {
            'technical_analysis': Mock(key_indicators=[Mock(signal="BUY"), Mock(signal="BUY")]),
            'sentiment_analysis': Mock(overall_sentiment="BULLISH"),
            'fundamental_analysis': Mock(price_change_24h=0.05)
        }

        action = strategy_advisor._determine_action(analyses)

        assert action in ["BUY", "SELL", "HOLD"]

    def test_calculate_expected_win_rate(self, strategy_advisor):
        """Test expected win rate calculation"""
        analyses = {
            'technical_analysis': Mock(key_indicators=[Mock(signal="BUY"), Mock(signal="BUY")]),
            'sentiment_analysis': Mock(
                news_sentiment=0.6,
                social_sentiment=0.4,
                market_sentiment=0.7,
                confidence=0.8
            ),
            'fundamental_analysis': Mock(price_change_24h=0.05)
        }

        win_rate = strategy_advisor._calculate_expected_win_rate(analyses)

        assert 0 <= win_rate <= 1


class TestRiskRewardAnalyzer:
    """Test cases for RiskRewardAnalyzer"""

    @pytest.fixture
    def risk_reward_analyzer(self):
        """Create a RiskRewardAnalyzer instance"""
        return RiskRewardAnalyzer()

    @pytest.fixture
    def sample_strategy(self):
        """Create a sample strategy recommendation"""
        return StrategyRecommendation(
            action="BUY",
            symbol="BTCUSDT",
            entry_recommendation=Mock(price=50000),
            risk_management=Mock(stop_loss=45000, take_profit_levels=[55000], risk_reward_ratio=2.0),
            expected_win_rate=0.6
        )

    @pytest.mark.asyncio
    async def test_analyze(self, risk_reward_analyzer, sample_strategy):
        """Test risk-reward analysis"""
        analysis_data = {}

        analysis = await risk_reward_analyzer.analyze(sample_strategy, analysis_data)

        assert isinstance(analysis, RiskRewardAnalysis)
        assert analysis.expected_return is not None
        assert analysis.max_drawdown is not None
        assert analysis.win_probability is not None
        assert analysis.risk_reward_ratio == 2.0

    @pytest.mark.asyncio
    async def test_calculate_expected_return(self, risk_reward_analyzer, sample_strategy):
        """Test expected return calculation"""
        analysis_data = {
            'technical_analysis': Mock(volatility=0.2),
            'sentiment_analysis': Mock(
                news_sentiment=0.3,
                social_sentiment=0.2,
                market_sentiment=0.4
            )
        }

        expected_return = await risk_reward_analyzer._calculate_expected_return(sample_strategy, analysis_data)

        assert isinstance(expected_return, float)

    @pytest.mark.asyncio
    async def test_calculate_max_drawdown(self, risk_reward_analyzer, sample_strategy):
        """Test maximum drawdown calculation"""
        analysis_data = {
            'technical_analysis': Mock(volatility=0.2)
        }

        max_drawdown = await risk_reward_analyzer._calculate_max_drawdown(sample_strategy, analysis_data)

        assert isinstance(max_drawdown, float)
        assert 0 <= max_drawdown <= 1


class TestReportVisualizer:
    """Test cases for ReportVisualizer"""

    @pytest.fixture
    def report_visualizer(self):
        """Create a ReportVisualizer instance"""
        return ReportVisualizer()

    @pytest.mark.asyncio
    async def test_generate_technical_chart(self, report_visualizer):
        """Test technical chart generation"""
        technical_analysis = Mock(
            trend="UPTREND",
            momentum="BULLISH",
            volatility=0.2,
            key_indicators=[Mock(name="RSI", value=45.0, confidence=0.7)],
            support_levels=[45000, 44000],
            resistance_levels=[52000, 53000]
        )

        chart = await report_visualizer.generate_technical_chart(technical_analysis)

        assert isinstance(chart, str)
        assert chart.startswith("data:image/png;base64,")

    @pytest.mark.asyncio
    async def test_generate_risk_reward_chart(self, report_visualizer):
        """Test risk-reward chart generation"""
        chart = await report_visualizer.generate_risk_reward_chart(50000, 45000, 55000)

        assert isinstance(chart, str)
        assert chart.startswith("data:image/png;base64,")

    @pytest.mark.asyncio
    async def test_generate_interactive_dashboard(self, report_visualizer):
        """Test interactive dashboard generation"""
        technical_analysis = Mock()
        sentiment_analysis = Mock()
        market_data = []

        dashboard = await report_visualizer.generate_interactive_dashboard(technical_analysis, sentiment_analysis, market_data)

        assert isinstance(dashboard, str)
        assert "html" in dashboard.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])