# 做多分析师代理 (Long Analyst Agent)

## Epic Overview
做多分析师代理是加密货币多代理交易系统中的核心分析组件，专门负责接收来自交易数据获取代理、新闻收集代理和社交媒体分析代理的多维度数据，通过技术指标分析专门识别做多信号，结合LLM深度分析生成高质量的做多分析报告和胜率评估。

## GitHub Issue Links
- **主Epic**: [#29 做多分析师代理](https://github.com/cys813/crypto_trading_multi_agents/issues/29)
- **任务分解**: 10个子任务，详见下方任务列表

## 任务分解 (Task Breakdown)

### 核心任务列表

| Issue | 任务名称 | 工期 | 优先级 | 状态 |
|-------|---------|------|--------|------|
| [#30](https://github.com/cys813/crypto_trading_multi_agents/issues/30) | 多维分析架构设计 | 5天 | P1 | 待处理 |
| [#31](https://github.com/cys813/crypto_trading_multi_agents/issues/31) | 数据接收与处理模块 | 6天 | P1 | 待处理 |
| [#32](https://github.com/cys813/crypto_trading_multi_agents/issues/32) | 技术指标计算引擎 | 8天 | P1 | 待处理 |
| [#33](https://github.com/cys813/crypto_trading_multi_agents/issues/33) | 信号识别算法实现 | 7天 | P2 | 待处理 |
| [#34](https://github.com/cys813/crypto_trading_multi_agents/issues/34) | LLM服务集成模块 | 6天 | P2 | 待处理 |
| [#35](https://github.com/cys813/crypto_trading_multi_agents/issues/35) | 胜率计算算法开发 | 5天 | P2 | 待处理 |
| [#36](https://github.com/cys813/crypto_trading_multi_agents/issues/36) | 分析报告生成模块 | 4天 | P3 | 待处理 |
| [#37](https://github.com/cys813/crypto_trading_multi_agents/issues/37) | 配置管理系统 | 3天 | P3 | 待处理 |
| [#38](https://github.com/cys813/crypto_trading_multi_agents/issues/38) | 监控与质量保证 | 3天 | P4 | 待处理 |
| [#39](https://github.com/cys813/crypto_trading_multi_agents/issues/39) | 集成测试与优化 | 5天 | P4 | 待处理 |

### 任务依赖关系
```
架构设计 (#30)
├── 数据接收 (#31)
├── 技术指标引擎 (#32)
├── 信号识别 (#33) (依赖 #30, #32)
├── LLM集成 (#34)
├── 胜率计算 (#35) (依赖 #30, #33)
├── 报告生成 (#36) (依赖 #30, #34, #35)
├── 配置管理 (#37)
├── 监控系统 (#38) (依赖 #30, #37)
└── 集成测试 (#39) (依赖 #31-38)
```

## Worktree说明
本目录为做多分析师代理epic的专用worktree，基于分支 `epic/long-analyst-agent`。
- **Worktree路径**: `/home/lighthouse/crypto_trading_multi_agents/epic/做多分析师代理`
- **Git分支**: `epic/long-analyst-agent`
- **用途**: 专门用于做多分析师代理的开发和测试

## 相关文档
- **Epic详细文档**: `../.claude/epics/做多分析师代理/epic.md`
- **PRD文档**: `../.claude/prds/做多分析师代理.md`
- **任务文件**: `../.claude/epics/做多分析师代理/tasks/`

## 开发说明
1. 所有与做多分析师代理相关的开发工作应在此worktree中进行
2. 定期同步main分支的最新更改
3. 遵循既定的代码规范和架构设计
4. 定期更新任务状态和进度报告

---
*最后更新: 2025-09-25*
*Git分支: epic/long-analyst-agent*
*Worktree创建: Claude Code*