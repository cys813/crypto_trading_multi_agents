"""
中性辩论者 - 平衡风险和收益，提供客观分析

基于原版辩论架构，针对加密货币市场特性优化
"""

from typing import Dict, Any, List
import logging

from src.crypto_trading_agents.services.ai_analysis_mixin import StandardAIAnalysisMixin

logger = logging.getLogger(__name__)

class NeutralDebator(StandardAIAnalysisMixin):
    """加密货币中性辩论者"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化中性辩论者
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.risk_tolerance = config.get("risk_config", {}).get("neutral_tolerance", 0.5)
        
        # 初始化AI分析混入类
        super().__init__()
        
        # 初始化LLM服务（如果还未初始化）
        llm_service_config = config.get("llm_service_config")
        if llm_service_config:
            try:
                from src.crypto_trading_agents.services.unified_llm_service import initialize_llm_service
                initialize_llm_service(llm_service_config)
                logger.info("NeutralDebator: 统一LLM服务初始化完成")
            except ImportError:
                logger.warning("NeutralDebator: 无法导入LLM服务，将使用纯规则分析")
        
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
            
            # AI增强分析（如果启用）
            ai_enhancement = {}
            if self.is_ai_enabled():
                try:
                    ai_enhancement = self._enhance_neutral_analysis_with_ai(
                        risk_analysis, market_report, sentiment_report, news_report, fundamentals_report
                    )
                    # 将AI分析结果合并到主分析中
                    risk_analysis.update(ai_enhancement)
                except Exception as e:
                    logger.warning(f"NeutralDebator AI增强分析失败: {e}")
                    ai_enhancement = {"ai_error": str(e)}

            return {
                "risk_analysis": risk_analysis,
                "balanced_strategies": balanced_strategies,
                "risk_reward_assessment": risk_reward_assessment,
                "neutral_recommendations": neutral_recommendations,
                "risk_level": "medium",
                "expected_return": "balanced",
                "confidence": self._calculate_confidence(risk_analysis),
                "key_observations": self._generate_key_observations(risk_analysis),
                "ai_enhanced": self.is_ai_enabled(),
                "ai_analysis": ai_enhancement,
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
    
    def _calculate_confidence(self, risk_analysis: Dict[str, Any]) -> float:
        """计算分析置信度"""
        
        # 中性分析的置信度基于市场成熟度和效率
        maturity_score = 0.6 if risk_analysis.get("market_maturity") == "developing" else 0.8
        efficiency_score = 0.7 if risk_analysis.get("market_efficiency") == "improving" else 0.5
        
        confidence_score = (maturity_score + efficiency_score) / 2
        
        return min(confidence_score, 0.95)
    
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

    def _enhance_neutral_analysis_with_ai(self, risk_analysis: Dict[str, Any], 
                                         market_report: str, sentiment_report: str,
                                         news_report: str, fundamentals_report: str) -> Dict[str, Any]:
        """使用AI增强中性分析"""
        try:
            # 构建AI分析提示词
            prompt = self._build_neutral_analysis_prompt(
                risk_analysis, market_report, sentiment_report, news_report, fundamentals_report
            )
            
            # 调用AI分析
            ai_response = self.call_ai_analysis(prompt)
            
            # 解析AI响应
            ai_analysis = self.parse_ai_json_response(ai_response, {
                "enhanced_balance_assessment": {},
                "strategy_optimization": [],
                "market_neutrality_adjustment": {},
                "risk_reward_optimization": {},
                "portfolio_allocation_tuning": {},
                "ai_insights": []
            })
            
            return {
                "ai_enhanced": True,
                "ai_balance_assessment": ai_analysis.get("enhanced_balance_assessment", {}),
                "ai_strategy_optimization": ai_analysis.get("strategy_optimization", []),
                "ai_neutrality_adjustment": ai_analysis.get("market_neutrality_adjustment", {}),
                "ai_risk_reward_optimization": ai_analysis.get("risk_reward_optimization", {}),
                "ai_portfolio_tuning": ai_analysis.get("portfolio_allocation_tuning", {}),
                "ai_insights": ai_analysis.get("ai_insights", [])
            }
            
        except Exception as e:
            logger.error(f"AI增强中性分析失败: {e}")
            return {
                "ai_enhanced": False,
                "ai_error": str(e)
            }
    
    def _build_neutral_analysis_prompt(self, risk_analysis: Dict[str, Any], 
                                       market_report: str, sentiment_report: str,
                                       news_report: str, fundamentals_report: str) -> str:
        """构建中性分析AI提示词"""
        return f"""作为专业的加密货币市场中性分析专家，请基于以下分析结果提供深度AI增强分析：

当前中性风险分析结果：
{risk_analysis}

市场报告：
{market_report}

情绪报告：
{sentiment_report}

新闻报告：
{news_report}

基本面报告：
{fundamentals_report}

请从中性的、客观的角度提供分析，既要识别机会也要评估风险：

1. 增强的平衡评估 - 提供更细致的风险收益平衡分析
2. 策略优化建议 - 优化现有投资策略以获得更好的风险调整收益
3. 市场中性调整 - 根据当前市场环境调整中性立场
4. 风险收益优化 - 提供具体的风险收益比例优化建议
5. 投资组合调优 - 基于AI分析优化资产配置比例
6. AI洞察 - 提供基于大数据的市场中性洞察

请特别关注：
- 市场周期的当前位置和转折点识别
- 机构资金流向的深层分析
- 技术指标和基本面的协同分析
- 市场情绪的极端值识别和反向指标
- 跨资产类别的相关性变化

请以JSON格式回复，包含enhanced_balance_assessment, strategy_optimization, market_neutrality_adjustment, risk_reward_optimization, portfolio_allocation_tuning, ai_insights字段。"""

    def analyze_with_debate_material(self, debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于辩论材料进行分析
        
        Args:
            debate_material: 包含所有分析师和研究员分析结果的辩论材料
            
        Returns:
            中性辩论分析结果
        """
        try:
            # 解析辩论材料
            analyst_data = debate_material.get("analyst_data", {})
            researcher_data = debate_material.get("researcher_data", {})
            risk_data = debate_material.get("risk_data", {})
            
            # 增强的平衡风险分析
            balanced_risk_analysis = self._analyze_balanced_risks_enhanced(
                analyst_data, researcher_data, risk_data
            )
            
            # 平衡策略
            balanced_strategies = self._generate_enhanced_balanced_strategies(balanced_risk_analysis, debate_material)
            
            # 风险收益评估
            risk_reward_assessment = self._assess_enhanced_risk_reward_balance(balanced_risk_analysis, debate_material)
            
            # 中性投资建议
            neutral_recommendations = self._generate_enhanced_neutral_recommendations(
                balanced_risk_analysis, balanced_strategies, risk_reward_assessment, debate_material
            )
            
            # AI增强分析
            ai_enhancement = {}
            if self.is_ai_enabled():
                try:
                    ai_enhancement = self._enhance_neutral_debate_with_ai(
                        balanced_risk_analysis, debate_material
                    )
                except Exception as e:
                    logger.warning(f"NeutralDebator AI增强辩论分析失败: {e}")
                    ai_enhancement = {"ai_error": str(e)}
            
            return {
                "risk_analysis": balanced_risk_analysis,
                "balanced_strategies": balanced_strategies,
                "risk_reward_assessment": risk_reward_assessment,
                "neutral_recommendations": neutral_recommendations,
                "risk_level": "medium",
                "expected_return": "balanced",
                "confidence": self._calculate_enhanced_confidence(balanced_risk_analysis, debate_material),
                "key_observations": self._generate_enhanced_observations(balanced_risk_analysis, debate_material),
                "ai_enhanced": self.is_ai_enabled(),
                "ai_analysis": ai_enhancement,
                "debate_material_summary": self._summarize_debate_material(debate_material)
            }
            
        except Exception as e:
            logger.error(f"NeutralDebator analyze_with_debate_material失败: {e}")
            return {"error": str(e)}
    
    def _analyze_balanced_risks_enhanced(self, analyst_data: Dict[str, Any], 
                                       researcher_data: Dict[str, Any], 
                                       risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """增强平衡风险分析"""
        
        # 基础风险分析
        base_risks = {
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
        
        # 从分析师数据中提取平衡视角
        enhanced_risks = base_risks.copy()
        
        # 技术分析平衡视角
        technical_analysis = analyst_data.get("technical_analysis", {})
        if technical_analysis:
            tech_indicators = technical_analysis.get("indicators", {})
            if tech_indicators.get("rsi", 50) > 70:
                enhanced_risks["technical_overbought"] = "moderate"
            elif tech_indicators.get("rsi", 50) < 30:
                enhanced_risks["technical_oversold"] = "moderate"
            
            if technical_analysis.get("signals", {}).get("trend_strength", "") == "strong":
                enhanced_risks["trend_momentum"] = "strong"
        
        # 链上分析平衡视角
        onchain_analysis = analyst_data.get("onchain_analysis", {})
        if onchain_analysis:
            onchain_metrics = onchain_analysis.get("metrics", {})
            if onchain_metrics.get("active_addresses_growth", 0) > 0:
                enhanced_risks["network_growth"] = "positive"
            elif onchain_metrics.get("active_addresses_decline", 0) > 0:
                enhanced_risks["network_growth"] = "negative"
        
        # 情绪分析平衡视角
        sentiment_analysis = analyst_data.get("sentiment_analysis", {})
        if sentiment_analysis:
            sentiment_score = sentiment_analysis.get("sentiment_score", 0.5)
            if sentiment_score > 0.6:
                enhanced_risks["sentiment_bias"] = "bullish"
            elif sentiment_score < 0.4:
                enhanced_risks["sentiment_bias"] = "bearish"
            else:
                enhanced_risks["sentiment_bias"] = "neutral"
        
        # 研究员观点平衡
        if researcher_data.get("bull_analysis") and researcher_data.get("bear_analysis"):
            bull_confidence = researcher_data["bull_analysis"].get("confidence", 0.5)
            bear_confidence = researcher_data["bear_analysis"].get("confidence", 0.5)
            
            confidence_diff = abs(bull_confidence - bear_confidence)
            if confidence_diff < 0.2:
                enhanced_risks["research_consensus"] = "balanced"
            elif bull_confidence > bear_confidence:
                enhanced_risks["research_consensus"] = "slightly_bullish"
            else:
                enhanced_risks["research_consensus"] = "slightly_bearish"
        
        # 计算平衡评分
        enhanced_risks["balance_score"] = self._calculate_balance_score(enhanced_risks)
        enhanced_risks["market_equilibrium"] = self._assess_market_equilibrium(enhanced_risks)
        
        return enhanced_risks
    
    def _calculate_balance_score(self, risk_analysis: Dict[str, Any]) -> float:
        """计算平衡评分"""
        balance_factors = 0
        total_factors = 0
        
        # 情绪平衡
        sentiment_bias = risk_analysis.get("sentiment_bias", "neutral")
        if sentiment_bias == "neutral":
            balance_factors += 1
        total_factors += 1
        
        # 研究共识平衡
        research_consensus = risk_analysis.get("research_consensus", "balanced")
        if research_consensus == "balanced":
            balance_factors += 1
        total_factors += 1
        
        # 网络增长平衡
        network_growth = risk_analysis.get("network_growth", "neutral")
        if network_growth in ["neutral", "positive"]:
            balance_factors += 1
        total_factors += 1
        
        return balance_factors / total_factors if total_factors > 0 else 0.5
    
    def _assess_market_equilibrium(self, risk_analysis: Dict[str, Any]) -> str:
        """评估市场均衡状态"""
        balance_score = risk_analysis.get("balance_score", 0.5)
        
        if balance_score >= 0.8:
            return "highly_balanced"
        elif balance_score >= 0.6:
            return "moderately_balanced"
        elif balance_score >= 0.4:
            return "slightly_imbalanced"
        else:
            return "significantly_imbalanced"
    
    def _generate_enhanced_balanced_strategies(self, risk_analysis: Dict[str, Any], 
                                             debate_material: Dict[str, Any]) -> List[str]:
        """生成增强平衡策略"""
        strategies = []
        
        balance_score = risk_analysis.get("balance_score", 0.5)
        equilibrium = risk_analysis.get("market_equilibrium", "moderately_balanced")
        
        # 基于平衡评分的策略
        if balance_score >= 0.7:
            strategies.append("市场高度平衡：采用核心卫星策略")
            strategies.append("60%核心配置，40%卫星配置")
            strategies.append("定期再平衡维持平衡")
        elif balance_score >= 0.5:
            strategies.append("市场中度平衡：均衡配置策略")
            strategies.append("50%主流币种，30%中市值，20%小市值")
            strategies.append("适度动态调整")
        else:
            strategies.append("市场失衡：倾向防御性平衡")
            strategies.append("增加稳定币比例至40-50%")
            strategies.append("降低风险资产配置")
        
        # 基于市场状况的策略
        market_condition = debate_material.get("market_condition", "normal")
        if market_condition == "bullish":
            strategies.append("牛市环境：逐步获利了结，保持平衡")
            strategies.append("避免过度追高，维持合理配置")
        elif market_condition == "bearish":
            strategies.append("熊市环境：分批建仓，逐步平衡")
            strategies.append("保持耐心，等待市场稳定")
        
        # 基于研究共识的策略
        research_consensus = risk_analysis.get("research_consensus", "balanced")
        if research_consensus == "balanced":
            strategies.append("研究观点平衡：维持中性配置")
            strategies.append("关注市场变化，灵活调整")
        elif research_consensus == "slightly_bullish":
            strategies.append("研究偏牛：适度增加风险敞口")
            strategies.append("设置合理止损，控制下行风险")
        elif research_consensus == "slightly_bearish":
            strategies.append("研究偏熊：适度降低风险敞口")
            strategies.append("保持流动性，等待机会")
        
        return strategies
    
    def _assess_enhanced_risk_reward_balance(self, risk_analysis: Dict[str, Any], 
                                           debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """评估增强风险收益平衡"""
        balance_score = risk_analysis.get("balance_score", 0.5)
        market_condition = debate_material.get("market_condition", "normal")
        
        if balance_score >= 0.7:
            return {
                "risk_level": "medium",
                "reward_potential": "moderate",
                "risk_reward_ratio": "1:1",
                "recommended_allocation": {
                    "conservative": "30%",
                    "balanced": "50%",
                    "aggressive": "20%"
                },
                "position_size_guidelines": "5-8% per position",
                "stop_loss_recommendations": "8-12%",
                "take_profit_recommendations": "15-25%",
                "rebalancing_frequency": "monthly"
            }
        elif balance_score >= 0.5:
            return {
                "risk_level": "medium_to_high",
                "reward_potential": "moderate_to_high",
                "risk_reward_ratio": "1:1.5",
                "recommended_allocation": {
                    "conservative": "25%",
                    "balanced": "45%",
                    "aggressive": "30%"
                },
                "position_size_guidelines": "6-10% per position",
                "stop_loss_recommendations": "6-10%",
                "take_profit_recommendations": "20-30%",
                "rebalancing_frequency": "bi_weekly"
            }
        else:
            return {
                "risk_level": "high",
                "reward_potential": "low_to_moderate",
                "risk_reward_ratio": "1:0.8",
                "recommended_allocation": {
                    "conservative": "40%",
                    "balanced": "40%",
                    "aggressive": "20%"
                },
                "position_size_guidelines": "3-6% per position",
                "stop_loss_recommendations": "5-8%",
                "take_profit_recommendations": "10-15%",
                "rebalancing_frequency": "weekly"
            }
    
    def _generate_enhanced_neutral_recommendations(self, risk_analysis: Dict[str, Any],
                                                strategies: List[str],
                                                risk_reward: Dict[str, Any],
                                                debate_material: Dict[str, Any]) -> List[str]:
        """生成增强中性投资建议"""
        recommendations = []
        
        balance_score = risk_analysis.get("balance_score", 0.5)
        equilibrium = risk_analysis.get("market_equilibrium", "moderately_balanced")
        
        # 基于平衡状态的核心建议
        if equilibrium == "highly_balanced":
            recommendations.append("⚖️ 市场高度平衡：维持均衡配置策略")
            recommendations.append("🎯 采用核心卫星投资组合")
            recommendations.append("📊 定期再平衡维持平衡状态")
        elif equilibrium == "moderately_balanced":
            recommendations.append("⚖️ 市场中度平衡：采用灵活平衡策略")
            recommendations.append("🎯 关注市场变化，适度调整配置")
            recommendations.append("📊 保持风险收益平衡")
        else:
            recommendations.append("⚖️ 市场失衡：倾向防御性平衡")
            recommendations.append("🎯 增加防御性资产配置")
            recommendations.append("📊 等待市场恢复平衡")
        
        # 资产配置建议
        allocation = risk_reward.get("recommended_allocation", {})
        recommendations.append(f"💰 推荐配置：保守{allocation.get('conservative', '30%')}，平衡{allocation.get('balanced', '50%')}，激进{allocation.get('aggressive', '20%')}")
        
        # 风险控制建议
        recommendations.append("🎯 风险控制：")
        recommendations.append(f"   • 单笔仓位：{risk_reward.get('position_size_guidelines', '5-8%')}")
        recommendations.append(f"   • 止损设置：{risk_reward.get('stop_loss_recommendations', '8-12%')}")
        recommendations.append(f"   • 止盈目标：{risk_reward.get('take_profit_recommendations', '15-25%')}")
        
        # 策略建议
        if strategies:
            recommendations.append("🔧 平衡策略：")
            for strategy in strategies[:3]:
                recommendations.append(f"   • {strategy}")
        
        # 监控建议
        recommendations.append("📋 监控建议：")
        recommendations.append(f"   • 再平衡频率：{risk_reward.get('rebalancing_frequency', 'monthly')}")
        recommendations.append("   • 密切关注市场情绪变化")
        recommendations.append("   • 跟踪研究观点变化")
        
        return recommendations
    
    def _calculate_enhanced_confidence(self, risk_analysis: Dict[str, Any], 
                                     debate_material: Dict[str, Any]) -> float:
        """计算增强分析置信度"""
        base_confidence = 0.6
        
        # 基于市场平衡性的置信度调整
        balance_score = risk_analysis.get("balance_score", 0.5)
        balance_bonus = balance_score * 0.2
        
        # 基于数据完整性的置信度调整
        analyst_data = debate_material.get("analyst_data", {})
        available_analyses = len([k for k, v in analyst_data.items() if v])
        data_completeness_bonus = min(available_analyses * 0.05, 0.2)
        
        # 基于研究平衡性的置信度调整
        research_consensus = risk_analysis.get("research_consensus", "balanced")
        if research_consensus == "balanced":
            research_bonus = 0.15
        elif research_consensus in ["slightly_bullish", "slightly_bearish"]:
            research_bonus = 0.1
        else:
            research_bonus = 0.05
        
        final_confidence = base_confidence + balance_bonus + data_completeness_bonus + research_bonus
        return min(final_confidence, 0.95)
    
    def _generate_enhanced_observations(self, risk_analysis: Dict[str, Any], 
                                      debate_material: Dict[str, Any]) -> List[str]:
        """生成增强关键观察"""
        observations = []
        
        # 平衡状态观察
        balance_score = risk_analysis.get("balance_score", 0.5)
        equilibrium = risk_analysis.get("market_equilibrium", "moderately_balanced")
        observations.append(f"⚖️ 平衡评分：{balance_score:.2f}/1.0")
        observations.append(f"🎯 市场均衡：{equilibrium}")
        
        # 研究共识观察
        research_consensus = risk_analysis.get("research_consensus", "balanced")
        observations.append(f"🔍 研究共识：{research_consensus}")
        
        # 情绪偏差观察
        sentiment_bias = risk_analysis.get("sentiment_bias", "neutral")
        observations.append(f"😊 情绪偏差：{sentiment_bias}")
        
        # 网络增长观察
        network_growth = risk_analysis.get("network_growth", "neutral")
        observations.append(f"🌐 网络增长：{network_growth}")
        
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
            "balance_assessment": {},
            "data_coverage": {},
            "market_context": {},
            "research_harmony": "unknown"
        }
        
        # 平衡评估
        analyst_data = debate_material.get("analyst_data", {})
        for analyst_type, analysis in analyst_data.items():
            if analysis:
                summary["balance_assessment"][analyst_type] = {
                    "available": True,
                    "bias": "neutral",  # 简化处理
                    "confidence": analysis.get("confidence", 0.5)
                }
        
        # 数据覆盖
        available_analyses = len([v for v in analyst_data.values() if v])
        summary["data_coverage"] = {
            "available_analyses": available_analyses,
            "total_analyses": 5,
            "coverage_ratio": available_analyses / 5
        }
        
        # 市场背景
        summary["market_context"] = {
            "condition": debate_material.get("market_condition", "unknown"),
            "symbol": debate_material.get("symbol", "unknown"),
            "timestamp": debate_material.get("timestamp", "unknown")
        }
        
        # 研究和谐度
        researcher_data = debate_material.get("researcher_data", {})
        if researcher_data.get("bull_analysis") and researcher_data.get("bear_analysis"):
            bull_confidence = researcher_data["bull_analysis"].get("confidence", 0.5)
            bear_confidence = researcher_data["bear_analysis"].get("confidence", 0.5)
            harmony_score = 1.0 - abs(bull_confidence - bear_confidence)
            
            if harmony_score >= 0.8:
                summary["research_harmony"] = "high"
            elif harmony_score >= 0.6:
                summary["research_harmony"] = "medium"
            else:
                summary["research_harmony"] = "low"
        
        return summary
    
    def _enhance_neutral_debate_with_ai(self, risk_analysis: Dict[str, Any], 
                                       debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI增强中性辩论分析"""
        try:
            # 构建AI分析prompt
            prompt = self._build_neutral_debate_prompt(risk_analysis, debate_material)
            
            # 调用AI分析
            ai_response = self.call_ai_analysis(prompt)
            
            # 解析AI响应
            ai_analysis = self.parse_ai_json_response(ai_response, {
                "enhanced_balance_assessment": {},
                "market_equilibrium_analysis": {},
                "strategy_optimization": [],
                "risk_reward_calibration": {},
                "timing_recommendations": [],
                "confidence_adjustment": 0.0,
                "strategic_insights": []
            })
            
            return {
                "ai_enhanced": True,
                "ai_balance_assessment": ai_analysis.get("enhanced_balance_assessment", {}),
                "ai_equilibrium_analysis": ai_analysis.get("market_equilibrium_analysis", {}),
                "ai_strategy_optimization": ai_analysis.get("strategy_optimization", []),
                "ai_risk_reward_calibration": ai_analysis.get("risk_reward_calibration", {}),
                "ai_timing_recommendations": ai_analysis.get("timing_recommendations", []),
                "ai_confidence_adjustment": ai_analysis.get("confidence_adjustment", 0.0),
                "ai_strategic_insights": ai_analysis.get("strategic_insights", [])
            }
            
        except Exception as e:
            logger.error(f"AI增强中性辩论分析失败: {e}")
            return {"ai_enhanced": False, "ai_error": str(e)}
    
    def _build_neutral_debate_prompt(self, risk_analysis: Dict[str, Any], 
                                   debate_material: Dict[str, Any]) -> str:
        """构建中性辩论AI提示词"""
        return f"""作为专业的加密货币中性市场分析师，请基于以下辩论材料提供深度AI增强分析：

当前中性风险分析结果：
{risk_analysis}

辩论材料概要：
- 平衡评分：{risk_analysis.get('balance_score', 0.5)}
- 市场均衡：{risk_analysis.get('market_equilibrium', 'moderately_balanced')}
- 研究共识：{risk_analysis.get('research_consensus', 'balanced')}
- 数据覆盖：{len([v for v in debate_material.get('analyst_data', {}).values() if v])}/5

请从中性、客观的角度提供深度辩论分析：

1. 增强的平衡评估 - 基于多维度辩论材料的市场平衡状态评估
2. 市场均衡分析 - 分析当前市场的均衡程度和可持续性
3. 策略优化 - 提供最优的中性投资策略优化建议
4. 风险收益校准 - 精确校准风险收益比例以达到最佳平衡
5. 时机建议 - 提供基于市场均衡状态的最佳操作时机
6. 置信度调整建议 - 基于辩论材料调整整体分析置信度
7. 战略洞察 - 提供基于大数据的中性市场战略洞察

请特别关注：
- 多维度信号的平衡性和一致性
- 研究观点差异中的中性机会
- 市场情绪极端化的中性应对策略
- 技术面和基本面的协同平衡分析
- 机构资金和零售资金的平衡动态

请以JSON格式回复，包含enhanced_balance_assessment, market_equilibrium_analysis, strategy_optimization, risk_reward_calibration, timing_recommendations, confidence_adjustment, strategic_insights字段。"""
