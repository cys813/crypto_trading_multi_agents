"""
AI分析混入类 (Mixin)

为所有分析模块提供统一的AI增强分析能力。
避免重复代码，提供标准化的AI集成接口。
"""

import logging
from typing import Dict, Any, Optional
from .llm_service import llm_service, call_llm_analysis, parse_llm_json_response, is_llm_service_available

logger = logging.getLogger(__name__)


class AIAnalysisMixin:
    """AI分析混入类"""
    
    def __init__(self, config=None, *args, **kwargs):
        """初始化AI分析配置"""
        # 调用父类初始化，不传递参数
        super().__init__()
        
        # 存储config引用
        self.config = config
        
        # AI配置
        if config:
            self.ai_analysis_config = config.get("ai_analysis_config", {})
            self.ai_enabled = self.ai_analysis_config.get("enabled", True)
        else:
            self.ai_analysis_config = {}
            self.ai_enabled = False
            logger.warning(f"{self.__class__.__name__}: 缺少config配置，AI分析功能禁用")
    
    def is_ai_enabled(self) -> bool:
        """检查AI分析是否启用且可用"""
        return self.ai_enabled and is_llm_service_available()
    
    def call_ai_analysis(self, prompt: str, provider: Optional[str] = None, **kwargs) -> str:
        """
        调用AI进行分析
        
        Args:
            prompt: 分析提示词
            provider: 指定LLM提供商
            **kwargs: 其他参数
            
        Returns:
            str: AI分析结果
        """
        if not self.is_ai_enabled():
            raise Exception("AI分析服务不可用")
        
        try:
            # 使用配置中的默认参数
            call_kwargs = {
                "temperature": self.ai_analysis_config.get("temperature", 0.3),
                "max_tokens": self.ai_analysis_config.get("max_tokens", 2000),
                **kwargs  # 传入的参数会覆盖默认配置
            }
            
            response = call_llm_analysis(prompt, provider, **call_kwargs)
            return response
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: AI分析调用失败: {str(e)}")
            raise
    
    def parse_ai_json_response(self, response: str, default_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        解析AI的JSON响应
        
        Args:
            response: AI原始响应
            default_result: 解析失败时的默认结果
            
        Returns:
            Dict[str, Any]: 解析后的结果
        """
        try:
            parsed_result = parse_llm_json_response(response, default_result)
            
            # 添加元数据
            if isinstance(parsed_result, dict):
                parsed_result["_ai_analysis"] = True
                parsed_result["_analyzer"] = self.__class__.__name__
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: AI响应解析失败: {str(e)}")
            return default_result or {"error": f"AI响应解析失败: {str(e)}"}
    
    def analyze_with_ai_enhancement(self, data: Dict[str, Any], traditional_analysis_method=None) -> Dict[str, Any]:
        """
        通用的AI增强分析流程
        
        Args:
            data: 原始分析数据
            traditional_analysis_method: 传统分析方法（如果为None，会调用self._traditional_analyze）
            
        Returns:
            Dict[str, Any]: 增强后的分析结果
        """
        try:
            # 1. 执行传统分析
            if traditional_analysis_method:
                traditional_analysis = traditional_analysis_method(data)
            elif hasattr(self, '_traditional_analyze'):
                traditional_analysis = self._traditional_analyze(data)
            else:
                raise Exception(f"{self.__class__.__name__}: 未找到传统分析方法")
            
            # 2. 检查是否启用AI增强
            if not self.is_ai_enabled():
                logger.info(f"{self.__class__.__name__}: AI分析未启用，返回传统分析结果")
                traditional_analysis["ai_enhanced"] = False
                return traditional_analysis
            
            # 3. 执行AI增强分析
            try:
                ai_analysis = self._analyze_with_ai(traditional_analysis, data)
                enhanced_analysis = self._combine_analyses(traditional_analysis, ai_analysis)
                enhanced_analysis["ai_enhanced"] = True
                return enhanced_analysis
                
            except Exception as ai_error:
                logger.warning(f"{self.__class__.__name__}: AI分析失败，回退到传统分析: {str(ai_error)}")
                fallback_analysis = traditional_analysis.copy()
                fallback_analysis["ai_enhanced"] = False
                fallback_analysis["ai_fallback_reason"] = str(ai_error)
                return fallback_analysis
                
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: 分析失败: {str(e)}")
            return {"error": f"分析失败: {str(e)}"}
    
    def _analyze_with_ai(self, traditional_analysis: Dict[str, Any], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI分析方法（需要子类实现）
        
        Args:
            traditional_analysis: 传统分析结果
            raw_data: 原始数据
            
        Returns:
            Dict[str, Any]: AI分析结果
        """
        raise NotImplementedError(f"{self.__class__.__name__} 必须实现 _analyze_with_ai 方法")
    
    def _combine_analyses(self, traditional_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        组合传统分析和AI分析结果（需要子类实现）
        
        Args:
            traditional_analysis: 传统分析结果
            ai_analysis: AI分析结果
            
        Returns:
            Dict[str, Any]: 组合后的分析结果
        """
        raise NotImplementedError(f"{self.__class__.__name__} 必须实现 _combine_analyses 方法")
    
    def get_ai_analysis_info(self) -> Dict[str, Any]:
        """获取AI分析配置信息"""
        return {
            "analyzer": self.__class__.__name__,
            "ai_enabled": self.ai_enabled,
            "ai_available": is_llm_service_available(),
            "ai_config": self.ai_analysis_config,
            "llm_service_info": llm_service.get_service_info() if is_llm_service_available() else None
        }


class StandardAIAnalysisMixin(AIAnalysisMixin):
    """
    标准AI分析混入类
    
    提供常用的AI分析模式实现，减少子类需要实现的方法数量。
    """
    
    def _build_standard_analysis_prompt(self, 
                                      analyzer_type: str,
                                      traditional_analysis: Dict[str, Any], 
                                      raw_data: Dict[str, Any],
                                      analysis_dimensions: list,
                                      output_fields: list) -> str:
        """
        构建标准化的分析提示词
        
        Args:
            analyzer_type: 分析器类型（如"链上分析师"、"情感分析师"等）
            traditional_analysis: 传统分析结果
            raw_data: 原始数据
            analysis_dimensions: 分析维度列表
            output_fields: 输出字段列表
            
        Returns:
            str: 构建好的提示词
        """
        import json
        
        # 格式化传统分析结果（只显示关键信息）
        traditional_summary = self._format_traditional_analysis_summary(traditional_analysis)
        
        # 格式化原始数据概要
        data_summary = self._format_raw_data_summary(raw_data)
        
        # 构建分析维度说明
        dimensions_text = "\n".join([f"{i+1}. **{dim}**" for i, dim in enumerate(analysis_dimensions)])
        
        # 构建输出字段说明
        output_fields_text = ",\n    ".join([f'"{field}": "相应分析结果"' for field in output_fields])
        
        prompt = f"""你是一位专业的加密货币{analyzer_type}，擅长深度数据分析和市场洞察。

请基于以下数据进行专业分析：

## 传统量化分析结果：
{json.dumps(traditional_summary, ensure_ascii=False, indent=2)}

## 原始市场数据：
{json.dumps(data_summary, ensure_ascii=False, indent=2)}

请从以下{len(analysis_dimensions)}个维度进行深度分析：

{dimensions_text}

请以JSON格式返回分析结果，包含以下{len(output_fields)}个字段：

{{
    {output_fields_text}
}}

请确保分析专业、客观，基于数据驱动的判断，避免过度投机的预测。"""

        return prompt
    
    def _format_traditional_analysis_summary(self, traditional_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化传统分析结果摘要（子类可重写）
        
        Args:
            traditional_analysis: 传统分析结果
            
        Returns:
            Dict[str, Any]: 格式化后的摘要
        """
        # 默认实现：提取一些通用字段
        summary = {}
        
        # 通用字段提取
        common_fields = ["confidence", "risk_level", "recommendation", "status", "sentiment", "strength"]
        for field in common_fields:
            if field in traditional_analysis:
                summary[field] = traditional_analysis[field]
        
        # 如果有嵌套的分析结果，也提取一些关键信息
        for key, value in traditional_analysis.items():
            if isinstance(value, dict) and len(value) <= 5:  # 只包含小的字典
                summary[key] = value
        
        return summary if summary else traditional_analysis
    
    def _format_raw_data_summary(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化原始数据摘要（子类可重写）
        
        Args:
            raw_data: 原始数据
            
        Returns:
            Dict[str, Any]: 格式化后的摘要
        """
        # 默认实现：直接返回原始数据
        # 子类可以重写此方法来提取特定的数据字段
        return raw_data
    
    def _combine_standard_analyses(self, 
                                 traditional_analysis: Dict[str, Any], 
                                 ai_analysis: Dict[str, Any],
                                 confidence_weight_ai: float = 0.6) -> Dict[str, Any]:
        """
        标准化的分析结果组合方法
        
        Args:
            traditional_analysis: 传统分析结果
            ai_analysis: AI分析结果
            confidence_weight_ai: AI分析在置信度计算中的权重
            
        Returns:
            Dict[str, Any]: 组合后的分析结果
        """
        try:
            # 计算综合置信度
            traditional_confidence = traditional_analysis.get("confidence", 50)
            ai_confidence = ai_analysis.get("confidence", 50)
            combined_confidence = (traditional_confidence * (1 - confidence_weight_ai) + 
                                 ai_confidence * confidence_weight_ai)
            
            # 创建增强分析结果
            enhanced_analysis = traditional_analysis.copy()
            enhanced_analysis.update({
                "ai_enhanced": True,
                "confidence": combined_confidence,
                "ai_analysis": ai_analysis,
                "enhancement_info": {
                    "traditional_confidence": traditional_confidence,
                    "ai_confidence": ai_confidence,
                    "combined_confidence": combined_confidence,
                    "ai_weight": confidence_weight_ai
                }
            })
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: 标准分析结果组合失败: {str(e)}")
            # 发生错误时返回传统分析结果
            fallback_analysis = traditional_analysis.copy()
            fallback_analysis["ai_enhanced"] = False
            fallback_analysis["combine_error"] = str(e)
            return fallback_analysis