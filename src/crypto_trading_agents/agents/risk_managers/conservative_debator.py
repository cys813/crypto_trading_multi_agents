"""
保守辩论者 - 专注风险规避和资本保护

基于原版辩论架构，针对加密货币高风险特性优化
"""

from typing import Dict, Any, List
import logging

from src.crypto_trading_agents.services.ai_analysis_mixin import StandardAIAnalysisMixin

logger = logging.getLogger(__name__)

class ConservativeDebator(StandardAIAnalysisMixin):
    """加密货币保守辩论员"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化保守辩论者
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.risk_tolerance = config.get("risk_config", {}).get("conservative_tolerance", 0.2)
        
        # 初始化AI分析混入类
        super().__init__()
        
        # 初始化LLM服务（如果还未初始化）
        llm_service_config = config.get("llm_service_config")
        if llm_service_config:
            try:
                from src.crypto_trading_agents.services.unified_llm_service import initialize_llm_service
                initialize_llm_service(llm_service_config)
                logger.info("ConservativeDebator: 统一LLM服务初始化完成")
            except ImportError:
                logger.warning("ConservativeDebator: 无法导入LLM服务，将使用纯规则分析")
    
    def use_ai_enhanced_analysis(self) -> bool:
        """检查是否使用AI增强分析"""
        return self.is_ai_enabled()
    
    def _analyze_with_ai(self, prompt: str) -> Dict[str, Any]:
        """使用AI进行分析"""
        try:
            response = self.call_ai_analysis(prompt)
            return self.parse_ai_json_response(response, {})
        except Exception as e:
            logger.error(f"ConservativeDebator AI分析失败: {e}")
            return {"ai_error": str(e)}
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析市场数据，提供保守型观点
        
        Args:
            market_data: 市场数据
            
        Returns:
            分析结果
        """
        try:
            # 基础风险评估
            risk_analysis = self._assess_market_risk(market_data)
            
            # 构建保守型分析提示
            prompt = self._build_conservative_analysis_prompt(risk_analysis, market_data)
            
            # 使用AI增强分析（如果启用）
            if self.use_ai_enhanced_analysis():
                ai_analysis = self._analyze_with_ai(prompt)
                risk_analysis.update(ai_analysis)
            
            # 生成保守型策略建议
            strategy = self._generate_conservative_strategy(risk_analysis)
            
            return {
                "debator_type": "conservative",
                "risk_level": risk_analysis.get("overall_risk", "high"),
                "confidence": risk_analysis.get("confidence", 0.7),
                "key_observations": risk_analysis.get("key_observations", []),
                "conservative_strategies": strategy.get("recommendations", []),
                "risk_management": strategy.get("risk_management", {}),
                "expected_return": "low",
                "analysis_timestamp": risk_analysis.get("timestamp", ""),
                "market_assessment": risk_analysis.get("market_assessment", {})
            }
            
        except Exception as e:
            logger.error(f"Error in conservative analysis: {str(e)}")
            return {
                "debator_type": "conservative",
                "risk_level": "high",
                "confidence": 0.5,
                "key_observations": [f"Analysis error: {str(e)}"],
                "conservative_strategies": ["HOLD"],
                "risk_management": {"stop_loss": "tight"},
                "expected_return": "low",
                "analysis_timestamp": "",
                "market_assessment": {},
                "error": str(e)
            }
    
    def analyze_with_debate_material(self, debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用辩论材料进行分析
        
        Args:
            debate_material: 辩论材料，包含各种分析报告
            
        Returns:
            分析结果
        """
        try:
            # 提取关键信息
            market_report = debate_material.get("market_report", "")
            sentiment_report = debate_material.get("sentiment_report", "")
            news_report = debate_material.get("news_report", "")
            fundamentals_report = debate_material.get("fundamentals_report", "")
            investment_plan = debate_material.get("investment_plan", "")
            research_summary = debate_material.get("research_summary", {})
            bull_analysis = debate_material.get("bull_analysis", {})
            bear_analysis = debate_material.get("bear_analysis", {})
            technical_analysis = debate_material.get("technical_analysis", {})
            onchain_analysis = debate_material.get("onchain_analysis", {})
            sentiment_analysis = debate_material.get("sentiment_analysis", {})
            market_analysis = debate_material.get("market_analysis", {})
            defi_analysis = debate_material.get("defi_analysis", {})
            
            # 保守型风险评估
            risk_assessment = self._conservative_risk_assessment({
                "market_report": market_report,
                "sentiment_report": sentiment_report,
                "news_report": news_report,
                "fundamentals_report": fundamentals_report,
                "investment_plan": investment_plan,
                "research_summary": research_summary,
                "bull_analysis": bull_analysis,
                "bear_analysis": bear_analysis,
                "technical_analysis": technical_analysis,
                "onchain_analysis": onchain_analysis,
                "sentiment_analysis": sentiment_analysis,
                "market_analysis": market_analysis,
                "defi_analysis": defi_analysis
            })
            
            # 构建保守型辩论提示
            prompt = self._build_conservative_debate_prompt(risk_assessment, debate_material)
            
            # 使用AI增强分析（如果启用）
            if self.use_ai_enhanced_analysis():
                ai_analysis = self._analyze_with_ai(prompt)
                risk_assessment.update(ai_analysis)
            
            # 生成保守型辩论策略
            strategy = self._generate_conservative_debate_strategy(risk_assessment)
            
            return {
                "debator_type": "conservative",
                "risk_level": risk_assessment.get("overall_risk", "high"),
                "confidence": risk_assessment.get("confidence", 0.8),
                "key_observations": risk_assessment.get("key_observations", []),
                "conservative_strategies": strategy.get("recommendations", []),
                "risk_management": strategy.get("risk_management", {}),
                "expected_return": "low",
                "analysis_timestamp": risk_assessment.get("timestamp", ""),
                "debate_assessment": risk_assessment.get("debate_assessment", {}),
                "market_outlook": risk_assessment.get("market_outlook", "bearish")
            }
            
        except Exception as e:
            logger.error(f"Error in conservative debate analysis: {str(e)}")
            return {
                "debator_type": "conservative",
                "risk_level": "high",
                "confidence": 0.5,
                "key_observations": [f"Debate analysis error: {str(e)}"],
                "conservative_strategies": ["HOLD", "REDUCE_POSITION"],
                "risk_management": {"stop_loss": "very_tight"},
                "expected_return": "low",
                "analysis_timestamp": "",
                "debate_assessment": {},
                "market_outlook": "bearish",
                "error": str(e)
            }
    
    def _assess_market_risk(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估市场风险"""
        # 实现保守型风险评估逻辑
        return {
            "overall_risk": "high",
            "confidence": 0.7,
            "key_observations": ["Market volatility detected", "Risk factors present"],
            "timestamp": ""
        }
    
    def _build_conservative_analysis_prompt(self, risk_analysis: Dict[str, Any], 
                                           market_data: Dict[str, Any]) -> str:
        """构建保守型分析提示"""
        return f"""
        作为保守型辩论员，请分析以下市场数据并提供风险评估：
        
        风险分析: {risk_analysis}
        市场数据: {market_data}
        
        请重点关注：
        1. 下行风险和保护措施
        2. 资本保全策略
        3. 最坏情况分析
        4. 保守型投资建议
        """
    
    def _generate_conservative_strategy(self, risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成保守型策略"""
        return {
            "recommendations": ["HOLD", "REDUCE_EXPOSURE"],
            "risk_management": {
                "stop_loss": "tight",
                "position_size": "small"
            }
        }
    
    def _conservative_risk_assessment(self, debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """保守型风险评估"""
        return {
            "overall_risk": "high",
            "confidence": 0.8,
            "key_observations": ["Multiple risk factors identified", "Conservative approach recommended"],
            "timestamp": "",
            "debate_assessment": {
                "bull_bear_ratio": "bearish",
                "sentiment_alignment": "negative"
            },
            "market_outlook": "bearish"
        }
    
    def _build_conservative_debate_prompt(self, risk_assessment: Dict[str, Any], 
                                        debate_material: Dict[str, Any]) -> str:
        """构建保守型辩论提示"""
        return f"""
        作为保守型辩论员，请基于以下辩论材料提供风险评估：
        
        风险评估: {risk_assessment}
        辩论材料: {debate_material}
        
        请重点关注：
        1. 各个分析报告中的风险信号
        2. 研究员观点中的保守因素
        3. 市场情绪中的负面信号
        4. 技术分析中的支撑位和阻力位
        5. 链上数据中的风险指标
        """
    
    def _generate_conservative_debate_strategy(self, risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """生成保守型辩论策略"""
        return {
            "recommendations": ["HOLD", "REDUCE_POSITION", "INCREASE_CASH"],
            "risk_management": {
                "stop_loss": "very_tight",
                "position_size": "minimal",
                "hedging": "recommended"
            }
        }