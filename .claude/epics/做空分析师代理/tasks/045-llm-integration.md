---
name: LLM分析与推理引擎
epic: 做空分析师代理
task_id: 045-llm-integration
status: pending
priority: P1
estimated_hours: 48
parallel: true
dependencies: ["041-architecture-design", "042-data-receiver", "043-short-indicators", "044-signal-recognition"]
github_issue: https://github.com/cys813/crypto_trading_multi_agents/issues/45
---

# Task: LLM分析与推理引擎

## Task Description
实现LLM分析与推理引擎，整合技术分析结果、市场情绪、新闻信息和原始交易数据，利用大语言模型进行深度分析和推理，生成高质量的做空分析报告。专门设计做空分析的提示词工程和上下文管理。

## Acceptance Criteria

### LLM集成功能
- [ ] 完成LLM服务模块集成和接口封装
- [ ] 实现做空专用提示词工程和模板
- [ ] 建立上下文管理和数据整合系统
- [ ] 实现多轮对话和推理机制
- [ ] 完成分析结果解析和结构化输出

### 分析能力
- [ ] 实现技术面、基本面、情绪面综合分析
- [ ] 建立市场逻辑推理和因果关系分析
- [ ] 完成风险因素识别和评估
- [ ] 实现做空机会的深度推理
- [ ] 建立分析质量和一致性评估

### 性能与成本
- [ ] LLM分析响应时间 < 3秒
- [ ] API调用成本优化 < 基准成本的80%
- [ ] 支持模型热切换和负载均衡
- [ ] 实现缓存和上下文复用
- [ ] 分析准确性评分 > 85%

## Technical Implementation Details

### 核心LLM分析引擎
1. **ShortLLMAnalyzer (做空LLM分析器)**
   ```python
   class ShortLLMAnalyzer:
       def __init__(self, config: LLMAnalyzerConfig):
           self.config = config
           self.llm_service = LLMService(config.llm_config)
           self.prompt_engine = ShortPromptEngine(config.prompt_config)
           self.context_manager = ContextManager(config.context_config)
           self.response_parser = ResponseParser(config.parser_config)
           self.quality_assessor = AnalysisQualityAssessor(config.quality_config)

       async def analyze_short_opportunity(self, analysis_input: ShortAnalysisInput) -> ShortLLMAnalysis:
           # 主要分析流程
           # 1. 整合分析数据
           integrated_data = await self.context_manager.integrate_analysis_data(analysis_input)

           # 2. 构建分析上下文
           analysis_context = await self.build_analysis_context(integrated_data)

           # 3. 生成分析提示词
           analysis_prompt = await self.prompt_engine.generate_short_analysis_prompt(
               analysis_context, integrated_data
           )

           # 4. 调用LLM进行分析
           llm_response = await self.llm_service.analyze(analysis_prompt)

           # 5. 解析和结构化分析结果
           structured_analysis = await self.response_parser.parse_analysis_response(llm_response)

           # 6. 评估分析质量
           quality_assessment = await self.quality_assessor.assess_analysis_quality(
               structured_analysis, analysis_input
           )

           return ShortLLMAnalysis(
               analysis_result=structured_analysis,
               quality_assessment=quality_assessment,
               confidence=quality_assessment.confidence_score,
               reasoning_trace=llm_response.reasoning_trace,
               timestamp=datetime.now()
           )
   ```

2. **做空专用提示词引擎**
   ```python
   class ShortPromptEngine:
       def generate_short_analysis_prompt(self, context: AnalysisContext, data: IntegratedData) -> str:
           # 生成做空分析的主要提示词
           system_prompt = self.get_system_prompt()
           market_data_prompt = self.format_market_data_prompt(data.market_data)
           technical_prompt = self.format_technical_analysis_prompt(data.technical_signals)
           fundamental_prompt = self.format_fundamental_analysis_prompt(data.fundamental_data)
           sentiment_prompt = self.format_sentiment_analysis_prompt(data.sentiment_data)
           risk_prompt = self.format_risk_analysis_prompt(data.risk_factors)

           analysis_task = self.get_analysis_task_prompt(context.analysis_objective)

           return f"""
           {system_prompt}

           **市场数据:**
           {market_data_prompt}

           **技术分析:**
           {technical_prompt}

           **基本面分析:**
           {fundamental_prompt}

           **市场情绪:**
           {sentiment_prompt}

           **风险因素:**
           {risk_prompt}

           **分析任务:**
           {analysis_task}

           请基于以上信息，提供专业的做空分析报告，包括:
           1. 做空机会识别和理由
           2. 潜在入场点和时机
           3. 风险因素和止损建议
           4. 预期收益和胜率评估
           5. 市场逻辑推理链
           """

       def get_system_prompt(self) -> str:
           # 系统角色定义
           return """
           你是一个专业的加密货币做空分析师，具有丰富的市场分析经验。
           你的任务是识别高质量的做空机会，提供深入的市场分析和风险评估。

           分析原则:
           1. 重点关注市场过热、泡沫形成和趋势反转信号
           2. 综合技术分析、基本面和市场情绪进行判断
           3. 严格评估做空特有风险（如无限上涨风险）
           4. 提供具体的入场点、止损点和目标价位
           5. 基于历史数据和当前市场条件评估胜率

           输出要求:
           - 客观、理性的分析，避免情绪化判断
           - 明确的分析逻辑和推理过程
           - 具体的量化指标和阈值
           - 清晰的风险提示和止损建议
           """

       def format_technical_analysis_prompt(self, signals: TechnicalSignals) -> str:
           # 格式化技术分析数据
           signal_summary = []
           for signal in signals.strong_signals:
               signal_summary.append(f"- {signal.type}: 强度{signal.strength:.1f}/10, 置信度{signal.confidence:.1f}%")

           return f"""
           强势做空信号:
           {'\n'.join(signal_summary)}

           关键技术指标:
           - RSI: {signals.rsi_value:.2f} ({'超买' if signals.rsi_value > 70 else '正常'})
           - MACD: {signals.macd_status} ({'顶背离' if signals.macd_divergence else '正常'})
           - 布林带: {signals.bollinger_position} (价格接近{signals.bollinger_position})
           - 成交量: {signals.volume_status} ({'放量下跌' if signals.volume_distribution else '正常'})

           顶部形态识别:
           {self.format_pattern_analysis(signals.patterns)}
           """

       def format_risk_analysis_prompt(self, risk_factors: RiskFactors) -> str:
           # 格式化风险分析数据
           return f"""
           主要风险因素:
           - 无限上涨风险: {'高' if risk_factors.unlimited_upside_risk else '中'}
           - 流动性风险: {risk_factors.liquidity_risk_level}
           - 强制平仓风险: {risk_factors.liquidation_risk_level}
           - 市场波动风险: {risk_factors.volatility_risk_level}
           - 监管风险: {risk_factors.regulatory_risk_level}

           风险评估: {risk_factors.overall_risk_score:.1f}/10
           """
   ```

3. **上下文管理系统**
   ```python
   class ContextManager:
       def __init__(self, config: ContextConfig):
           self.config = config
           self.context_cache = ContextCache(config.cache_config)
           self.data_integrator = DataIntegrator(config.integrator_config)

       async def build_analysis_context(self, integrated_data: IntegratedData) -> AnalysisContext:
           # 构建分析上下文
           market_context = await self.build_market_context(integrated_data.market_data)
           historical_context = await self.build_historical_context(integrated_data.historical_data)
           analysis_context = await self.build_analysis_objective_context()

           return AnalysisContext(
               market_context=market_context,
               historical_context=historical_context,
               analysis_context=analysis_context,
               timestamp=datetime.now()
           )

       async def build_market_context(self, market_data: MarketData) -> MarketContext:
           # 构建市场环境上下文
           return MarketContext(
               market_regime=self.identify_market_regime(market_data),
               volatility_state=self.assess_volatility_state(market_data),
               liquidity_state=self.assess_liquidity_state(market_data),
               sentiment_state=self.assess_sentiment_state(market_data),
               trend_state=self.identify_trend_state(market_data)
           )

       async def integrate_analysis_data(self, analysis_input: ShortAnalysisInput) -> IntegratedData:
           # 整合分析数据
           market_data = await self.process_market_data(analysis_input.market_data)
           technical_signals = await self.process_technical_signals(analysis_input.technical_signals)
           fundamental_data = await self.process_fundamental_data(analysis_input.fundamental_data)
           sentiment_data = await self.process_sentiment_data(analysis_input.sentiment_data)
           risk_factors = await self.process_risk_factors(analysis_input.risk_factors)

           return IntegratedData(
               market_data=market_data,
               technical_signals=technical_signals,
               fundamental_data=fundamental_data,
               sentiment_data=sentiment_data,
               risk_factors=risk_factors
           )
   ```

4. **响应解析器**
   ```python
   class ResponseParser:
       async def parse_analysis_response(self, llm_response: LLMResponse) -> StructuredAnalysis:
           # 解析LLM分析响应
           try:
               # 解析做空机会识别
               short_opportunity = self.parse_short_opportunity(llm_response.content)

               # 解析入场点建议
               entry_points = self.parse_entry_points(llm_response.content)

               # 解析止损建议
               stop_loss = self.parse_stop_loss(llm_response.content)

               # 解析目标价位
               target_prices = self.parse_target_prices(llm_response.content)

               # 解析风险评估
               risk_assessment = self.parse_risk_assessment(llm_response.content)

               # 解析胜率评估
               win_rate_assessment = self.parse_win_rate_assessment(llm_response.content)

               # 解析推理过程
               reasoning_chain = self.parse_reasoning_chain(llm_response.content)

               return StructuredAnalysis(
                   short_opportunity=short_opportunity,
                   entry_points=entry_points,
                   stop_loss=stop_loss,
                   target_prices=target_prices,
                   risk_assessment=risk_assessment,
                   win_rate_assessment=win_rate_assessment,
                   reasoning_chain=reasoning_chain,
                   confidence_score=self.calculate_confidence_score(llm_response),
                   analysis_quality=self.analyze_analysis_quality(llm_response)
               )

           except Exception as e:
               logger.error(f"Failed to parse LLM response: {e}")
               return self.create_fallback_analysis(llm_response)

       def parse_short_opportunity(self, content: str) -> ShortOpportunity:
           # 解析做空机会识别
           opportunity_patterns = [
               r"做空机会[：:]\s*(.+)",
               r"建议做空[：:]\s*(.+)",
               r"空头机会[：:]\s*(.+)"
           ]

           for pattern in opportunity_patterns:
               match = re.search(pattern, content, re.IGNORECASE)
               if match:
                   return ShortOpportunity(
                       opportunity_type=self.classify_opportunity_type(match.group(1)),
                       confidence=self.extract_confidence_from_text(match.group(1)),
                       reasoning=match.group(1)
                   )

           return ShortOpportunity(
               opportunity_type="unclear",
               confidence=0.0,
               reasoning="无法解析做空机会识别"
           )
   ```

5. **分析质量评估**
   ```python
   class AnalysisQualityAssessor:
       async def assess_analysis_quality(self, analysis: StructuredAnalysis, input_data: ShortAnalysisInput) -> QualityAssessment:
           # 评估分析质量
           logical_consistency = self.assess_logical_consistency(analysis)
           data_utilization = self.assess_data_utilization(analysis, input_data)
           risk_awareness = self.assess_risk_awareness(analysis)
           reasoning_depth = self.assess_reasoning_depth(analysis)
           actionability = self.assess_actionability(analysis)

           overall_quality = self.calculate_overall_quality(
               logical_consistency, data_utilization, risk_awareness, reasoning_depth, actionability
           )

           return QualityAssessment(
               overall_quality=overall_quality,
               logical_consistency=logical_consistency,
               data_utilization=data_utilization,
               risk_awareness=risk_awareness,
               reasoning_depth=reasoning_depth,
               actionability=actionability,
               confidence_score=overall_quality / 100
           )

       def assess_logical_consistency(self, analysis: StructuredAnalysis) -> float:
           # 评估逻辑一致性
           consistency_score = 100.0

           # 检查分析逻辑是否自洽
           if self.has_contradictory_conclusions(analysis):
               consistency_score -= 30

           # 检查推理链是否完整
           if not self.has_complete_reasoning_chain(analysis):
               consistency_score -= 20

           # 检查结论是否基于数据
           if not self.conclusion_based_on_data(analysis):
               consistency_score -= 25

           return max(0, consistency_score)

       def assess_risk_awareness(self, analysis: StructuredAnalysis) -> float:
           # 评估风险意识
           risk_score = 100.0

           # 检查是否提到做空特有风险
           if not self.mentions_short_selling_risks(analysis):
               risk_score -= 40

           # 检查是否提供止损建议
           if not self.has_stop_loss_recommendation(analysis):
               risk_score -= 30

           # 检查风险评估是否充分
           if not self.has_comprehensive_risk_assessment(analysis):
               risk_score -= 20

           return max(0, risk_score)
   ```

### LLM服务优化
1. **缓存和上下文复用**
   ```python
   class LLMCache:
       def __init__(self, config: CacheConfig):
           self.config = config
           self.redis_client = Redis(config.redis_config)
           self.local_cache = {}

       async def get_cached_analysis(self, cache_key: str) -> Optional[ShortLLMAnalysis]:
           # 获取缓存的分析结果
           # 1. 检查本地缓存
           if cache_key in self.local_cache:
               cached_result = self.local_cache[cache_key]
               if self.is_cache_valid(cached_result):
                   return cached_result

           # 2. 检查Redis缓存
           cached_data = await self.redis_client.get(cache_key)
           if cached_data:
               return self.deserialize_analysis(cached_data)

           return None

       async def cache_analysis(self, cache_key: str, analysis: ShortLLMAnalysis):
           # 缓存分析结果
           # 1. 本地缓存
           self.local_cache[cache_key] = analysis

           # 2. Redis缓存
           serialized = self.serialize_analysis(analysis)
           await self.redis_client.setex(
               cache_key,
               self.config.cache_ttl,
               serialized
           )
   ```

2. **模型负载均衡**
   ```python
   class ModelLoadBalancer:
       def __init__(self, config: LoadBalancerConfig):
           self.config = config
           self.models = config.available_models
           self.model_performance = {}

       async def select_best_model(self, task_type: str, complexity: str) -> str:
           # 选择最佳模型
           # 1. 基于任务类型
           if task_type == "complex_analysis":
               preferred_models = [m for m in self.models if m.capabilities.get("complex_reasoning")]
           elif task_type == "quick_assessment":
               preferred_models = [m for m in self.models if m.capabilities.get("fast_response")]

           # 2. 基于性能指标选择
           best_model = None
           best_score = -1

           for model in preferred_models:
               performance_score = self.calculate_model_performance_score(model)
               if performance_score > best_score:
                   best_score = performance_score
                   best_model = model

           return best_model.name if best_model else self.models[0].name

       def calculate_model_performance_score(self, model: LLMModel) -> float:
           # 计算模型性能得分
           latency_score = 1.0 / (model.avg_latency + 0.1)
           accuracy_score = model.accuracy_score
           cost_score = 1.0 / (model.cost_per_1k_tokens + 0.1)

           return (latency_score * 0.3 + accuracy_score * 0.5 + cost_score * 0.2)
   ```

### 技术实现要点
- **专业提示词**: 针对做空分析的专业提示词工程
- **上下文管理**: 智能的上下文整合和管理
- **质量控制**: 完善的分析质量评估机制
- **性能优化**: 缓存、负载均衡和成本优化
- **错误处理**: 健壮的错误处理和降级机制

## Deliverables

1. **LLM分析引擎**
   - ShortLLMAnalyzer 主类实现
   - 做空专用提示词模板
   - 上下文管理系统

2. **响应处理系统**
   - 响应解析器
   - 结构化输出格式
   - 质量评估算法

3. **优化组件**
   - 缓存管理系统
   - 模型负载均衡器
   - 成本优化机制

4. **测试与文档**
   - LLM分析质量测试
   - 性能基准测试
   - 成本效益分析
   - 使用指南

## Dependencies
- 040-architecture-design (架构设计完成)
- 041-data-receiver (数据接收模块)
- 042-short-indicators (做空指标引擎)
- 043-signal-recognition (信号识别系统)
- LLM服务模块接口

## Risks and Mitigation

### 技术风险
- **LLM性能**: 模型性能不稳定影响分析质量
  - 缓解: 实现模型监控和自动切换
- **响应延迟**: LLM响应时间影响系统实时性
  - 缓解: 使用缓存和异步处理优化

### 业务风险
- **分析质量**: LLM分析质量可能不够专业
  - 缓解: 专业的提示词工程和质量评估
- **成本控制**: LLM API调用成本可能过高
  - 缓解: 智能缓存和成本优化策略

## Success Metrics
- LLM分析响应时间: <3秒
- 分析质量评分: >85%
- API调用成本优化: <基准成本的80%
- 缓存命中率: >70%
- 分析一致性评分: >90%
- 系统可用性: >99%

## Notes
- 重点关注做空分析的专业性和准确性
- 确保LLM分析的质量和一致性
- 优化API调用成本和响应时间
- 建立完善的质量控制机制