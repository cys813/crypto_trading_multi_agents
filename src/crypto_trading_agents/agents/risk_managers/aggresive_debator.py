"""
激进辩论者 - 专注高风险高回报策略

基于原版辩论架构，针对加密货币高波动性优化
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class AggressiveDebator:
    """加密货币激进辩论者"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化激进辩论者
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.risk_tolerance = config.get("risk_config", {}).get("aggressive_tolerance", 0.8)
        
    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析风险状况（激进视角）
        
        Args:
            state: 当前状态
            
        Returns:
            激进风险分析结果
        """
        try:
            # 获取基础分析报告
            market_report = state.get("market_report", "")
            sentiment_report = state.get("sentiment_report", "")
            news_report = state.get("news_report", "")
            fundamentals_report = state.get("fundamentals_report", "")
            
            # 获取当前投资计划
            investment_plan = state.get("investment_plan", "")
            
            # 激进风险分析
            risk_analysis = self._analyze_aggressive_opportunities(
                market_report, sentiment_report, news_report, fundamentals_report
            )
            
            # 高收益策略建议
            high_return_strategies = self._generate_high_return_strategies(risk_analysis)
            
            # 杠杆机会评估
            leverage_opportunities = self._assess_leverage_opportunities(risk_analysis)
            
            # 激进投资建议
            aggressive_recommendations = self._generate_aggressive_recommendations(
                risk_analysis, high_return_strategies, leverage_opportunities
            )
            
            return {
                "risk_analysis": risk_analysis,
                "high_return_strategies": high_return_strategies,
                "leverage_opportunities": leverage_opportunities,
                "aggressive_recommendations": aggressive_recommendations,
                "risk_level": "high",
                "expected_return": "very_high",
                "confidence": self._calculate_confidence(risk_analysis),
                "key_observations": self._generate_key_observations(risk_analysis),
            }
            
        except Exception as e:
            logger.error(f"Error in aggressive debator analysis: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_aggressive_opportunities(self, market_report: str, sentiment_report: str, 
                                        news_report: str, fundamentals_report: str) -> Dict[str, Any]:
        """分析激进投资机会"""
        
        # 模拟激进机会分析
        return {
            "market_momentum": "strong_bullish",
            "sentiment_extreme": "extreme_greed",
            "volume_breakout": True,
            "technical_breakthrough": True,
            "whale_accumulation": True,
            "institutional_fomo": True,
            "short_squeeze_potential": "high",
            "leverage_opportunity_score": 0.85,
            "volatility_advantage": "high",
            "market_irrationality": "high",
            "quick_profit_potential": "very_high",
            "risk_reward_ratio": "3:1",
        }
    
    def _generate_high_return_strategies(self, risk_analysis: Dict[str, Any]) -> List[str]:
        """生成高收益策略"""
        
        strategies = []
        
        # 基于市场动量的策略
        if risk_analysis.get("market_momentum") == "strong_bullish":
            strategies.append("杠杆做多策略")
            strategies.append("突破追涨策略")
        
        # 基于情绪极端的策略
        if risk_analysis.get("sentiment_extreme") == "extreme_greed":
            strategies.append("情绪反转做空策略")
            strategies.append("泡沫破裂策略")
        
        # 基于成交量突破的策略
        if risk_analysis.get("volume_breakout"):
            strategies.append("成交量放大策略")
            strategies.append("突破加仓策略")
        
        # 基于技术突破的策略
        if risk_analysis.get("technical_breakthrough"):
            strategies.append("技术突破策略")
            strategies.append("趋势跟踪策略")
        
        # 基于鲸鱼积累的策略
        if risk_analysis.get("whale_accumulation"):
            strategies.append("鲸鱼跟单策略")
            strategies.append("大户持仓策略")
        
        # 杠杆策略
        if risk_analysis.get("leverage_opportunity_score", 0) > 0.7:
            strategies.append("5-10倍杠杆策略")
            strategies.append("期货杠杆策略")
        
        return strategies
    
    def _assess_leverage_opportunities(self, risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """评估杠杆机会"""
        
        leverage_score = risk_analysis.get("leverage_opportunity_score", 0.5)
        
        return {
            "recommended_leverage": "10x" if leverage_score > 0.8 else "5x" if leverage_score > 0.6 else "3x",
            "liquidation_risk": "high" if leverage_score > 0.7 else "medium",
            "funding_rate_impact": "significant" if leverage_score > 0.6 else "moderate",
            "volatility_amplification": "extreme" if leverage_score > 0.8 else "high",
            "quick_profit_window": "24-48小时",
            "stop_loss_required": True,
            "position_size_recommendation": "20-30% of portfolio",
        }
    
    def _generate_aggressive_recommendations(self, risk_analysis: Dict[str, Any], 
                                           strategies: List[str], 
                                           leverage: Dict[str, Any]) -> List[str]:
        """生成激进投资建议"""
        
        recommendations = []
        
        # 基于风险评分的核心建议
        if risk_analysis.get("leverage_opportunity_score", 0) > 0.8:
            recommendations.append("建议使用10倍杠杆全仓做多")
            recommendations.append("设置5%止损，目标30%收益")
        
        elif risk_analysis.get("leverage_opportunity_score", 0) > 0.6:
            recommendations.append("建议使用5倍杠杆重仓参与")
            recommendations.append("设置8%止损，目标20%收益")
        
        else:
            recommendations.append("建议使用3倍杠杆适度参与")
            recommendations.append("设置10%止损，目标15%收益")
        
        # 基于策略的具体建议
        if "杠杆做多策略" in strategies:
            recommendations.append("优先选择永续合约，关注资金费率")
        
        if "情绪反转做空策略" in strategies:
            recommendations.append("准备做空仓位，关注情绪指标反转信号")
        
        if "鲸鱼跟单策略" in strategies:
            recommendations.append("监控大户持仓变化，及时跟单")
        
        # 风险管理建议
        recommendations.append("严格执行止损纪律")
        recommendations.append("分批建仓，控制单笔风险")
        recommendations.append("关注市场流动性，避免滑点损失")
        
        return recommendations
    
    def _calculate_confidence(self, risk_analysis: Dict[str, Any]) -> float:
        """计算分析置信度"""
        
        leverage_score = risk_analysis.get("leverage_opportunity_score", 0.5)
        momentum_strength = 1.0 if risk_analysis.get("market_momentum") == "strong_bullish" else 0.5
        
        return min((leverage_score + momentum_strength) / 2, 1.0)
    
    def _generate_key_observations(self, risk_analysis: Dict[str, Any]) -> List[str]:
        """生成关键观察"""
        
        observations = []
        
        # 市场动量观察
        momentum = risk_analysis.get("market_momentum", "unknown")
        observations.append(f"市场动量: {momentum}")
        
        # 杠杆机会观察
        leverage_score = risk_analysis.get("leverage_opportunity_score", 0)
        if leverage_score > 0.8:
            observations.append("杠杆机会: 极佳")
        elif leverage_score > 0.6:
            observations.append("杠杆机会: 良好")
        else:
            observations.append("杠杆机会: 一般")
        
        # 波动性观察
        volatility = risk_analysis.get("volatility_advantage", "unknown")
        observations.append(f"波动性优势: {volatility}")
        
        # 风险回报比观察
        risk_reward = risk_analysis.get("risk_reward_ratio", "unknown")
        observations.append(f"风险回报比: {risk_reward}")
        
        return observations