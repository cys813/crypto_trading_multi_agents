#!/usr/bin/env python3
"""
测试LLM服务调用
"""

import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_llm_service():
    """测试LLM服务调用"""
    print("🔍 测试LLM服务调用")
    print("=" * 50)
    
    try:
        # 导入相关模块
        from src.crypto_trading_agents.services.llm_service import initialize_llm_service, llm_service, call_llm_analysis
        from src.crypto_trading_agents.unified_config import get_unified_config
        
        # 获取配置
        config = get_unified_config()
        llm_config = config.get('llm', {})
        
        print(f"LLM配置:")
        print(f"  默认提供商: {llm_config.get('default_provider', 'N/A')}")
        print(f"  默认模型: {llm_config.get('default_model', 'N/A')}")
        
        # 检查API密钥
        providers_config = llm_config.get('service_config', {}).get('providers', {})
        for provider_name, provider_config in providers_config.items():
            api_key = provider_config.get('api_key', 'N/A')
            if api_key and not str(api_key).startswith('${'):
                print(f"  {provider_name} API密钥: 已配置")
            else:
                print(f"  {provider_name} API密钥: 未配置或使用环境变量")
        
        # 初始化LLM服务
        print(f"\n初始化LLM服务...")
        init_result = initialize_llm_service(llm_config)
        print(f"  初始化结果: {init_result}")
        
        # 获取服务信息
        if init_result:
            service_info = llm_service.get_service_info()
            print(f"  服务信息:")
            print(f"    默认提供商: {service_info.get('default_provider')}")
            print(f"    可用提供商: {service_info.get('available_providers')}")
            print(f"    服务已初始化: {service_info.get('service_initialized')}")
            print(f"    适配器数量: {service_info.get('adapters_count')}")
            
            # 测试简单的API调用
            print(f"\n测试LLM服务...")
            test_prompt = "请用一句话回答：Solana区块链的特点是什么？"
            
            try:
                response = call_llm_analysis(
                    prompt=test_prompt,
                    temperature=0.1,
                    max_tokens=500
                )
                
                print(f"  ✅ LLM调用成功")
                print(f"  响应: {response[:200]}...")  # 只显示前200个字符
                
            except Exception as e:
                print(f"  ❌ LLM调用失败: {str(e)}")
        else:
            print(f"  ❌ LLM服务初始化失败")
            
    except Exception as e:
        print(f"测试LLM服务时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llm_service()