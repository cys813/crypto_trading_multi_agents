---
name: 做空分析报告生成器
epic: 做空分析师代理
task_id: 047-report-generator
status: pending
priority: P1
estimated_hours: 32
parallel: true
dependencies: ["041-architecture-design", "042-data-receiver", "043-short-indicators", "044-signal-recognition", "045-llm-integration", "046-winrate-calculation"]
github_issue: https://github.com/cys813/crypto_trading_multi_agents/issues/47
---

# Task: 做空分析报告生成器

## Task Description
实现做空分析报告生成器，整合技术分析、LLM分析结果、胜率计算和风险评估，生成结构化、易读的做空分析报告。支持多种输出格式，提供清晰的交易建议和风险评估，为最终策略决策代理提供高质量的输入。

## Acceptance Criteria

### 报告生成功能
- [ ] 完成结构化做空分析报告生成
- [ ] 实现多种输出格式支持(JSON、Markdown、HTML)
- [ ] 建立报告模板和格式化系统
- [ ] 完成数据可视化和图表生成
- [ ] 实现报告质量评估和优化

### 分析内容完整性
- [ ] 提供详细的做空信号分析
- [ ] 包含具体的交易建议（入场点、止损点、止盈点）
- [ ] 完成胜率分析和风险评估
- [ ] 实现置信度评分和推理过程
- [ ] 建立历史表现对比和验证

### 用户体验与性能
- [ ] 报告生成时间 < 1秒
- [ ] 报告可读性和易懂性评分 > 85%
- [ ] 支持多语言输出
- [ ] 实现报告个性化定制
- [ ] 完成报告历史记录和追溯

## Technical Implementation Details

### 核心报告生成引擎
1. **ShortReportGenerator (做空报告生成器)**
   ```python
   class ShortReportGenerator:
       def __init__(self, config: ReportGeneratorConfig):
           self.config = config
           self.template_engine = ReportTemplateEngine(config.template_config)
           self.data_formatter = DataFormatter(config.formatter_config)
           self.visualizer = ReportVisualizer(config.visualizer_config)
           self.quality_assessor = ReportQualityAssessor(config.quality_config)
           self.exporter = ReportExporter(config.exporter_config)

       async def generate_short_analysis_report(self, analysis_data: ShortAnalysisData) -> ShortAnalysisReport:
           # 主要报告生成流程
           # 1. 整合分析数据
           integrated_data = await self.integrate_analysis_data(analysis_data)

           # 2. 生成报告主体内容
           report_content = await self.generate_report_content(integrated_data)

           # 3. 添加可视化图表
           visualizations = await self.visualizer.generate_visualizations(integrated_data)

           # 4. 生成最终报告
           report = await self.assemble_report(report_content, visualizations)

           # 5. 评估报告质量
           quality_assessment = await self.quality_assessor.assess_report_quality(report)

           return ShortAnalysisReport(
               report_content=report_content,
               visualizations=visualizations,
               metadata=ReportMetadata(
                   generated_at=datetime.now(),
                   asset=analysis_data.asset,
                   signal_type=analysis_data.signal_type,
                   quality_score=quality_assessment.quality_score,
                   confidence_level=quality_assessment.confidence_level
               ),
               formats=await self.exporter.generate_export_formats(report)
           )

       async def generate_report_content(self, data: IntegratedAnalysisData) -> ReportContent:
           # 生成报告内容
           return ReportContent(
               executive_summary=self.generate_executive_summary(data),
               signal_analysis=self.generate_signal_analysis(data),
               technical_analysis=self.generate_technical_analysis(data),
               market_analysis=self.generate_market_analysis(data),
               risk_assessment=self.generate_risk_assessment(data),
               trading_recommendations=self.generate_trading_recommendations(data),
               winrate_analysis=self.generate_winrate_analysis(data),
               llm_analysis=self.generate_llm_analysis(data),
               conclusion=self.generate_conclusion(data)
           )
   ```

2. **报告模板引擎**
   ```python
   class ReportTemplateEngine:
       def __init__(self, config: TemplateConfig):
           self.config = config
           self.templates = self.load_templates()

       async def render_template(self, template_name: str, data: dict) -> str:
           # 渲染报告模板
           template = self.templates.get(template_name)
           if not template:
               raise ValueError(f"Template {template_name} not found")

           return await template.render_async(**data)

       def generate_executive_summary(self, data: IntegratedAnalysisData) -> str:
           # 生成执行摘要
           signal_strength = data.signal_analysis.primary_signal.strength
           winrate = data.winrate_analysis.estimated_winrate
           risk_level = data.risk_assessment.overall_risk_score
           recommendation = data.trading_recommendations.primary_recommendation

           summary = f"""
           ## 执行摘要

           **做空信号强度**: {signal_strength:.1f}/10 ({self.classify_signal_strength(signal_strength)})

           **预期胜率**: {winrate:.1%} (置信区间: {data.winrate_analysis.confidence_interval.lower_bound:.1%} - {data.winrate_analysis.confidence_interval.upper_bound:.1%})

           **风险等级**: {risk_level:.1f}/10 ({self.classify_risk_level(risk_level)})

           **主要建议**: {recommendation.action} - {recommendation.reasoning}

           **核心发现**:
           {self.generate_key_findings(data)}
           """

           return summary

       def generate_signal_analysis(self, data: IntegratedAnalysisData) -> str:
           # 生成信号分析
           primary_signal = data.signal_analysis.primary_signal
           secondary_signals = data.signal_analysis.secondary_signals

           analysis = f"""
           ## 做空信号分析

           ### 主要做空信号
           - **信号类型**: {primary_signal.type}
           - **信号强度**: {primary_signal.strength:.1f}/10
           - **置信度**: {primary_signal.confidence:.1%}
           - **检测时间**: {primary_signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

           ### 信号详细分析
           {self.generate_signal_detail_analysis(primary_signal)}

           ### 次要信号支持
           {self.generate_secondary_signals_analysis(secondary_signals)}

           ### 信号质量评估
           - **数据质量评分**: {data.signal_analysis.data_quality_score:.1f}/10
           - **技术指标一致性**: {data.signal_analysis.indicator_consistency:.1f}/10
           - **市场环境适配性**: {data.signal_analysis.market_environment_fit:.1f}/10
           """

           return analysis

       def generate_trading_recommendations(self, data: IntegratedAnalysisData) -> str:
           # 生成交易建议
           recommendations = data.trading_recommendations

           return f"""
           ## 交易建议

           ### 入场建议
           - **推荐入场价位**: {recommendations.entry_price_range.min:.4f} - {recommendations.entry_price_range.max:.4f}
           - **入场时机**: {recommendations.entry_timing}
           - **仓位建议**: {recommendations.position_size_suggestion}

           ### 止损建议
           - **止损价位**: {recommendations.stop_loss_price:.4f}
           - **止损幅度**: {recommendations.stop_loss_percentage:.1%}
           - **止损策略**: {recommendations.stop_loss_strategy}

           ### 止盈建议
           - **目标价位**: {recommendations.take_profit_price:.4f}
           - **止盈幅度**: {recommendations.take_profit_percentage:.1%}
           - **止盈策略**: {recommendations.take_profit_strategy}

           ### 风险收益比
           - **风险收益比**: 1:{recommendations.risk_reward_ratio:.1f}
           - **预期盈利**: {recommendations.expected_profit_percentage:.1%}
           - **最大亏损**: {recommendations.max_loss_percentage:.1%}

           ### 交易时间框架
           - **建议持仓时间**: {recommendations.suggested_holding_period}
           - **监控频率**: {recommendations.monitoring_frequency}
           """
   ```

3. **数据可视化生成器**
   ```python
   class ReportVisualizer:
       def __init__(self, config: VisualizerConfig):
           self.config = config
           self.chart_generator = ChartGenerator(config.chart_config)
           self.diagram_generator = DiagramGenerator(config.diagram_config)

       async def generate_visualizations(self, data: IntegratedAnalysisData) -> ReportVisualizations:
           # 生成可视化图表
           return ReportVisualizations(
               price_chart=await self.generate_price_chart(data),
               signal_chart=await self.generate_signal_chart(data),
               risk_chart=await self.generate_risk_chart(data),
               winrate_chart=await self.generate_winrate_chart(data),
               technical_indicators_chart=await self.generate_technical_indicators_chart(data),
               market_sentiment_chart=await self.generate_market_sentiment_chart(data)
           )

       async def generate_price_chart(self, data: IntegratedAnalysisData) -> Chart:
           # 生成价格图表
           price_data = data.market_data.price_history

           fig = go.Figure()

           # 添加K线图
           fig.add_trace(go.Candlestick(
               x=price_data.timestamps,
               open=price_data.open_prices,
               high=price_data.high_prices,
               low=price_data.low_prices,
               close=price_data.close_prices,
               name="价格走势"
           ))

           # 添加信号标记
           for signal in data.signal_analysis.signals:
               fig.add_trace(go.Scatter(
                   x=[signal.timestamp],
                   y=[signal.price],
                   mode='markers',
                   marker=dict(
                       symbol='triangle-down',
                       size=15,
                       color=self.get_signal_color(signal.type)
                   ),
                   name=f"{signal.type}信号",
                   text=f"{signal.type}: 强度{signal.strength:.1f}",
                   showlegend=False
               ))

           # 添加支撑阻力位
           if data.technical_analysis.support_resistance_levels:
               for level in data.technical_analysis.support_resistance_levels:
                   fig.add_hline(y=level.price, line_dash="dash", line_color="red",
                                annotation_text=f"阻力位 {level.price:.4f}")

           fig.update_layout(
               title="价格走势与做空信号",
               xaxis_title="时间",
               yaxis_title="价格",
               template="plotly_dark"
           )

           return Chart(
               type="price_chart",
               plotly_json=fig.to_json(),
               description="价格走势图，包含做空信号标记和关键阻力位"
           )

       async def generate_signal_strength_chart(self, data: IntegratedAnalysisData) -> Chart:
           # 生成信号强度图表
           signals = data.signal_analysis.signals

           fig = go.Figure(data=[
               go.Bar(
                   x=[signal.type for signal in signals],
                   y=[signal.strength for signal in signals],
                   marker_color=[self.get_signal_color(signal.type) for signal in signals],
                   text=[f"{signal.strength:.1f}/10" for signal in signals],
                   textposition='auto',
               )
           ])

           fig.update_layout(
               title="做空信号强度分析",
               xaxis_title="信号类型",
               yaxis_title="信号强度",
               yaxis=dict(range=[0, 10]),
               template="plotly_dark"
           )

           return Chart(
               type="signal_strength_chart",
               plotly_json=fig.to_json(),
               description="各类做空信号的强度对比"
           )
   ```

4. **报告质量评估器**
   ```python
   class ReportQualityAssessor:
       async def assess_report_quality(self, report: ShortAnalysisReport) -> ReportQualityAssessment:
           # 评估报告质量
           completeness_score = self.assess_completeness(report)
           accuracy_score = self.assess_accuracy(report)
           clarity_score = self.assess_clarity(report)
           actionability_score = self.assess_actionability(report)
           consistency_score = self.assess_consistency(report)

           overall_score = self.calculate_overall_quality_score(
               completeness_score, accuracy_score, clarity_score, actionability_score, consistency_score
           )

           return ReportQualityAssessment(
               overall_quality_score=overall_score,
               completeness_score=completeness_score,
               accuracy_score=accuracy_score,
               clarity_score=clarity_score,
               actionability_score=actionability_score,
               consistency_score=consistency_score,
               confidence_level=self.calculate_confidence_level(report),
               improvement_suggestions=self.generate_improvement_suggestions(report)
           )

       def assess_actionability(self, report: ShortAnalysisReport) -> float:
           # 评估报告的可操作性
           actionability_score = 100.0

           # 检查是否提供具体的交易建议
           recommendations = report.report_content.trading_recommendations
           if not recommendations.entry_price_range:
               actionability_score -= 30
           if not recommendations.stop_loss_price:
               actionability_score -= 25
           if not recommendations.take_profit_price:
               actionability_score -= 20

           # 检查建议是否具体可执行
           if not self.has_specific_actionable_items(recommendations):
               actionability_score -= 15

           # 检查是否有明确的时间框架
           if not recommendations.suggested_holding_period:
               actionability_score -= 10

           return max(0, actionability_score)
   ```

5. **多格式导出器**
   ```python
   class ReportExporter:
       def __init__(self, config: ExporterConfig):
           self.config = config
           self.exporters = {
               'json': JSONExporter(config.json_config),
               'markdown': MarkdownExporter(config.markdown_config),
               'html': HTMLExporter(config.html_config),
               'pdf': PDFExporter(config.pdf_config)
           }

       async def generate_export_formats(self, report: ShortAnalysisReport) -> dict:
           # 生成多种格式的导出
           formats = {}

           for format_name, exporter in self.exporters.items():
               try:
                   if format_name in self.config.enabled_formats:
                       formats[format_name] = await exporter.export(report)
               except Exception as e:
                   logger.error(f"Failed to export {format_name}: {e}")
                   formats[format_name] = None

           return formats

       async def generate_markdown_report(self, report: ShortAnalysisReport) -> str:
           # 生成Markdown格式报告
           markdown_content = f"""# 做空分析报告

           ## 基本信息
           - **资产**: {report.metadata.asset}
           - **生成时间**: {report.metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
           - **信号类型**: {report.metadata.signal_type}
           - **质量评分**: {report.metadata.quality_score:.1f}/10

           {report.report_content.executive_summary}

           {report.report_content.signal_analysis}

           {report.report_content.technical_analysis}

           {report.report_content.trading_recommendations}

           {report.report_content.risk_assessment}

           {report.report_content.winrate_analysis}

           {report.report_content.conclusion}

           ---
           *报告由做空分析师代理自动生成，质量评分: {report.metadata.quality_score:.1f}/10*
           """

           return markdown_content
   ```

### 报告内容生成算法
1. **智能内容摘要**
   ```python
   def generate_intelligent_summary(self, data: IntegratedAnalysisData) -> str:
       # 生成智能内容摘要
       key_points = []

       # 信号强度评估
       if data.signal_analysis.primary_signal.strength >= 7.0:
           key_points.append(f"检测到强烈的做空信号({data.signal_analysis.primary_signal.strength:.1f}/10)")
       elif data.signal_analysis.primary_signal.strength >= 5.0:
           key_points.append(f"检测到中等强度做空信号({data.signal_analysis.primary_signal.strength:.1f}/10)")

       # 胜率评估
       if data.winrate_analysis.estimated_winrate >= 0.65:
           key_points.append(f"预期胜率较高({data.winrate_analysis.estimated_winrate:.1%})")
       elif data.winrate_analysis.estimated_winrate >= 0.5:
           key_points.append(f"预期胜率中等({data.winrate_analysis.estimated_winrate:.1%})")

       # 风险评估
       if data.risk_assessment.overall_risk_score >= 7.0:
           key_points.append("风险较高，需要谨慎")
       elif data.risk_assessment.overall_risk_score >= 5.0:
           key_points.append("风险适中")

       # 生成摘要
       summary = " | ".join(key_points)
       return summary if summary else "暂无明确的交易信号"
   ```

### 技术实现要点
- **结构化输出**: 清晰的报告结构和层次
- **多格式支持**: 支持JSON、Markdown、HTML等多种格式
- **可视化**: 丰富的图表和可视化元素
- **质量保证**: 完善的报告质量评估机制
- **性能优化**: 高效的模板渲染和图表生成

## Deliverables

1. **报告生成引擎**
   - ShortReportGenerator 主类实现
   - 报告模板系统
   - 数据格式化器

2. **可视化组件**
   - 图表生成器
   - 可视化模板
   - 交互式图表支持

3. **导出系统**
   - 多格式导出器
   - 报告质量评估
   - 个性化定制功能

4. **测试与文档**
   - 报告生成测试
   - 格式兼容性测试
   - 用户界面测试
   - 使用文档

## Dependencies
- 041-architecture-design (架构设计完成)
- 042-data-receiver (数据接收模块)
- 043-short-indicators (做空指标引擎)
- 044-signal-recognition (信号识别系统)
- 045-llm-integration (LLM分析引擎)
- 046-winrate-calculation (胜率计算系统)

## Risks and Mitigation

### 技术风险
- **模板复杂性**: 复杂的模板可能影响性能
  - 缓解: 预编译模板和缓存机制
- **图表生成**: 图表生成可能消耗大量资源
  - 缓解: 异步生成和资源优化

### 业务风险
- **报告质量**: 自动生成的报告质量可能不够专业
  - 缓解: 严格的质量评估和优化机制
- **用户体验**: 报告可读性可能不够友好
  - 缓解: 用户测试和反馈优化

## Success Metrics
- 报告生成时间: <1秒
- 报告质量评分: >85%
- 用户满意度: >90%
- 格式兼容性: 100%
- 图表生成成功率: >95%
- 系统稳定性: >99%

## Notes
- 重点关注报告的专业性和可读性
- 确保多种输出格式的兼容性
- 优化图表生成的性能和美观度
- 建立完善的报告质量控制机制