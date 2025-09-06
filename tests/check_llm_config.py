#!/usr/bin/env python3
"""
检查LLM配置结构
"""

import os
import sys
import json

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def check_llm_config_structure():
    """检查LLM配置结构"""
    print("🔍 检查LLM配置结构")
    print("=" * 50)
    
    try:
        # 导入相关模块
        from src.crypto_trading_agents.unified_config import get_unified_config
        
        # 获取配置
        config = get_unified_config()
        llm_config = config.get('llm', {})
        
        print(f"LLM配置结构:")
        print(json.dumps(llm_config, indent=2, ensure_ascii=False))
        
        print(f"\n服务配置结构:")
        service_config = llm_config.get('service_config', {})
        print(json.dumps(service_config, indent=2, ensure_ascii=False))
        
        print(f"\n提供商配置结构:")
        providers_config = service_config.get('providers', {})
        print(json.dumps(providers_config, indent=2, ensure_ascii=False))
        
        # 检查LLM服务期望的配置结构
        print(f"\nLLM服务期望的配置结构:")
        expected_providers = llm_config.get('service_config', {}).get('providers', {})
        print(f"  providers键是否存在: {'providers' in llm_config}")
        print(f"  service_config.providers键是否存在: {'providers' in service_config}")
        print(f"  期望的提供商: {list(expected_providers.keys())}")
        
        # 测试修复后的初始化
        print(f"\n测试修复后的初始化...")
        fixed_config = {
            "default_provider": llm_config.get("default_provider", "zhipuai"),
            "providers": expected_providers
        }
        
        print(f"  修复后的配置:")
        print(json.dumps(fixed_config, indent=2, ensure_ascii=False))
        
        # 导入LLM服务
        from src.crypto_trading_agents.services.llm_service import LLMService
        llm_service = LLMService()
        
        # 使用修复后的配置进行初始化
        init_result = llm_service.initialize(fixed_config)
        print(f"  初始化结果: {init_result}")
        
        if init_result:
            service_info = llm_service.get_service_info()
            print(f"  服务信息:")
            print(f"    默认提供商: {service_info.get('default_provider')}")
            print(f"    可用提供商: {service_info.get('available_providers')}")
            print(f"    适配器数量: {service_info.get('adapters_count')}")
        else:
            print(f"  初始化仍然失败")
            
    except Exception as e:
        print(f"检查LLM配置结构时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_llm_config_structure()