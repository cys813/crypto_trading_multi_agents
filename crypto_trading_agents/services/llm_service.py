"""
统一LLM服务管理器

提供整个交易系统的统一LLM接口，避免重复代码和配置。
支持多种LLM提供商（阿里百炼DashScope、DeepSeek等）。
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLM提供商枚举"""
    DASHSCOPE = "dashscope"
    DEEPSEEK = "deepseek"


class LLMService:
    """统一LLM服务管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化LLM服务"""
        if not self._initialized:
            self.llm_adapters = {}
            self.default_provider = None
            self.config = {}
            self._initialized = True
    
    def initialize(self, config: Dict[str, Any]):
        """
        初始化LLM服务配置
        
        Args:
            config: LLM服务配置
                {
                    "default_provider": "dashscope",
                    "providers": {
                        "dashscope": {
                            "api_key": "xxx",
                            "model": "qwen-plus",
                            "temperature": 0.3,
                            "max_tokens": 2000
                        },
                        "deepseek": {
                            "api_key": "xxx", 
                            "model": "deepseek-chat",
                            "temperature": 0.1,
                            "max_tokens": 2000
                        }
                    }
                }
        """
        try:
            self.config = config
            self.default_provider = config.get("default_provider", "dashscope")
            
            # 初始化各个提供商的适配器
            providers_config = config.get("providers", {})
            
            for provider_name, provider_config in providers_config.items():
                if self._is_provider_available(provider_name, provider_config):
                    adapter = self._create_adapter(provider_name, provider_config)
                    if adapter:
                        self.llm_adapters[provider_name] = adapter
                        logger.info(f"LLM适配器初始化成功: {provider_name}")
            
            if not self.llm_adapters:
                logger.warning("没有可用的LLM适配器初始化成功")
                return False
            
            # 确保默认提供商可用
            if self.default_provider not in self.llm_adapters:
                available_providers = list(self.llm_adapters.keys())
                self.default_provider = available_providers[0]
                logger.warning(f"默认提供商不可用，切换到: {self.default_provider}")
            
            logger.info(f"LLM服务初始化完成，默认提供商: {self.default_provider}")
            logger.info(f"可用提供商: {list(self.llm_adapters.keys())}")
            
            return True
            
        except Exception as e:
            logger.error(f"LLM服务初始化失败: {str(e)}")
            return False
    
    def _is_provider_available(self, provider_name: str, provider_config: Dict[str, Any]) -> bool:
        """检查提供商是否可用"""
        try:
            api_key = provider_config.get("api_key") or os.getenv(f"{provider_name.upper()}_API_KEY")
            if not api_key:
                logger.warning(f"提供商 {provider_name} 缺少API密钥")
                return False
            
            # 可以添加更多可用性检查
            return True
            
        except Exception as e:
            logger.error(f"检查提供商 {provider_name} 可用性失败: {str(e)}")
            return False
    
    def _create_adapter(self, provider_name: str, provider_config: Dict[str, Any]):
        """创建LLM适配器"""
        try:
            if provider_name == "dashscope":
                return self._create_dashscope_adapter(provider_config)
            elif provider_name == "deepseek":
                return self._create_deepseek_adapter(provider_config)
            else:
                logger.error(f"不支持的LLM提供商: {provider_name}")
                return None
                
        except Exception as e:
            logger.error(f"创建 {provider_name} 适配器失败: {str(e)}")
            return None
    
    def _create_dashscope_adapter(self, config: Dict[str, Any]):
        """创建阿里百炼适配器"""
        try:
            import dashscope
            from http import HTTPStatus
            
            api_key = config.get("api_key") or os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("DashScope API密钥未配置")
            
            dashscope.api_key = api_key
            
            class DashScopeAdapter:
                def __init__(self, model, temperature, max_tokens):
                    self.model = model
                    self.temperature = temperature
                    self.max_tokens = max_tokens
                
                def call(self, prompt: str, **kwargs) -> str:
                    """调用DashScope API"""
                    try:
                        response = dashscope.Generation.call(
                            model=self.model,
                            prompt=prompt,
                            temperature=kwargs.get("temperature", self.temperature),
                            max_tokens=kwargs.get("max_tokens", self.max_tokens),
                            result_format='message'
                        )
                        
                        if response.status_code == HTTPStatus.OK:
                            return response.output.text
                        else:
                            raise Exception(f"DashScope API调用失败: {response.code} - {response.message}")
                            
                    except Exception as e:
                        logger.error(f"DashScope API调用失败: {str(e)}")
                        raise
                
                def get_info(self):
                    return {
                        "provider": "dashscope",
                        "model": self.model,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
            
            return DashScopeAdapter(
                model=config.get("model", "qwen-plus"),
                temperature=config.get("temperature", 0.3),
                max_tokens=config.get("max_tokens", 2000)
            )
            
        except ImportError:
            logger.error("DashScope库未安装，请运行: pip install dashscope")
            return None
        except Exception as e:
            logger.error(f"创建DashScope适配器失败: {str(e)}")
            return None
    
    def _create_deepseek_adapter(self, config: Dict[str, Any]):
        """创建DeepSeek适配器"""
        try:
            import openai
            
            api_key = config.get("api_key") or os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("DeepSeek API密钥未配置")
            
            class DeepSeekAdapter:
                def __init__(self, model, temperature, max_tokens, api_key):
                    self.model = model
                    self.temperature = temperature
                    self.max_tokens = max_tokens
                    self.client = openai.OpenAI(
                        api_key=api_key,
                        base_url="https://api.deepseek.com"
                    )
                
                def call(self, prompt: str, **kwargs) -> str:
                    """调用DeepSeek API"""
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "user", "content": prompt}
                            ],
                            temperature=kwargs.get("temperature", self.temperature),
                            max_tokens=kwargs.get("max_tokens", self.max_tokens)
                        )
                        
                        return response.choices[0].message.content
                        
                    except Exception as e:
                        logger.error(f"DeepSeek API调用失败: {str(e)}")
                        raise
                
                def get_info(self):
                    return {
                        "provider": "deepseek",
                        "model": self.model,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
            
            return DeepSeekAdapter(
                model=config.get("model", "deepseek-chat"),
                temperature=config.get("temperature", 0.1),
                max_tokens=config.get("max_tokens", 2000),
                api_key=api_key
            )
            
        except ImportError:
            logger.error("OpenAI库未安装，请运行: pip install openai")
            return None
        except Exception as e:
            logger.error(f"创建DeepSeek适配器失败: {str(e)}")
            return None
    
    def call_llm(self, prompt: str, provider: Optional[str] = None, **kwargs) -> str:
        """
        调用LLM进行分析
        
        Args:
            prompt: 分析提示词
            provider: 指定LLM提供商，None表示使用默认提供商
            **kwargs: 其他参数（temperature, max_tokens等）
            
        Returns:
            str: LLM响应结果
        """
        if not self.llm_adapters:
            raise Exception("LLM服务未初始化或没有可用的适配器")
        
        # 确定使用的提供商
        target_provider = provider or self.default_provider
        
        if target_provider not in self.llm_adapters:
            available_providers = list(self.llm_adapters.keys())
            if available_providers:
                target_provider = available_providers[0]
                logger.warning(f"指定提供商 {provider} 不可用，使用 {target_provider}")
            else:
                raise Exception("没有可用的LLM适配器")
        
        try:
            adapter = self.llm_adapters[target_provider]
            response = adapter.call(prompt, **kwargs)
            
            logger.debug(f"LLM调用成功，提供商: {target_provider}")
            return response
            
        except Exception as e:
            logger.error(f"LLM调用失败，提供商: {target_provider}, 错误: {str(e)}")
            
            # 尝试其他可用的提供商
            for fallback_provider in self.llm_adapters:
                if fallback_provider != target_provider:
                    try:
                        logger.info(f"尝试备用提供商: {fallback_provider}")
                        adapter = self.llm_adapters[fallback_provider]
                        response = adapter.call(prompt, **kwargs)
                        logger.info(f"备用提供商调用成功: {fallback_provider}")
                        return response
                    except Exception as fallback_e:
                        logger.error(f"备用提供商 {fallback_provider} 也失败: {str(fallback_e)}")
                        continue
            
            # 所有提供商都失败
            raise Exception(f"所有LLM提供商都不可用，最后错误: {str(e)}")
    
    def parse_json_response(self, response: str, default_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        解析LLM的JSON响应
        
        Args:
            response: LLM原始响应
            default_result: 解析失败时的默认结果
            
        Returns:
            Dict[str, Any]: 解析后的JSON对象
        """
        try:
            import re
            
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_result = json.loads(json_str)
                return parsed_result
            else:
                logger.warning("LLM响应中未找到JSON格式内容")
                return default_result or {"error": "未找到JSON格式响应"}
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            return default_result or {"error": f"JSON解析失败: {str(e)}"}
        except Exception as e:
            logger.error(f"响应解析异常: {str(e)}")
            return default_result or {"error": f"响应解析异常: {str(e)}"}
    
    def is_available(self) -> bool:
        """检查LLM服务是否可用"""
        return len(self.llm_adapters) > 0
    
    def get_available_providers(self) -> List[str]:
        """获取可用的LLM提供商列表"""
        return list(self.llm_adapters.keys())
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取LLM服务信息"""
        providers_info = {}
        for provider_name, adapter in self.llm_adapters.items():
            try:
                providers_info[provider_name] = adapter.get_info()
            except:
                providers_info[provider_name] = {"error": "无法获取适配器信息"}
        
        return {
            "default_provider": self.default_provider,
            "available_providers": list(self.llm_adapters.keys()),
            "providers_info": providers_info,
            "service_initialized": self._initialized,
            "adapters_count": len(self.llm_adapters)
        }
    
    @classmethod
    def get_instance(cls):
        """获取LLM服务单例"""
        return cls()


# 全局LLM服务实例
llm_service = LLMService()


def initialize_llm_service(config: Dict[str, Any]) -> bool:
    """
    初始化全局LLM服务
    
    Args:
        config: LLM服务配置
        
    Returns:
        bool: 初始化是否成功
    """
    return llm_service.initialize(config)


def call_llm_analysis(prompt: str, provider: Optional[str] = None, **kwargs) -> str:
    """
    便捷函数：调用LLM进行分析
    
    Args:
        prompt: 分析提示词
        provider: 指定LLM提供商
        **kwargs: 其他参数
        
    Returns:
        str: LLM分析结果
    """
    return llm_service.call_llm(prompt, provider, **kwargs)


def parse_llm_json_response(response: str, default_result: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    便捷函数：解析LLM的JSON响应
    
    Args:
        response: LLM原始响应
        default_result: 默认结果
        
    Returns:
        Dict[str, Any]: 解析后的结果
    """
    return llm_service.parse_json_response(response, default_result)


def is_llm_service_available() -> bool:
    """便捷函数：检查LLM服务是否可用"""
    return llm_service.is_available()