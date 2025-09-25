"""
JSON配置文件加载器 - 支持环境变量替换和预设配置

将配置改为JSON格式，支持:
1. 环境变量替换 (${VAR_NAME:default_value})
2. LLM和市场条件预设
3. 配置验证和便捷函数
"""

import os
import json
import re
from copy import deepcopy
from typing import Dict, Any, Optional, List
from pathlib import Path


class JSONConfigLoader:
    """JSON配置加载器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，默认为项目根目录的config.json
        """
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config.json"
        
        self.config_path = Path(config_path)
        self._config_cache = None
        self._base_config = None
        
    def _load_base_config(self) -> Dict[str, Any]:
        """加载基础配置文件"""
        if self._base_config is not None:
            return self._base_config
            
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._base_config = json.load(f)
            
        return self._base_config
    
    def _resolve_env_variables(self, value: Any) -> Any:
        """
        递归解析环境变量
        
        支持格式:
        - ${VAR_NAME} - 必须存在的环境变量
        - ${VAR_NAME:default} - 带默认值的环境变量
        
        Args:
            value: 要解析的值
            
        Returns:
            解析后的值
        """
        if isinstance(value, str):
            # 匹配 ${VAR_NAME} 或 ${VAR_NAME:default} 格式
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
            
            def replacer(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ""
                
                env_value = os.getenv(var_name, default_value)
                
                # 处理布尔值
                if env_value.lower() in ('true', 'false'):
                    return env_value.lower() == 'true'
                
                # 处理数字
                if env_value.isdigit():
                    return int(env_value)
                    
                return env_value
            
            # 如果整个字符串都是环境变量，直接返回解析后的值
            full_match = re.match(r'^\$\{([^}:]+)(?::([^}]*))?\}$', value)
            if full_match:
                var_name = full_match.group(1)
                default_value = full_match.group(2) if full_match.group(2) is not None else ""
                env_value = os.getenv(var_name, default_value)
                
                # 处理布尔值
                if isinstance(env_value, str) and env_value.lower() in ('true', 'false'):
                    return env_value.lower() == 'true'
                
                # 处理数字
                if isinstance(env_value, str) and env_value.isdigit():
                    return int(env_value)
                    
                return env_value
            
            # 部分替换
            return re.sub(pattern, replacer, value)
            
        elif isinstance(value, dict):
            return {k: self._resolve_env_variables(v) for k, v in value.items()}
            
        elif isinstance(value, list):
            return [self._resolve_env_variables(item) for item in value]
            
        return value
    
    def _apply_preset(self, config: Dict[str, Any], preset_config: Dict[str, str]) -> Dict[str, Any]:
        """
        应用预设配置
        
        Args:
            config: 基础配置
            preset_config: 预设配置 (key为配置路径，value为新值)
            
        Returns:
            应用预设后的配置
        """
        result = deepcopy(config)
        
        for path, new_value in preset_config.items():
            # 分割路径 (如 "trading.max_position_size")
            keys = path.split('.')
            current = result
            
            # 导航到目标位置
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 设置新值
            current[keys[-1]] = new_value
        
        return result
    
    def get_config(
        self, 
        market_condition: str = "normal",
        llm_provider: str = None,
        reload: bool = False
    ) -> Dict[str, Any]:
        """
        获取配置
        
        Args:
            market_condition: 市场条件
            llm_provider: LLM提供商
            reload: 是否重新加载配置文件
            
        Returns:
            配置字典
        """
        # 重新加载或首次加载
        if reload or self._config_cache is None:
            base_config = self._load_base_config()
            self._config_cache = self._resolve_env_variables(base_config)
        
        config = deepcopy(self._config_cache)
        
        # 应用LLM预设
        if llm_provider and llm_provider in config.get("presets", {}).get("llm", {}):
            llm_preset = config["presets"]["llm"][llm_provider]
            config = self._apply_preset(config, llm_preset)
        
        # 应用市场条件预设
        if market_condition in config.get("presets", {}).get("market_conditions", {}):
            market_preset = config["presets"]["market_conditions"][market_condition]
            config = self._apply_preset(config, market_preset)
        
        return config
    
    def get_llm_config(self, provider: str = None) -> Dict[str, Any]:
        """
        获取LLM配置
        
        Args:
            provider: LLM提供商，为None时使用默认提供商
            
        Returns:
            LLM配置字典
        """
        config = self.get_config()
        
        if provider is None:
            provider = config.get("llm", {}).get("default_provider", "zhipuai")
        
        llm_service = config.get("llm", {}).get("service_config", {})
        providers = llm_service.get("providers", {})
        provider_config = providers.get(provider, {})
        
        return {
            "provider": provider,
            "api_key": provider_config.get("api_key", ""),
            "model": provider_config.get("model", ""),
            "temperature": provider_config.get("temperature", 0.1),
            "max_tokens": provider_config.get("max_tokens", 2000)
        }
    
    def get_available_llm_providers(self) -> List[str]:
        """
        获取所有可用的LLM提供商
        
        Returns:
            LLM提供商名称列表
        """
        config = self.get_config()
        providers = config.get("llm", {}).get("service_config", {}).get("providers", {})
        available = []
        
        for provider, provider_config in providers.items():
            api_key = provider_config.get("api_key")
            if api_key:  # 只返回有API密钥的提供商
                available.append(provider)
        
        return available
    
    def validate_config(self, config: Dict[str, Any] = None) -> bool:
        """
        验证配置的有效性
        
        Args:
            config: 配置字典，为None时使用当前配置
            
        Returns:
            是否有效
        """
        if config is None:
            config = self.get_config()
        
        required_sections = ["llm", "ai_analysis", "trading", "crypto"]
        
        for section in required_sections:
            if section not in config:
                return False
        
        # 验证交易配置
        trading = config.get("trading", {})
        if trading.get("risk_per_trade", 0) <= 0:
            return False
        if trading.get("max_position_size", 0) <= 0:
            return False
        
        # 验证LLM配置
        llm = config.get("llm", {})
        service_config = llm.get("service_config", {})
        if not service_config.get("providers"):
            return False
        
        # 验证AI分析配置
        ai_analysis = config.get("ai_analysis", {})
        if "enabled" not in ai_analysis:
            return False
        
        return True
    
    def get_config_template(self, template_name: str = "default") -> Dict[str, Any]:
        """
        获取配置模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            配置字典
        """
        if template_name in ["zhipuai", "dashscope", "deepseek", "traditional"]:
            return self.get_config(llm_provider=template_name)
        else:
            return self.get_config()
    
    def print_config_info(self):
        """打印配置信息，用于调试"""
        config = self.get_config()
        
        print("🔧 JSON配置系统信息")
        print("=" * 60)
        
        print("1. LLM服务配置:")
        llm = config.get("llm", {})
        default_provider = llm.get("default_provider", "未设置")
        print(f"   默认提供商: {default_provider}")
        
        service_config = llm.get("service_config", {})
        providers = service_config.get("providers", {})
        for provider, provider_config in providers.items():
            api_key = provider_config.get("api_key")
            model = provider_config.get("model", "未设置")
            status = "✅ 已配置" if api_key else "❌ 未配置"
            print(f"   {provider}: {status} ({model})")
        
        print(f"\n2. AI分析配置:")
        ai_analysis = config.get("ai_analysis", {})
        ai_enabled = ai_analysis.get("enabled", False)
        print(f"   AI启用状态: {'✅ 启用' if ai_enabled else '❌ 禁用'}")
        print(f"   温度参数: {ai_analysis.get('temperature', '未设置')}")
        print(f"   最大tokens: {ai_analysis.get('max_tokens', '未设置')}")
        
        print(f"\n3. 交易配置:")
        trading = config.get("trading", {})
        print(f"   最大仓位: {trading.get('max_position_size', '未设置')}")
        print(f"   每笔风险: {trading.get('risk_per_trade', '未设置')}")
        print(f"   最大杠杆: {trading.get('max_leverage', '未设置')}")
        
        print(f"\n4. 可用LLM提供商:")
        available_providers = self.get_available_llm_providers()
        if available_providers:
            for provider in available_providers:
                print(f"   ✅ {provider}")
        else:
            print("   ❌ 无可用提供商 (检查环境变量)")
        
        print("\n" + "=" * 60)


# 全局配置加载器实例
_config_loader = JSONConfigLoader()

# 便捷函数，保持与原unified_config.py的兼容性
def get_unified_config(market_condition: str = "normal", llm_provider: str = None) -> Dict[str, Any]:
    """获取统一配置"""
    return _config_loader.get_config(market_condition=market_condition, llm_provider=llm_provider)

def get_config_template(template_name: str = "default") -> Dict[str, Any]:
    """获取配置模板"""
    return _config_loader.get_config_template(template_name)

def get_llm_config(provider: str = None) -> Dict[str, Any]:
    """获取LLM配置"""
    return _config_loader.get_llm_config(provider)

def get_available_llm_providers() -> List[str]:
    """获取可用的LLM提供商"""
    return _config_loader.get_available_llm_providers()

def validate_config(config: Dict[str, Any] = None) -> bool:
    """验证配置"""
    return _config_loader.validate_config(config)

def print_config_info():
    """打印配置信息"""
    _config_loader.print_config_info()

def reload_config():
    """重新加载配置文件"""
    _config_loader.get_config(reload=True)