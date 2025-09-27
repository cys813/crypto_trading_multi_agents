#!/usr/bin/env python3
"""
做空分析师代理使用示例

该文件展示了如何使用做空分析师代理进行做空分析。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# 导入做空分析师代理
from src.short_analyst import (
    ShortAnalystArchitecture,
    ShortAnalystConfig,
    AnalysisMode,
    ShortSignal,
    ShortSignalType,
    ShortSignalStrength,
    MarketData,
    OHLCV,
    Ticker,
    OrderBook,
    OrderBookLevel,
    TimeFrame,
    ShortAnalysisResult,
    AnalysisRecommendation
)

# 导入技术指标引擎
from src.short_analyst.indicators import ShortTechnicalIndicatorsEngine
from src.short_analyst.config import ConfigManager

# 导入智能信号识别系统
from src.short_analyst.signal_recognition import IntelligentSignalRecognition

# 导入LLM分析引擎
from src.short_analyst.llm_analysis import (
    LLMAnalysisEngine,
    LLMAnalysisInput,
    AnalysisType,
    RiskTolerance,
    TimeHorizon,
    SentimentPolarity
)

# 导入数据接收器
from src.short_analyst.data_flow import DataReceiver, MarketDataType, DataSource

# 导入配置管理
from src.short_analyst.config import initialize_config, get_config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_sample_market_data(symbol: str) -> MarketData:
    """创建示例市场数据"""
    # 创建OHLCV数据
    ohlcv = OHLCV(
        symbol=symbol,
        timestamp=datetime.now(),
        open=50000.0,
        high=50500.0,
        low=49500.0,
        close=49800.0,
        volume=1000000.0,
        timeframe=TimeFrame.ONE_HOUR
    )

    # 创建行情数据
    ticker = Ticker(
        symbol=symbol,
        timestamp=datetime.now(),
        last_price=49800.0,
        bid_price=49790.0,
        ask_price=49810.0,
        bid_volume=50000.0,
        ask_volume=48000.0
    )

    # 创建订单簿数据
    orderbook = OrderBook(
        symbol=symbol,
        timestamp=datetime.now(),
        bids=[
            OrderBookLevel(price=49790.0, volume=50000.0),
            OrderBookLevel(price=49780.0, volume=30000.0),
            OrderBookLevel(price=49770.0, volume=20000.0)
        ],
        asks=[
            OrderBookLevel(price=49810.0, volume=48000.0),
            OrderBookLevel(price=49820.0, volume=35000.0),
            OrderBookLevel(price=49830.0, volume=25000.0)
        ]
    )

    # 创建综合市场数据
    market_data = MarketData(
        symbol=symbol,
        timestamp=datetime.now(),
        ohlcv=ohlcv,
        ticker=ticker,
        orderbook=orderbook,
        volatility=0.02,  # 2%波动率
        trend_strength=-0.3,  # 轻微下跌趋势
        market_sentiment=-0.4,  # 略微看跌情绪
        data_quality_score=0.95,
        completeness_score=0.98,
        timeliness_score=0.99
    )

    return market_data


async def basic_analysis_example():
    """基础分析示例"""
    logger.info("=== 基础做空分析示例 ===")

    # 初始化配置
    config_manager = initialize_config()
    config = config_manager.get_config()

    # 创建做空分析师代理
    analyst = ShortAnalystArchitecture(config.core)

    try:
        # 启动分析师
        await analyst.start()

        # 创建示例市场数据
        market_data = await create_sample_market_data("BTC/USDT")

        # 执行做空分析
        logger.info("开始做空分析...")
        result = await analyst.analyze_short_opportunity(
            symbol="BTC/USDT",
            market_data=market_data,
            mode=AnalysisMode.REAL_TIME
        )

        # 输出分析结果
        logger.info(f"分析结果摘要:")
        logger.info(f"  交易对: {result.symbol}")
        logger.info(f"  综合评分: {result.overall_score:.2f}")
        logger.info(f"  建议: {result.recommendation.value}")
        logger.info(f"  置信度: {result.confidence_level:.2f}")
        logger.info(f"  信号数量: {len(result.signals)}")
        logger.info(f"  处理时间: {result.processing_time_ms:.2f}ms")

        # 输出信号详情
        if result.signals:
            logger.info("做空信号详情:")
            for signal in result.signals:
                logger.info(f"  - {signal.signal_type.value}: 强度={signal.strength.name}, 置信度={signal.confidence_score:.2f}")

        # 输出风险评估
        if result.risk_assessment:
            logger.info(f"风险评估:")
            logger.info(f"  整体风险等级: {result.risk_assessment.overall_risk_level.name}")
            logger.info(f"  轧空风险: {result.risk_assessment.short_squeeze_risk:.2f}")
            logger.info(f"  流动性风险: {result.risk_assessment.liquidity_risk:.2f}")

        return result

    finally:
        # 停止分析师
        await analyst.stop()


async def batch_analysis_example():
    """批量分析示例"""
    logger.info("=== 批量做空分析示例 ===")

    # 创建分析师
    analyst = ShortAnalystArchitecture()

    try:
        await analyst.start()

        # 创建多个交易对的市场数据
        symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT"]
        market_data_dict = {}

        for symbol in symbols:
            market_data_dict[symbol] = await create_sample_market_data(symbol)

        # 执行批量分析
        logger.info(f"开始批量分析 {len(symbols)} 个交易对...")
        results = await analyst.batch_analyze_symbols(symbols, market_data_dict)

        # 输出批量分析结果
        logger.info("批量分析结果:")
        for symbol, result in results.items():
            logger.info(f"  {symbol}: {result.recommendation.value} (评分: {result.overall_score:.2f})")

        # 统计分析结果
        strong_shorts = [r for r in results.values() if r.recommendation == AnalysisRecommendation.STRONG_SHORT]
        moderate_shorts = [r for r in results.values() if r.recommendation == AnalysisRecommendation.MODERATE_SHORT]

        logger.info(f"统计结果:")
        logger.info(f"  强烈做空: {len(strong_shorts)} 个")
        logger.info(f"  适度做空: {len(moderate_shorts)} 个")
        logger.info(f"  其他建议: {len(results) - len(strong_shorts) - len(moderate_shorts)} 个")

        return results

    finally:
        await analyst.stop()


async def system_status_example():
    """系统状态示例"""
    logger.info("=== 系统状态示例 ===")

    # 创建分析师
    analyst = ShortAnalystArchitecture()

    try:
        await analyst.start()

        # 获取系统状态
        status = analyst.get_system_status()

        logger.info("系统状态:")
        logger.info(f"  运行状态: {'运行中' if status['is_running'] else '已停止'}")
        logger.info(f"  活跃分析任务: {status['active_analysis_tasks']}")
        logger.info(f"  最大并发请求数: {status['config']['max_concurrent_requests']}")
        logger.info(f"  目标延迟: {status['config']['target_latency_ms']}ms")

        # 获取性能指标
        metrics = status['performance_metrics']
        if metrics:
            logger.info("性能指标:")
            logger.info(f"  平均延迟: {metrics.get('avg_latency_ms', 0):.2f}ms")
            logger.info(f"  请求总数: {metrics.get('total_requests', 0)}")
            logger.info(f"  错误率: {metrics.get('error_rate', 0):.2%}")

        # 健康检查
        is_healthy = await analyst.health_check()
        logger.info(f"健康状态: {'健康' if is_healthy else '不健康'}")

        return status

    finally:
        await analyst.stop()


async def configuration_example():
    """配置管理示例"""
    logger.info("=== 配置管理示例 ===")

    from src.short_analyst.config import get_config_manager

    # 获取配置管理器
    config_manager = get_config_manager()

    # 获取当前配置
    config = config_manager.get_config()
    logger.info("当前配置:")
    logger.info(f"  环境: {config.environment}")
    logger.info(f"  调试模式: {config.debug}")
    logger.info(f"  最大并发请求: {config.core.max_concurrent_requests}")

    # 获取配置摘要
    summary = config_manager.get_config_summary()
    logger.info("配置摘要:")
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")

    # 验证配置
    errors = config_manager.validate_config()
    if errors:
        logger.warning("配置验证发现问题:")
        for error in errors:
            logger.warning(f"  - {error}")
    else:
        logger.info("配置验证通过")


async def custom_analysis_example():
    """自定义分析示例"""
    logger.info("=== 自定义分析示例 ===")

    # 创建自定义配置
    custom_config = ShortAnalystConfig(
        max_concurrent_requests=500,
        target_latency_ms=1000,
        min_signal_strength=0.8,
        enable_llm_analysis=True,
        llm_temperature=0.2
    )

    # 创建分析师
    analyst = ShortAnalystArchitecture(custom_config)

    try:
        await analyst.start()

        # 创建市场数据
        market_data = await create_sample_market_data("BTC/USDT")

        # 使用自定义设置进行分析
        result = await analyst.analyze_short_opportunity(
            symbol="BTC/USDT",
            market_data=market_data,
            mode=AnalysisMode.REAL_TIME
        )

        logger.info(f"自定义分析结果:")
        logger.info(f"  配置: 最大并发={custom_config.max_concurrent_requests}, 信号强度阈值={custom_config.min_signal_strength}")
        logger.info(f"  结果: {result.recommendation.value} (评分: {result.overall_score:.2f})")

        return result

    finally:
        await analyst.stop()


async def main():
    """主函数"""
    logger.info("做空分析师代理使用示例")
    logger.info("=" * 50)

    try:
        # 基础分析示例
        await basic_analysis_example()
        logger.info("")

        # 批量分析示例
        await batch_analysis_example()
        logger.info("")

        # 系统状态示例
        await system_status_example()
        logger.info("")

        # 配置管理示例
        await configuration_example()
        logger.info("")

        # 自定义分析示例
        await custom_analysis_example()

        # 技术指标引擎示例
        await indicators_example()

        # 数据接收处理示例
        await data_processing_example()

        # 智能信号识别示例
        await signal_recognition_example()

        # LLM分析引擎示例
        await llm_analysis_example()
        logger.info("")

        # 胜率计算与风险评估示例
        await win_rate_calculation_example()

    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        raise


async def indicators_example():
    """技术指标引擎示例"""
    logger.info("=== 技术指标引擎示例 ===")

    config_manager = ConfigManager()
    engine = ShortTechnicalIndicatorsEngine(config_manager)

    # 创建市场数据
    market_data = MarketData(
        symbol="BTC/USDT",
        timestamp=datetime.now(),
        timeframe="1h",
        ohlcv=OHLCV(
            timestamps=[datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)],
            open_prices=[40000 + i * 100 for i in range(100)],
            high_prices=[40500 + i * 100 for i in range(100)],
            low_prices=[39500 + i * 100 for i in range(100)],
            close_prices=[40200 + i * 100 for i in range(100)],
            volumes=[1000000 + i * 10000 for i in range(100)]
        )
    )

    try:
        # 计算所有指标
        logger.info("正在计算所有技术指标...")
        results = await engine.calculate_all_indicators(market_data)
        logger.info(f"成功计算 {len(results)} 个技术指标")

        # 显示指标结果
        logger.info("=== 指标结果 ===")
        for result in results:
            logger.info(f"{result.name}: {result.value:.4f}")
            if result.signal_type:
                logger.info(f"  信号: {result.signal_type.value}")
                logger.info(f"  强度: {result.signal_strength.value if result.signal_strength else 'N/A'}")
                logger.info(f"  置信度: {result.confidence:.2f}")

        # 获取做空信号
        logger.info("=== 做空信号 ===")
        signals = await engine.get_short_signals(market_data)
        if signals:
            for signal in signals:
                logger.info(f"做空信号: {signal.signal_type.value}")
                logger.info(f"信号强度: {signal.signal_strength.value if signal.signal_strength else 'N/A'}")
                logger.info(f"置信度: {signal.confidence:.2f}")
        else:
            logger.info("当前未检测到做空信号")

        # 获取指标摘要
        logger.info("=== 指标摘要 ===")
        summary = engine.get_indicator_summary("BTC/USDT")
        logger.info(f"缓存指标数: {summary['cached_indicators']}")
        logger.info(f"最后更新: {summary['last_update']}")
        logger.info(f"信号数量: {len(summary['signals'])}")

        # 缓存统计
        logger.info("=== 缓存统计 ===")
        cache_stats = engine.get_cache_stats()
        logger.info(f"缓存条目: {cache_stats['total_cache_entries']}")
        logger.info(f"缓存大小: {cache_stats['cache_size_mb']:.2f} MB")
        logger.info(f"缓存币种: {cache_stats['symbols_cached']}")

    finally:
        await engine.close()


async def data_processing_example():
    """数据处理示例"""
    logger.info("=== 数据接收与处理示例 ===")

    config_manager = ConfigManager()
    data_receiver = DataReceiver(config_manager)

    # 创建原始市场数据
    raw_data = {
        'symbol': 'BTC/USDT',
        'timestamp': datetime.now().isoformat(),
        'ohlcv': {
            'open': 45000,
            'high': 45500,
            'low': 44800,
            'close': 45200,
            'volume': 1500000
        }
    }

    try:
        # 接收和处理数据
        data_id = await data_receiver.receive_data(
            raw_data=raw_data,
            data_type=MarketDataType.OHLCV,
            source=DataSource.EXCHANGE_API,
            symbol='BTC/USDT'
        )

        logger.info(f"数据处理完成，ID: {data_id}")

        # 获取数据质量评估
        quality = await data_receiver.assess_data_quality('BTC/USDT')
        logger.info(f"数据质量评分: {quality.overall_score:.2f}")

        # 获取处理统计
        stats = data_receiver.get_processing_stats()
        logger.info(f"总处理数据量: {stats['total_processed']}")
        logger.info(f"成功率: {stats['success_rate']:.2%}")

    finally:
        await data_receiver.close()


async def signal_recognition_example():
    """智能信号识别示例"""
    logger.info("=== 智能信号识别系统示例 ===")

    # 创建配置
    config_manager = ConfigManager()

    # 创建指标引擎
    indicator_engine = ShortTechnicalIndicatorsEngine(config_manager)

    # 创建信号识别系统
    signal_config = {
        'fusion_method': 'weighted_sum',
        'min_confidence_threshold': 0.6,
        'min_supporting_indicators': 1,
        'indicator_weights': {
            'MA_CROSSOVER': 0.3,
            'RSI_OVERBOUGHT': 0.25,
            'BOLLINGER_UPPER': 0.2,
            'VOLUME_DIVERGENCE': 0.15,
            'MACD_DIVERGENCE': 0.1
        }
    }

    signal_recognition = IntelligentSignalRecognition(indicator_engine, signal_config)

    # 创建市场数据
    market_data = MarketData(
        symbol="BTC/USDT",
        timestamp=datetime.now(),
        timeframe="1h",
        ohlcv=OHLCV(
            timestamps=[datetime.now() - timedelta(hours=i) for i in range(50, 0, -1)],
            open_prices=[45000 + i * 200 for i in range(50)],
            high_prices=[45200 + i * 200 for i in range(50)],
            low_prices=[44800 + i * 200 for i in range(50)],
            close_prices=[45100 + i * 200 for i in range(50)],
            volumes=[800000 + i * 20000 for i in range(50)]
        )
    )

    try:
        # 识别做空信号
        logger.info("正在识别智能做空信号...")
        signals = await signal_recognition.recognize_signals(market_data)

        logger.info(f"识别到 {len(signals)} 个融合信号")

        # 显示融合信号详情
        for i, signal in enumerate(signals, 1):
            logger.info(f"=== 融合信号 {i} ===")
            logger.info(f"信号ID: {signal.signal_id}")
            logger.info(f"信号类型: {signal.signal_type.value}")
            logger.info(f"信号强度: {signal.signal_strength.value}")
            logger.info(f"总体置信度: {signal.overall_confidence:.2f}")
            logger.info(f"融合方法: {signal.fusion_method.value}")
            logger.info(f"风险分数: {signal.risk_score:.2f}")
            logger.info(f"预期持续时间: {signal.expected_duration}")
            logger.info(f"支持指标: {', '.join(signal.supporting_indicators)}")

            if signal.conflicting_indicators:
                logger.info(f"冲突指标: {', '.join(signal.conflicting_indicators)}")

            logger.info("信号组成:")
            for component in signal.components:
                logger.info(f"  - {component.indicator_name}: 权重={component.weight:.2f}, "
                           f"置信度={component.confidence:.2f}")

            logger.info("")

        # 测试不同的融合方法
        logger.info("=== 测试不同融合方法 ===")

        fusion_methods = [
            SignalFusionMethod.WEIGHTED_SUM,
            SignalFusionMethod.CONSENSUS,
            SignalFusionMethod.HIERARCHICAL
        ]

        for method in fusion_methods:
            signal_recognition.fusion_config.fusion_method = method
            method_signals = await signal_recognition.recognize_signals(market_data)

            logger.info(f"{method.value} 方法: 识别到 {len(method_signals)} 个信号")
            for signal in method_signals:
                logger.info(f"  - {signal.signal_type.value}: "
                           f"置信度={signal.overall_confidence:.2f}, "
                           f"强度={signal.signal_strength.value}")

        # 信号历史和统计
        logger.info("=== 信号统计 ===")
        stats = signal_recognition.get_signal_statistics()
        logger.info(f"总信号数: {stats['performance_metrics']['total_signals']}")
        logger.info(f"平均置信度: {stats['performance_metrics']['avg_confidence']:.2f}")
        logger.info(f"缓存大小: {stats['cache_size']}")

        # 获取最近的信号
        recent_signals = signal_recognition.get_recent_signals(limit=5)
        logger.info(f"最近 {len(recent_signals)} 个信号:")
        for signal in recent_signals:
            logger.info(f"  - {signal.signal_id}: {signal.signal_type.value}")

    finally:
        await indicator_engine.close()


async def llm_analysis_example():
    """LLM分析引擎示例"""
    logger.info("=== LLM分析与推理引擎示例 ===")

    # 创建LLM分析引擎配置
    llm_config = {
        'provider': 'mock',
        'model': 'gpt-4',
        'max_tokens': 2000,
        'temperature': 0.3,
        'enable_cache': True,
        'cache_ttl': 300,
        'enable_context': True
    }

    llm_engine = LLMAnalysisEngine(llm_config)

    try:
        # 创建LLM分析输入
        logger.info("创建LLM分析输入...")

        # 模拟融合信号
        mock_signals = []
        for i in range(2):
            signal = MockFusionSignal(
                signal_type=MockShortSignalType.TREND_REVERSAL if i == 0 else MockShortSignalType.RSI_OVERBOUGHT,
                signal_strength=MockShortSignalStrength.MODERATE,
                overall_confidence=0.8 + i * 0.1,
                risk_score=0.3 + i * 0.2
            )
            signal.components = [MockSignalComponent(f"Indicator_{i}", 0.8 + i * 0.1)]
            mock_signals.append(signal)

        analysis_input = LLMAnalysisInput(
            symbol="BTC/USDT",
            current_price=45000.0,
            price_change_24h=-2.5,
            volume_24h=2500000000,
            market_cap=850000000000,
            fusion_signals=mock_signals,
            news_headlines=[
                "Bitcoin面临监管压力",
                "机构投资者开始减持",
                "技术指标显示超买信号",
                "市场波动率上升"
            ],
            social_media_sentiment=SentimentPolarity.BEARISH,
            fear_greed_index=72,
            market_conditions="高波动率",
            trend_context="短期下跌趋势",
            analysis_types=[
                AnalysisType.MARKET_SENTIMENT,
                AnalysisType.TECHNICAL_EXPLANATION,
                AnalysisType.RISK_ASSESSMENT,
                AnalysisType.TRADING_DECISION
            ],
            risk_tolerance=RiskTolerance.MODERATE,
            time_horizon=TimeHorizon.SHORT_TERM
        )

        # 执行LLM分析
        logger.info("执行LLM分析...")
        result = await llm_engine.analyze(analysis_input)

        # 显示分析结果
        logger.info(f"LLM分析完成 - {result.symbol}")
        logger.info(f"整体评分: {result.overall_score:.2f}")
        logger.info(f"置信度等级: {result.confidence.name}")

        # 市场情绪分析
        if result.market_sentiment:
            logger.info("=== 市场情绪分析 ===")
            logger.info(f"整体情绪: {result.market_sentiment.overall_sentiment.name}")
            logger.info(f"情绪分数: {result.market_sentiment.sentiment_score:.2f}")
            logger.info(f"情绪趋势: {result.market_sentiment.sentiment_trend}")
            logger.info(f"关键因素: {', '.join(result.market_sentiment.key_factors[:3])}")

        # 技术指标解释
        if result.technical_explanations:
            logger.info("=== 技术指标解释 ===")
            for i, explanation in enumerate(result.technical_explanations, 1):
                logger.info(f"指标 {i}: {explanation.indicator_name}")
                logger.info(f"解释: {explanation.interpretation}")
                logger.info(f"重要性: {explanation.significance}")
                logger.info(f"短期展望: {explanation.short_term_outlook}")

        # 风险评估
        if result.risk_assessment:
            logger.info("=== 风险评估 ===")
            logger.info(f"整体风险分数: {result.risk_assessment.overall_risk_score:.2f}")
            logger.info(f"风险等级: {result.risk_assessment.risk_level}")
            logger.info(f"轧空风险: {result.risk_assessment.short_squeeze_risk:.2f}")
            logger.info(f"建议仓位限制: {result.risk_assessment.position_size_limit:.1%}")

        # 交易决策
        if result.trading_decision:
            logger.info("=== 交易决策 ===")
            logger.info(f"建议动作: {result.trading_decision.action}")
            logger.info(f"信心等级: {result.trading_decision.conviction_level.name}")
            logger.info(f"建议仓位: {result.trading_decision.position_size:.1%}")
            logger.info(f"止损距离: {result.trading_decision.stop_loss_distance:.1%}")
            logger.info(f"风险收益比: {result.trading_decision.risk_reward_ratio:.2f}")
            logger.info(f"预计胜率: {result.trading_decision.win_probability:.1%}")

        # 关键洞察
        if result.key_insights:
            logger.info("=== 关键洞察 ===")
            for i, insight in enumerate(result.key_insights, 1):
                logger.info(f"{i}. {insight}")

        # 警告信号
        if result.warning_signals:
            logger.info("=== 警告信号 ===")
            for warning in result.warning_signals:
                logger.info(f"⚠️  {warning}")

        # 性能统计
        logger.info("=== 性能统计 ===")
        stats = llm_engine.get_performance_stats()
        logger.info(f"总分析次数: {stats['total_analyses']}")
        logger.info(f"成功率: {stats['success_rate']:.1%}")
        logger.info(f"平均处理时间: {stats['avg_processing_time']:.2f}s")
        logger.info(f"缓存大小: {stats['cache_size']}")
        logger.info(f"LLM提供商: {stats['provider']}")

        # 测试缓存机制
        logger.info("=== 测试缓存机制 ===")
        start_time = datetime.now()
        cached_result = await llm_engine.analyze(analysis_input)
        cache_time = (datetime.now() - start_time).total_seconds()

        logger.info(f"缓存分析时间: {cache_time:.3f}s")
        logger.info(f"结果相同: {result.overall_score == cached_result.overall_score}")

        # 测试不同分析类型组合
        logger.info("=== 测试不同分析类型 ===")
        test_types = [
            [AnalysisType.MARKET_SENTIMENT],
            [AnalysisType.TECHNICAL_EXPLANATION],
            [AnalysisType.RISK_ASSESSMENT],
            [AnalysisType.TRADING_DECISION],
            [AnalysisType.MARKET_SENTIMENT, AnalysisType.RISK_ASSESSMENT]
        ]

        for types in test_types:
            analysis_input.analysis_types = types
            partial_result = await llm_engine.analyze(analysis_input)
            type_names = [t.value for t in types]
            logger.info(f"{', '.join(type_names)}: 评分={partial_result.overall_score:.2f}")

    finally:
        # 清理资源
        llm_engine.clear_cache()
        llm_engine.clear_contexts()
        logger.info("LLM分析引擎资源已清理")


async def win_rate_calculation_example():
    """胜率计算与风险评估示例"""
    logger.info("=== 胜率计算与风险评估示例 ===")

    from src.short_analyst.win_rate_calculation import (
        WinRateCalculator, RiskAssessor, OptimizationEngine,
        WinRateMetric, TradeResult, MockShortSignalType, MockShortSignalStrength
    )
    from test_win_rate_simple import generate_mock_trade_history, generate_mock_signals

    # 生成模拟数据
    logger.info("生成模拟交易历史和信号数据...")
    trade_history = generate_mock_trade_history(100)
    signal_history = generate_mock_signals(30)

    # 1. 胜率计算分析
    logger.info("1. 执行胜率分析...")
    calculator = WinRateCalculator()

    win_rate_analysis = await calculator.calculate_win_rate(
        trade_history=trade_history,
        signal_history=signal_history,
        period="30d",
        metrics=[WinRateMetric.OVERALL_SUCCESS_RATE, WinRateMetric.SIGNAL_TYPE_SUCCESS]
    )

    logger.info(f"胜率分析结果:")
    logger.info(f"  总信号数: {win_rate_analysis.total_signals}")
    logger.info(f"  整体成功率: {win_rate_analysis.overall_success_rate:.2%}")
    logger.info(f"  置信区间: [{win_rate_analysis.confidence_interval[0]:.2%}, {win_rate_analysis.confidence_interval[1]:.2%}]")
    logger.info(f"  强度相关性: {win_rate_analysis.strength_correlation:.3f}")

    if win_rate_analysis.success_by_signal_type:
        logger.info("  信号类型成功率:")
        for signal_type, rate in win_rate_analysis.success_by_signal_type.items():
            logger.info(f"    {signal_type}: {rate:.2%}")

    # 2. 绩效指标计算
    logger.info("\n2. 计算绩效指标...")
    performance_metrics = await calculator.calculate_performance_metrics(
        trade_history=trade_history,
        period="60d",
        benchmark_return=0.05
    )

    logger.info(f"绩效指标:")
    logger.info(f"  总交易次数: {performance_metrics.total_trades}")
    logger.info(f"  胜率: {performance_metrics.win_rate:.2%}")
    logger.info(f"  盈亏比: {performance_metrics.profit_factor:.2f}")
    logger.info(f"  夏普比率: {performance_metrics.sharpe_ratio:.3f}")
    logger.info(f"  最大回撤: {performance_metrics.max_drawdown:.2%}")
    logger.info(f"  最大连续亏损: {performance_metrics.max_consecutive_losses}")

    # 3. 风险评估
    logger.info("\n3. 执行风险评估...")
    risk_assessor = RiskAssessor()

    market_data = {
        'volume_24h': 50000000,
        'market_cap': 850000000000,
        'correlation_with_btc': 0.8,
        'trend': 'uptrend',
        'volatility': 0.04,
        'funding_rate': 0.0001,
        'long_short_ratio': 2.5,
        'fear_greed_index': 65,
        'regulatory_news': []
    }

    risk_assessment = await risk_assessor.assess_risk(
        current_signals=signal_history[:10],  # 取前10个信号
        trade_history=trade_history,
        market_data=market_data
    )

    logger.info(f"风险评估结果:")
    logger.info(f"  整体风险评分: {risk_assessment.overall_risk_score:.3f}")
    logger.info(f"  风险等级: {risk_assessment.risk_level}")
    logger.info(f"  建议仓位限制: {risk_assessment.position_size_limit:.1%}")
    logger.info(f"  VaR(95%): {risk_assessment.var_95:.2%}")
    logger.info(f"  轧空概率: {risk_assessment.short_squeeze_probability:.3f}")

    if risk_assessment.risk_warnings:
        logger.info("  风险预警:")
        for warning in risk_assessment.risk_warnings[:3]:  # 显示前3个
            logger.info(f"    - {warning}")

    # 4. 优化建议
    logger.info("\n4. 生成优化建议...")
    optimization_engine = OptimizationEngine()

    recommendations = await optimization_engine.generate_optimization_recommendations(
        trade_history=trade_history,
        signal_history=signal_history,
        current_metrics=performance_metrics
    )

    logger.info(f"优化建议 (共{len(recommendations)}条):")
    for i, rec in enumerate(recommendations[:3]):  # 显示前3条
        logger.info(f"  建议{i+1}:")
        logger.info(f"    目标: {rec.optimization_target}")
        logger.info(f"    策略: {rec.strategy}")
        logger.info(f"    预期改进: {rec.expected_improvement:.3f}")
        logger.info(f"    优先级: {rec.priority}")
        logger.info(f"    置信度: {rec.confidence_level:.1%}")

    # 5. 信号质量报告
    logger.info("\n5. 生成信号质量报告...")
    quality_report = await optimization_engine.generate_signal_quality_report(
        signal_history=signal_history,
        trade_history=trade_history
    )

    logger.info(f"信号质量报告:")
    logger.info(f"  总信号数: {quality_report['total_signals']}")
    logger.info(f"  执行交易数: {quality_report['executed_trades']}")

    if quality_report['signal_types']:
        logger.info("  信号类型分布:")
        for signal_type, count in quality_report['signal_types'].items():
            logger.info(f"    {signal_type}: {count}")

    if quality_report['quality_trends']:
        logger.info("  质量趋势:")
        for month, stats in list(quality_report['quality_trends'].items())[-3:]:  # 最近3个月
            logger.info(f"    {month}: 质量比={stats['quality_ratio']:.2%}")

    logger.info("\n胜率计算与风险评估示例完成！")

    # 返回结果汇总
    return {
        'win_rate': win_rate_analysis.overall_success_rate,
        'risk_score': risk_assessment.overall_risk_score,
        'profit_factor': performance_metrics.profit_factor,
        'recommendations_count': len(recommendations)
    }


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())