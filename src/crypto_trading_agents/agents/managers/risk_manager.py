"""
风险管理器 - 协调激进、中性和保守辩论者的风险辩论

基于原版风险管理架构，针对加密货币高风险特性优化
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    """加密货币风险管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化风险管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.debate_rounds = config.get("risk_config", {}).get("debate_rounds", 3)
        
    def manage_risk_debate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        管理风险辩论
        
        Args:
            state: 当前状态
            
        Returns:
            风险辩论结果
        """
        try:
            # 获取基础分析报告
            market_report = state.get("market_report", "")
            sentiment_report = state.get("sentiment_report", "")
            news_report = state.get("news_report", "")
            fundamentals_report = state.get("fundamentals_report", "")
            
            # 获取投资计划
            investment_plan = state.get("investment_plan", "")
            
            # 获取风险辩论者分析结果
            aggressive_analysis = state.get("aggressive_risk_analysis", {})
            conservative_analysis = state.get("conservative_risk_analysis", {})
            neutral_analysis = state.get("neutral_risk_analysis", {})
            
            # 组织风险辩论
            debate_results = self._organize_risk_debate(
                aggressive_analysis, conservative_analysis, neutral_analysis,
                market_report, sentiment_report, news_report, fundamentals_report, investment_plan
            )
            
            # 生成风险总结
            risk_summary = self._generate_risk_summary(debate_results)
            
            # 最终风险决策
            final_decision = self._make_final_decision(risk_summary, investment_plan)
            
            return {
                "debate_results": debate_results,
                "risk_summary": risk_summary,
                "final_decision": final_decision,
                "risk_level": final_decision.get("risk_level", "medium"),
                "action_recommendation": final_decision.get("action", "hold"),
                "confidence": final_decision.get("confidence", 0.5),
                "position_size": final_decision.get("position_size", "medium"),
                "stop_loss": final_decision.get("stop_loss", 0.0),
            }
            
        except Exception as e:
            logger.error(f"Error in risk manager: {str(e)}")
            return {"error": str(e)}
    
    def _organize_risk_debate(self, aggressive_analysis: Dict[str, Any], conservative_analysis: Dict[str, Any],
                             neutral_analysis: Dict[str, Any], market_report: str, sentiment_report: str, 
                             news_report: str, fundamentals_report: str, investment_plan: str) -> Dict[str, Any]:
        """组织风险辩论"""
        
        debate_history = []
        
        # 第一轮：各自陈述风险观点
        round1 = self._conduct_risk_round1_debate(aggressive_analysis, conservative_analysis, neutral_analysis)
        debate_history.append(round1)
        
        # 第二轮：风险策略辩论
        round2 = self._conduct_risk_round2_debate(round1, aggressive_analysis, conservative_analysis, neutral_analysis)
        debate_history.append(round2)
        
        # 第三轮：最终风险建议
        round3 = self._conduct_risk_round3_debate(round2, aggressive_analysis, conservative_analysis, neutral_analysis)
        debate_history.append(round3)
        
        return {
            "debate_rounds": debate_history,
            "aggressive_stance": self._assess_aggressive_stance(aggressive_analysis, debate_history),
            "conservative_stance": self._assess_conservative_stance(conservative_analysis, debate_history),
            "neutral_stance": self._assess_neutral_stance(neutral_analysis, debate_history),
            "risk_consensus": self._find_risk_consensus(debate_history),
            "key_risk_disagreements": self._identify_risk_disagreements(debate_history),
        }
    
    def _conduct_risk_round1_debate(self, aggressive_analysis: Dict[str, Any], 
                                  conservative_analysis: Dict[str, Any], 
                                  neutral_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """第一轮风险辩论：各自陈述观点"""
        
        return {
            "round": 1,
            "aggressive_position": {
                "risk_level": "high",
                "expected_return": "very_high",
                "key_strategies": aggressive_analysis.get("high_return_strategies", [])[:3],
                "leverage_recommendation": aggressive_analysis.get("leverage_opportunities", {}).get("recommended_leverage", "5x"),
                "confidence": aggressive_analysis.get("confidence", 0.5),
                "argument": "高风险高回报，应该充分利用市场机会"
            },
            "conservative_position": {
                "risk_level": "low",
                "expected_return": "moderate",
                "key_strategies": conservative_analysis.get("capital_protection", [])[:3],
                "leverage_recommendation": "zero_leverage",
                "confidence": conservative_analysis.get("confidence", 0.5),
                "argument": "资本保护优先，应该规避重大风险"
            },
            "neutral_position": {
                "risk_level": "medium",
                "expected_return": "balanced",
                "key_strategies": neutral_analysis.get("balanced_strategies", [])[:3],
                "leverage_recommendation": "limited_to_2x",
                "confidence": neutral_analysis.get("confidence", {}).get("overall_confidence", 0.5),
                "argument": "平衡风险收益，寻找最优配置"
            },
            "initial_diversity": self._calculate_risk_diversity(aggressive_analysis, conservative_analysis, neutral_analysis),
        }
    
    def _conduct_risk_round2_debate(self, round1: Dict[str, Any], aggressive_analysis: Dict[str, Any], 
                                   conservative_analysis: Dict[str, Any], neutral_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """第二轮风险辩论：策略辩论"""
        
        # 激进派反驳保守派
        aggressive_rebuttals = self._generate_aggressive_risk_rebuttals(aggressive_analysis, round1["conservative_position"])
        
        # 保守派反驳激进派
        conservative_rebuttals = self._generate_conservative_risk_rebuttals(conservative_analysis, round1["aggressive_position"])
        
        # 中性派调和
        neutral_moderation = self._generate_neutral_moderation(neutral_analysis, round1)
        
        return {
            "round": 2,
            "aggressive_rebuttals": aggressive_rebuttals,
            "conservative_rebuttals": conservative_rebuttals,
            "neutral_moderation": neutral_moderation,
            "key_risk_contentions": self._identify_risk_contentions(aggressive_rebuttals, conservative_rebuttals),
            "moderation_effectiveness": self._assess_moderation_effectiveness(neutral_moderation),
        }
    
    def _conduct_risk_round3_debate(self, round2: Dict[str, Any], aggressive_analysis: Dict[str, Any], 
                                   conservative_analysis: Dict[str, Any], neutral_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """第三轮风险辩论：最终建议"""
        
        # 基于辩论调整激进立场
        aggressive_final = self._refine_aggressive_position(aggressive_analysis, round2)
        
        # 基于辩论调整保守立场
        conservative_final = self._refine_conservative_position(conservative_analysis, round2)
        
        # 中性派最终建议
        neutral_final = self._refine_neutral_position(neutral_analysis, round2)
        
        return {
            "round": 3,
            "aggressive_final": aggressive_final,
            "conservative_final": conservative_final,
            "neutral_final": neutral_final,
            "risk_convergence": self._identify_risk_convergence(aggressive_final, conservative_final, neutral_final),
            "remaining_risk_divergences": self._identify_remaining_risk_divergences(aggressive_final, conservative_final, neutral_final),
        }
    
    def _generate_aggressive_risk_rebuttals(self, aggressive_analysis: Dict[str, Any], 
                                          conservative_position: Dict[str, Any]) -> List[str]:
        """生成激进派反驳"""
        
        rebuttals = []
        
        # 反驳保守观点
        if conservative_position.get("leverage_recommendation") == "zero_leverage":
            rebuttals.append("零杠杆策略过于保守，错失市场机会")
        
        if conservative_position.get("risk_level") == "low":
            rebuttals.append("低风险策略在牛市中表现不佳")
        
        # 基于激进分析的反驳
        leverage_score = aggressive_analysis.get("leverage_opportunities", {}).get("leverage_opportunity_score", 0.5)
        if leverage_score > 0.7:
            rebuttals.append("当前市场条件支持使用高杠杆")
        
        return rebuttals
    
    def _generate_conservative_risk_rebuttals(self, conservative_analysis: Dict[str, Any], 
                                             aggressive_position: Dict[str, Any]) -> List[str]:
        """生成保守派反驳"""
        
        rebuttals = []
        
        # 反驳激进观点
        if aggressive_position.get("leverage_recommendation") in ["5x", "10x"]:
            rebuttals.append("高杠杆策略风险过大，可能导致爆仓")
        
        if aggressive_position.get("risk_level") == "high":
            rebuttals.append("高风险策略在熊市中损失惨重")
        
        # 基于保守分析的反驳
        market_volatility = conservative_analysis.get("risk_analysis", {}).get("market_volatility", "unknown")
        if market_volatility == "extreme":
            rebuttals.append("极端波动性下应该降低风险敞口")
        
        return rebuttals
    
    def _generate_neutral_moderation(self, neutral_analysis: Dict[str, Any], round1: Dict[str, Any]) -> List[str]:
        """生成中性派调和"""
        
        moderation = []
        
        # 调和观点
        moderation.append("激进和保守策略各有优劣，应根据市场环境选择")
        moderation.append("关键是要根据个人风险承受能力来配置")
        moderation.append("建议采用核心卫星策略，平衡风险和收益")
        
        # 基于中性分析的建议
        assessment = neutral_analysis.get("risk_reward_assessment", {})
        if assessment:
            allocation = assessment.get("recommended_allocation", {})
            moderation.append(f"建议配置：大市值{allocation.get('large_cap_crypto', '40%')}，稳定币{allocation.get('stablecoins', '20%')}")
        
        return moderation
    
    def _assess_aggressive_stance(self, aggressive_analysis: Dict[str, Any], debate_history: List[Dict[str, Any]]) -> float:
        """评估激进立场强度"""
        
        base_strength = aggressive_analysis.get("confidence", 0.5)
        
        # 根据辩论表现调整
        if len(debate_history) >= 2:
            round2 = debate_history[1]
            rebuttals = round2.get("aggressive_rebuttals", [])
            debate_performance = min(len(rebuttals) * 0.1, 0.2)
        else:
            debate_performance = 0.0
        
        return min(base_strength + debate_performance, 1.0)
    
    def _assess_conservative_stance(self, conservative_analysis: Dict[str, Any], debate_history: List[Dict[str, Any]]) -> float:
        """评估保守立场强度"""
        
        base_strength = conservative_analysis.get("confidence", 0.5)
        
        # 根据辩论表现调整
        if len(debate_history) >= 2:
            round2 = debate_history[1]
            rebuttals = round2.get("conservative_rebuttals", [])
            debate_performance = min(len(rebuttals) * 0.1, 0.2)
        else:
            debate_performance = 0.0
        
        return min(base_strength + debate_performance, 1.0)
    
    def _assess_neutral_stance(self, neutral_analysis: Dict[str, Any], debate_history: List[Dict[str, Any]]) -> float:
        """评估中性立场强度"""
        
        confidence_data = neutral_analysis.get("confidence", {})
        if isinstance(confidence_data, dict):
            return confidence_data.get("overall_confidence", 0.5)
        else:
            return confidence_data
    
    def _find_risk_consensus(self, debate_history: List[Dict[str, Any]]) -> List[str]:
        """寻找风险共识"""
        
        consensus = []
        
        if len(debate_history) >= 3:
            round3 = debate_history[2]
            convergence = round3.get("risk_convergence", [])
            consensus.extend(convergence)
        
        # 默认共识
        if not consensus:
            consensus = [
                "风险管理是必需的",
                "应根据个人情况调整策略",
                "多元化配置很重要"
            ]
        
        return consensus
    
    def _identify_risk_disagreements(self, debate_history: List[Dict[str, Any]]) -> List[str]:
        """识别风险分歧"""
        
        disagreements = []
        
        if len(debate_history) >= 2:
            round2 = debate_history[1]
            contentions = round2.get("key_risk_contentions", [])
            disagreements.extend(contentions)
        
        return disagreements
    
    def _generate_risk_summary(self, debate_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成风险总结"""
        
        aggressive_strength = debate_results.get("aggressive_stance", 0.5)
        conservative_strength = debate_results.get("conservative_stance", 0.5)
        neutral_strength = debate_results.get("neutral_stance", 0.5)
        
        # 确定风险倾向
        if aggressive_strength > conservative_strength + 0.2 and aggressive_strength > neutral_strength + 0.1:
            risk_tendency = "aggressive"
            confidence = aggressive_strength
        elif conservative_strength > aggressive_strength + 0.2 and conservative_strength > neutral_strength + 0.1:
            risk_tendency = "conservative"
            confidence = conservative_strength
        else:
            risk_tendency = "neutral"
            confidence = neutral_strength
        
        return {
            "risk_tendency": risk_tendency,
            "confidence": confidence,
            "strength_scores": {
                "aggressive": aggressive_strength,
                "conservative": conservative_strength,
                "neutral": neutral_strength,
            },
            "consensus_areas": debate_results.get("risk_consensus", []),
            "disagreement_areas": debate_results.get("key_risk_disagreements", []),
        }
    
    def _make_final_decision(self, risk_summary: Dict[str, Any], investment_plan: str) -> Dict[str, Any]:
        """做出最终风险决策"""
        
        risk_tendency = risk_summary.get("risk_tendency", "neutral")
        confidence = risk_summary.get("confidence", 0.5)
        
        if risk_tendency == "aggressive":
            action = "buy"
            risk_level = "high"
            position_size = "large"
            leverage = "3-5x"
            stop_loss = 0.05  # 5%
            
        elif risk_tendency == "conservative":
            action = "sell" if confidence > 0.7 else "hold"
            risk_level = "low"
            position_size = "small"
            leverage = "no_leverage"
            stop_loss = 0.02  # 2%
            
        else:  # neutral
            action = "hold"
            risk_level = "medium"
            position_size = "medium"
            leverage = "1-2x"
            stop_loss = 0.08  # 8%
        
        return {
            "action": action,
            "risk_level": risk_level,
            "confidence": confidence,
            "position_size": position_size,
            "leverage": leverage,
            "stop_loss": stop_loss,
            "reasoning": f"基于{risk_tendency}风险倾向，建议{action}操作",
            "implementation_notes": self._generate_implementation_notes(risk_tendency, position_size, leverage, stop_loss),
        }
    
    def _calculate_risk_diversity(self, aggressive_analysis: Dict[str, Any], 
                                 conservative_analysis: Dict[str, Any], 
                                 neutral_analysis: Dict[str, Any]) -> float:
        """计算风险观点多样性"""
        
        # 简化的多样性计算
        aggressive_risk = aggressive_analysis.get("risk_level", "high")
        conservative_risk = conservative_analysis.get("risk_level", "low")
        neutral_risk = neutral_analysis.get("risk_level", "medium")
        
        risk_scores = {"high": 1.0, "medium": 0.5, "low": 0.0}
        
        scores = [
            risk_scores.get(aggressive_risk, 0.5),
            risk_scores.get(conservative_risk, 0.5),
            risk_scores.get(neutral_risk, 0.5)
        ]
        
        # 计算标准差作为多样性指标
        import statistics
        try:
            return statistics.stdev(scores)
        except:
            return 0.5
    
    def _identify_risk_contentions(self, aggressive_rebuttals: List[str], conservative_rebuttals: List[str]) -> List[str]:
        """识别风险争论点"""
        
        contentions = []
        
        for rebuttal in aggressive_rebuttals + conservative_rebuttals:
            if "杠杆" in rebuttal:
                contentions.append("杠杆使用策略")
            elif "风险" in rebuttal:
                contentions.append("风险水平评估")
            elif "策略" in rebuttal:
                contentions.append("投资策略选择")
        
        return list(set(contentions))
    
    def _assess_moderation_effectiveness(self, neutral_moderation: List[str]) -> float:
        """评估调和有效性"""
        return min(len(neutral_moderation) * 0.2, 1.0)
    
    def _refine_aggressive_position(self, aggressive_analysis: Dict[str, Any], round2: Dict[str, Any]) -> Dict[str, Any]:
        """优化激进立场"""
        return {
            "adjusted_leverage": "3-5x",  # 降低杠杆
            "added_risk_controls": ["止损设置", "仓位控制"],
            "maintained_strategies": aggressive_analysis.get("high_return_strategies", [])[:2],
        }
    
    def _refine_conservative_position(self, conservative_analysis: Dict[str, Any], round2: Dict[str, Any]) -> Dict[str, Any]:
        """优化保守立场"""
        return {
            "increased_allocation": "小幅增加风险资产配置",
            "maintained_protection": conservative_analysis.get("capital_protection", [])[:2],
            "added_flexibility": ["分批建仓", "动态调整"],
        }
    
    def _refine_neutral_position(self, neutral_analysis: Dict[str, Any], round2: Dict[str, Any]) -> Dict[str, Any]:
        """优化中性立场"""
        return {
            "final_allocation": neutral_analysis.get("risk_reward_assessment", {}).get("recommended_allocation", {}),
            "implementation_strategy": "核心卫星策略",
            "risk_monitoring": "定期评估调整",
        }
    
    def _identify_risk_convergence(self, aggressive_final: Dict[str, Any], 
                                 conservative_final: Dict[str, Any], 
                                 neutral_final: Dict[str, Any]) -> List[str]:
        """识别风险收敛点"""
        return ["需要风险控制", "重视资金管理", "关注市场变化"]
    
    def _identify_remaining_risk_divergences(self, aggressive_final: Dict[str, Any], 
                                           conservative_final: Dict[str, Any], 
                                           neutral_final: Dict[str, Any]) -> List[str]:
        """识别剩余风险分歧"""
        return ["杠杆使用程度", "风险资产配置比例", "止损设置策略"]
    
    def _generate_implementation_notes(self, risk_tendency: str, position_size: str, leverage: str, stop_loss: float) -> List[str]:
        """生成实施说明"""
        
        notes = []
        
        if risk_tendency == "aggressive":
            notes.append("严格控制单笔风险不超过总资金的5%")
            notes.append("设置自动止损，避免情绪化决策")
            notes.append("关注市场流动性，避免滑点损失")
            
        elif risk_tendency == "conservative":
            notes.append("保持充足现金储备")
            notes.append("优先选择流动性好的主流币种")
            notes.append("定期评估投资组合风险")
            
        else:  # neutral
            notes.append("采用核心卫星策略配置")
            notes.append("定期再平衡投资组合")
            notes.append("根据市场环境动态调整")
        
        notes.append(f"建议止损设置: {stop_loss*100:.1f}%")
        notes.append(f"建议杠杆水平: {leverage}")
        
        return notes