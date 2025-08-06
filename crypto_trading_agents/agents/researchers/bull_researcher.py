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