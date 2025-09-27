"""
Example usage of the reporting system
"""

import asyncio
import json
from datetime import datetime, timedelta
from src.long_analyst.reporting import (
    ReportGenerator,
    ReportConfig,
    AnalysisRequest,
    ReportFormat,
    ReportType
)
from src.long_analyst.reporting.models import (
    MarketDataPoint,
    TechnicalIndicator,
    TechnicalAnalysis,
    FundamentalAnalysis,
    SentimentAnalysis
)


async def reporting_example():
    """Example of using the reporting system"""
    print("=== Reporting System Example ===")

    # Create report generator
    config = ReportConfig(
        report_type=ReportType.STANDARD,
        output_format=ReportFormat.HTML,
        include_charts=True,
        template_name="standard"
    )
    generator = ReportGenerator(config)

    # Create analysis request
    request = AnalysisRequest(
        symbol="BTCUSDT",
        report_type=ReportType.STANDARD,
        timeframe="1h",
        lookback_period=100,
        include_technical=True,
        include_fundamental=True,
        include_sentiment=True
    )

    try:
        # Generate a single report
        print("Generating single report...")
        report = await generator.generate_report(request)
        print(f"Report generated: {report.report_id}")
        print(f"Symbol: {report.symbol}")
        print(f"Generated at: {report.generated_at}")
        print(f"Report type: {report.report_type}")

        # Export report to different formats
        print("\nExporting reports...")
        json_report = await generator.export_report(report, ReportFormat.JSON)
        html_report = await generator.export_report(report, ReportFormat.HTML)
        markdown_report = await generator.export_report(report, ReportFormat.MARKDOWN)

        print(f"JSON report length: {len(json_report)} characters")
        print(f"HTML report length: {len(html_report)} characters")
        print(f"Markdown report length: {len(markdown_report)} characters")

        # Save HTML report to file
        with open("example_report.html", "w", encoding="utf-8") as f:
            f.write(html_report)
        print("HTML report saved to example_report.html")

        # Generate batch reports
        print("\nGenerating batch reports...")
        requests = [
            AnalysisRequest(symbol="BTCUSDT", report_type=ReportType.STANDARD),
            AnalysisRequest(symbol="ETHUSDT", report_type=ReportType.QUICK_DECISION),
            AnalysisRequest(symbol="BNBUSDT", report_type=ReportType.TECHNICAL)
        ]

        batch_reports = await generator.generate_batch_reports(requests)
        print(f"Generated {len(batch_reports)} batch reports")

        for i, batch_report in enumerate(batch_reports):
            print(f"  {i+1}. {batch_report.symbol} - {batch_report.report_type}")

        # Get performance statistics
        print("\nPerformance Statistics:")
        stats = generator.get_performance_stats()
        print(json.dumps(stats, indent=2))

    except Exception as e:
        print(f"Error generating reports: {e}")


async def template_example():
    """Example of using template system"""
    print("\n=== Template System Example ===")

    from src.long_analyst.reporting import TemplateEngine

    # Create template engine
    engine = TemplateEngine()

    # List available templates
    templates = engine.list_templates()
    print(f"Available templates: {templates}")

    # Get template configuration
    config = engine.get_template_config("standard")
    print(f"\nStandard template config:")
    print(f"  Name: {config.name}")
    print(f"  Description: {config.description}")
    print(f"  Variables: {config.variables}")

    # Render template
    context = {
        'symbol': 'BTCUSDT',
        'generated_time': datetime.now(),
        'model_version': '1.0.0',
        'technical_analysis': TechnicalAnalysis(
            trend="UPTREND",
            key_indicators=[
                TechnicalIndicator(
                    name="RSI",
                    value=45.0,
                    signal="BUY",
                    confidence=0.7,
                    timestamp=datetime.now()
                )
            ],
            support_levels=[45000, 44000],
            resistance_levels=[52000, 53000],
            momentum="BULLISH",
            volatility=0.2
        ),
        'summary': {
            'signal_strength': {'overall_score': 7.5},
            'key_findings': ['Technical trend is bullish'],
            'confidence_score': 0.85
        }
    }

    rendered = engine.render_template("standard", context)
    print(f"\nRendered template length: {len(rendered)} characters")


async def strategy_advisor_example():
    """Example of using strategy advisor"""
    print("\n=== Strategy Advisor Example ===")

    from src.long_analyst.reporting import StrategyAdvisor

    advisor = StrategyAdvisor()

    # Mock analysis data
    analyses = {
        'technical_analysis': {
            'key_indicators': [
                {'signal': 'BUY', 'confidence': 0.8},
                {'signal': 'BUY', 'confidence': 0.7},
                {'signal': 'HOLD', 'confidence': 0.5}
            ],
            'trend': 'UPTREND',
            'momentum': 'BULLISH',
            'volatility': 0.2
        },
        'sentiment_analysis': {
            'overall_sentiment': 'BULLISH',
            'news_sentiment': 0.6,
            'social_sentiment': 0.4,
            'market_sentiment': 0.7,
            'confidence': 0.8
        },
        'fundamental_analysis': {
            'price_change_24h': 0.05,
            'volume_24h': 50000000,
            'market_cap': 1000000000
        }
    }

    # Generate recommendation
    recommendation = await advisor.generate_recommendation(analyses, "BTCUSDT")

    print(f"Strategy Recommendation for {recommendation.symbol}:")
    print(f"  Action: {recommendation.action}")
    print(f"  Entry Price: ${recommendation.entry_recommendation.price:,.2f}")
    print(f"  Stop Loss: ${recommendation.risk_management.stop_loss:,.2f}")
    print(f"  Take Profit: ${recommendation.risk_management.take_profit_levels[0]:,.2f}")
    print(f"  Risk-Reward Ratio: {recommendation.risk_management.risk_reward_ratio:.2f}")
    print(f"  Expected Win Rate: {recommendation.expected_win_rate:.1%}")
    print(f"  Confidence: {recommendation.confidence}")
    print(f"  Time Horizon: {recommendation.time_horizon}")
    print(f"  Reasoning: {recommendation.reasoning}")


async def risk_reward_analyzer_example():
    """Example of using risk-reward analyzer"""
    print("\n=== Risk-Reward Analyzer Example ===")

    from src.long_analyst.reporting import RiskRewardAnalyzer
    from src.long_analyst.reporting.models import StrategyRecommendation, EntryRecommendation, RiskManagement

    analyzer = RiskRewardAnalyzer()

    # Create sample strategy recommendation
    strategy = StrategyRecommendation(
        action="BUY",
        symbol="BTCUSDT",
        entry_recommendation=EntryRecommendation(
            price=50000.0,
            timing="Immediate",
            confidence="HIGH",
            reasoning=["Technical indicators support buy"],
            risk_level="MEDIUM"
        ),
        risk_management=RiskManagement(
            stop_loss=45000.0,
            take_profit_levels=[55000.0, 60000.0, 70000.0],
            position_size=0.05,
            risk_per_trade=0.02,
            risk_reward_ratio=2.0
        ),
        expected_win_rate=0.6,
        time_horizon="Medium",
        confidence="HIGH"
    )

    # Analyze risk-reward
    analysis_data = {
        'technical_analysis': {'volatility': 0.2},
        'sentiment_analysis': {
            'news_sentiment': 0.3,
            'social_sentiment': 0.2,
            'market_sentiment': 0.4
        }
    }

    analysis = await analyzer.analyze(strategy, analysis_data)

    print("Risk-Reward Analysis:")
    print(f"  Expected Return: {analysis.expected_return:.2%}")
    print(f"  Max Drawdown: {analysis.max_drawdown:.2%}")
    print(f"  Sharpe Ratio: {analysis.sharpe_ratio:.2f}")
    print(f"  Win Probability: {analysis.win_probability:.2%}")
    print(f"  Risk-Reward Ratio: {analysis.risk_reward_ratio:.2f}")
    print(f"  Breakeven Points: {[f'${x:,.2f}' for x in analysis.breakeven_points]}")

    print("\nSensitivity Analysis:")
    for param, sensitivity in analysis.sensitivity_analysis.items():
        print(f"  {param}: {sensitivity:.4f}")


async def main():
    """Run all examples"""
    await reporting_example()
    await template_example()
    await strategy_advisor_example()
    await risk_reward_analyzer_example()

    print("\n=== All Examples Completed ===")


if __name__ == "__main__":
    asyncio.run(main())