"""
激进辩论者 - 专注高风险高回报策略

基于原版辩论架构，针对加密货币高波动性优化
"""

from typing import Dict, Any, List
import logging

from src.crypto_trading_agents.services.ai_analysis_mixin import StandardAIAnalysisMixin

logger = logging.getLogger(__name__)

class AggressiveDebator(StandardAIAnalysisMixin):
    """加密货币激进辩论者"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化激进辩论者
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.risk_tolerance = config.get("risk_config", {}).get("aggressive_tolerance", 0.8)
        
        # 初始化AI分析混入类
        super().__init__()
        
        # 初始化LLM服务（如果还未初始化）
        llm_service_config = config.get("llm_service_config")
        if llm_service_config:
            try:
                from src.crypto_trading_agents.services.unified_llm_service import initialize_llm_service
                initialize_llm_service(llm_service_config)
                logger.info("AggressiveDebator: 统一LLM服务初始化完成")
            except ImportError:
                logger.warning("AggressiveDebator: 无法导入LLM服务，将使用纯规则分析")
        
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
            
            # AI增强分析（如果启用）
            ai_enhancement = {}
            if self.is_ai_enabled():
                try:
                    ai_enhancement = self._enhance_aggressive_analysis_with_ai(
                        risk_analysis, market_report, sentiment_report, news_report, fundamentals_report
                    )
                    # 将AI分析结果合并到主分析中
                    risk_analysis.update(ai_enhancement)
                except Exception as e:
                    logger.warning(f"AggressiveDebator AI增强分析失败: {e}")
                    ai_enhancement = {"ai_error": str(e)}

            return {
                "risk_analysis": risk_analysis,
                "high_return_strategies": high_return_strategies,
                "leverage_opportunities": leverage_opportunities,
                "aggressive_recommendations": aggressive_recommendations,
                "risk_level": "high",
                "expected_return": "very_high",
                "confidence": self._calculate_confidence(risk_analysis),
                "key_observations": self._generate_key_observations(risk_analysis),
                "ai_enhanced": self.is_ai_enabled(),
                "ai_analysis": ai_enhancement,
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

    def _enhance_aggressive_analysis_with_ai(self, risk_analysis: Dict[str, Any], 
                                            market_report: str, sentiment_report: str,
                                            news_report: str, fundamentals_report: str) -> Dict[str, Any]:
        """使用AI增强激进分析"""
        try:
            # 构建AI分析提示词
            prompt = self._build_aggressive_analysis_prompt(
                risk_analysis, market_report, sentiment_report, news_report, fundamentals_report
            )
            
            # 调用AI分析
            ai_response = self.call_ai_analysis(prompt)
            
            # 解析AI响应
            ai_analysis = self.parse_ai_json_response(ai_response, {
                "enhanced_opportunity_signals": [],
                "leverage_optimization": {},
                "timing_precision_analysis": {},
                "market_momentum_acceleration": {},
                "high_conviction_triggers": [],
                "risk_amplification_factors": []
            })
            
            return {
                "ai_enhanced": True,
                "ai_opportunity_signals": ai_analysis.get("enhanced_opportunity_signals", []),
                "ai_leverage_optimization": ai_analysis.get("leverage_optimization", {}),
                "ai_timing_analysis": ai_analysis.get("timing_precision_analysis", {}),
                "ai_momentum_acceleration": ai_analysis.get("market_momentum_acceleration", {}),
                "ai_conviction_triggers": ai_analysis.get("high_conviction_triggers", []),
                "ai_risk_amplification": ai_analysis.get("risk_amplification_factors", [])
            }
            
        except Exception as e:
            logger.error(f"AI增强激进分析失败: {e}")
            return {
                "ai_enhanced": False,
                "ai_error": str(e)
            }
    
    def _build_aggressive_analysis_prompt(self, risk_analysis: Dict[str, Any], 
                                         market_report: str, sentiment_report: str,
                                         news_report: str, fundamentals_report: str) -> str:
        """构建激进分析AI提示词"""
        return f"""作为专业的加密货币激进机会挖掘专家，请基于以下分析结果提供深度AI增强分析：

当前激进机会分析结果：
{risk_analysis}

市场报告：
{market_report}

情绪报告：
{sentiment_report}

新闻报告：
{news_report}

基本面报告：
{fundamentals_report}

请从极度激进的机会挖掘角度提供分析，专注于识别高收益机会：

1. 增强的机会信号 - 识别传统分析可能遗漏的高Alpha机会
2. 杠杆优化策略 - 提供精确的杠杆使用优化方案
3. 精准时机分析 - 提供高精度的入场和出场时机分析
4. 市场动量加速 - 识别动量加速的早期信号
5. 高置信度触发器 - 识别高胜率的交易触发条件
6. 风险放大因素 - 分析如何在可控风险下放大收益

请特别关注：
- 极端市场情绪下的反向投资机会
- 流动性危机中的套利机会
- 技术突破前的早期识别信号
- 杠杆产品的最优使用时机
- 高波动性环境下的收益放大策略
- 市场无效性的套利机会

请以JSON格式回复，包含enhanced_opportunity_signals, leverage_optimization, timing_precision_analysis, market_momentum_acceleration, high_conviction_triggers, risk_amplification_factors字段。"""

    def analyze_with_debate_material(self, debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于辩论材料进行分析
        
        Args:
            debate_material: 包含所有分析师和研究员分析结果的辩论材料
            
        Returns:
            激进辩论分析结果
        """
        try:
            # 解析辩论材料
            analyst_data = debate_material.get("analyst_data", {})
            researcher_data = debate_material.get("researcher_data", {})
            risk_data = debate_material.get("risk_data", {})
            
            # 增强的机会分析
            opportunity_analysis = self._analyze_aggressive_opportunities_enhanced(
                analyst_data, researcher_data, risk_data
            )
            
            # 激进策略
            aggressive_strategies = self._generate_enhanced_aggressive_strategies(opportunity_analysis, debate_material)
            
            # 杠杆机会评估
            leverage_assessment = self._assess_enhanced_leverage_opportunities(opportunity_analysis, debate_material)
            
            # 激进投资建议
            aggressive_recommendations = self._generate_enhanced_aggressive_recommendations(
                opportunity_analysis, aggressive_strategies, leverage_assessment, debate_material
            )
            
            # AI增强分析
            ai_enhancement = {}
            if self.is_ai_enabled():
                try:
                    ai_enhancement = self._enhance_aggressive_debate_with_ai(
                        opportunity_analysis, debate_material
                    )
                except Exception as e:
                    logger.warning(f"AggressiveDebator AI增强辩论分析失败: {e}")
                    ai_enhancement = {"ai_error": str(e)}
            
            return {
                "opportunity_analysis": opportunity_analysis,
                "aggressive_strategies": aggressive_strategies,
                "leverage_assessment": leverage_assessment,
                "aggressive_recommendations": aggressive_recommendations,
                "risk_level": "high",
                "expected_return": "very_high",
                "confidence": self._calculate_enhanced_confidence(opportunity_analysis, debate_material),
                "key_observations": self._generate_enhanced_observations(opportunity_analysis, debate_material),
                "ai_enhanced": self.is_ai_enabled(),
                "ai_analysis": ai_enhancement,
                "debate_material_summary": self._summarize_debate_material(debate_material)
            }
            
        except Exception as e:
            logger.error(f"AggressiveDebator analyze_with_debate_material失败: {e}")
            return {"error": str(e)}
    
    def _analyze_aggressive_opportunities_enhanced(self, analyst_data: Dict[str, Any], 
                                                 researcher_data: Dict[str, Any], 
                                                 risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """增强激进机会分析"""
        
        # 基础机会分析
        base_opportunities = {
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
        
        # 从分析师数据中提取机会信号
        enhanced_opportunities = base_opportunities.copy()
        
        # 技术分析机会
        technical_analysis = analyst_data.get("technical_analysis", {})
        if technical_analysis:
            signals = technical_analysis.get("signals", {})
            if signals.get("strong_breakout", False):
                enhanced_opportunities["breakout_strength"] = "very_strong"
            if signals.get("volume_surge", False):
                enhanced_opportunities["volume_momentum"] = "explosive"
        
        # 链上分析机会
        onchain_analysis = analyst_data.get("onchain_analysis", {})
        if onchain_analysis:
            metrics = onchain_analysis.get("metrics", {})
            if metrics.get("whale_accumulation", False):
                enhanced_opportunities["whane_confidence"] = "very_high"
            if metrics.get("network_activity_surge", False):
                enhanced_opportunities["network_momentum"] = "strong"
        
        # 情绪分析机会
        sentiment_analysis = analyst_data.get("sentiment_analysis", {})
        if sentiment_analysis:
            sentiment_score = sentiment_analysis.get("sentiment_score", 0.5)
            if sentiment_score > 0.8:
                enhanced_opportunities["sentiment_euphoria"] = "extreme"
                enhanced_opportunities["fomo_potential"] = "very_high"
        
        # 研究员观点机会
        if researcher_data.get("bull_analysis"):
            bull_analysis = researcher_data["bull_analysis"]
            bull_signals = bull_analysis.get("bull_signals", {})
            if bull_signals.get("signal_strength") == "强":
                enhanced_opportunities["research_bullish_consensus"] = "strong"
        
        # 计算机会评分
        enhanced_opportunities["opportunity_score"] = self._calculate_opportunity_score(enhanced_opportunities)
        enhanced_opportunities["action_recommendation"] = self._determine_aggressive_action(enhanced_opportunities)
        
        return enhanced_opportunities
    
    def _calculate_opportunity_score(self, opportunity_analysis: Dict[str, Any]) -> float:
        """计算机会评分"""
        opportunity_factors = 0
        total_factors = 0
        
        # 关键机会因素
        key_factors = [
            ("market_momentum", "strong_bullish"),
            ("sentiment_extreme", "extreme_greed"),
            ("volume_breakout", True),
            ("technical_breakthrough", True),
            ("whale_accumulation", True),
            ("institutional_fomo", True)
        ]
        
        for factor, target_value in key_factors:
            if opportunity_analysis.get(factor) == target_value:
                opportunity_factors += 1
            total_factors += 1
        
        # 强信号因素
        strong_signals = [
            "breakout_strength", "volume_momentum", "whane_confidence", 
            "network_momentum", "sentiment_euphoria", "research_bullish_consensus"
        ]
        
        for signal in strong_signals:
            if opportunity_analysis.get(signal) in ["very_strong", "explosive", "very_high", "strong", "extreme"]:
                opportunity_factors += 0.5
            total_factors += 0.5
        
        return opportunity_factors / total_factors if total_factors > 0 else 0.5
    
    def _determine_aggressive_action(self, opportunity_analysis: Dict[str, Any]) -> str:
        """确定激进操作建议"""
        score = opportunity_analysis.get("opportunity_score", 0.5)
        
        if score >= 0.8:
            return "强烈买入"
        elif score >= 0.6:
            return "积极买入"
        elif score >= 0.4:
            return "适度买入"
        else:
            return "观望"
    
    def _generate_enhanced_aggressive_strategies(self, opportunity_analysis: Dict[str, Any], 
                                                debate_material: Dict[str, Any]) -> List[str]:
        """生成增强激进策略"""
        strategies = []
        
        opportunity_score = opportunity_analysis.get("opportunity_score", 0.5)
        action = opportunity_analysis.get("action_recommendation", "观望")
        
        # 基于机会评分的策略
        if opportunity_score >= 0.8:
            strategies.append("极高机会评分：采用最大化收益策略")
            strategies.append("大仓位配置，目标收益50-100%")
            strategies.append("短期持有，快速获利了结")
        elif opportunity_score >= 0.6:
            strategies.append("高机会评分：采用积极进取策略")
            strategies.append("中到大仓位配置，目标收益30-50%")
            strategies.append("中短期持有，灵活调整")
        else:
            strategies.append("中等机会评分：采用谨慎激进策略")
            strategies.append("小到中仓位配置，目标收益15-30%")
            strategies.append("严格止损，控制风险")
        
        # 基于市场状况的策略
        market_condition = debate_material.get("market_condition", "normal")
        if market_condition == "bullish":
            strategies.append("牛市环境：顺势而为，加大仓位")
            strategies.append("利用市场情绪，追涨突破")
        elif market_condition == "bearish":
            strategies.append("熊市环境：寻找超跌反弹机会")
            strategies.append("短线操作，快进快出")
        
        # 基于技术信号策略
        if opportunity_analysis.get("breakout_strength") == "very_strong":
            strategies.append("技术突破：突破买入策略")
            strategies.append("跟进强势趋势，放大收益")
        
        if opportunity_analysis.get("volume_momentum") == "explosive":
            strategies.append("成交量爆发：成交量驱动策略")
            strategies.append("跟随资金流向，顺势操作")
        
        return strategies
    
    def _assess_enhanced_leverage_opportunities(self, opportunity_analysis: Dict[str, Any], 
                                                 debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """评估增强杠杆机会"""
        opportunity_score = opportunity_analysis.get("opportunity_score", 0.5)
        
        if opportunity_score >= 0.8:
            return {
                "recommended_leverage": "5-10x",
                "leverage_confidence": "high",
                "liquidation_risk": "high",
                "funding_rate_impact": "significant",
                "volatility_amplification": "extreme",
                "position_size_recommendation": "20-30% of portfolio",
                "quick_profit_window": "24-48小时",
                "risk_management": "very_tight_stops"
            }
        elif opportunity_score >= 0.6:
            return {
                "recommended_leverage": "3-5x",
                "leverage_confidence": "medium",
                "liquidation_risk": "medium",
                "funding_rate_impact": "moderate",
                "volatility_amplification": "high",
                "position_size_recommendation": "15-25% of portfolio",
                "quick_profit_window": "48-72小时",
                "risk_management": "tight_stops"
            }
        else:
            return {
                "recommended_leverage": "1-3x",
                "leverage_confidence": "low",
                "liquidation_risk": "low",
                "funding_rate_impact": "minimal",
                "volatility_amplification": "moderate",
                "position_size_recommendation": "10-15% of portfolio",
                "quick_profit_window": "72-120小时",
                "risk_management": "moderate_stops"
            }
    
    def _generate_enhanced_aggressive_recommendations(self, opportunity_analysis: Dict[str, Any],
                                                    strategies: List[str],
                                                    leverage: Dict[str, Any],
                                                    debate_material: Dict[str, Any]) -> List[str]:
        """生成增强激进投资建议"""
        recommendations = []
        
        opportunity_score = opportunity_analysis.get("opportunity_score", 0.5)
        action = opportunity_analysis.get("action_recommendation", "观望")
        
        # 基于机会评分的核心建议
        if opportunity_score >= 0.8:
            recommendations.append("🚀 极高机会：强烈建议大仓位介入")
            recommendations.append("🎯 目标收益50-100%，短期持有")
            recommendations.append("⚡ 快速操作，把握时间窗口")
        elif opportunity_score >= 0.6:
            recommendations.append("🚀 高机会：建议积极建仓")
            recommendations.append("🎯 目标收益30-50%，中短期持有")
            recommendations.append("⚡ 灵活调整，控制节奏")
        else:
            recommendations.append("🚀 中等机会：谨慎介入")
            recommendations.append("🎯 目标收益15-30%，小仓位试水")
            recommendations.append("⚡ 严格止损，防范风险")
        
        # 杠杆建议
        leverage_rec = leverage.get("recommended_leverage", "1-3x")
        recommendations.append(f"💹 推荐杠杆：{leverage_rec}")
        
        # 仓位建议
        position_size = leverage.get("position_size_recommendation", "10-15% of portfolio")
        recommendations.append(f"📊 仓位规模：{position_size}")
        
        # 时间窗口建议
        time_window = leverage.get("quick_profit_window", "72-120小时")
        recommendations.append(f"⏰ 操作窗口：{time_window}")
        
        # 策略建议
        if strategies:
            recommendations.append("🔧 激进策略：")
            for strategy in strategies[:3]:
                recommendations.append(f"   • {strategy}")
        
        # 风险控制建议
        risk_management = leverage.get("risk_management", "moderate_stops")
        recommendations.append(f"🛡️ 风险控制：{risk_management}")
        
        return recommendations
    
    def _calculate_enhanced_confidence(self, opportunity_analysis: Dict[str, Any], 
                                     debate_material: Dict[str, Any]) -> float:
        """计算增强分析置信度"""
        base_confidence = 0.5
        
        # 基于机会评分的置信度调整
        opportunity_score = opportunity_analysis.get("opportunity_score", 0.5)
        opportunity_bonus = opportunity_score * 0.3
        
        # 基于数据完整性的置信度调整
        analyst_data = debate_material.get("analyst_data", {})
        available_analyses = len([k for k, v in analyst_data.items() if v])
        data_completeness_bonus = min(available_analyses * 0.05, 0.2)
        
        # 基于市场状况的置信度调整
        market_condition = debate_material.get("market_condition", "normal")
        if market_condition == "bullish":
            market_bonus = 0.15
        elif market_condition == "normal":
            market_bonus = 0.1
        else:
            market_bonus = 0.05
        
        final_confidence = base_confidence + opportunity_bonus + data_completeness_bonus + market_bonus
        return min(final_confidence, 0.95)
    
    def _generate_enhanced_observations(self, opportunity_analysis: Dict[str, Any], 
                                      debate_material: Dict[str, Any]) -> List[str]:
        """生成增强关键观察"""
        observations = []
        
        # 机会评分观察
        opportunity_score = opportunity_analysis.get("opportunity_score", 0.5)
        observations.append(f"🎯 机会评分：{opportunity_score:.2f}/1.0")
        
        # 操作建议观察
        action = opportunity_analysis.get("action_recommendation", "观望")
        observations.append(f"🚀 操作建议：{action}")
        
        # 市场动量观察
        momentum = opportunity_analysis.get("market_momentum", "unknown")
        observations.append(f"📈 市场动量：{momentum}")
        
        # 情绪状态观察
        sentiment = opportunity_analysis.get("sentiment_extreme", "unknown")
        observations.append(f"😊 情绪状态：{sentiment}")
        
        # 技术突破观察
        breakthrough = opportunity_analysis.get("technical_breakthrough", False)
        observations.append(f"🔧 技术突破：{'是' if breakthrough else '否'}")
        
        # 数据覆盖观察
        analyst_data = debate_material.get("analyst_data", {})
        available_analyses = len([v for v in analyst_data.values() if v])
        observations.append(f"📊 分析覆盖：{available_analyses}/5")
        
        # 市场状况观察
        market_condition = debate_material.get("market_condition", "unknown")
        observations.append(f"🌊 市场状况：{market_condition}")
        
        return observations
    
    def _summarize_debate_material(self, debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """总结辩论材料"""
        summary = {
            "opportunity_assessment": {},
            "signal_strength": {},
            "market_context": {},
            "data_quality": "medium"
        }
        
        # 机会评估
        analyst_data = debate_material.get("analyst_data", {})
        for analyst_type, analysis in analyst_data.items():
            if analysis:
                summary["opportunity_assessment"][analyst_type] = {
                    "available": True,
                    "opportunity_score": 0.7,  # 简化处理
                    "confidence": analysis.get("confidence", 0.5)
                }
        
        # 信号强度
        available_analyses = len([v for v in analyst_data.values() if v])
        if available_analyses >= 4:
            summary["signal_strength"] = "strong"
        elif available_analyses >= 2:
            summary["signal_strength"] = "medium"
        else:
            summary["signal_strength"] = "weak"
        
        # 市场背景
        summary["market_context"] = {
            "condition": debate_material.get("market_condition", "unknown"),
            "symbol": debate_material.get("symbol", "unknown"),
            "timestamp": debate_material.get("timestamp", "unknown")
        }
        
        # 数据质量
        summary["data_quality"] = "high" if available_analyses >= 4 else "medium" if available_analyses >= 2 else "low"
        
        return summary
    
    def _enhance_aggressive_debate_with_ai(self, opportunity_analysis: Dict[str, Any], 
                                         debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI增强激进辩论分析"""
        try:
            # 构建AI分析prompt
            prompt = self._build_aggressive_debate_prompt(opportunity_analysis, debate_material)
            
            # 调用AI分析
            ai_response = self.call_ai_analysis(prompt)
            
            # 解析AI响应
            ai_analysis = self.parse_ai_json_response(ai_response, {
                "enhanced_opportunity_assessment": {},
                "leverage_optimization": {},
                "timing_precision": [],
                "risk_amplification_analysis": [],
                "market_irrationality_exploitation": [],
                "confidence_adjustment": 0.0,
                "strategic_insights": []
            })
            
            return {
                "ai_enhanced": True,
                "ai_opportunity_assessment": ai_analysis.get("enhanced_opportunity_assessment", {}),
                "ai_leverage_optimization": ai_analysis.get("leverage_optimization", {}),
                "ai_timing_precision": ai_analysis.get("timing_precision", []),
                "ai_risk_amplification": ai_analysis.get("risk_amplification_analysis", []),
                "ai_market_irrationality": ai_analysis.get("market_irrationality_exploitation", []),
                "ai_confidence_adjustment": ai_analysis.get("confidence_adjustment", 0.0),
                "ai_strategic_insights": ai_analysis.get("strategic_insights", [])
            }
            
        except Exception as e:
            logger.error(f"AI增强激进辩论分析失败: {e}")
            return {"ai_enhanced": False, "ai_error": str(e)}
    
    def _build_aggressive_debate_prompt(self, opportunity_analysis: Dict[str, Any], 
                                       debate_material: Dict[str, Any]) -> str:
        """构建激进辩论AI提示词"""
        return f"""作为专业的加密货币激进机会挖掘专家，请基于以下辩论材料提供深度AI增强分析：

当前激进机会分析结果：
{opportunity_analysis}

辩论材料概要：
- 机会评分：{opportunity_analysis.get('opportunity_score', 0.5)}
- 信号强度：{len([v for v in debate_material.get('analyst_data', {}).values() if v])}/5
- 市场状况：{debate_material.get('market_condition', 'unknown')}

请从极度激进的机会挖掘角度提供深度辩论分析：

1. 增强的机会评估 - 基于多维度辩论材料的高Alpha机会识别
2. 杠杆优化 - 提供精确的杠杆使用优化方案和时机
3. 时机精度 - 提供高精度的入场和出场时机分析
4. 风险放大分析 - 分析如何在可控风险下放大收益
5. 市场非理性利用 - 识别和利用市场非理性状态
6. 置信度调整建议 - 基于辩论材料调整整体分析置信度
7. 战略洞察 - 提供基于大数据的激进投资战略洞察

请特别关注：
- 多维度高Alpha信号的识别和验证
- 市场情绪极端化的机会窗口
- 技术突破和成交量爆发的协同效应
- 机构FOMO和鲸鱼行为的跟庄策略
- 杠杆产品的最优使用时机和风险控制

请以JSON格式回复，包含enhanced_opportunity_assessment, leverage_optimization, timing_precision, risk_amplification_analysis, market_irrationality_exploitation, confidence_adjustment, strategic_insights字段。"""
