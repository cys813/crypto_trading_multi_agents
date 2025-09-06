"""
熊市研究员 - 专注寻找和确认熊市信号

基于原版研究架构，针对加密货币熊市特征优化
"""

from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

# 导入统一LLM服务
from ...services.ai_analysis_mixin import StandardAIAnalysisMixin
from ...services.llm_service import initialize_llm_service
from ...services.trading_data_service import TradingDataService

logger = logging.getLogger(__name__)

class BearResearcher(StandardAIAnalysisMixin):
    """加密货币熊市研究员"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化熊市研究员
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.bear_indicators = config.get("analysis_config", {}).get("bear_indicators", [])
        
        # 熊市指标权重
        self.indicator_weights = {
            "price_decline": 0.20,            # 价格下跌
            "volume_distribution": 0.15,      # 成交量派发
            "market_structure_breakdown": 0.15, # 市场结构破坏
            "institutional_outflows": 0.20,   # 机构流出
            "regulatory_pressure": 0.10,      # 监管压力
            "technical_breakdowns": 0.10,     # 技术破坏
            "sentiment_deterioration": 0.10,  # 情绪恶化
        }
        
        # 初始化AI分析混入类
        super().__init__()
        
        # 初始化新的交易数据服务
        self.trading_data_service = TradingDataService(config)
        
        # 初始化LLM服务（如果还未初始化）
        llm_service_config = config.get("llm_service_config")
        if llm_service_config:
            initialize_llm_service(llm_service_config)
            logger.info("BearResearcher: 统一LLM服务初始化完成")
    
    def trading_data_bear_signals(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        基于统一交易数据的熊市信号分析
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            熊市信号分析结果
        """
        try:
            # 使用新的交易数据服务获取数据
            trading_data = self.trading_data_service.get_trading_data(symbol, end_date)
            
            # 分析分层数据中的熊市信号
            analysis_result = self._analyze_layered_kline_for_bear_signals(symbol, trading_data, end_date)
            
            # 如果有AI分析能力，进行AI增强分析
            if self.is_ai_enabled():
                try:
                    ai_analysis = self._enhance_bear_analysis_with_ai(analysis_result, trading_data)
                    analysis_result.update(ai_analysis)
                except Exception as e:
                    logger.warning(f"AI增强分析失败: {e}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"熊市信号分析失败: {e}")
            return {
                "signal_strength": "弱",
                "action": "观望",
                "confidence": 0.3,
                "error": str(e)
            }
    
    def _analyze_layered_kline_for_bear_signals(self, symbol: str, layers: Dict[str, Any], end_date: str) -> Dict[str, Any]:
        """
        分析分层数据中的熊市信号
        
        Args:
            symbol: 交易对符号
            layers: 分层数据
            end_date: 截止日期
            
        Returns:
            分层熊市分析结果
        """
        try:
            base_currency = symbol.split('/')[0]
            
            # 分析各层熊市信号
            layer_signals = {}
            for timeframe, data in layers.items():
                if data:  # 只分析有数据的层
                    layer_signals[timeframe] = self._analyze_single_layer_bear_signals(data, timeframe)
            
            # 综合多层信号
            combined_signal = self._combine_layered_bear_signals(layer_signals)
            
            # 生成最终分析结果
            analysis_result = {
                "symbol": symbol,
                "analysis_date": end_date,
                "layer_signals": layer_signals,
                "combined_signal": combined_signal,
                "signal_strength": combined_signal.get("strength", "弱"),
                "action": self._generate_bear_action(combined_signal),
                "confidence": combined_signal.get("confidence", 0.5),
                "key_indicators": combined_signal.get("key_indicators", []),
                "market_conditions": combined_signal.get("market_conditions", "未知")
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"分层数据熊市信号分析失败: {e}")
            return self._generate_default_bear_analysis(symbol, end_date)
    
    def _analyze_single_layer_bear_signals(self, data: List[Dict[str, Any]], timeframe: str) -> Dict[str, Any]:
        """
        分析单层熊市信号
        """
        if len(data) < 10:
            return {"signals": [], "strength": "弱", "confidence": 0.3}
        
        # 简单的熊市信号检测逻辑
        signals = []
        
        # 价格下跌信号
        if len(data) >= 2:
            price_change = (data[-1]['close'] - data[-2]['close']) / data[-2]['close']
            if price_change < -0.02:  # 2%以上跌幅
                signals.append({
                    "type": "price_decline",
                    "strength": "强" if price_change < -0.05 else "中",
                    "description": f"价格{timeframe}框架下跌{abs(price_change):.2%}"
                })
        
        # 成交量信号
        if len(data) >= 20:
            recent_volume = sum(d['volume'] for d in data[-5:])
            avg_volume = sum(d['volume'] for d in data[-20:-5]) / 15
            if recent_volume > avg_volume * 1.5:
                signals.append({
                    "type": "volume_distribution",
                    "strength": "强",
                    "description": f"{timeframe}框架成交量放大{(recent_volume/avg_volume-1):.1%}"
                })
        
        return {
            "signals": signals,
            "strength": "强" if len([s for s in signals if s['strength'] == '强']) >= 2 else "中" if signals else "弱",
            "confidence": min(0.9, 0.3 + len(signals) * 0.1)
        }
    
    def _combine_layered_bear_signals(self, layer_signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并多层熊市信号
        """
        if not layer_signals:
            return {"strength": "弱", "confidence": 0.3, "key_indicators": []}
        
        all_signals = []
        total_confidence = 0
        layer_count = 0
        
        for timeframe, signal_data in layer_signals.items():
            all_signals.extend(signal_data.get("signals", []))
            total_confidence += signal_data.get("confidence", 0.5)
            layer_count += 1
        
        avg_confidence = total_confidence / layer_count if layer_count > 0 else 0.5
        
        # 确定综合信号强度
        strong_signals = len([s for s in all_signals if s.get("strength") == "强"])
        if strong_signals >= 2:
            strength = "强"
        elif strong_signals >= 1 or len(all_signals) >= 2:
            strength = "中"
        else:
            strength = "弱"
        
        return {
            "strength": strength,
            "confidence": min(0.95, avg_confidence + (len(all_signals) * 0.05)),
            "key_indicators": [s['description'] for s in all_signals[:3]],
            "market_conditions": "熊市迹象" if strength == "强" else "潜在熊市" if strength == "中" else "震荡"
        }
    
    def _generate_bear_action(self, combined_signal: Dict[str, Any]) -> str:
        """
        生成熊市操作建议
        """
        strength = combined_signal.get("strength", "弱")
        confidence = combined_signal.get("confidence", 0.5)
        
        if strength == "强" and confidence > 0.7:
            return "卖出"
        elif strength == "中" and confidence > 0.6:
            return "考虑卖出"
        else:
            return "观望"
    
    def _generate_default_bear_analysis(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        生成默认熊市分析结果
        """
        return {
            "symbol": symbol,
            "analysis_date": end_date,
            "signal_strength": "弱",
            "action": "观望",
            "confidence": 0.3,
            "key_indicators": ["数据不足"],
            "market_conditions": "未知"
        }
    
    def _enhance_bear_analysis_with_ai(self, analysis_result: Dict[str, Any], trading_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用AI增强熊市分析
        """
        try:
            # 构建AI分析prompt
            prompt = self._build_bear_analysis_prompt(analysis_result, trading_data)
            
            # 调用AI分析
            ai_response = self.call_ai_analysis(prompt)
            
            # 解析AI响应
            ai_analysis = self.parse_ai_json_response(ai_response, {
                "enhanced_signals": [],
                "market_outlook": "中性",
                "risk_factors": [],
                "opportunities": [],
                "confidence_adjustment": 0.0
            })
            
            return {
                "ai_enhanced": True,
                "ai_signals": ai_analysis.get("enhanced_signals", []),
                "ai_market_outlook": ai_analysis.get("market_outlook", "中性"),
                "ai_risk_factors": ai_analysis.get("risk_factors", []),
                "ai_opportunities": ai_analysis.get("opportunities", [])
            }
            
        except Exception as e:
            logger.error(f"AI增强熊市分析失败: {e}")
            return {"ai_enhanced": False, "ai_error": str(e)}
    
    def _build_bear_analysis_prompt(self, analysis_result: Dict[str, Any], trading_data: Dict[str, Any]) -> str:
        """
        构建熊市分析AI提示词
        """
        return f"""作为专业的加密货币熊市分析师，请分析以下市场数据：

当前分析结果：
{analysis_result}

分层数据：
{trading_data}

请提供：
1. 增强的熊市信号识别
2. 市场前景展望
3. 潜在风险因素
4. 投资机会分析
5. 置信度调整建议

请以JSON格式回复，包含enhanced_signals, market_outlook, risk_factors, opportunities, confidence_adjustment字段。
"""

    def analyze(self, debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """
        接收辩论材料进行分析
        
        Args:
            debate_material: 包含所有分析师分析结果的辩论材料
            
        Returns:
            熊市研究分析结果
        """
        try:
            # 解析辩论材料
            technical_analysis = debate_material.get("technical_analysis", {})
            onchain_analysis = debate_material.get("onchain_analysis", {})
            sentiment_analysis = debate_material.get("sentiment_analysis", {})
            market_analysis = debate_material.get("market_analysis", {})
            defi_analysis = debate_material.get("defi_analysis", {})
            
            # 综合熊市信号分析
            bear_signals = self._analyze_comprehensive_bear_signals(
                technical_analysis, onchain_analysis, sentiment_analysis, 
                market_analysis, defi_analysis
            )
            
            # AI增强分析
            ai_enhancement = {}
            if self.is_ai_enabled():
                try:
                    ai_enhancement = self._enhance_bear_research_with_ai(
                        bear_signals, debate_material
                    )
                except Exception as e:
                    logger.warning(f"BearResearcher AI增强分析失败: {e}")
                    ai_enhancement = {"ai_error": str(e)}
            
            return {
                "bear_signals": bear_signals,
                "bear_recommendations": self._generate_bear_recommendations(bear_signals),
                "risk_assessment": self._assess_bear_risks(bear_signals, debate_material),
                "confidence": self._calculate_bear_confidence(bear_signals),
                "key_observations": self._generate_bear_observations(bear_signals),
                "ai_enhanced": self.is_ai_enabled(),
                "ai_analysis": ai_enhancement,
                "debate_material_summary": self._summarize_debate_material(debate_material)
            }
            
        except Exception as e:
            logger.error(f"BearResearcher analyze失败: {e}")
            return {"error": str(e)}
    
    def _analyze_comprehensive_bear_signals(self, technical_analysis: Dict[str, Any],
                                          onchain_analysis: Dict[str, Any],
                                          sentiment_analysis: Dict[str, Any],
                                          market_analysis: Dict[str, Any],
                                          defi_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        综合分析所有分析师数据中的熊市信号
        
        Args:
            technical_analysis: 技术分析结果
            onchain_analysis: 链上分析结果
            sentiment_analysis: 情绪分析结果
            market_analysis: 市场分析结果
            defi_analysis: DeFi分析结果
            
        Returns:
            综合熊市信号分析
        """
        bear_signals = {
            "technical_bear_signals": self._extract_technical_bear_signals(technical_analysis),
            "onchain_bear_signals": self._extract_onchain_bear_signals(onchain_analysis),
            "sentiment_bear_signals": self._extract_sentiment_bear_signals(sentiment_analysis),
            "market_bear_signals": self._extract_market_bear_signals(market_analysis),
            "defi_bear_signals": self._extract_defi_bear_signals(defi_analysis),
            "signal_strength": "弱",
            "signal_count": 0,
            "strong_signals": [],
            "medium_signals": [],
            "weak_signals": []
        }
        
        # 统计信号强度
        all_signals = []
        all_signals.extend(bear_signals["technical_bear_signals"])
        all_signals.extend(bear_signals["onchain_bear_signals"])
        all_signals.extend(bear_signals["sentiment_bear_signals"])
        all_signals.extend(bear_signals["market_bear_signals"])
        all_signals.extend(bear_signals["defi_bear_signals"])
        
        # 分类信号
        for signal in all_signals:
            if signal["strength"] == "强":
                bear_signals["strong_signals"].append(signal)
            elif signal["strength"] == "中":
                bear_signals["medium_signals"].append(signal)
            else:
                bear_signals["weak_signals"].append(signal)
        
        bear_signals["signal_count"] = len(all_signals)
        
        # 确定整体信号强度
        strong_count = len(bear_signals["strong_signals"])
        medium_count = len(bear_signals["medium_signals"])
        
        if strong_count >= 3:
            bear_signals["signal_strength"] = "强"
        elif strong_count >= 1 or medium_count >= 3:
            bear_signals["signal_strength"] = "中"
        else:
            bear_signals["signal_strength"] = "弱"
        
        return bear_signals
    
    def _extract_technical_bear_signals(self, technical_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从技术分析中提取熊市信号"""
        signals = []
        
        indicators = technical_analysis.get("indicators", {})
        signals_data = technical_analysis.get("signals", {})
        
        # 价格下跌信号
        if indicators.get("rsi", 50) < 30:
            signals.append({
                "type": "technical",
                "indicator": "RSI",
                "value": indicators["rsi"],
                "strength": "强" if indicators["rsi"] < 20 else "中",
                "description": f"RSI处于{indicators['rsi']}，显示超卖状态"
            })
        
        # 成交量派发信号
        if signals_data.get("volume_distribution", False):
            signals.append({
                "type": "technical",
                "indicator": "成交量派发",
                "value": True,
                "strength": "强",
                "description": "成交量显示派发模式，确认下跌趋势"
            })
        
        # 移动平均线信号
        if indicators.get("ma_trend", "") == "bearish":
            signals.append({
                "type": "technical",
                "indicator": "移动平均线",
                "value": indicators["ma_trend"],
                "strength": "中",
                "description": "移动平均线呈空头排列"
            })
        
        # 支撑位突破信号
        if signals_data.get("support_break", False):
            signals.append({
                "type": "technical",
                "indicator": "支撑位突破",
                "value": True,
                "strength": "强",
                "description": "关键技术支撑位被突破"
            })
        
        return signals
    
    def _extract_onchain_bear_signals(self, onchain_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从链上分析中提取熊市信号"""
        signals = []
        
        metrics = onchain_analysis.get("metrics", {})
        
        # 活跃地址下降信号
        if metrics.get("active_addresses_decline", 0) > 10:
            signals.append({
                "type": "onchain",
                "indicator": "活跃地址下降",
                "value": f"{metrics['active_addresses_decline']}%",
                "strength": "中" if metrics['active_addresses_decline'] > 20 else "弱",
                "description": f"活跃地址下降{metrics['active_addresses_decline']}%，显示网络活跃度降低"
            })
        
        # 大户抛售信号
        if metrics.get("whale_distribution", False):
            signals.append({
                "type": "onchain",
                "indicator": "鲸鱼抛售",
                "value": True,
                "strength": "强",
                "description": "检测到鲸鱼地址持续抛售，显示机构看空"
            })
        
        # 交易量下降信号
        if metrics.get("transaction_volume_decline", 0) > 15:
            signals.append({
                "type": "onchain",
                "indicator": "交易量下降",
                "value": f"{metrics['transaction_volume_decline']}%",
                "strength": "中",
                "description": f"链上交易量下降{metrics['transaction_volume_decline']}%"
            })
        
        return signals
    
    def _extract_sentiment_bear_signals(self, sentiment_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从情绪分析中提取熊市信号"""
        signals = []
        
        sentiment_score = sentiment_analysis.get("sentiment_score", 0.5)
        social_metrics = sentiment_analysis.get("social_metrics", {})
        
        # 整体情绪信号
        if sentiment_score < 0.4:
            signals.append({
                "type": "sentiment",
                "indicator": "整体情绪",
                "value": sentiment_score,
                "strength": "强" if sentiment_score < 0.2 else "中",
                "description": f"市场情绪悲观，评分{sentiment_score:.2f}"
            })
        
        # 社交媒体活跃度下降信号
        if social_metrics.get("social_volume_decline", 0) > 20:
            signals.append({
                "type": "sentiment",
                "indicator": "社交活跃度",
                "value": f"{social_metrics['social_volume_decline']}%",
                "strength": "中",
                "description": f"社交媒体讨论度下降{social_metrics['social_volume_decline']}%"
            })
        
        # 恐惧贪婪指数信号
        fear_greed = sentiment_analysis.get("fear_greed_index", 50)
        if fear_greed < 40:
            signals.append({
                "type": "sentiment",
                "indicator": "恐惧贪婪指数",
                "value": fear_greed,
                "strength": "中" if fear_greed < 25 else "弱",
                "description": f"恐惧贪婪指数{fear_greed}，显示恐惧情绪"
            })
        
        return signals
    
    def _extract_market_bear_signals(self, market_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从市场分析中提取熊市信号"""
        signals = []
        
        market_metrics = market_analysis.get("market_metrics", {})
        liquidity_metrics = market_analysis.get("liquidity_metrics", {})
        
        # 市场深度不足信号
        if market_metrics.get("market_depth_poor", False):
            signals.append({
                "type": "market",
                "indicator": "市场深度",
                "value": True,
                "strength": "中",
                "description": "市场深度不足，易受大额交易影响"
            })
        
        # 流动性下降信号
        if liquidity_metrics.get("liquidity_score", 0.5) < 0.3:
            signals.append({
                "type": "market",
                "indicator": "流动性",
                "value": liquidity_metrics["liquidity_score"],
                "strength": "中",
                "description": f"流动性评分{liquidity_metrics['liquidity_score']:.2f}，显示流动性不足"
            })
        
        # 做市商活动减少信号
        if market_metrics.get("maker_activity_low", False):
            signals.append({
                "type": "market",
                "indicator": "做市商活动",
                "value": True,
                "strength": "中",
                "description": "做市商活跃度降低，流动性恶化"
            })
        
        return signals
    
    def _extract_defi_bear_signals(self, defi_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从DeFi分析中提取熊市信号"""
        signals = []
        
        defi_metrics = defi_analysis.get("defi_metrics", {})
        protocol_metrics = defi_analysis.get("protocol_metrics", {})
        
        # TVL下降信号
        if defi_metrics.get("tvl_decline", 0) > 10:
            signals.append({
                "type": "defi",
                "indicator": "TVL下降",
                "value": f"{defi_metrics['tvl_decline']}%",
                "strength": "中" if defi_metrics['tvl_decline'] > 20 else "弱",
                "description": f"DeFi总锁仓量下降{defi_metrics['tvl_decline']}%"
            })
        
        # 协议风险信号
        if protocol_metrics.get("protocol_risk_high", False):
            signals.append({
                "type": "defi",
                "indicator": "协议风险",
                "value": True,
                "strength": "强",
                "description": "DeFi协议风险升高，需警惕"
            })
        
        # 收益率下降信号
        if defi_metrics.get("yield_unattractive", False):
            signals.append({
                "type": "defi",
                "indicator": "收益率",
                "value": True,
                "strength": "中",
                "description": "DeFi收益率缺乏吸引力"
            })
        
        return signals
    
    def _generate_bear_recommendations(self, bear_signals: Dict[str, Any]) -> List[str]:
        """生成熊市投资建议"""
        recommendations = []
        
        signal_strength = bear_signals.get("signal_strength", "弱")
        strong_count = len(bear_signals.get("strong_signals", []))
        
        if signal_strength == "强" and strong_count >= 3:
            recommendations.append("强烈建议减仓或清仓，多个维度显示强烈熊市信号")
            recommendations.append("建议将资金转向稳定币或其他避险资产")
            recommendations.append("避免在此时抄底，等待更明确的底部信号")
        elif signal_strength == "中":
            recommendations.append("建议谨慎减仓，市场显示中等强度熊市信号")
            recommendations.append("降低仓位至总资金的30-50%")
            recommendations.append("设置更严格的止损，建议3-5%")
        else:
            recommendations.append("建议谨慎观望，熊市信号不足")
            recommendations.append("保持现有仓位，但设置更严格的止损")
            recommendations.append("密切监控市场变化，准备应对可能的风险")
        
        # 基于具体信号的建议
        if any(s["type"] == "technical" for s in bear_signals.get("strong_signals", [])):
            recommendations.append("技术面显示弱势，优先考虑技术面驱动的减仓")
        
        if any(s["type"] == "onchain" for s in bear_signals.get("strong_signals", [])):
            recommendations.append("链上数据消极，基本面支撑薄弱")
        
        if any(s["type"] == "sentiment" for s in bear_signals.get("strong_signals", [])):
            recommendations.append("市场情绪悲观，需警惕恐慌性抛售")
        
        return recommendations
    
    def _assess_bear_risks(self, bear_signals: Dict[str, Any], debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """评估熊市风险"""
        risk_factors = []
        
        # 信号一致性风险
        signal_types = ["technical", "onchain", "sentiment", "market", "defi"]
        active_signals = []
        
        for signal_type in signal_types:
            type_signals = bear_signals.get(f"{signal_type}_bear_signals", [])
            if any(s["strength"] in ["强", "中"] for s in type_signals):
                active_signals.append(signal_type)
        
        if len(active_signals) >= 4:
            risk_factors.append({
                "type": "signal_consistency",
                "level": "high",
                "description": f"{len(active_signals)}个维度显示熊市信号，系统性风险较高"
            })
        
        # 情绪恐慌风险
        sentiment_signals = bear_signals.get("sentiment_bear_signals", [])
        if any(s["strength"] == "强" for s in sentiment_signals):
            risk_factors.append({
                "type": "sentiment_panic",
                "level": "high",
                "description": "情绪信号过强，需警惕恐慌性抛售风险"
            })
        
        # 技术面崩溃风险
        technical_signals = bear_signals.get("technical_bear_signals", [])
        strong_technical = [s for s in technical_signals if s["strength"] == "强"]
        if len(strong_technical) >= 2:
            risk_factors.append({
                "type": "technical_collapse",
                "level": "high",
                "description": "技术面多个强信号，可能出现大幅下跌"
            })
        
        return {
            "risk_factors": risk_factors,
            "overall_risk_level": "low" if not risk_factors else "high" if any(r["level"] == "high" for r in risk_factors) else "medium",
            "risk_mitigation": self._generate_bear_risk_mitigation(risk_factors)
        }
    
    def _generate_bear_risk_mitigation(self, risk_factors: List[Dict[str, Any]]) -> List[str]:
        """生成熊市风险缓解建议"""
        mitigation = []
        
        for factor in risk_factors:
            if factor["type"] == "signal_consistency":
                mitigation.append("立即大幅减仓，降低风险敞口")
                mitigation.append("转向稳定币或其他避险资产")
            elif factor["type"] == "sentiment_panic":
                mitigation.append("避免恐慌性抛售，理性减仓")
                mitigation.append("等待情绪稳定后再做决策")
            elif factor["type"] == "technical_collapse":
                mitigation.append("严格止损，防止更大损失")
                mitigation.append("暂时远离市场，等待技术修复")
        
        # 通用风险缓解措施
        mitigation.append("保持充足的现金储备")
        mitigation.append("设置3-5%的严格止损")
        mitigation.append("定期重新评估市场状况")
        
        return mitigation
    
    def _calculate_bear_confidence(self, bear_signals: Dict[str, Any]) -> float:
        """计算熊市分析置信度"""
        base_confidence = 0.5
        
        # 信号强度加分
        signal_strength = bear_signals.get("signal_strength", "弱")
        if signal_strength == "强":
            base_confidence += 0.3
        elif signal_strength == "中":
            base_confidence += 0.2
        
        # 信号数量加分
        signal_count = bear_signals.get("signal_count", 0)
        if signal_count > 10:
            base_confidence += 0.2
        elif signal_count > 5:
            base_confidence += 0.1
        
        # 强信号数量加分
        strong_count = len(bear_signals.get("strong_signals", []))
        if strong_count > 3:
            base_confidence += 0.2
        elif strong_count > 1:
            base_confidence += 0.1
        
        return min(base_confidence, 0.95)
    
    def _generate_bear_observations(self, bear_signals: Dict[str, Any]) -> List[str]:
        """生成熊市关键观察"""
        observations = []
        
        signal_strength = bear_signals.get("signal_strength", "弱")
        observations.append(f"综合熊市信号强度: {signal_strength}")
        
        signal_count = bear_signals.get("signal_count", 0)
        observations.append(f"检测到熊市信号数量: {signal_count}")
        
        strong_count = len(bear_signals.get("strong_signals", []))
        observations.append(f"强信号数量: {strong_count}")
        
        # 各维度信号分布
        for signal_type in ["technical", "onchain", "sentiment", "market", "defi"]:
            type_signals = bear_signals.get(f"{signal_type}_bear_signals", [])
            strong_type_signals = [s for s in type_signals if s["strength"] == "强"]
            if strong_type_signals:
                observations.append(f"{signal_type}维度有{len(strong_type_signals)}个强信号")
        
        return observations
    
    def _summarize_debate_material(self, debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """总结辩论材料"""
        summary = {
            "available_analyses": [],
            "analysis_quality": {},
            "data_completeness": "high"
        }
        
        analysis_types = ["technical_analysis", "onchain_analysis", "sentiment_analysis", "market_analysis", "defi_analysis"]
        
        for analysis_type in analysis_types:
            if analysis_type in debate_material and debate_material[analysis_type]:
                summary["available_analyses"].append(analysis_type.replace("_analysis", ""))
                
                # 评估分析质量
                analysis = debate_material[analysis_type]
                if analysis.get("confidence", 0) > 0.7:
                    summary["analysis_quality"][analysis_type.replace("_analysis", "")] = "high"
                elif analysis.get("confidence", 0) > 0.5:
                    summary["analysis_quality"][analysis_type.replace("_analysis", "")] = "medium"
                else:
                    summary["analysis_quality"][analysis_type.replace("_analysis", "")] = "low"
            else:
                summary["data_completeness"] = "medium"
        
        return summary
    
    def _enhance_bear_research_with_ai(self, bear_signals: Dict[str, Any], debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI增强熊市研究"""
        try:
            # 构建AI分析prompt
            prompt = self._build_enhanced_bear_research_prompt(bear_signals, debate_material)
            
            # 调用AI分析
            ai_response = self.call_ai_analysis(prompt)
            
            # 解析AI响应
            ai_analysis = self.parse_ai_json_response(ai_response, {
                "enhanced_signal_interpretation": {},
                "market_timing_analysis": {},
                "risk_factor_enhancement": [],
                "protection_strategy": [],
                "confidence_adjustment": 0.0,
                "strategic_recommendations": []
            })
            
            return {
                "ai_enhanced": True,
                "ai_signal_interpretation": ai_analysis.get("enhanced_signal_interpretation", {}),
                "ai_timing_analysis": ai_analysis.get("market_timing_analysis", {}),
                "ai_risk_enhancement": ai_analysis.get("risk_factor_enhancement", []),
                "ai_protection_strategy": ai_analysis.get("protection_strategy", []),
                "ai_confidence_adjustment": ai_analysis.get("confidence_adjustment", 0.0),
                "ai_strategic_recommendations": ai_analysis.get("strategic_recommendations", [])
            }
            
        except Exception as e:
            logger.error(f"AI增强熊市研究失败: {e}")
            return {"ai_enhanced": False, "ai_error": str(e)}
    
    def _build_enhanced_bear_research_prompt(self, bear_signals: Dict[str, Any], debate_material: Dict[str, Any]) -> str:
        """构建增强熊市研究AI提示词"""
        return f"""作为专业的加密货币熊市研究专家，请基于以下综合分析结果提供深度AI增强分析：

当前熊市信号分析结果：
{bear_signals}

辩论材料包含的分析：
{list(debate_material.keys())}

请从多维度综合角度提供深度分析：

1. 增强的信号解读 - 基于多维度熊市信号的深层含义和市场影响
2. 市场时机分析 - 识别最佳的减仓和避险时机
3. 风险因素增强 - 识别传统分析可能遗漏的系统性风险
4. 保护策略 - 提供具体的资产保护和风险规避策略
5. 置信度调整 - 基于综合分析调整整体置信度
6. 战略建议 - 提供具体的投资策略和操作建议

请特别关注：
- 多维度熊市信号的一致性和严重程度
- 市场下行风险的传播路径和影响范围
- 不同时间周期的风险信号差异
- 机构资金流出和市场恐慌的相互作用
- 技术面和基本面的协同恶化分析

请以JSON格式回复，包含enhanced_signal_interpretation, market_timing_analysis, risk_factor_enhancement, protection_strategy, confidence_adjustment, strategic_recommendations字段。"""
