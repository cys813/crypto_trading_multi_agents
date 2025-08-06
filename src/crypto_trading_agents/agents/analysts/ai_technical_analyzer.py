"""
AI增强技术分析模块
结合传统技术指标和AI大模型分析，提供更智能的技术分析结果
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np

# 导入统一LLM服务
from ...services.ai_analysis_mixin import StandardAIAnalysisMixin
from ...services.llm_service import initialize_llm_service

logger = logging.getLogger(__name__)

class AITechnicalAnalyzer(StandardAIAnalysisMixin):
    """AI增强技术分析器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI技术分析器
        
        Args:
            config: 配置字典，包含LLM设置
        """
        self.config = config
        
        # AI分析配置
        self.model_name = config.get("llm_service_config", {}).get("providers", {}).get("dashscope", {}).get("model", "qwen-plus")
        
        # 初始化AI分析混入类
        super().__init__()
        
        # 初始化LLM服务（如果还未初始化）
        llm_service_config = config.get("llm_service_config")
        if llm_service_config:
            initialize_llm_service(llm_service_config)
            logger.info("AITechnicalAnalyzer: 统一LLM服务初始化完成")
    
    def analyze_with_ai(self, traditional_analysis: Dict[str, Any], 
                       raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用AI分析传统技术指标和原始数据
        
        Args:
            traditional_analysis: 传统技术分析结果
            raw_data: 原始市场数据
            
        Returns:
            AI增强的分析结果
        """
        if not self.is_ai_enabled():
            logger.warning("AI分析未启用，返回传统分析结果")
            return {"ai_analysis": "AI分析未启用", "enhanced_signals": traditional_analysis}
        
        try:
            # 使用统一的AI增强分析流程
            return self.analyze_with_ai_enhancement(raw_data, lambda data: traditional_analysis)
            
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return {
                "ai_analysis": f"AI分析失败: {str(e)}",
                "enhanced_signals": traditional_analysis,
                "confidence": traditional_analysis.get("confidence", 0.5)
            }

    def _analyze_with_ai(self, traditional_analysis: Dict[str, Any], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用AI进行技术分析增强
        
        Args:
            traditional_analysis: 传统分析结果
            raw_data: 原始数据
            
        Returns:
            AI分析结果
        """
        try:
            # 构建技术分析prompt
            prompt = self._build_technical_analysis_prompt(traditional_analysis, raw_data)
            
            # 调用统一LLM服务
            ai_response = self.call_ai_analysis(prompt)
            
            # 解析AI响应
            ai_analysis = self.parse_ai_json_response(ai_response, {
                "trend_analysis": {"direction": "未知", "strength": 0.5, "confidence": 0.5},
                "support_resistance": {"support_levels": [], "resistance_levels": []},
                "pattern_recognition": {"patterns": [], "reliability": 0.5},
                "momentum_analysis": {"momentum_direction": "中性", "strength": 0.5},
                "volume_analysis": {"volume_trend": "正常", "significance": 0.5},
                "entry_exit_signals": {"entry_signals": [], "exit_signals": []},
                "risk_assessment": {"risk_level": "中", "stop_loss": 0},
                "confidence_level": 0.5,
                "key_insights": ["AI分析不可用"]
            })
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"AITechnicalAnalyzer: AI分析失败: {str(e)}")
            raise

    def _build_technical_analysis_prompt(self, traditional_analysis: Dict[str, Any], raw_data: Dict[str, Any]) -> str:
        """构建技术分析AI提示词"""
        
        # 使用标准化prompt构建方法
        analysis_dimensions = [
            "趋势分析 - 分析价格趋势方向、强度和持续性，识别趋势转折点",
            "支撑阻力分析 - 识别关键支撑位和阻力位，评估突破概率",
            "技术形态识别 - 识别经典技术形态，评估形态完成度和可靠性",
            "动量分析 - 分析价格动量变化，识别超买超卖信号",
            "成交量分析 - 分析成交量与价格的关系，确认价格走势",
            "进出场信号 - 基于技术指标生成具体的买卖信号",
            "风险评估 - 评估技术面风险，设定止损位和目标位"
        ]
        
        output_fields = [
            "trend_analysis",
            "support_resistance", 
            "pattern_recognition",
            "momentum_analysis",
            "volume_analysis",
            "entry_exit_signals",
            "risk_assessment",
            "confidence_level",
            "key_insights"
        ]
        
        # 如果有分层数据，添加分层分析维度
        if "layered_data" in raw_data:
            analysis_dimensions.extend([
                "多时间框架分析 - 分析不同时间框架的趋势一致性",
                "分层指标分析 - 综合分析各层技术指标的信号",
                "跨层验证 - 通过多层数据验证分析结果的可靠性"
            ])
            output_fields.extend([
                "multi_timeframe_analysis",
                "layered_indicator_analysis",
                "cross_layer_validation"
            ])
        
        prompt = self._build_standard_analysis_prompt(
            "专业技术分析师",
            traditional_analysis,
            raw_data,
            analysis_dimensions,
            output_fields
        )
        
        # 添加分层数据的特殊指导
        if "layered_data" in raw_data:
            layered_data = raw_data["layered_data"]
            prompt += f"""
            
分层数据分析要求：
- 数据包含 {len(layered_data.get('layers', {}))} 个时间层，请进行多时间框架分析
- 各层数据时间框架：{[layer.get('timeframe', '') for layer in layered_data.get('layers', {}).values()]}
- 请特别关注不同时间框架之间的趋势一致性
- 利用多层数据验证分析结果的可靠性
- 基于分层技术指标提供更准确的市场判断
"""
        
        return prompt

    def _combine_analyses(self, traditional_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        组合传统分析和AI分析结果
        
        Args:
            traditional_analysis: 传统分析结果
            ai_analysis: AI分析结果
            
        Returns:
            组合后的分析结果
        """
        try:
            # 使用标准化组合方法
            enhanced_analysis = self._combine_standard_analyses(
                traditional_analysis, 
                ai_analysis, 
                confidence_weight_ai=0.7  # AI在技术分析中的权重较高
            )
            
            # 添加技术分析特定的增强字段
            enhanced_analysis.update({
                "ai_trend_analysis": ai_analysis.get("trend_analysis", {}),
                "ai_support_resistance": ai_analysis.get("support_resistance", {}),
                "ai_pattern_recognition": ai_analysis.get("pattern_recognition", {}),
                "ai_momentum_analysis": ai_analysis.get("momentum_analysis", {}),
                "ai_volume_analysis": ai_analysis.get("volume_analysis", {}),
                "ai_entry_exit_signals": ai_analysis.get("entry_exit_signals", {}),
                "ai_risk_assessment": ai_analysis.get("risk_assessment", {}),
                "ai_key_insights": ai_analysis.get("key_insights", []),
                "combined_insights": {
                    "traditional_signals": traditional_analysis.get("technical_signals", {}),
                    "ai_signals": ai_analysis.get("entry_exit_signals", {}),
                    "final_recommendation": self._generate_final_recommendation(traditional_analysis, ai_analysis)
                }
            })
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"AITechnicalAnalyzer: 分析结果组合失败: {str(e)}")
            # 发生错误时返回传统分析结果
            fallback_analysis = traditional_analysis.copy()
            fallback_analysis["ai_enhanced"] = False
            fallback_analysis["combine_error"] = str(e)
            return fallback_analysis

    def _generate_final_recommendation(self, traditional_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终技术分析建议"""
        try:
            traditional_confidence = traditional_analysis.get("confidence", 0.5)
            ai_confidence = ai_analysis.get("confidence_level", 0.5)
            
            # 综合信号强度
            traditional_signals = traditional_analysis.get("technical_signals", {})
            ai_signals = ai_analysis.get("entry_exit_signals", {})
            
            # 计算综合推荐
            combined_confidence = (traditional_confidence * 0.3 + ai_confidence * 0.7)
            
            if combined_confidence > 0.7:
                recommendation_strength = "强"
            elif combined_confidence > 0.5:
                recommendation_strength = "中"
            else:
                recommendation_strength = "弱"
            
            return {
                "overall_signal": "买入" if combined_confidence > 0.6 else "观望" if combined_confidence > 0.4 else "卖出",
                "signal_strength": recommendation_strength,
                "confidence": combined_confidence,
                "key_factors": ai_analysis.get("key_insights", [])[:3]
            }
            
        except Exception as e:
            logger.error(f"生成最终建议失败: {str(e)}")
            return {
                "overall_signal": "观望",
                "signal_strength": "弱", 
                "confidence": 0.5,
                "key_factors": ["建议生成失败"]
            }

    def _format_traditional_analysis_summary(self, traditional_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """格式化传统分析结果摘要（重写父类方法）"""
        return {
            "技术信号": traditional_analysis.get("technical_signals", {}),
            "趋势强度": traditional_analysis.get("trend_strength", {}),
            "支撑阻力": traditional_analysis.get("support_resistance", {}),
            "波动率": traditional_analysis.get("volatility", {}),
            "风险评估": traditional_analysis.get("risk_assessment", {}),
            "置信度": traditional_analysis.get("confidence", 0)
        }

    def _format_raw_data_summary(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化原始数据摘要（重写父类方法）"""
        summary = {
            "技术指标": raw_data.get("indicators", {}),
            "市场结构": raw_data.get("market_structure", {}),
            "成交量": raw_data.get("volume_profile", {}),
            "价格数据": raw_data.get("ohlcv", {}),
        }
        
        # 添加分层数据信息
        if "layered_data" in raw_data:
            layered_data = raw_data["layered_data"]
            summary["分层数据"] = {
                "层数": len(layered_data.get("layers", {})),
                "数据质量": layered_data.get("summary", {}).get("data_quality", {}),
                "总K线数": layered_data.get("summary", {}).get("total_candles", 0),
                "最后更新": layered_data.get("summary", {}).get("last_updated", "")
            }
            
            # 添加各层详细信息
            layers_summary = {}
            for layer_name, layer_info in layered_data.get("layers", {}).items():
                layers_summary[layer_name] = {
                    "时间框架": layer_info.get("timeframe", ""),
                    "数据点数": len(layer_info.get("data", [])),
                    "天数": layer_info.get("days", 0)
                }
            summary["各层详情"] = layers_summary
        
        return summary
    

