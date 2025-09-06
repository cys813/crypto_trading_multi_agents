"""
牛市研究员 - 专注寻找和确认牛市信号

基于原版研究架构，针对加密货币牛市特征优化
"""

from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

# 导入统一LLM服务
from ...services.ai_analysis_mixin import StandardAIAnalysisMixin
from ...services.llm_service import initialize_llm_service
from ...services.trading_data_service import TradingDataService

logger = logging.getLogger(__name__)

class BullResearcher(StandardAIAnalysisMixin):
    """加密货币牛市研究员"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化牛市研究员
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.bull_indicators = config.get("analysis_config", {}).get("bull_indicators", [])
        
        # 牛市指标权重
        self.indicator_weights = {
            "price_momentum": 0.20,
            "volume_breakout": 0.15,
            "market_structure": 0.15,
            "institutional_inflows": 0.20,
            "regulatory_catalysts": 0.10,
            "technical_breakouts": 0.10,
            "sentiment_shift": 0.10,
        }
        
        # 初始化AI分析混入类
        super().__init__()
        
        # 初始化新的交易数据服务
        self.trading_data_service = TradingDataService(config)
        
        # 初始化LLM服务（如果还未初始化）
        llm_service_config = config.get("llm_service_config")
        if llm_service_config:
            initialize_llm_service(llm_service_config)
            logger.info("BullResearcher: 统一LLM服务初始化完成")
    
    def trading_data_bull_signals(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        基于统一交易数据的牛市信号分析
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            牛市信号分析结果
        """
        try:
            # 使用新的交易数据服务获取数据
            trading_data = self.trading_data_service.get_trading_data(symbol, end_date)
            
            # 分析分层数据中的牛市信号
            analysis_result = self._analyze_layered_kline_for_bull_signals(symbol, trading_data, end_date)
            
            # 如果有AI分析能力，进行AI增强分析
            if self.is_ai_enabled():
                try:
                    ai_analysis = self._enhance_bull_analysis_with_ai(analysis_result, trading_data)
                    analysis_result.update(ai_analysis)
                except Exception as e:
                    logger.warning(f"AI增强分析失败: {e}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"牛市信号分析失败: {e}")
            return {
                "signal_strength": "弱",
                "action": "观望",
                "confidence": 0.3,
                "error": str(e)
            }
    
    def _analyze_layered_kline_for_bull_signals(self, symbol: str, layers: Dict[str, Any], end_date: str) -> Dict[str, Any]:
        """
        分析分层数据中的牛市信号
        
        Args:
            symbol: 交易对符号
            layers: 分层数据
            end_date: 截止日期
            
        Returns:
            分层牛市分析结果
        """
        try:
            base_currency = symbol.split('/')[0]
            
            # 分析各层牛市信号
            layer_signals = {}
            for timeframe, data in layers.items():
                if data:  # 只分析有数据的层
                    layer_signals[timeframe] = self._analyze_single_layer_bull_signals(data, timeframe)
            
            # 综合多层信号
            combined_signal = self._combine_layered_bull_signals(layer_signals)
            
            # 生成最终分析结果
            analysis_result = {
                "symbol": symbol,
                "analysis_date": end_date,
                "layer_signals": layer_signals,
                "combined_signal": combined_signal,
                "signal_strength": combined_signal.get("strength", "弱"),
                "action": self._generate_bull_action(combined_signal),
                "confidence": combined_signal.get("confidence", 0.5),
                "key_indicators": combined_signal.get("key_indicators", []),
                "market_conditions": combined_signal.get("market_conditions", "未知")
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"分层数据牛市信号分析失败: {e}")
            return self._generate_default_bull_analysis(symbol, end_date)
                
        except Exception as e:
            logger.error(f"分析K线数据牛市信号失败: {e}")
            return {"error": str(e)}
    
    def _analyze_single_layer_bull_signals(self, data: List[Dict[str, Any]], timeframe: str) -> Dict[str, Any]:
        """
        分析单层牛市信号
        """
        if len(data) < 10:
            return {"signals": [], "strength": "弱", "confidence": 0.3}
        
        # 简单的牛市信号检测逻辑
        signals = []
        
        # 价格动量信号
        if len(data) >= 2:
            price_change = (data[-1]['close'] - data[-2]['close']) / data[-2]['close']
            if price_change > 0.02:  # 2%以上涨幅
                signals.append({
                    "type": "price_momentum",
                    "strength": "强" if price_change > 0.05 else "中",
                    "description": f"价格{timeframe}框架上涨{price_change:.2%}"
                })
        
        # 成交量信号
        if len(data) >= 20:
            recent_volume = sum(d['volume'] for d in data[-5:])
            avg_volume = sum(d['volume'] for d in data[-20:-5]) / 15
            if recent_volume > avg_volume * 1.5:
                signals.append({
                    "type": "volume_breakout",
                    "strength": "强",
                    "description": f"{timeframe}框架成交量放大{(recent_volume/avg_volume-1):.1%}"
                })
        
        return {
            "signals": signals,
            "strength": "强" if len([s for s in signals if s['strength'] == '强']) >= 2 else "中" if signals else "弱",
            "confidence": min(0.9, 0.3 + len(signals) * 0.1)
        }
    
    def _combine_layered_bull_signals(self, layer_signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并多层牛市信号
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
            "market_conditions": "牛市迹象" if strength == "强" else "潜在牛市" if strength == "中" else "震荡"
        }
    
    def _generate_bull_action(self, combined_signal: Dict[str, Any]) -> str:
        """
        生成牛市操作建议
        """
        strength = combined_signal.get("strength", "弱")
        confidence = combined_signal.get("confidence", 0.5)
        
        if strength == "强" and confidence > 0.7:
            return "买入"
        elif strength == "中" and confidence > 0.6:
            return "考虑买入"
        else:
            return "观望"
    
    def _generate_default_bull_analysis(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        生成默认牛市分析结果
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
    
    def _enhance_bull_analysis_with_ai(self, analysis_result: Dict[str, Any], trading_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用AI增强牛市分析
        """
        try:
            # 构建AI分析prompt
            prompt = self._build_bull_analysis_prompt(analysis_result, trading_data)
            
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
            logger.error(f"AI增强牛市分析失败: {e}")
            return {"ai_enhanced": False, "ai_error": str(e)}
    
    def _build_bull_analysis_prompt(self, analysis_result: Dict[str, Any], trading_data: Dict[str, Any]) -> str:
        """
        构建牛市分析AI提示词
        """
        return f"""作为专业的加密货币牛市分析师，请分析以下市场数据：

当前分析结果：
{analysis_result}

分层数据：
{trading_data}

请提供：
1. 增强的牛市信号识别
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
            牛市研究分析结果
        """
        try:
            # 解析辩论材料
            technical_analysis = debate_material.get("technical_analysis", {})
            onchain_analysis = debate_material.get("onchain_analysis", {})
            sentiment_analysis = debate_material.get("sentiment_analysis", {})
            market_analysis = debate_material.get("market_analysis", {})
            defi_analysis = debate_material.get("defi_analysis", {})
            
            # 综合牛市信号分析
            bull_signals = self._analyze_comprehensive_bull_signals(
                technical_analysis, onchain_analysis, sentiment_analysis, 
                market_analysis, defi_analysis
            )
            
            # AI增强分析
            ai_enhancement = {}
            if self.is_ai_enabled():
                try:
                    ai_enhancement = self._enhance_bull_research_with_ai(
                        bull_signals, debate_material
                    )
                except Exception as e:
                    logger.warning(f"BullResearcher AI增强分析失败: {e}")
                    ai_enhancement = {"ai_error": str(e)}
            
            return {
                "bull_signals": bull_signals,
                "bull_recommendations": self._generate_bull_recommendations(bull_signals),
                "risk_assessment": self._assess_bull_risks(bull_signals, debate_material),
                "confidence": self._calculate_bull_confidence(bull_signals),
                "key_observations": self._generate_bull_observations(bull_signals),
                "ai_enhanced": self.is_ai_enabled(),
                "ai_analysis": ai_enhancement,
                "debate_material_summary": self._summarize_debate_material(debate_material)
            }
            
        except Exception as e:
            logger.error(f"BullResearcher analyze失败: {e}")
            return {"error": str(e)}

    def _analyze_comprehensive_bull_signals(self, technical_analysis: Dict[str, Any], 
                                           onchain_analysis: Dict[str, Any], 
                                           sentiment_analysis: Dict[str, Any],
                                           market_analysis: Dict[str, Any], 
                                           defi_analysis: Dict[str, Any]) -> List[str]:
        """
        分析综合看涨信号
        
        Args:
            technical_analysis: 技术分析结果
            onchain_analysis: 链上分析结果
            sentiment_analysis: 情绪分析结果
            market_analysis: 市场分析结果
            defi_analysis: DeFi分析结果
            
        Returns:
            看涨信号列表
        """
        try:
            bull_signals = []
            
            # 技术分析看涨信号
            if technical_analysis and "error" not in technical_analysis:
                tech_signals = self._extract_technical_bull_signals(technical_analysis)
                bull_signals.extend(tech_signals)
            
            # 链上分析看涨信号
            if onchain_analysis and "error" not in onchain_analysis:
                onchain_signals = self._extract_onchain_bull_signals(onchain_analysis)
                bull_signals.extend(onchain_signals)
            
            # 情绪分析看涨信号
            if sentiment_analysis and "error" not in sentiment_analysis:
                sentiment_signals = self._extract_sentiment_bull_signals(sentiment_analysis)
                bull_signals.extend(sentiment_signals)
            
            # 市场分析看涨信号
            if market_analysis and "error" not in market_analysis:
                market_signals = self._extract_market_bull_signals(market_analysis)
                bull_signals.extend(market_signals)
            
            # DeFi分析看涨信号
            if defi_analysis and "error" not in defi_analysis:
                defi_signals = self._extract_defi_bull_signals(defi_analysis)
                bull_signals.extend(defi_signals)
            
            return bull_signals
            
        except Exception as e:
            logger.error(f"分析综合看涨信号失败: {str(e)}")
            return ["信号分析出错"]
    
    def _extract_technical_bull_signals(self, technical_analysis: Dict[str, Any]) -> List[str]:
        """提取技术分析看涨信号"""
        signals = []
        
        # 检查技术指标
        if "indicators" in technical_analysis:
            indicators = technical_analysis["indicators"]
            if indicators.get("rsi", 50) < 30:
                signals.append("RSI超卖，可能反弹")
            if indicators.get("macd", {}).get("signal") == "bullish":
                signals.append("MACD金叉看涨信号")
            if indicators.get("ma_trend") == "upward":
                signals.append("均线趋势向上")
        
        # 检查价格动量
        if "momentum" in technical_analysis:
            momentum = technical_analysis["momentum"]
            if momentum.get("strength") == "strong":
                signals.append("价格动量强劲")
        
        return signals
    
    def _extract_onchain_bull_signals(self, onchain_analysis: Dict[str, Any]) -> List[str]:
        """提取链上分析看涨信号"""
        signals = []
        
        # 检查链上指标
        if "metrics" in onchain_analysis:
            metrics = onchain_analysis["metrics"]
            if metrics.get("active_addresses_growth") > 0.1:
                signals.append("活跃地址增长")
            if metrics.get("exchange_outflow") > 0:
                signals.append("交易所流出增加")
            if metrics.get("whale_accumulation") > 0:
                signals.append("巨鲸积累信号")
        
        return signals
    
    def _extract_sentiment_bull_signals(self, sentiment_analysis: Dict[str, Any]) -> List[str]:
        """提取情绪分析看涨信号"""
        signals = []
        
        # 检查情绪指标
        if "sentiment_score" in sentiment_analysis:
            sentiment = sentiment_analysis["sentiment_score"]
            if sentiment > 0.6:
                signals.append("市场情绪偏向看涨")
        
        # 检查社交媒体情绪
        if "social_sentiment" in sentiment_analysis:
            social = sentiment_analysis["social_sentiment"]
            if social.get("twitter_sentiment") > 0.5:
                signals.append("Twitter情绪看涨")
        
        return signals
    
    def _extract_market_bull_signals(self, market_analysis: Dict[str, Any]) -> List[str]:
        """提取市场分析看涨信号"""
        signals = []
        
        # 检查市场微观结构
        if "market_structure" in market_analysis:
            structure = market_analysis["market_structure"]
            if structure.get("order_book_pressure") == "buying_pressure":
                signals.append("订单簿买压较强")
            if structure.get("liquidity_quality") == "excellent":
                signals.append("市场流动性充足")
        
        # 检查价差
        if "spreads" in market_analysis:
            spreads = market_analysis["spreads"]
            if spreads.get("spread_level") == "tight":
                signals.append("买卖价差收窄")
        
        return signals
    
    def _extract_defi_bull_signals(self, defi_analysis: Dict[str, Any]) -> List[str]:
        """提取DeFi分析看涨信号"""
        signals = []
        
        # 检查DeFi指标
        if "defi_metrics" in defi_analysis:
            metrics = defi_analysis["defi_metrics"]
            if metrics.get("tvl_growth") > 0.1:
                signals.append("DeFi TVL增长")
            if metrics.get("yield_farming_activity") > 0.5:
                signals.append("收益耕作活跃")
        
        return signals
    
    def _generate_bull_recommendations(self, bull_signals: List[str]) -> List[str]:
        """生成看涨建议"""
        recommendations = []
        
        if len(bull_signals) >= 3:
            recommendations.append("强烈建议买入，多个维度显示看涨信号")
        elif len(bull_signals) >= 2:
            recommendations.append("建议考虑买入，看涨信号较强")
        elif len(bull_signals) >= 1:
            recommendations.append("可关注买入机会，看涨信号出现")
        else:
            recommendations.append("建议观望，看涨信号不足")
        
        return recommendations
    
    def _assess_bull_risks(self, bull_signals: List[str], debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """评估看涨风险"""
        try:
            risk_level = "low"
            risk_factors = []
            
            # 基于信号数量评估风险
            if len(bull_signals) < 2:
                risk_level = "medium"
                risk_factors.append("看涨信号不足，风险较高")
            
            # 检查市场整体风险
            market_condition = debate_material.get("market_condition", "normal")
            if market_condition == "volatile":
                risk_level = "high"
                risk_factors.append("市场波动性高")
            
            return {
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "risk_score": len(risk_factors) * 0.2
            }
            
        except Exception as e:
            logger.error(f"评估看涨风险失败: {str(e)}")
            return {"risk_level": "medium", "risk_factors": ["风险评估失败"], "risk_score": 0.5}
    
    def _calculate_bull_confidence(self, bull_signals: List[str]) -> float:
        """计算看涨置信度"""
        try:
            base_confidence = 0.3
            signal_bonus = min(0.5, len(bull_signals) * 0.1)
            
            confidence = base_confidence + signal_bonus
            return min(0.95, confidence)
            
        except Exception as e:
            logger.error(f"计算看涨置信度失败: {str(e)}")
            return 0.5
    
    def _generate_bull_observations(self, bull_signals: List[str]) -> List[str]:
        """生成看涨观察"""
        observations = []
        
        if bull_signals:
            observations.append(f"检测到{len(bull_signals)}个看涨信号")
            observations.extend(bull_signals[:3])  # 前3个信号
        else:
            observations.append("未检测到明显看涨信号")
        
        return observations
    
    def _enhance_bull_research_with_ai(self, bull_signals: List[str], debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI增强看涨研究"""
        try:
            # 构建AI分析提示词
            prompt = self._build_bull_research_ai_prompt(bull_signals, debate_material)
            
            # 调用AI分析
            ai_response = self.call_ai_analysis(prompt)
            
            # 解析AI响应
            ai_analysis = self.parse_ai_json_response(ai_response, {
                "enhanced_signals": [],
                "market_outlook": "moderate_bullish",
                "risk_factors": [],
                "opportunities": [],
                "confidence_adjustment": 0.0
            })
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"AI增强看涨研究失败: {str(e)}")
            return {"ai_error": str(e)}
    
    def _build_bull_research_ai_prompt(self, bull_signals: List[str], debate_material: Dict[str, Any]) -> str:
        """构建看涨研究AI提示词"""
        import json
        
        return f"""
作为专业的加密货币看涨研究员，请基于以下分析结果提供AI增强洞察：

## 当前看涨信号
{json.dumps(bull_signals, ensure_ascii=False, indent=2)}

## 辩论材料摘要
{json.dumps({k: v for k, v in debate_material.items() if isinstance(v, dict) and "error" not in v}, ensure_ascii=False, indent=2)}

## 请提供以下AI增强分析：

### 1. 增强的看涨信号识别
- 识别可能被遗漏的看涨信号
- 分析信号的强度和可靠性

### 2. 市场前景展望
- 短期、中期、长期市场展望
- 关键支撑位和阻力位分析

### 3. 潜在风险因素
- 识别可能的市场风险
- 评估风险对看涨观点的影响

### 4. 投资机会分析
- 识别具体的投资机会
- 建议的入场时机和策略

### 5. 置信度调整建议
- 基于AI分析的置信度调整
- 关键的不确定性因素

请以JSON格式返回分析结果，包含enhanced_signals, market_outlook, risk_factors, opportunities, confidence_adjustment字段。
"""
    
    def _summarize_debate_material(self, debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """总结辩论材料"""
        try:
            summary = {}
            
            for key, value in debate_material.items():
                if isinstance(value, dict) and "error" not in value:
                    summary[key] = {
                        "status": "available",
                        "key_metrics": list(value.keys())[:5]  # 前5个关键指标
                    }
                else:
                    summary[key] = {
                        "status": "error" if "error" in value else "unknown",
                        "message": value.get("error", "Unknown status") if isinstance(value, dict) else "Data unavailable"
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"总结辩论材料失败: {str(e)}")
            return {"error": f"Material summary failed: {str(e)}"}
