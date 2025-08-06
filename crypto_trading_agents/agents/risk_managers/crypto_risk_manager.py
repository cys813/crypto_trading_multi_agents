"""
加密货币风险管理器 - 综合风险监控和管理

基于原版风险管理架构，针对加密货币市场特征优化
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from enum import Enum

from crypto_trading_agents.services.ai_analysis_mixin import StandardAIAnalysisMixin

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class RiskType(Enum):
    """风险类型"""
    MARKET_RISK = "market_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    CREDIT_RISK = "credit_risk"
    OPERATIONAL_RISK = "operational_risk"
    REGULATORY_RISK = "regulatory_risk"
    SYSTEMIC_RISK = "systemic_risk"

class CryptoRiskManager(StandardAIAnalysisMixin):
    """加密货币风险管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化加密货币风险管理器
        
        Args:
            config: 配置字典
        """
        super().__init__()
        self.config = config
        self.risk_config = config.get("risk_config", {})
        
        # 初始化统一LLM服务
        from crypto_trading_agents.services.llm_service import initialize_llm_service
        from crypto_trading_agents.config.ai_analysis_config import get_unified_llm_service_config
        
        llm_config = get_unified_llm_service_config()
        initialize_llm_service(llm_config)
        
        # 风险阈值配置
        self.max_portfolio_risk = self.risk_config.get("max_portfolio_risk", 0.02)
        self.max_position_risk = self.risk_config.get("max_position_risk", 0.005)
        self.max_drawdown = self.risk_config.get("max_drawdown", 0.10)
        self.stop_loss_threshold = self.risk_config.get("stop_loss_threshold", 0.05)
        self.var_confidence = self.risk_config.get("var_confidence", 0.95)
        
        # 风险监控数据
        self.risk_metrics = {}
        self.risk_alerts = []
        self.risk_limits = {}
        self.historical_risk = []
        
        # 风险模型配置
        self.risk_models = self.risk_config.get("risk_models", ["var", "stress_test", "scenario"])
    
    def collect_data(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        收集风险评估数据
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            风险评估数据
        """
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            start_dt = end_dt - timedelta(days=30)  # 风险分析需要更长历史数据
            
            return {
                "symbol": symbol,
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_date,
                "market_risk_data": self._collect_market_risk_data(symbol),
                "liquidity_risk_data": self._collect_liquidity_risk_data(symbol),
                "credit_risk_data": self._collect_credit_risk_data(symbol),
                "operational_risk_data": self._collect_operational_risk_data(symbol),
                "regulatory_risk_data": self._collect_regulatory_risk_data(symbol),
                "portfolio_risk_data": self._collect_portfolio_risk_data(symbol), 
                "systemic_risk_data": self._collect_systemic_risk_data(symbol),
            }
            
        except Exception as e:
            logger.error(f"Error collecting risk data for {symbol}: {str(e)}")
            return {"error": str(e)}
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析风险数据 - AI增强版本
        
        Args:
            data: 风险评估数据
            
        Returns:
            风险分析结果（包含AI增强分析）
        """
        try:
            if "error" in data:
                return {"error": data["error"]}
            
            # 执行传统风险分析
            traditional_analysis = self._perform_traditional_risk_analysis(data)
            
            # 使用AI增强分析
            return self.analyze_with_ai_enhancement(
                data, 
                lambda raw_data: traditional_analysis
            )
            
        except Exception as e:
            logger.error(f"Error analyzing risk data: {str(e)}")
            return {"error": str(e)}
    
    def _perform_traditional_risk_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行传统的风险分析
        
        Args:
            data: 风险评估数据
            
        Returns:
            传统风险分析结果
        """
        market_risk_data = data.get("market_risk_data", {})
        liquidity_risk_data = data.get("liquidity_risk_data", {})
        credit_risk_data = data.get("credit_risk_data", {})
        operational_risk_data = data.get("operational_risk_data", {})
        regulatory_risk_data = data.get("regulatory_risk_data", {})
        portfolio_risk_data = data.get("portfolio_risk_data", {})
        systemic_risk_data = data.get("systemic_risk_data", {})
        
        # 分析各类风险
        market_risk_analysis = self._analyze_market_risk(market_risk_data)
        liquidity_risk_analysis = self._analyze_liquidity_risk(liquidity_risk_data)
        credit_risk_analysis = self._analyze_credit_risk(credit_risk_data)
        operational_risk_analysis = self._analyze_operational_risk(operational_risk_data)
        regulatory_risk_analysis = self._analyze_regulatory_risk(regulatory_risk_data)
        portfolio_risk_analysis = self._analyze_portfolio_risk(portfolio_risk_data)
        systemic_risk_analysis = self._analyze_systemic_risk(systemic_risk_data)
        
        # 综合风险评估
        overall_risk = self._assess_overall_risk(
            market_risk_analysis, liquidity_risk_analysis, credit_risk_analysis,
            operational_risk_analysis, regulatory_risk_analysis, 
            portfolio_risk_analysis, systemic_risk_analysis
        )
        
        # 生成风险预警
        risk_alerts = self._generate_risk_alerts(overall_risk)
        
        # 生成风险缓解建议
        risk_mitigation = self._generate_risk_mitigation(overall_risk)
        
        # 检查风险限额
        risk_limit_check = self._check_risk_limits(overall_risk)
        
        # 压力测试
        stress_test_results = self._run_stress_tests(data)
        
        return {
            "market_risk": market_risk_analysis,
            "liquidity_risk": liquidity_risk_analysis,
            "credit_risk": credit_risk_analysis,
            "operational_risk": operational_risk_analysis,
            "regulatory_risk": regulatory_risk_analysis,
            "portfolio_risk": portfolio_risk_analysis,
            "systemic_risk": systemic_risk_analysis,
            "overall_risk": overall_risk,
            "risk_alerts": risk_alerts,
            "risk_mitigation": risk_mitigation,
            "risk_limit_check": risk_limit_check,
            "stress_test_results": stress_test_results,
            "confidence": self._calculate_confidence(overall_risk),
            "risk_dashboard": self._generate_risk_dashboard(overall_risk),
        }
    
    def _build_risk_analysis_prompt(self, raw_data: Dict[str, Any], traditional_analysis: Dict[str, Any]) -> str:
        """
        构建风险分析的AI提示词
        
        Args:
            raw_data: 原始数据
            traditional_analysis: 传统分析结果
            
        Returns:
            AI分析提示词
        """
        symbol = raw_data.get("symbol", "Unknown")
        
        # 综合风险评估摘要
        overall_risk = traditional_analysis.get("overall_risk", {})
        risk_level = overall_risk.get("risk_level", "medium")
        risk_score = overall_risk.get("overall_score", 0.5)
        dominant_risk = overall_risk.get("dominant_risk_type", "market_risk")
        
        # 各类风险摘要
        market_risk = traditional_analysis.get("market_risk", {})
        liquidity_risk = traditional_analysis.get("liquidity_risk", {})
        portfolio_risk = traditional_analysis.get("portfolio_risk", {})
        
        # 风险预警数量
        risk_alerts = traditional_analysis.get("risk_alerts", [])
        alert_count = len(risk_alerts)
        
        # 压力测试结果
        stress_test = traditional_analysis.get("stress_test_results", {})
        worst_case_loss = stress_test.get("worst_case_scenario", {}).get("portfolio_loss", 0)
        
        prompt = f"""
作为专业的加密货币风险管理专家，请基于以下传统风险分析结果提供深度AI增强分析：

## 交易对信息
- 符号: {symbol}
- 分析时间: {raw_data.get('end_date', 'Unknown')}

## 传统风险分析结果摘要

### 综合风险评估
- 风险等级: {risk_level}
- 风险评分: {risk_score:.3f}
- 主导风险类型: {dominant_risk}
- 风险预警数量: {alert_count}

### 主要风险分类分析
- 市场风险等级: {market_risk.get('risk_level', 'unknown')}
- 流动性风险等级: {liquidity_risk.get('risk_level', 'unknown')}
- 投资组合风险等级: {portfolio_risk.get('risk_level', 'unknown')}

### 压力测试结果
- 最坏情况损失: {worst_case_loss:.2%}
- 通过测试场景数: {len([s for s in stress_test.get('scenarios', []) if s.get('pass', True)])}

### 当前风险预警
{chr(10).join([f"- {alert.get('message', '')}" for alert in risk_alerts[:5]])}

## 请提供以下AI增强风险分析

### 1. 风险场景预测
- 基于当前风险状况，预测未来1-7天可能的风险场景
- 识别可能触发风险升级的关键因素
- 评估系统性风险传导的可能性

### 2. 动态风险模型建议
- 基于市场环境变化，建议风险模型参数调整
- 评估当前VaR模型的有效性
- 推荐适合的风险度量指标

### 3. 智能风险预警
- 设计更精准的风险预警触发条件
- 建议风险预警的优先级排序
- 识别可能的风险预警误报

### 4. 风险对冲策略
- 基于当前风险暴露，推荐最优对冲策略
- 评估不同对冲工具的成本效益
- 设计动态风险对冲方案

### 5. 资产配置优化
- 基于风险预算模型，建议资产配置调整
- 评估各资产的边际风险贡献
- 推荐风险调整后的目标收益

### 6. 风险管理建议
- 综合风险管理建议 (降低/维持/接受风险)
- 建议的风险限额调整
- 关键风险监控指标

请以JSON格式返回分析结果，确保包含具体的数值和可执行的风险管理建议。
"""
        return prompt
    
    def _combine_risk_analyses(self, traditional_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        整合传统风险分析和AI分析结果
        
        Args:
            traditional_analysis: 传统风险分析结果
            ai_analysis: AI风险分析结果
            
        Returns:
            整合后的风险分析结果
        """
        # 整合置信度
        traditional_confidence = traditional_analysis.get("confidence", 0.3)
        ai_confidence = ai_analysis.get("confidence", 0.3)
        combined_confidence = (traditional_confidence * 0.3 + ai_confidence * 0.7)
        
        # 整合风险等级评估
        traditional_risk = traditional_analysis.get("overall_risk", {})
        ai_risk_assessment = ai_analysis.get("risk_assessment", {})
        
        combined_risk_assessment = {
            "risk_level": ai_risk_assessment.get("overall_risk_level", traditional_risk.get("risk_level", "medium")),
            "confidence": combined_confidence,
            "traditional_score": traditional_risk.get("overall_score", 0.5),
            "ai_score": ai_risk_assessment.get("risk_score", 0.5),
            "consensus": self._determine_risk_consensus(traditional_risk, ai_risk_assessment),
        }
        
        # 创建增强洞察
        enhanced_insights = {
            "risk_scenario_forecast": ai_analysis.get("risk_scenarios", []),
            "dynamic_risk_factors": ai_analysis.get("dynamic_factors", []),
            "optimal_hedge_strategy": ai_analysis.get("hedge_strategy", {}),
            "asset_allocation_advice": ai_analysis.get("allocation_advice", {}),
            "risk_model_recommendations": ai_analysis.get("model_recommendations", {}),
            "intelligent_alerts": ai_analysis.get("intelligent_alerts", []),
        }
        
        return {
            **traditional_analysis,
            "ai_analysis": ai_analysis,
            "combined_confidence": combined_confidence,  
            "final_risk_assessment": combined_risk_assessment,
            "enhanced_insights": enhanced_insights,
            "analysis_type": "ai_enhanced_risk_management",
        }
    
    def _determine_risk_consensus(self, traditional_risk: Dict[str, Any], ai_risk: Dict[str, Any]) -> str:
        """确定传统风险分析和AI风险分析的共识"""
        traditional_level = traditional_risk.get("risk_level", "medium")
        ai_level = ai_risk.get("overall_risk_level", "medium")
        
        if traditional_level == ai_level:
            return f"strong_consensus_{traditional_level}"
        else:
            # 根据严重程度确定共识类型
            risk_levels = {"low": 1, "medium": 2, "high": 3, "extreme": 4}
            traditional_score = risk_levels.get(traditional_level, 2)
            ai_score = risk_levels.get(ai_level, 2)
            
            if abs(traditional_score - ai_score) == 1:
                return "moderate_consensus"
            else:
                return "low_consensus"

    def _collect_market_risk_data(self, symbol: str) -> Dict[str, Any]:
        """收集市场风险数据"""
        # 模拟市场风险数据
        return {
            "volatility": {
                "daily_volatility": 0.05,
                "weekly_volatility": 0.12,
                "monthly_volatility": 0.25,
            },
            "price_movements": {
                "max_daily_change": 0.08,
                "average_daily_change": 0.02,
                "downside_deviation": 0.03,
            },
            "correlation_data": {
                "btc_correlation": 0.85,
                "market_correlation": 0.72,
                "traditional_assets_correlation": 0.15,
            },
        }
    
    def _collect_liquidity_risk_data(self, symbol: str) -> Dict[str, Any]:
        """收集流动性风险数据"""
        return {
            "market_depth": {
                "bid_depth": 1000000,
                "ask_depth": 1200000,
                "depth_ratio": 0.83,
            },
            "trading_volume": {
                "avg_daily_volume": 50000000,
                "volume_volatility": 0.3,
                "volume_trend": "stable",
            },
            "liquidity_metrics": {
                "bid_ask_spread": 0.001,
                "market_impact": 0.002,
                "liquidity_score": 0.85,
            },
        }
    
    def _collect_credit_risk_data(self, symbol: str) -> Dict[str, Any]:
        """收集信用风险数据"""
        return {
            "counterparty_exposure": {
                "exchange_exposure": 0.8,
                "custodial_exposure": 0.2,
                "defi_exposure": 0.1,
            },
            "credit_ratings": {
                "exchange_rating": "A-",
                "custodian_rating": "A+",
                "protocol_rating": "B+",
            },
            "default_probabilities": {
                "exchange_default_prob": 0.001,
                "custodian_default_prob": 0.0005,
                "protocol_default_prob": 0.005,
            },
        }
    
    def _collect_operational_risk_data(self, symbol: str) -> Dict[str, Any]:
        """收集操作风险数据"""
        return {
            "system_reliability": {
                "uptime": 0.999,
                "error_rate": 0.001,
                "recovery_time": 30,  # seconds
            },
            "security_metrics": {
                "security_incidents": 0,
                "vulnerability_score": 0.1,
                "authentication_strength": 0.95,
            },
            "operational_metrics": {
                "trade_execution_time": 0.5,  # seconds
                "settlement_time": 3600,  # seconds
                "error_correction_time": 600,  # seconds
            },
        }
    
    def _collect_regulatory_risk_data(self, symbol: str) -> Dict[str, Any]:
        """收集监管风险数据"""
        return {
            "regulatory_environment": {
                "jurisdiction_risk": "medium",
                "regulatory_clarity": "high",
                "compliance_score": 0.9,
            },
            "regulatory_changes": {
                "pending_regulations": 2,
                "regulatory_stability": "stable",
                "compliance_cost": "low",
            },
        }
    
    def _collect_portfolio_risk_data(self, symbol: str) -> Dict[str, Any]:
        """收集投资组合风险数据"""
        return {
            "position_data": {
                "total_exposure": 100000,
                "position_concentration": 0.2,
                "leverage_ratio": 2.0,
            },
            "portfolio_metrics": {
                "diversification_ratio": 0.3,
                "correlation_matrix": [[1.0, 0.8], [0.8, 1.0]],
                "risk_contribution": {"btc": 0.6, "eth": 0.4},
            },
        }
    
    def _collect_systemic_risk_data(self, symbol: str) -> Dict[str, Any]:
        """收集系统性风险数据"""
        return {
            "market_conditions": {
                "market_stress_level": "normal",
                "systemic_risk_indicators": 0.3,
                "contagion_risk": "low",
            },
            "macro_factors": {
                "interest_rate_environment": "rising",
                "economic_uncertainty": "medium",
                "geopolitical_risk": "low",
            },
        }
    
    def _analyze_market_risk(self, market_risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析市场风险"""
        volatility = market_risk_data.get("volatility", {})
        daily_vol = volatility.get("daily_volatility", 0.05)
        
        if daily_vol < 0.02:
            risk_level = "low"
        elif daily_vol < 0.05:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            "risk_level": risk_level,
            "volatility_analysis": volatility,
            "var_95": daily_vol * 2.33,  # 95% VaR
            "expected_shortfall": daily_vol * 2.67,  # Expected Shortfall
        }
    
    def _analyze_liquidity_risk(self, liquidity_risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析流动性风险"""
        liquidity_metrics = liquidity_risk_data.get("liquidity_metrics", {})
        liquidity_score = liquidity_metrics.get("liquidity_score", 0.5)
        
        if liquidity_score > 0.8:
            risk_level = "low"
        elif liquidity_score > 0.5:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            "risk_level": risk_level,
            "liquidity_score": liquidity_score,
            "market_depth_analysis": liquidity_risk_data.get("market_depth", {}),
        }
    
    def _analyze_credit_risk(self, credit_risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析信用风险"""
        default_probs = credit_risk_data.get("default_probabilities", {})
        max_default_prob = max(default_probs.values()) if default_probs else 0
        
        if max_default_prob < 0.001:
            risk_level = "low"
        elif max_default_prob < 0.01:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            "risk_level": risk_level,
            "counterparty_analysis": credit_risk_data.get("counterparty_exposure", {}),
            "max_default_probability": max_default_prob,
        }
    
    def _analyze_operational_risk(self, operational_risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析操作风险"""
        system_reliability = operational_risk_data.get("system_reliability", {})
        uptime = system_reliability.get("uptime", 0.99)
        
        if uptime > 0.999:
            risk_level = "low"
        elif uptime > 0.995:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            "risk_level": risk_level,
            "system_reliability": system_reliability,
            "security_analysis": operational_risk_data.get("security_metrics", {}),
        }
    
    def _analyze_regulatory_risk(self, regulatory_risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析监管风险"""
        regulatory_env = regulatory_risk_data.get("regulatory_environment", {})
        compliance_score = regulatory_env.get("compliance_score", 0.5)
        
        if compliance_score > 0.9:
            risk_level = "low"
        elif compliance_score > 0.7:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            "risk_level": risk_level,
            "compliance_analysis": regulatory_env,
            "regulatory_changes": regulatory_risk_data.get("regulatory_changes", {}),
        }
    
    def _analyze_portfolio_risk(self, portfolio_risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析投资组合风险"""
        position_data = portfolio_risk_data.get("position_data", {})
        concentration = position_data.get("position_concentration", 0.2)
        
        if concentration < 0.1:
            risk_level = "low"
        elif concentration < 0.3:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            "risk_level": risk_level,
            "concentration_analysis": position_data,
            "diversification_metrics": portfolio_risk_data.get("portfolio_metrics", {}),
        }
    
    def _analyze_systemic_risk(self, systemic_risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析系统性风险"""
        market_conditions = systemic_risk_data.get("market_conditions", {})
        stress_level = market_conditions.get("market_stress_level", "normal")
        
        risk_level_mapping = {
            "low": "low",
            "normal": "medium", 
            "high": "high",
            "extreme": "extreme"
        }
        
        risk_level = risk_level_mapping.get(stress_level, "medium")
        
        return {
            "risk_level": risk_level,
            "market_stress_analysis": market_conditions,
            "macro_factors": systemic_risk_data.get("macro_factors", {}),
        }
    
    def _assess_overall_risk(self, market_risk: Dict[str, Any], liquidity_risk: Dict[str, Any],
                           credit_risk: Dict[str, Any], operational_risk: Dict[str, Any],
                           regulatory_risk: Dict[str, Any], portfolio_risk: Dict[str, Any],
                           systemic_risk: Dict[str, Any]) -> Dict[str, Any]:
        """评估综合风险"""
        risk_scores = {
            "market": self._risk_level_to_score(market_risk.get("risk_level", "medium")),
            "liquidity": self._risk_level_to_score(liquidity_risk.get("risk_level", "medium")),
            "credit": self._risk_level_to_score(credit_risk.get("risk_level", "medium")),
            "operational": self._risk_level_to_score(operational_risk.get("risk_level", "medium")),
            "regulatory": self._risk_level_to_score(regulatory_risk.get("risk_level", "medium")),
            "portfolio": self._risk_level_to_score(portfolio_risk.get("risk_level", "medium")),
            "systemic": self._risk_level_to_score(systemic_risk.get("risk_level", "medium")),
        }
        
        # 加权平均风险分数
        weights = {
            "market": 0.25,
            "liquidity": 0.15,
            "credit": 0.10,
            "operational": 0.10,
            "regulatory": 0.10,
            "portfolio": 0.20,
            "systemic": 0.10,
        }
        
        overall_score = sum(risk_scores[risk_type] * weights[risk_type] for risk_type in risk_scores)
        overall_level = self._score_to_risk_level(overall_score)
        
        # 识别主导风险
        dominant_risk = self._identify_dominant_risk(risk_scores)
        
        return {
            "overall_score": overall_score,
            "risk_level": overall_level,
            "risk_scores": risk_scores,
            "dominant_risk_type": dominant_risk,
            "risk_distribution": weights,
        }
    
    def _generate_risk_alerts(self, overall_risk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成风险预警"""
        alerts = []
        risk_level = overall_risk.get("risk_level", "medium")
        risk_scores = overall_risk.get("risk_scores", {})
        
        # 高风险预警
        for risk_type, score in risk_scores.items():
            if score > 0.7:
                alerts.append({
                    "type": "high_risk",
                    "risk_category": risk_type,
                    "severity": "high",
                    "message": f"{risk_type}风险等级过高",
                    "score": score,
                })
        
        # 综合风险预警
        if overall_risk.get("overall_score", 0) > 0.6:
            alerts.append({
                "type": "overall_risk",
                "risk_category": "综合",
                "severity": "high",
                "message": "综合风险水平过高，建议降低风险暴露",
                "score": overall_risk.get("overall_score", 0),
            })
        
        return alerts
    
    def _generate_risk_mitigation(self, overall_risk: Dict[str, Any]) -> Dict[str, Any]:
        """生成风险缓解建议"""
        risk_scores = overall_risk.get("risk_scores", {})
        mitigation_strategies = {}
        
        for risk_type, score in risk_scores.items():
            if score > 0.5:
                if risk_type == "market":
                    mitigation_strategies[risk_type] = [
                        "增加对冲头寸",
                        "降低杠杆比率",
                        "分散投资组合",
                    ]
                elif risk_type == "liquidity":
                    mitigation_strategies[risk_type] = [
                        "增加现金储备",
                        "选择流动性更高的资产",
                        "建立应急流动性安排",
                    ]
                elif risk_type == "portfolio":
                    mitigation_strategies[risk_type] = [
                        "降低头寸集中度",
                        "重新平衡投资组合",
                        "调整风险预算分配",
                    ]
        
        return {
            "mitigation_strategies": mitigation_strategies,
            "priority_actions": list(mitigation_strategies.keys())[:3],
            "implementation_timeline": "immediate",
        }
    
    def _check_risk_limits(self, overall_risk: Dict[str, Any]) -> Dict[str, Any]:
        """检查风险限额"""
        risk_score = overall_risk.get("overall_score", 0)
        
        limit_checks = {
            "portfolio_risk_limit": {
                "limit": self.max_portfolio_risk,
                "current": risk_score,
                "status": "pass" if risk_score <= self.max_portfolio_risk else "fail",
            },
            "drawdown_limit": {
                "limit": self.max_drawdown,
                "current": risk_score * 0.5,  # 简化的回撤估算
                "status": "pass" if risk_score * 0.5 <= self.max_drawdown else "fail",
            },
        }
        
        return {
            "limit_checks": limit_checks,
            "overall_status": "pass" if all(check["status"] == "pass" for check in limit_checks.values()) else "fail",
        }
    
    def _run_stress_tests(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """运行压力测试"""
        scenarios = [
            {
                "name": "market_crash", 
                "description": "市场崩盘情景",
                "price_shock": -0.3,
                "liquidity_shock": -0.5,
            },
            {
                "name": "liquidity_crisis",
                "description": "流动性危机情景", 
                "price_shock": -0.1,
                "liquidity_shock": -0.8,
            },
            {
                "name": "regulatory_shock",
                "description": "监管冲击情景",
                "price_shock": -0.2,
                "liquidity_shock": -0.3,
            },
        ]
        
        stress_results = []
        for scenario in scenarios:
            result = self._calculate_scenario_impact(scenario)
            stress_results.append({
                **scenario,
                **result,
                "pass": result["portfolio_loss"] <= self.max_drawdown,
            })
        
        return {
            "scenarios": stress_results,
            "worst_case_scenario": max(stress_results, key=lambda x: x["portfolio_loss"]),
            "pass_rate": sum(1 for r in stress_results if r["pass"]) / len(stress_results),
        }
    
    def _calculate_scenario_impact(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """计算情景影响"""
        price_shock = scenario.get("price_shock", 0)
        liquidity_shock = scenario.get("liquidity_shock", 0)
        
        # 简化的情景影响计算
        portfolio_loss = abs(price_shock) * 0.8 + abs(liquidity_shock) * 0.2
        
        return {
            "portfolio_loss": portfolio_loss,
            "var_impact": portfolio_loss * 1.2,
            "liquidity_impact": abs(liquidity_shock),
        }
    
    def _calculate_risk_level(self, score: float) -> str:
        """根据分数计算风险等级"""
        return self._score_to_risk_level(score)
    
    def _risk_level_to_score(self, risk_level: str) -> float:
        """风险等级转换为分数"""
        mapping = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "extreme": 1.0,
        }
        return mapping.get(risk_level, 0.5)
    
    def _score_to_risk_level(self, score: float) -> str:
        """分数转换为风险等级"""
        if score < 0.3:
            return "low"
        elif score < 0.6:
            return "medium"
        elif score < 0.9:
            return "high"
        else:
            return "extreme"
    
    def _identify_dominant_risk(self, risk_scores: Dict[str, float]) -> str:
        """识别主导风险类型"""
        if not risk_scores:
            return "unknown"
        
        dominant_risk = max(risk_scores.items(), key=lambda x: x[1])
        return dominant_risk[0]
    
    def _calculate_confidence(self, overall_risk: Dict[str, Any]) -> float:
        """计算风险分析置信度"""
        # 基于风险分析的完整性和一致性
        risk_scores = overall_risk.get("risk_scores", {})
        
        if not risk_scores:
            return 0.3
        
        # 风险分析覆盖度
        coverage = len(risk_scores) / 7  # 总共7类风险
        
        # 风险分数方差（一致性）
        scores = list(risk_scores.values())
        variance = sum((score - sum(scores)/len(scores))**2 for score in scores) / len(scores)
        consistency = 1.0 - min(variance, 1.0)
        
        return (coverage * 0.6 + consistency * 0.4)
    
    def _generate_risk_dashboard(self, overall_risk: Dict[str, Any]) -> Dict[str, Any]:
        """生成风险仪表板"""
        return {
            "overall_risk_level": overall_risk.get("risk_level", "medium"),
            "risk_score": overall_risk.get("overall_score", 0.5),
            "dominant_risk": overall_risk.get("dominant_risk_type", "market"),
            "risk_trend": "stable",  # 需要历史数据
            "last_updated": datetime.now().isoformat(),
        }