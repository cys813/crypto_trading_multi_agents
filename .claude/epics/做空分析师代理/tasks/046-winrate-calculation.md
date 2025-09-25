---
name: 做空胜率计算与风险评估
epic: 做空分析师代理
task_id: 046-winrate-calculation
status: pending
priority: P1
estimated_hours: 40
parallel: true
dependencies: ["041-architecture-design", "042-data-receiver", "043-short-indicators", "044-signal-recognition", "045-llm-integration"]
github_issue: https://github.com/cys813/crypto_trading_multi_agents/issues/46
---

# Task: 做空胜率计算与风险评估

## Task Description
实现做空胜率计算与风险评估系统，基于历史数据分析、实时市场条件和多维度信号评估，提供准确的做空交易胜率预测。专门针对做空交易的特有风险进行建模和评估，包括无限上涨风险、流动性风险和强制平仓风险。

## Acceptance Criteria

### 胜率计算功能
- [ ] 实现基于历史数据的胜率计算算法
- [ ] 建立多维度胜率影响因素模型
- [ ] 完成实时市场条件适应性调整
- [ ] 实现胜率置信区间计算
- [ ] 建立胜率预测准确性验证

### 做空特有风险评估
- [ ] 实现无限上涨风险评估模型
- [ ] 建立流动性风险评估算法
- [ ] 完成强制平仓风险分析
- [ ] 实现市场波动风险评估
- [ ] 建立综合风险评分系统

### 动态调整与优化
- [ ] 实现胜率模型的自适应学习
- [ ] 完成风险阈值的动态调整
- [ ] 建立模型性能监控和预警
- [ ] 实现胜率预测的回测验证
- [ ] 完成模型参数优化

## Technical Implementation Details

### 核心胜率计算引擎
1. **ShortWinrateCalculator (做空胜率计算器)**
   ```python
   class ShortWinrateCalculator:
       def __init__(self, config: WinrateConfig):
           self.config = config
           self.historical_analyzer = HistoricalAnalyzer(config.historical_config)
           self.market_condition_analyzer = MarketConditionAnalyzer(config.market_config)
           self.signal_analyzer = SignalAnalyzer(config.signal_config)
           self.risk_modeler = ShortRiskModeler(config.risk_config)
           self.model_optimizer = ModelOptimizer(config.optimizer_config)

       async def calculate_short_winrate(self, analysis_input: WinrateCalculationInput) -> WinrateResult:
           # 主要胜率计算流程
           # 1. 分析历史胜率数据
           historical_winrate = await self.historical_analyzer.analyze_historical_winrate(
               analysis_input.asset, analysis_input.signal_type
           )

           # 2. 评估当前市场条件
           market_conditions = await self.market_condition_analyzer.analyze_current_conditions(
               analysis_input.market_data
           )

           # 3. 分析信号质量
           signal_quality = await self.signal_analyzer.analyze_signal_quality(
               analysis_input.signals
           )

           # 4. 评估做空特有风险
           short_risks = await self.risk_modeler.assess_short_risks(
               analysis_input.market_data, analysis_input.asset_info
           )

           # 5. 计算综合胜率
           base_winrate = self.calculate_base_winrate(historical_winrate)
           market_adjusted_winrate = self.adjust_for_market_conditions(base_winrate, market_conditions)
           signal_adjusted_winrate = self.adjust_for_signal_quality(market_adjusted_winrate, signal_quality)
           risk_adjusted_winrate = self.adjust_for_risk_factors(signal_adjusted_winrate, short_risks)

           # 6. 计算置信区间
           confidence_interval = self.calculate_confidence_interval(
               risk_adjusted_winrate, historical_winrate.sample_size
           )

           return WinrateResult(
               estimated_winrate=risk_adjusted_winrate,
               confidence_interval=confidence_interval,
               confidence_level=self.calculate_confidence_level(
                   historical_winrate, market_conditions, signal_quality, short_risks
               ),
               risk_factors=short_risks,
               market_conditions=market_conditions,
               historical_performance=historical_winrate,
               signal_quality=signal_quality,
               timestamp=datetime.now()
           )
   ```

2. **历史胜率分析器**
   ```python
   class HistoricalAnalyzer:
       def __init__(self, config: HistoricalConfig):
           self.config = config
           self.database = HistoricalDatabase(config.db_config)
           self.backtesting_engine = BacktestingEngine(config.backtesting_config)

       async def analyze_historical_winrate(self, asset: str, signal_type: str) -> HistoricalWinrate:
           # 分析历史胜率数据
           # 1. 获取历史信号数据
           historical_signals = await self.database.get_historical_signals(
               asset, signal_type, config.lookback_period
           )

           # 2. 回测历史表现
           backtest_results = await self.backtesting_engine.backtest_signals(historical_signals)

           # 3. 计算胜率统计
           winrate_stats = self.calculate_winrate_statistics(backtest_results)

           # 4. 分析时间序列模式
           time_series_patterns = self.analyze_time_series_patterns(backtest_results)

           # 5. 计算条件胜率
           conditional_winrates = self.calculate_conditional_winrates(backtest_results)

           return HistoricalWinrate(
               overall_winrate=winrate_stats.overall_winrate,
               sample_size=len(backtest_results),
               winrate_by_market_regime=winrate_stats.by_regime,
               winrate_by_volatility=winrate_stats.by_volatility,
               winrate_by_timeframe=winrate_stats.by_timeframe,
               conditional_winrates=conditional_winrates,
               time_series_patterns=time_series_patterns,
               statistical_significance=winrate_stats.statistical_significance,
               confidence_interval=winrate_stats.confidence_interval
           )

       def calculate_winrate_statistics(self, backtest_results: List[BacktestResult]) -> WinrateStats:
           # 计算胜率统计数据
           total_trades = len(backtest_results)
           winning_trades = sum(1 for result in backtest_results if result.profit > 0)
           overall_winrate = winning_trades / total_trades if total_trades > 0 else 0

           # 按市场 regime 分类胜率
           by_regime = self.classify_by_market_regime(backtest_results)

           # 按波动率分类胜率
           by_volatility = self.classify_by_volatility(backtest_results)

           # 按时间框架分类胜率
           by_timeframe = self.classify_by_timeframe(backtest_results)

           # 统计显著性检验
           statistical_significance = self.perform_statistical_test(backtest_results)

           # 置信区间计算
           confidence_interval = self.calculate_winrate_confidence_interval(overall_winrate, total_trades)

           return WinrateStats(
               overall_winrate=overall_winrate,
               by_regime=by_regime,
               by_volatility=by_volatility,
               by_timeframe=by_timeframe,
               statistical_significance=statistical_significance,
               confidence_interval=confidence_interval
           )
   ```

3. **市场条件分析器**
   ```python
   class MarketConditionAnalyzer:
       def __init__(self, config: MarketConfig):
           self.config = config
           self.regime_detector = MarketRegimeDetector(config.regime_config)
           self.volatility_analyzer = VolatilityAnalyzer(config.volatility_config)
           self.liquidity_analyzer = LiquidityAnalyzer(config.liquidity_config)

       async def analyze_current_conditions(self, market_data: MarketData) -> MarketConditions:
           # 分析当前市场条件
           # 1. 识别市场 regime
           market_regime = await self.regime_detector.detect_regime(market_data)

           # 2. 分析波动率状态
           volatility_state = await self.volatility_analyzer.analyze_volatility(market_data)

           # 3. 分析流动性状态
           liquidity_state = await self.liquidity_analyzer.analyze_liquidity(market_data)

           # 4. 分析趋势状态
           trend_state = self.analyze_trend_state(market_data)

           # 5. 分析情绪状态
           sentiment_state = self.analyze_sentiment_state(market_data)

           # 6. 计算市场压力指标
           market_pressure = self.calculate_market_pressure(market_data)

           return MarketConditions(
               market_regime=market_regime,
               volatility_state=volatility_state,
               liquidity_state=liquidity_state,
               trend_state=trend_state,
               sentiment_state=sentiment_state,
               market_pressure=market_pressure,
               overall_score=self.calculate_overall_market_score(
                   market_regime, volatility_state, liquidity_state, trend_state, sentiment_state
               )
           )

       def calculate_market_adjustment_factor(self, market_conditions: MarketConditions) -> float:
           # 计算市场条件调整因子
           adjustment_factor = 1.0

           # 根据 market regime 调整
           regime_adjustment = self.get_regime_adjustment(market_conditions.market_regime)
           adjustment_factor *= regime_adjustment

           # 根据波动率调整
           volatility_adjustment = self.get_volatility_adjustment(market_conditions.volatility_state)
           adjustment_factor *= volatility_adjustment

           # 根据流动性调整
           liquidity_adjustment = self.get_liquidity_adjustment(market_conditions.liquidity_state)
           adjustment_factor *= liquidity_adjustment

           # 根据趋势调整
           trend_adjustment = self.get_trend_adjustment(market_conditions.trend_state)
           adjustment_factor *= trend_adjustment

           return adjustment_factor
   ```

4. **做空特有风险建模器**
   ```python
   class ShortRiskModeler:
       def __init__(self, config: RiskConfig):
           self.config = config
           self.unlimited_upside_modeler = UnlimitedUpsideRiskModeler(config.unlimited_config)
           self.liquidity_risk_modeler = LiquidityRiskModeler(config.liquidity_config)
           self.liquidation_risk_modeler = LiquidationRiskModeler(config.liquidation_config)

       async def assess_short_risks(self, market_data: MarketData, asset_info: AssetInfo) -> ShortRiskAssessment:
           # 评估做空特有风险
           # 1. 无限上涨风险评估
           unlimited_upside_risk = await self.unlimited_upside_modeler.assess_risk(market_data, asset_info)

           # 2. 流动性风险评估
           liquidity_risk = await self.liquidity_risk_modeler.assess_risk(market_data, asset_info)

           # 3. 强制平仓风险评估
           liquidation_risk = await self.liquidation_risk_modeler.assess_risk(market_data, asset_info)

           # 4. 市场波动风险评估
           volatility_risk = self.assess_volatility_risk(market_data)

           # 5. 综合风险评分
           overall_risk_score = self.calculate_overall_risk_score(
               unlimited_upside_risk, liquidity_risk, liquidation_risk, volatility_risk
           )

           return ShortRiskAssessment(
               unlimited_upside_risk=unlimited_upside_risk,
               liquidity_risk=liquidity_risk,
               liquidation_risk=liquidation_risk,
               volatility_risk=volatility_risk,
               overall_risk_score=overall_risk_score,
               risk_level=self.classify_risk_level(overall_risk_score),
               risk_adjustment_factor=self.calculate_risk_adjustment_factor(overall_risk_score)
           )

       def calculate_risk_adjustment_factor(self, risk_score: float) -> float:
           # 计算风险调整因子
           if risk_score >= 8.0:  # 极高风险
               return 0.3  # 胜率降低70%
           elif risk_score >= 6.0:  # 高风险
               return 0.5  # 胜率降低50%
           elif risk_score >= 4.0:  # 中等风险
               return 0.7  # 胜率降低30%
           elif risk_score >= 2.0:  # 低风险
               return 0.85  # 胜率降低15%
           else:  # 极低风险
               return 1.0  # 胜率不变
   ```

5. **无限上涨风险模型器**
   ```python
   class UnlimitedUpsideRiskModeler:
       def __init__(self, config: UnlimitedUpsideConfig):
           self.config = config

       async def assess_risk(self, market_data: MarketData, asset_info: AssetInfo) -> UnlimitedUpsideRisk:
           # 评估无限上涨风险
           # 1. 分析历史暴涨事件
           historical_pumps = self.analyze_historical_pumps(market_data)

           # 2. 评估当前市场情绪
           sentiment_risk = self.assess_sentiment_risk(market_data.sentiment_data)

           # 3. 分析流动性状况
           liquidity_risk = self.assess_liquidity_risk(market_data.volume_data)

           # 4. 评估新闻催化剂
           news_catalyst_risk = self.assess_news_catalyst_risk(market_data.news_data)

           # 5. 计算综合风险评分
           risk_score = self.calculate_unlimited_upside_risk_score(
               historical_pumps, sentiment_risk, liquidity_risk, news_catalyst_risk
           )

           return UnlimitedUpsideRisk(
               risk_score=risk_score,
               risk_level=self.classify_risk_level(risk_score),
               historical_pump_frequency=historical_pumps.frequency,
               sentiment_extremeness=sentiment_risk.extremeness,
               liquidity_vulnerability=liquidity_risk.vulnerability,
               news_catalyst_intensity=news_catalyst_risk.intensity,
               worst_case_scenario=self.calculate_worst_case_scenario(market_data, risk_score)
           )

       def calculate_worst_case_scenario(self, market_data: MarketData, risk_score: float) -> WorstCaseScenario:
           # 计算最坏情况情景
           current_price = market_data.current_price

           # 基于历史数据计算最大潜在涨幅
           historical_max_increase = self.calculate_historical_max_increase(market_data)

           # 基于风险评分调整潜在涨幅
           adjusted_max_increase = historical_max_increase * (1 + risk_score * 0.5)

           return WorstCaseScenario(
               potential_upside=adjusted_max_increase,
               potential_loss_multiple=adjusted_max_increase,  # 理论上无上限
               probability_of_occurrence=risk_score / 10.0,
               estimated_max_price=current_price * (1 + adjusted_max_increase),
               time_horizon=self.estimate_time_horizon(risk_score)
           )
   ```

### 动态胜率调整算法
1. **多维度胜率调整**
   ```python
   def calculate_base_winrate(self, historical_winrate: HistoricalWinrate) -> float:
       # 计算基础胜率
       base_winrate = historical_winrate.overall_winrate

       # 考虑统计显著性
       if historical_winrate.statistical_significance < config.min_significance_level:
           # 如果统计显著性不足，使用保守估计
           base_winrate = base_winrate * 0.8

       # 考虑样本大小
       if historical_winrate.sample_size < config.min_sample_size:
           # 样本太小，降低可信度
           base_winrate = base_winrate * (0.5 + 0.5 * historical_winrate.sample_size / config.min_sample_size)

       return base_winrate

   def adjust_for_market_conditions(self, base_winrate: float, market_conditions: MarketConditions) -> float:
       # 根据市场条件调整胜率
       adjustment_factor = self.market_condition_analyzer.calculate_market_adjustment_factor(market_conditions)
       return base_winrate * adjustment_factor

   def adjust_for_signal_quality(self, winrate: float, signal_quality: SignalQuality) -> float:
       # 根据信号质量调整胜率
       quality_factor = self.calculate_signal_quality_factor(signal_quality)
       return winrate * quality_factor

   def adjust_for_risk_factors(self, winrate: float, short_risks: ShortRiskAssessment) -> float:
       # 根据风险因素调整胜率
       risk_adjustment = short_risks.risk_adjustment_factor
       return winrate * risk_adjustment
   ```

2. **置信区间计算**
   ```python
   def calculate_confidence_interval(self, winrate: float, sample_size: int) -> ConfidenceInterval:
       # 计算胜率的置信区间
       if sample_size < 30:
           # 小样本使用 t 分布
           alpha = 1 - config.confidence_level
           t_critical = stats.t.ppf(1 - alpha/2, sample_size - 1)
           standard_error = math.sqrt(winrate * (1 - winrate) / sample_size)
           margin_of_error = t_critical * standard_error
       else:
           # 大样本使用正态分布
           alpha = 1 - config.confidence_level
           z_critical = stats.norm.ppf(1 - alpha/2)
           standard_error = math.sqrt(winrate * (1 - winrate) / sample_size)
           margin_of_error = z_critical * standard_error

       return ConfidenceInterval(
           lower_bound=max(0, winrate - margin_of_error),
           upper_bound=min(1, winrate + margin_of_error),
           confidence_level=config.confidence_level,
           margin_of_error=margin_of_error
       )
   ```

### 技术实现要点
- **做空特有**: 专门针对做空交易的风险建模
- **多维评估**: 结合历史、市场、信号和风险多维度评估
- **动态调整**: 实时动态调整胜率和风险评估
- **统计严谨**: 基于统计学的严格置信区间计算
- **实时性**: 优化的实时计算性能

## Deliverables

1. **胜率计算引擎**
   - ShortWinrateCalculator 主类实现
   - 历史胜率分析器
   - 市场条件分析器

2. **风险评估系统**
   - 做空特有风险建模器
   - 无限上涨风险评估
   - 流动性和强制平仓风险评估

3. **动态调整模块**
   - 多维度胜率调整算法
   - 自适应参数优化
   - 模型性能监控

4. **测试与验证**
   - 胜率预测准确性测试
   - 风险评估有效性验证
   - 历史回测报告
   - 统计分析报告

## Dependencies
- 041-architecture-design (架构设计完成)
- 042-data-receiver (数据接收模块)
- 043-short-indicators (做空指标引擎)
- 044-signal-recognition (信号识别系统)
- 045-llm-integration (LLM分析引擎)

## Risks and Mitigation

### 技术风险
- **模型复杂性**: 多维度模型增加了计算复杂性
  - 缓解: 优化算法和并行计算
- **数据质量**: 历史数据质量影响胜率预测准确性
  - 缓解: 数据清洗和质量评估

### 业务风险
- **预测准确性**: 胜率预测可能不够准确
  - 缓解: 多模型集成和保守估计
- **风险评估**: 做空特有风险评估可能遗漏重要因素
  - 缓解: 多角度风险分析和保守策略

## Success Metrics
- 胜率预测准确性: 预测误差 < 15%
- 风险评估覆盖率: >95%
- 计算响应时间: <1秒
- 模型更新频率: 每日自动更新
- 统计显著性: >95%置信水平
- 系统稳定性: >99%

## Notes
- 重点关注做空交易的特有风险和挑战
- 确保胜率计算的统计严谨性
- 采用保守的风险评估策略
- 建立完善的模型监控和更新机制