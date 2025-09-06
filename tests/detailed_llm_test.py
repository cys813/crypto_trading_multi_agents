#!/usr/bin/env python3
"""
详细测试LLM服务调用，包含错误诊断
"""

import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def detailed_llm_test():
    """详细测试LLM服务调用"""
    print("🔍 详细测试LLM服务调用")
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
        
        for provider_name, provider_config in providers_config.items():
            print(f"\n{provider_name}配置:")
            for key, value in provider_config.items():
                if key == 'api_key' and value and not str(value).startswith('${'):
                    print(f"  {key}: 已配置 (长度: {len(str(value))})")
                else:
                    print(f"  {key}: {value}")
        
        # 手动测试智谱AI
        print(f"\n手动测试智谱AI适配器...")
        try:
            from src.crypto_trading_agents.services.llm_service import LLMService
            llm_service = LLMService()
            
            # 直接调用初始化方法查看详细错误
            init_result = llm_service.initialize(llm_config)
            print(f"  初始化结果: {init_result}")
            
            # 获取服务信息
            service_info = llm_service.get_service_info()
            print(f"  服务信息:")
            print(f"    默认提供商: {service_info.get('default_provider')}")
            print(f"    可用提供商: {service_info.get('available_providers')}")
            print(f"    服务已初始化: {service_info.get('service_initialized')}")
            print(f"    适配器数量: {service_info.get('adapters_count')}")
            print(f"    提供商信息: {service_info.get('providers_info')}")
            
        except Exception as e:
            print(f"  初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"测试LLM服务时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    detailed_llm_test()