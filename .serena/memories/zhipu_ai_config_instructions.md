# 智谱AI配置说明

## 用户提供的配置信息
- API密钥: fb0baa47a3144339ab434c8bdd7b4ee2.Rk3yCpEU0FraOnQP
- 模型链接: https://open.bigmodel.cn/api/paas/v4/chat/completions
- 模型名称: glm-4.5-flash

## 集成步骤

### 1. 环境变量设置
```bash
export ZHIPUAI_API_KEY="fb0baa47a3144339ab434c8bdd7b4ee2.Rk3yCpEU0FraOnQP"
```

### 2. 需要修改的文件

#### src/crypto_trading_agents/services/llm_service.py
需要添加智谱AI的适配器支持：

1. 添加新的提供商常量
2. 在 `_is_provider_available` 方法中添加智谱AI检查
3. 创建 `_create_zhipuai_adapter` 方法
4. 在 `_create_adapter` 方法中添加智谱AI分支

#### src/crypto_trading_agents/config/ai_analysis_config.py
需要在配置模板中添加智谱AI支持

### 3. 验证配置
设置环境变量后，运行诊断脚本来验证配置是否正确