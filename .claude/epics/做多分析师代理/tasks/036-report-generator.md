---
name: 分析报告生成模块
epic: 做多分析师代理
task_id: 007-report-generator
status: pending
priority: P3
estimated_hours: 32
parallel: true
dependencies: ["001-architecture-design", "005-llm-integration", "006-winrate-calculation"]
github_issue: https://github.com/cys813/crypto_trading_multi_agents/issues/36
---

# Task: 分析报告生成模块

## Task Description
开发分析报告生成模块，基于技术分析、LLM分析和胜率计算结果，生成标准化的做多分析报告，包括多维度分析、策略建议、风险收益分析和可视化输出。

## Acceptance Criteria

### 报告模板系统
- [ ] 完成标准化分析报告模板设计
- [ ] 实现多格式报告输出(JSON, HTML, PDF)
- [ ] 建立报告模板配置管理
- [ ] 完成报告版本控制
- [ ] 实现模板动态更新机制

### 分析报告生成
- [ ] 完成技术面分析报告生成
- [ ] 完成基本面分析报告生成
- [ ] 完成情绪面分析报告生成
- [ ] 完成综合分析报告生成
- [ ] 实现报告摘要和关键指标提取

### 策略建议生成
- [ ] 完成入场时机建议生成
- [ ] 完成止损点位建议生成
- [ ] 完成止盈目标建议生成
- [ ] 完成仓位管理建议生成
- [ ] 实现建议置信度评分

### 风险收益分析
- [ ] 完成风险收益比计算
- [ ] 完成最大回撤预估
- [ ] 完成盈亏平衡点分析
- [ ] 完成时间价值评估
- [ ] 实现敏感性分析

### 可视化输出
- [ ] 完成技术指标图表生成
- [ ] 完成价格走势图表生成
- [ ] 完成风险评估图表生成
- [ ] 完成多时间框架对比图表
- [ ] 实现交互式可视化

### 性能要求
- [ ] 报告生成时间 <3秒
- [ ] 支持批量报告生成
- [ ] 图表生成响应时间 <1秒
- [ ] 报告准确性验证通过
- [ ] 性能压力测试通过

## Technical Implementation Details

### 核心架构设计
1. **ReportGenerator (报告生成器)**
   ```python
   class ReportGenerator:
       def __init__(self, config: ReportConfig):
           self.config = config
           self.template_engine = TemplateEngine()
           self.visualizer = ReportVisualizer()
           self.analyzer = ReportAnalyzer()

       async def generate_report(self, analysis_data: AnalysisData) -> AnalysisReport:
           # 生成分析报告
           pass

       async def generate_batch_reports(self, analysis_requests: List[AnalysisRequest]) -> List[AnalysisReport]:
           # 批量生成报告
           pass
   ```

2. **TemplateEngine (模板引擎)**
   ```python
   class TemplateEngine:
       def __init__(self, template_dir: str):
           self.templates = self._load_templates(template_dir)
           self.renderer = TemplateRenderer()

       def render_template(self, template_name: str, context: Dict) -> str:
           # 渲染模板
           pass

       def get_template_config(self, template_name: str) -> TemplateConfig:
           # 获取模板配置
           pass

       def update_template(self, template_name: str, new_content: str) -> None:
           # 更新模板
           pass
   ```

3. **ReportAnalyzer (报告分析器)**
   ```python
   class ReportAnalyzer:
       def analyze_technical_indicators(self, technical_data: TechnicalData) -> TechnicalAnalysis:
           # 分析技术指标
           pass

       def analyze_market_sentiment(self, sentiment_data: SentimentData) -> SentimentAnalysis:
           # 分析市场情绪
           pass

       def analyze_risk_reward(self, signal: Signal, market_data: MarketData) -> RiskRewardAnalysis:
           # 分析风险收益
           pass

       def generate_summary(self, analyses: Dict[str, Analysis]) -> ReportSummary:
           # 生成报告摘要
           pass
   ```

### 报告模板设计
1. **标准分析报告模板**
   ```python
   STANDARD_REPORT_TEMPLATE = """
   # 做多分析报告 - {symbol}

   ## 执行摘要
   {summary}

   ## 技术面分析
   ### 趋势分析
   {trend_analysis}

   ### 关键指标
   {key_indicators}

   ### 支撑阻力位
   {support_resistance}

   ## 基本面分析
   {fundamental_analysis}

   ## 市场情绪分析
   {sentiment_analysis}

   ## 策略建议
   ### 入场建议
   {entry_recommendation}

   ### 止损建议
   {stop_loss_recommendation}

   ### 止盈建议
   {take_profit_recommendation}

   ### 仓位管理
   {position_management}

   ## 风险收益分析
   ### 风险收益比
   {risk_reward_ratio}

   ### 最大回撤预估
   {max_drawdown}

   ### 胜率评估
   {win_rate_assessment}

   ## 结论
   {conclusion}

   ---
   报告生成时间: {generated_time}
   分析模型版本: {model_version}
   """
   ```

2. **快速决策模板**
   ```python
   QUICK_DECISION_TEMPLATE = """
   # 快速做多决策 - {symbol}

   ## 信号强度: {signal_strength}/10
   ## 推荐操作: {recommendation}
   ## 预期胜率: {expected_win_rate}%

   ### 关键数据
   - 入场价格: {entry_price}
   - 止损价格: {stop_loss_price}
   - 止盈价格: {take_profit_price}
   - 风险收益比: {risk_reward_ratio}

   ### 主要理由
   {key_reasons}

   ### 主要风险
   {key_risks}
   """
   ```

### 可视化组件
1. **技术指标图表**
   ```python
   class TechnicalChartGenerator:
       def generate_candlestick_chart(self, price_data: List[PriceData]) -> Chart:
           # 生成K线图
           pass

       def generate_indicator_chart(self, indicator_data: Dict[str, List[float]]) -> Chart:
           # 生成指标图
           pass

       def generate_volume_chart(self, volume_data: List[float]) -> Chart:
           # 生成成交量图
           pass

       def generate_multi_timeframe_chart(self, data: Dict[str, MarketData]) -> Chart:
           # 生成多时间框架图
           pass
   ```

2. **风险评估图表**
   ```python
   class RiskChartGenerator:
       def generate_risk_reward_chart(self, entry_price: float, stop_loss: float,
                                     take_profit: float) -> Chart:
           # 生成风险收益图
           pass

       def generate_probability_distribution(self, probabilities: List[float]) -> Chart:
           # 生成概率分布图
           pass

       def generate_drawdown_simulation(self, simulations: List[float]) -> Chart:
           # 生成回撤模拟图
           pass
   ```

### 策略建议生成
1. **入场建议生成器**
   ```python
   class EntryRecommendationGenerator:
       def generate_entry_recommendation(self, signal: Signal, market_data: MarketData) -> EntryRecommendation:
           # 生成入场建议
           pass

       def calculate_entry_price(self, signal: Signal) -> float:
           # 计算入场价格
           pass

       def assess_entry_timing(self, signal: Signal, market_data: MarketData) -> TimingScore:
           # 评估入场时机
           pass
   ```

2. **风险管理建议**
   ```python
   class RiskManagementAdvisor:
       def generate_stop_loss(self, signal: Signal, market_data: MarketData) -> float:
           # 生成止损价格
           pass

       def generate_take_profit(self, signal: Signal, market_data: MarketData) -> List[float]:
           # 生成止盈价格
           pass

       def calculate_position_size(self, account_size: float, risk_per_trade: float,
                                  stop_loss_distance: float) -> float:
           # 计算仓位大小
           pass

       def generate_risk_reward_ratio(self, entry: float, stop_loss: float,
                                    take_profit: float) -> float:
           # 计算风险收益比
           pass
   ```

### 风险收益分析
1. **风险收益计算器**
   ```python
   class RiskRewardCalculator:
       def calculate_expected_return(self, signal: Signal, win_rate: float) -> float:
           # 计算预期收益
           pass

       def calculate_max_drawdown(self, historical_data: List[Trade]) -> float:
           # 计算最大回撤
           pass

       def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float) -> float:
           # 计算夏普比率
           pass

       def sensitivity_analysis(self, parameters: Dict) -> SensitivityResult:
           # 敏感性分析
           pass
   ```

## Deliverables

1. **报告生成核心**
   - ReportGenerator 类实现
   - 模板引擎
   - 报告分析器
   - 可视化组件

2. **报告模板系统**
   - 标准分析报告模板
   - 快速决策模板
   - 模板配置管理
   - 模板更新机制

3. **策略建议系统**
   - 入场建议生成器
   - 风险管理建议
   - 仓位管理建议
   - 置信度评分

4. **可视化系统**
   - 技术指标图表
   - 风险评估图表
   - 交互式可视化
   - 图表导出功能

## Dependencies
- 001-architecture-design (架构设计完成)
- 005-llm-integration (LLM集成完成)
- 006-winrate-calculation (胜率计算完成)
- 图表生成库(Plotly, Matplotlib)
- PDF生成库

## Risks and Mitigation

### 技术风险
- **生成延迟**: 报告生成时间过长
  - 缓解: 缓存优化和异步处理
- **图表质量**: 可视化效果不佳
  - 缓解: 图表库选择和优化

### 内容风险
- **报告质量**: 分析报告质量不达标
  - 缓解: 报告模板优化和验证
- **建议准确性**: 策略建议不准确
  - 缓解: 多重验证和回测

## Success Metrics
- 报告生成时间: <3秒
- 图表生成时间: <1秒
- 报告准确性: >90%
- 用户满意度: >85%
- 系统可用性: >99%

## Notes
- 重点关注报告质量和用户体验
- 确保支持多种输出格式
- 考虑未来的模板扩展需求