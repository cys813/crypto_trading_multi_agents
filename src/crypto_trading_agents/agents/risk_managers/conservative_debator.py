"""
保守辩论者 - 专注风险规避和资本保护

基于原版辩论架构，针对加密货币高风险特性优化
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ConservativeDebator:
    """加密货币保守辩论者"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化保守辩论者
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.risk_tolerance = config.get("risk_config", {}).get("conservative_tolerance", 0.2)
        
    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析风险状况（保守视角）
        
        Args:
            state: 当前状态
            
        Returns:
            保守风险分析结果
        """
        try:
            # 获取基础分析报告
            market_report = state.get("market_report", "")
            sentiment_report = state.get("sentiment_report", "")
            news_report = state.get("news_report", "")
            fundamentals_report = state.get("fundamentals_report", "")
            
            # 获取当前投资计划
            investment_plan = state.get("investment_plan", "")
            
            # 保守风险分析
            risk_analysis = self._analyze_conservative_risks(
                market_report, sentiment_report, news_report, fundamentals_report
            )
            
            # 资本保护策略
            capital_protection = self._generate_capital_protection_strategies(risk_analysis)
            
            # 风险规避措施
            risk_avoidance = self._assess_risk_avoidance_measures(risk_analysis)
            
            # 保守投资建议
            conservative_recommendations = self._generate_conservative_recommendations(
                risk_analysis, capital_protection, risk_avoidance
            )
            
            return {
                "risk_analysis": risk_analysis,
                "capital_protection": capital_protection,
                "risk_avoidance": risk_avoidance,
                "conservative_recommendations": conservative_recommendations,
                "risk_level": "low",
                "expected_return": "moderate",
                "confidence": self._calculate_confidence(risk_analysis),
                "key_observations": self._generate_key_observations(risk_analysis),
            }
            
        except Exception as e:
            logger.error(f"Error in conservative debator analysis: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_conservative_risks(self, market_report: str, sentiment_report: str, 
                                  news_report: str, fundamentals_report: str) -> Dict[str, Any]:
        """分析保守风险因素"""
        
        # 模拟保守风险分析
        return {
            "market_volatility": "extreme",
            "regulatory_uncertainty": "high",
            "liquidity_risk": "medium",
            "counterparty_risk": "high",
            "exchange_risk": "high",
            "smart_contract_risk": "very_high",
            "market_manipulation": "common",
            "black_swan_probability": "elevated",
            "capital_preservation_priority": "critical",
            "drawdown_potential": "severe",
            "recovery_timeline": "uncertain",
            "systemic_risk": "significant",
        }
    
    def _generate_capital_protection_strategies(self, risk_analysis: Dict[str, Any]) -> List[str]:
        """生成资本保护策略"""
        
        strategies = []
        
        # 基于波动性的保护策略
        if risk_analysis.get("market_volatility") == "extreme":
            strategies.append("大部分资金稳定币保值")
            strategies.append("小额分散投资")
            strategies.append("定期再平衡策略")
        
        # 基于监管不确定性的保护策略
        if risk_analysis.get("regulatory_uncertainty") == "high":
            strategies.append("规避监管灰色地带项目")
            strategies.append("选择合规交易所")
            strategies.append("关注政策动向")
        
        # 基于智能合约风险的保护策略
        if risk_analysis.get("smart_contract_risk") == "very_high":
            strategies.append("选择审计过的项目")
            strategies.append("避免新合约交互")
            strategies.append("使用多签钱包")
        
        # 基于交易风险的保护策略
        if risk_analysis.get("exchange_risk") == "high":
            strategies.append("资金分散存放")
            strategies.append("冷钱包存储")
            strategies.append("定期提取资金")
        
        # 基于市场操纵的保护策略
        if risk_analysis.get("market_manipulation") == "common":
            strategies.append("避免小市值币种")
            strategies.append("关注大户动向")
            strategies.append("使用限价单")
        
        # 系统性风险保护
        strategies.append("保持充足现金流")
        strategies.append("设置严格止损")
        strategies.append("定期评估投资组合")
        
        return strategies
    
    def _assess_risk_avoidance_measures(self, risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险规避措施"""
        
        return {
            "recommended_allocation": {
                "stablecoins": "60-70%",
                "bitcoin": "15-20%",
                "ethereum": "10-15%",
                "altcoins": "0-5%",
                "cash": "5-10%"
            },
            "leverage_usage": "zero_leverage",
            "stop_loss_strategy": "tight_stops",
            "position_sizing": "small_positions",
            "investment_horizon": "long_term",
            "diversification_level": "high",
            "monitoring_frequency": "daily",
            "rebalancing_period": "weekly",
            "risk_per_trade": "1-2% of portfolio",
        }
    
    def _generate_conservative_recommendations(self, risk_analysis: Dict[str, Any], 
                                             protection: List[str], 
                                             avoidance: Dict[str, Any]) -> List[str]:
        """生成保守投资建议"""
        
        recommendations = []
        
        # 核心保守建议
        recommendations.append("建议将70%资金转换为USDT等稳定币")
        recommendations.append("仅投资比特币和以太坊等主流币种")
        recommendations.append("完全避免使用杠杆")
        recommendations.append("设置5%的严格止损")
        
        # 基于保护策略的建议
        if "小额分散投资" in protection:
            recommendations.append("单笔投资不超过总资金的5%")
        
        if "冷钱包存储" in protection:
            recommendations.append("长期资产转入冷钱包存储")
        
        if "资金分散存放" in protection:
            recommendations.append("在2-3个知名交易所分散资金")
        
        # 基于风险规避的建议
        allocation = avoidance.get("recommended_allocation", {})
        recommendations.append(f"按以下比例配置: 稳定币{allocation.get('stablecoins', '60%')}, 比特币{allocation.get('bitcoin', '20%')}")
        
        # 监控建议
        recommendations.append("每日监控投资组合")
        recommendations.append("每周进行一次再平衡")
        recommendations.append("关注重大新闻和监管动向")
        
        # 长期建议
        recommendations.append("采用定投策略降低成本")
        recommendations.append("保持耐心，避免频繁交易")
        recommendations.append("优先考虑资本保值而非高收益")
        
        return recommendations
    
    def _calculate_confidence(self, risk_analysis: Dict[str, Any]) -> float:
        """计算分析置信度"""
        
        # 保守分析通常有较高的置信度
        regulatory_clarity = 0.3 if risk_analysis.get("regulatory_uncertainty") == "high" else 0.7
        market_stability = 0.2 if risk_analysis.get("market_volatility") == "extreme" else 0.6
        
        return (regulatory_clarity + market_stability) / 2
    
    def _generate_key_observations(self, risk_analysis: Dict[str, Any]) -> List[str]:
        """生成关键观察"""
        
        observations = []
        
        # 波动性观察
        volatility = risk_analysis.get("market_volatility", "unknown")
        observations.append(f"市场波动性: {volatility}")
        
        # 监管观察
        regulatory = risk_analysis.get("regulatory_uncertainty", "unknown")
        observations.append(f"监管不确定性: {regulatory}")
        
        # 智能合约风险观察
        contract_risk = risk_analysis.get("smart_contract_risk", "unknown")
        observations.append(f"智能合约风险: {contract_risk}")
        
        # 系统性风险观察
        systemic_risk = risk_analysis.get("systemic_risk", "unknown")
        observations.append(f"系统性风险: {systemic_risk}")
        
        # 黑天鹅概率观察
        black_swan = risk_analysis.get("black_swan_probability", "unknown")
        observations.append(f"黑天鹅事件概率: {black_swan}")
        
        return observations