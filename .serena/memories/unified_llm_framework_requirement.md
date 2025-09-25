# 统一LLM框架架构要求

## 核心要求
**整个系统希望用一个LLM的框架，不要每一个都创建一个LLM的配置和调用**

## 架构原则

### 1. 统一LLM服务
- 使用单一的LLM服务管理器 (`LLMService`)
- 所有模块通过统一接口调用LLM
- 避免在各个模块中重复创建LLM配置和调用逻辑

### 2. 标准化AI分析混入
- 使用 `StandardAIAnalysisMixin` 作为基类
- 提供统一的AI分析模式和方法
- 确保所有AI分析模块具有一致的行为

### 3. 配置集中化
- 统一的LLM服务配置 (`get_unified_llm_service_config()`)
- 支持多个LLM提供商 (DashScope, DeepSeek等)
- 自动故障转移和错误处理

## 实现模式

### 模块结构
```python
class AnalystModule(StandardAIAnalysisMixin):
    def __init__(self, config):
        super().__init__()
        # 初始化统一LLM服务
        initialize_llm_service(config.get("llm_service_config"))
    
    def analyze_with_ai(self, traditional_analysis, raw_data):
        # 使用统一的AI增强分析流程
        return self.analyze_with_ai_enhancement(raw_data, lambda data: traditional_analysis)
```

### 核心文件
- `services/llm_service.py` - 统一LLM服务管理器
- `services/ai_analysis_mixin.py` - 标准化AI分析混入类
- `config/ai_analysis_config.py` - 统一LLM配置管理

### 已重构模块
1. **OnchainAnalyst** - 链上数据分析
2. **SentimentAnalyst** - 情绪分析  
3. **DeFiAnalyst** - DeFi协议分析
4. **BullResearcher** - 牛市研究
5. **BearResearcher** - 熊市研究
6. **AITechnicalAnalyzer** - AI技术分析

## 开发规范

### 新模块开发
1. 继承 `StandardAIAnalysisMixin`
2. 使用 `initialize_llm_service()` 初始化服务
3. 调用 `self.call_ai_analysis()` 进行AI分析
4. 使用 `self.parse_ai_json_response()` 解析响应
5. 实现专门化的 `_build_xxx_prompt()` 方法
6. 使用 `_combine_standard_analyses()` 组合结果

### 禁止模式
- ❌ 在模块中直接创建LLM客户端
- ❌ 在模块中维护独立的LLM配置
- ❌ 重复实现LLM调用逻辑
- ❌ 不同模块使用不同的AI分析模式

### 测试要求
- 使用统一的 `MockLLMAdapter` 进行测试
- 测试所有模块的LLM集成
- 验证fallback机制和错误处理

## 维护优势
- **代码重用**：消除LLM调用的重复代码
- **配置简化**：统一管理LLM提供商和配置
- **维护便利**：修改LLM逻辑只需在一处进行
- **一致性**：所有AI分析具有统一的行为模式
- **扩展性**：新增LLM提供商或模块都遵循同一模式

## 注意事项
- 所有新的AI分析模块都必须遵循这个统一框架
- 不允许为单个模块创建独立的LLM配置
- 确保所有AI相关功能都通过统一服务进行