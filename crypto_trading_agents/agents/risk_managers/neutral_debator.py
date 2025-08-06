"""
中性辩论者 - 平衡风险和收益，提供客观分析

基于原版辩论架构，针对加密货币市场特性优化
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class NeutralDebator:
    """加密货币中性辩论者"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化中性辩论者
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.risk_tolerance = config.get("risk_config", {}).get("neutral_tolerance", 0.5)
        
    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析风险状况（中性视角）
        
        Args:
            state: 当前状态
            
        Returns:
            中性风险分析结果
        """
        try:
            # 获取基础分析报告
            market_report = state.get("market_report", "")
            sentiment_report = state.get("sentiment_report", "")
            news_report = state.get("news_report", "")
            fundamentals_report = state.get("fundamentals_report", "")
            
            # 获取当前投资计划
            investment_plan = state.get("investment_plan", "")
            
            # 中性风险分析
            risk_analysis = self._analyze_balanced_risks(
                market_report, sentiment_report, news_report, fundamentals_report
            )
            
            # 平衡策略
            balanced_strategies = self._generate_balanced_strategies(risk_analysis)
            
            # 风险收益评估
            risk_reward_assessment = self._assess_risk_reward_balance(risk_analysis)
            
            # 中性投资建议
            neutral_recommendations = self._generate_neutral_recommendations(
                risk_analysis, balanced_strategies, risk_reward_assessment
            )
            
            return {
                "risk_analysis": risk_analysis,
                "balanced_strategies": balanced_strategies,
                "risk_reward_assessment": risk_reward_assessment,
                "neutral_recommendations": neutral_recommendations,
                "risk_level": "medium",
                "expected_return": "balanced",
                "confidence": self._calculate_confidence(risk_analysis),
                "key_observations": self._generate_key_observations(risk_analysis),
            }
            
        except Exception as e:
            logger.error(f"Error in neutral debator analysis: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_balanced_risks(self, market_report: str, sentiment_report: str, 
                                news_report: str, fundamentals_report: str) -> Dict[str, Any]:
        """分析平衡风险因素"""
        
        # 模拟平衡风险分析
        return {
            "market_volatility": "moderate_to_high",
            "regulatory_landscape": "evolving",
            "technological_adoption": "steady",
            "market_maturity": "developing",
            "liquidity_conditions": "adequate",
            "institutional_interest": "growing",
            "retail_participation": "active",
            "competitive_landscape": "intense",
            "innovation_pace": "rapid",
            "market_efficiency": "improving",
            "risk_distribution": "diversified",
        }
    
    def _generate_balanced_strategies(self, risk_analysis: Dict[str, Any]) -> List[str]:
        """生成平衡策略"""
        
        strategies = []
        
        # 基于市场成熟度的策略
        if risk_analysis.get("market_maturity") == "developing":
            strategies.append("核心卫星投资策略")
            strategies.append("定期定额投资")
            strategies.append("价值平均策略")
        
        # 基于机构兴趣的策略
        if risk_analysis.get("institutional_interest") == "growing":
            strategies.append("跟随机构布局")
            strategies.append("关注ETF动向")
            strategies.append("配置蓝筹币种")
        
        # 基于技术创新的策略
        if risk_analysis.get("innovation_pace") == "rapid":
            strategies.append("技术主题投资")
            strategies.append("赛道轮动策略")
            strategies.append("创新项目配置")
        
        # 基于流动性的策略
        if risk_analysis.get("liquidity_conditions") == "adequate":
            strategies.append("流动性分层策略")
            strategies.append("大市值优先策略")
        
        # 基于风险分布的策略
        if risk_analysis.get("risk_distribution") == "diversified":
            strategies.append("跨类别分散")
            strategies.append("时间分散投资")
            strategies.append("地域分散配置")
        
        # 平衡策略核心
        strategies.append("风险预算管理")
        strategies.append("动态再平衡")
        strategies.append("成本控制策略")
        
        return strategies
    
    def _assess_risk_reward_balance(self, risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险收益平衡"""
        
        return {
            "current_risk_level": "medium",
            "potential_upside": "moderate_to_high",
            "downside_protection": "limited",
            "time_horizon": "medium_term",
            "volatility_tolerance": "moderate",
            "liquidity_needs": "moderate",
            "recommended_allocation": {
                "large_cap_crypto": "40-50%",
                "mid_cap_crypto": "20-30%",
                "small_cap_crypto": "10-20%",
                "stablecoins": "15-25%",
                "defi_protocols": "5-15%"
            },
            "leverage_guidelines": "limited_to_2x",
            "position_size_limits": "5-10% per position",
            "rebalancing_frequency": "monthly",
            "risk_per_trade": "2-3% of portfolio",
        }
    
    def _generate_neutral_recommendations(self, risk_analysis: Dict[str, Any], 
                                          strategies: List[str], 
                                          assessment: Dict[str, Any]) -> List[str]:
        """生成中性投资建议"""
        
        recommendations = []
        
        # 核心平衡建议
        recommendations.append("建议采用60%配置 + 40%现金的平衡策略")
        recommendations.append("重点配置比特币和以太坊等主流币种")
        recommendations.append("小仓位配置有潜力的创新项目")
        recommendations.append("使用不超过2倍的杠杆")
        
        # 基于策略的建议
        if "核心卫星投资策略" in strategies:
            recommendations.append("核心仓位配置BTC/ETH，卫星仓位配置新兴项目")
        
        if "定期定额投资" in strategies:
            recommendations.append("采用定投策略平滑成本")
        
        if "动态再平衡" in strategies:
            recommendations.append("每月进行一次投资组合再平衡")
        
        # 基于资产配置的建议
        allocation = assessment.get("recommended_allocation", {})
        recommendations.append(f"资产配置建议: 大市值{allocation.get('large_cap_crypto', '40%')}, 稳定币{allocation.get('stablecoins', '20%')}")
        
        # 风险管理建议
        recommendations.append("单笔投资控制在总资金的5-10%")
        recommendations.append("设置8-12%的止损")
        recommendations.append("保持20-30%的现金以应对机会")
        
        # 监控建议
        recommendations.append("每周评估投资组合表现")
        recommendations.append("关注市场结构性变化")
        recommendations.append("定期学习和更新投资知识")
        
        # 长期建议
        recommendations.append("保持长期投资视角")
        recommendations.append("避免情绪化交易决策")
        recommendations.append("持续优化投资策略")
        
        return recommendations
    
    def _calculate_confidence(self, risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """计算分析置信度"""
        
        # 中性分析的置信度基于市场成熟度和效率
        maturity_score = 0.6 if risk_analysis.get("market_maturity") == "developing" else 0.8
        efficiency_score = 0.7 if risk_analysis.get("market_efficiency") == "improving" else 0.5
        
        confidence_score = (maturity_score + efficiency_score) / 2
        
        return {
            "overall_confidence": confidence_score,
            "analysis_reliability": "moderate_to_high",
            "uncertainty_factors": ["regulatory_changes", "market_sentiment_shifts", "technological_disruptions"],
            "confidence_level": "high" if confidence_score > 0.7 else "moderate" if confidence_score > 0.5 else "low",
        }
    
    def _generate_key_observations(self, risk_analysis: Dict[str, Any]) -> List[str]:
        """生成关键观察"""
        
        observations = []
        
        # 市场成熟度观察
        maturity = risk_analysis.get("market_maturity", "unknown")
        observations.append(f"市场成熟度: {maturity}")
        
        # 机构兴趣观察
        institutional = risk_analysis.get("institutional_interest", "unknown")
        observations.append(f"机构兴趣: {institutional}")
        
        # 创新速度观察
        innovation = risk_analysis.get("innovation_pace", "unknown")
        observations.append(f"创新速度: {innovation}")
        
        # 监管环境观察
        regulatory = risk_analysis.get("regulatory_landscape", "unknown")
        observations.append(f"监管环境: {regulatory}")
        
        # 流动性观察
        liquidity = risk_analysis.get("liquidity_conditions", "unknown")
        observations.append(f"流动性状况: {liquidity}")
        
        # 风险分布观察
        risk_dist = risk_analysis.get("risk_distribution", "unknown")
        observations.append(f"风险分布: {risk_dist}")
        
        return observations