# 加密货币交易系统项目概览

## 项目基本信息
- **项目名称**: crypto_trading_claude
- **项目路径**: /home/cys/crypto_trading_claude
- **项目类型**: 多Agent加密货币交易系统
- **开发语言**: Python
- **创建日期**: 2025-08-15
- **开发者**: cys

## 项目目标
基于Claude Code的agents功能构建一个智能化的多agent加密货币交易系统，实现市场分析、策略执行和风险控制的协同工作。

## 核心特性
- **多Agent协作**: 市场分析Agent、策略执行Agent、风险控制Agent
- **实时决策**: 基于实时市场数据进行交易决策
- **风险管理**: 多层次风险控制机制
- **可扩展性**: 支持多种交易策略和市场数据源

## 系统架构
### Agent角色定义
1. **市场分析Agent (Market Analysis Agent)**
   - 实时监控加密货币市场数据
   - 技术指标计算与分析
   - 市场趋势识别与预测
   - 生成交易信号

2. **策略执行Agent (Strategy Execution Agent)**
   - 接收市场分析信号
   - 执行交易策略
   - 订单管理
   - 交易记录和报告

3. **风险控制Agent (Risk Control Agent)**
   - 实时风险评估
   - 仓位管理
   - 止损止盈设置
   - 异常交易监控

### 技术栈
- **核心框架**: Python, Claude Code Agents
- **数据处理**: pandas, numpy, scipy
- **技术分析**: TA-Lib, ccxt
- **机器学习**: scikit-learn, tensorflow, torch
- **Web服务**: fastapi, uvicorn
- **异步编程**: asyncio, aiohttp, websockets

## 项目状态
- **当前阶段**: 需求分析和项目初始化阶段
- **项目文档**: 完整的需求规格说明书 (REQUIREMENTS.md)
- **开发环境**: 已配置Serena项目文件
- **代码结构**: 规划中，待实施

## 下一步计划
1. 搭建项目基础架构
2. 实现Agent通信机制
3. 开发核心功能模块
4. 集成外部数据源和交易接口
5. 完善监控和风险管理功能

## 风险评估
- **技术风险**: 系统复杂性、实时性要求
- **业务风险**: 市场波动、流动性风险
- **合规风险**: 监管政策变化
- **缓解措施**: 分阶段实施、监控告警、应急预案