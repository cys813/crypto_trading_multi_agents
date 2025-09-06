#!/usr/bin/env python3
"""
调试LLM服务初始化问题
"""

import os
import sys
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def debug_llm_initialization():
    """调试LLM初始化问题"""
    print("🔍 调试LLM服务初始化问题")
    print("=" * 50)
    
    try:
        # 导入相关模块
        from src.crypto_trading_agents.services.llm_service import LLMService
        from src.crypto_trading_agents.unified_config import get_unified_config
        
        # 获取配置
        config = get_unified_config()
        llm_config = config.get('llm', {})
        
        print(f"LLM配置:")
        print(f"  默认提供商: {llm_config.get('default_provider', 'N/A')}")
        print(f"  默认模型: {llm_config.get('default_model', 'N/A')}")
        
        # 检查服务配置
        service_config = llm_config.get('service_config', {})
        providers_config = service_config.get('providers', {})
        
        # 手动创建LLM服务并调试
        print(f"\n手动创建LLM服务...")
        llm_service = LLMService()
        
        # 检查提供商可用性
        for provider_name, provider_config in providers_config.items():
            print(f"\n检查{provider_name}可用性:")
            try:
                # 直接调用可用性检查
                is_available = llm_service._is_provider_available(provider_name, provider_config)
                print(f"  可用性检查结果: {is_available}")
                
                if is_available:
                    # 尝试创建适配器
                    print(f"  尝试创建{provider_name}适配器...")
                    adapter = llm_service._create_adapter(provider_name, provider_config)
                    if adapter:
                        print(f"  ✅ {provider_name}适配器创建成功")
                        print(f"    适配器信息: {adapter.get_info() if hasattr(adapter, 'get_info') else '无信息方法'}")
                    else:
                        print(f"  ❌ {provider_name}适配器创建失败")
                else:
                    print(f"  ❌ {provider_name}不可用")
                    
            except Exception as e:
                print(f"  检查{provider_name}时出错: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 尝试完整初始化
        print(f"\n尝试完整初始化...")
        init_result = llm_service.initialize(llm_config)
        print(f"  初始化结果: {init_result}")
        
        # 获取服务信息
        service_info = llm_service.get_service_info()
        print(f"  服务信息:")
        print(f"    默认提供商: {service_info.get('default_provider')}")
        print(f"    可用提供商: {service_info.get('available_providers')}")
        print(f"    适配器数量: {service_info.get('adapters_count')}")
        
    except Exception as e:
        print(f"调试LLM服务时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_llm_initialization()