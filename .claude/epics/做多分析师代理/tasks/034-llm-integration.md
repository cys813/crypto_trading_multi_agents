---
name: LLM服务集成模块
epic: 做多分析师代理
task_id: 005-llm-integration
status: pending
priority: P2
estimated_hours: 48
parallel: true
dependencies: ["001-architecture-design"]
github_issue: https://github.com/cys813/crypto_trading_multi_agents/issues/34
---

# Task: LLM服务集成模块

## Task Description
实现LLM服务集成模块，将技术分析、新闻和社交数据整合为结构化的LLM输入，通过专门的提示词工程和上下文管理，实现深度分析和推理，为做多决策提供智能化的分析支持。

## Acceptance Criteria

### LLM服务集成
- [ ] 完成多LLM服务提供商支持(OpenAI, Azure OpenAI, Anthropic)
- [ ] 实现统一的LLM接口封装
- [ ] 完成API连接和认证管理
- [ ] 实现请求重试和错误处理
- [ ] 建立成本控制和配额管理

### 数据整合引擎
- [ ] 完成多源数据结构化整合
- [ ] 实现上下文长度优化
- [ ] 建立数据优先级和过滤机制
- [ ] 完成数据压缩和格式化
- [ ] 实现实时数据更新机制

### 提示词工程
- [ ] 设计专门化的做多分析提示词模板
- [ ] 实现动态提示词生成
- [ ] 完成上下文管理优化
- [ ] 建立提示词效果评估
- [ ] 实现A/B测试和优化

### 性能和可靠性
- [ ] LLM分析响应时间 <10秒
- [ ] 服务可用性 >99%
- [ ] 成本控制在预算范围内
- [ ] 结果解析准确率 >95%
- [ ] 并发处理能力测试通过

## Technical Implementation Details

### 核心架构设计
1. **LLMService (LLM服务)**
   ```python
   class LLMService:
       def __init__(self, config: LLMConfig):
           self.config = config
           self.providers = self._init_providers()
           self.cost_tracker = CostTracker()
           self.cache = LLMCache()

       async def analyze(self, data: AnalysisInput, template: PromptTemplate) -> LLMResponse:
           # 执行LLM分析
           pass

       async def batch_analyze(self, requests: List[AnalysisRequest]) -> List[LLMResponse]:
           # 批量分析
           pass
   ```

2. **LLMProvider (LLM提供商基类)**
   ```python
   class LLMProvider(ABC):
       @abstractmethod
       async def generate(self, prompt: str, params: Dict) -> LLMResponse:
           pass

       async def validate_request(self, request: AnalysisRequest) -> bool:
           # 验证请求
           pass

       async def handle_error(self, error: Exception) -> LLMResponse:
           # 错误处理
           pass
   ```

3. **DataIntegrator (数据整合器)**
   ```python
   class DataIntegrator:
       def integrate_analysis_data(self,
                                technical_data: TechnicalData,
                                news_data: NewsData,
                                social_data: SocialData) -> AnalysisInput:
           # 整合分析数据
           pass

       def optimize_context(self, data: AnalysisInput, max_tokens: int) -> OptimizedInput:
           # 优化上下文
           pass

       def prioritize_data(self, data: AnalysisInput) -> PrioritizedInput:
           # 数据优先级排序
           pass
   ```

### 具体LLM提供商实现
1. **OpenAI Provider**
   ```python
   class OpenAIProvider(LLMProvider):
       def __init__(self, api_key: str, model: str = "gpt-4"):
           self.client = OpenAI(api_key=api_key)
           self.model = model

       async def generate(self, prompt: str, params: Dict) -> LLMResponse:
           response = await self.client.chat.completions.create(
               model=self.model,
               messages=self._format_messages(prompt),
               **params
           )
           return self._parse_response(response)
   ```

2. **Azure OpenAI Provider**
   ```python
   class AzureOpenAIProvider(LLMProvider):
       def __init__(self, endpoint: str, api_key: str, deployment: str):
           self.client = AzureOpenAI(
               azure_endpoint=endpoint,
               api_key=api_key,
               api_version="2024-02-15-preview"
           )
           self.deployment = deployment
   ```

3. **Anthropic Provider**
   ```python
   class AnthropicProvider(LLMProvider):
       def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
           self.client = Anthropic(api_key=api_key)
           self.model = model
   ```

### 提示词工程实现
1. **PromptTemplate (提示词模板)**
   ```python
   class PromptTemplate:
       def __init__(self, template_path: str):
           self.template = self._load_template(template_path)
           self.variables = self._extract_variables()

       def render(self, context: Dict) -> str:
           # 渲染提示词
           pass

       def optimize_length(self, context: Dict, max_tokens: int) -> str:
           # 优化提示词长度
           pass
   ```

2. **专门化的做多分析提示词**
   ```python
   LONG_ANALYSIS_TEMPLATE = """
   你是一位专业的加密货币做多分析师，请基于以下数据进行深度分析：

   技术面数据：
   - 主要趋势：{trend_data}
   - 关键指标：{indicators_data}
   - 支撑阻力：{support_resistance_data}
   - 信号强度：{signal_strength}

   基本面数据：
   - 项目动态：{fundamental_data}
   - 市场情绪：{market_sentiment}
   - 资金流向：{capital_flow}

   新闻和社交数据：
   - 重要新闻：{important_news}
   - 社交媒体情绪：{social_sentiment}
   - 影响力人物观点：{influencer_opinions}

   请分析：
   1. 当前市场环境的做多机会评估
   2. 技术面指标的一致性分析
   3. 潜在的入场时机和价格目标
   4. 风险因素和应对策略
   5. 做多成功的概率评估

   分析格式要求：
   - 结论先行：明确的做多建议
   - 数据支撑：用具体数据支持观点
   - 风险提示：客观分析风险因素
   - 操作建议：具体的入场、止损、止盈建议
   """
   ```

### 上下文管理优化
1. **ContextManager (上下文管理器)**
   ```python
   class ContextManager:
       def __init__(self, max_tokens: int = 4000):
           self.max_tokens = max_tokens
           self.compressor = ContextCompressor()

       def prepare_context(self, data: AnalysisInput) -> OptimizedContext:
           # 准备优化上下文
           pass

       def compress_context(self, context: str) -> str:
           # 压缩上下文
           pass

       def prioritize_information(self, context: Dict) -> Dict:
           # 信息优先级排序
           pass
   ```

2. **ContextCompressor (上下文压缩器)**
   ```python
   class ContextCompressor:
       def compress_technical_data(self, data: TechnicalData) -> str:
           # 压缩技术数据
           pass

       def compress_news_data(self, data: NewsData) -> str:
           # 压缩新闻数据
           pass

       def compress_social_data(self, data: SocialData) -> str:
           # 压缩社交数据
           pass
   ```

### 成本控制和配额管理
1. **CostTracker (成本追踪器)**
   ```python
   class CostTracker:
       def __init__(self, budget: float):
           self.budget = budget
           self.used = 0.0
           self.daily_usage = {}

       def track_usage(self, tokens: int, provider: str) -> float:
           # 追踪使用情况
           pass

       def check_budget(self, estimated_cost: float) -> bool:
           # 检查预算
           pass

       def get_usage_report(self) -> UsageReport:
           # 获取使用报告
           pass
   ```

2. **QuotaManager (配额管理器)**
   ```python
   class QuotaManager:
       def __init__(self, provider_configs: Dict[str, ProviderConfig]):
           self.providers = provider_configs
           self.current_usage = {}

       def check_quota(self, provider: str) -> bool:
           # 检查配额
           pass

       def rotate_provider(self) -> str:
           # 轮换提供商
           pass

       def reset_quota(self, provider: str) -> None:
           # 重置配额
           pass
   ```

## Deliverables

1. **LLM服务核心**
   - LLMService 类实现
   - 多LLM提供商支持
   - 统一接口封装
   - 错误处理和重试机制

2. **数据整合引擎**
   - DataIntegrator 实现
   - 上下文优化器
   - 数据优先级管理
   - 实时更新机制

3. **提示词系统**
   - PromptTemplate 类
   - 专门化提示词模板
   - 动态提示词生成
   - 提示词效果评估

4. **管理系统**
   - 成本追踪器
   - 配额管理器
   - 性能监控
   - 使用报告

## Dependencies
- 001-architecture-design (架构设计完成)
- LLM服务提供商账号和API密钥
- 数据接收模块提供的结构化数据
- 缓存系统配置

## Risks and Mitigation

### 技术风险
- **API稳定性**: LLM服务API不稳定
  - 缓解: 多提供商支持和重试机制
- **成本控制**: LLM调用成本过高
  - 缓解: 成本追踪和配额管理

### 质量风险
- **分析质量**: LLM分析质量不达标
  - 缓解: 提示词优化和结果验证
- **响应时间**: 分析响应时间过长
  - 缓解: 缓存优化和异步处理

## Success Metrics
- LLM分析响应时间: <10秒
- 服务可用性: >99%
- 成本控制: 预算内
- 结果解析准确率: >95%
- 用户满意度: >85%

## Notes
- 重点关注分析质量和成本控制
- 确支持多种LLM服务商切换
- 考虑未来的提示词优化需求