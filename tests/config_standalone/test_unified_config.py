#!/usr/bin/env python3
"""
统一配置系统测试脚本

用于验证配置整改后的功能是否正常工作
"""

import os
import sys
import json
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_config_loading():
    """测试基本配置加载"""
    print("🧪 测试基本配置加载...")
    try:
        from crypto_trading_agents.unified_config import (
            get_unified_config, 
            print_config_info,
            get_config_template,
            get_available_llm_providers,
            get_llm_config
        )
        
        # 测试默认配置
        config = get_unified_config()
        assert isinstance(config, dict), "配置应该是字典类型"
        assert "llm_service_config" in config, "应包含LLM服务配置"
        assert "ai_analysis_config" in config, "应包含AI分析配置"
        assert "trading_config" in config, "应包含交易配置"
        
        print("✅ 基本配置加载测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基本配置加载测试失败: {str(e)}")
        return False

def test_llm_provider_selection():
    """测试LLM提供商选择功能"""
    print("\n🧪 测试LLM提供商选择...")
    try:
        from crypto_trading_agents.unified_config import (
            get_unified_config,
            get_config_template,
            get_llm_config
        )
        
        # 测试不同LLM提供商的配置
        providers_to_test = ["zhipuai", "dashscope", "deepseek", "traditional"]
        
        for provider in providers_to_test:
            config = get_unified_config(llm_provider=provider)
            
            if provider != "traditional":
                llm_service = config.get("llm_service_config", {})
                default_provider = llm_service.get("default_provider")
                assert default_provider == provider, f"默认提供商应为 {provider}"
                
                # 测试模板方式
                template_config = get_config_template(provider)
                template_provider = template_config.get("llm_service_config", {}).get("default_provider")
                assert template_provider == provider, f"模板提供商应为 {provider}"
            else:
                # traditional模式应该禁用AI
                ai_enabled = config.get("ai_analysis_config", {}).get("enabled", True)
                assert not ai_enabled, "传统模式应该禁用AI"
        
        print("✅ LLM提供商选择测试通过")
        return True
        
    except Exception as e:
        print(f"❌ LLM提供商选择测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_market_condition_presets():
    """测试市场条件预设"""
    print("\n🧪 测试市场条件预设...")
    try:
        from crypto_trading_agents.unified_config import get_unified_config
        
        market_conditions = ["bull_market", "bear_market", "sideways_market", "high_volatility"]
        
        for condition in market_conditions:
            config = get_unified_config(market_condition=condition)
            trading_config = config.get("trading_config", {})
            
            # 检查不同市场条件下的风险参数是否不同
            assert "max_position_size" in trading_config, "应包含最大仓位配置"
            assert "risk_per_trade" in trading_config, "应包含每笔风险配置"
            
            # 特殊验证
            if condition == "high_volatility":
                # 高波动性市场应该有更保守的参数
                max_pos = trading_config.get("max_position_size", 0.1)
                assert max_pos <= 0.05, "高波动性市场应该有更小的仓位"
        
        print("✅ 市场条件预设测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 市场条件预设测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_config_validation():
    """测试配置验证"""
    print("\n🧪 测试配置验证...")
    try:
        from crypto_trading_agents.unified_config import validate_config, get_unified_config
        
        # 测试有效配置
        valid_config = get_unified_config()
        assert validate_config(valid_config), "默认配置应该是有效的"
        
        # 测试无效配置
        invalid_config = {"invalid": "config"}
        assert not validate_config(invalid_config), "无效配置应该返回False"
        
        print("✅ 配置验证测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置验证测试失败: {str(e)}")
        return False

def test_default_config_compatibility():
    """测试与原default_config的兼容性"""
    print("\n🧪 测试default_config兼容性...")
    try:
        from crypto_trading_agents.default_config import DEFAULT_CONFIG, get_config
        
        # 检查DEFAULT_CONFIG是否正常工作
        assert isinstance(DEFAULT_CONFIG, dict), "DEFAULT_CONFIG应该是字典"
        assert "llm_service_config" in DEFAULT_CONFIG, "应包含LLM服务配置"
        
        # 检查get_config函数是否正常工作
        config = get_config()
        assert isinstance(config, dict), "get_config()应返回字典"
        
        # 测试带参数的调用
        bull_config = get_config(market_condition="bull_market", llm_provider="zhipuai")
        llm_provider = bull_config.get("llm_service_config", {}).get("default_provider")
        assert llm_provider == "zhipuai", "应该设置正确的LLM提供商"
        
        print("✅ default_config兼容性测试通过")
        return True
        
    except Exception as e:
        print(f"❌ default_config兼容性测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_analysis_config_compatibility():
    """测试ai_analysis_config兼容性"""
    print("\n🧪 测试ai_analysis_config兼容性...")
    try:
        from crypto_trading_agents.config.ai_analysis_config import (
            get_unified_llm_service_config,
            get_config_template
        )
        
        # 测试委托函数是否正常工作
        config = get_unified_llm_service_config()
        assert isinstance(config, dict), "应返回字典配置"
        
        # 测试模板函数
        template_config = get_config_template("zhipuai")
        assert isinstance(template_config, dict), "应返回字典配置"
        
        print("✅ ai_analysis_config兼容性测试通过")
        return True
        
    except Exception as e:
        print(f"❌ ai_analysis_config兼容性测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """测试环境变量读取"""
    print("\n🧪 测试环境变量读取...")
    try:
        from crypto_trading_agents.unified_config import get_unified_config
        
        # 检查智谱AI的默认API密钥是否正确设置
        config = get_unified_config()
        zhipuai_config = config.get("llm_service_config", {}).get("providers", {}).get("zhipuai", {})
        api_key = zhipuai_config.get("api_key")
        
        # 应该有API密钥（从环境变量或默认值）
        assert api_key, "智谱AI应该有API密钥"
        
        # 检查默认值是否正确设置
        expected_key = "fb0baa47a3144339ab434c8bdd7b4ee2.Rk3yCpEU0FraOnQP"
        if not os.getenv("ZHIPUAI_API_KEY"):
            assert api_key == expected_key, "应该使用默认的智谱AI API密钥"
        
        print("✅ 环境变量读取测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 环境变量读取测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始统一配置系统测试")
    print("=" * 80)
    
    # 运行所有测试
    tests = [
        test_basic_config_loading,
        test_llm_provider_selection,
        test_market_condition_presets,
        test_config_validation,
        test_default_config_compatibility,
        test_ai_analysis_config_compatibility,
        test_environment_variables,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
            failed += 1
    
    # 显示配置信息
    print("\n📋 配置信息:")
    try:
        from crypto_trading_agents.unified_config import print_config_info
        print_config_info()
    except Exception as e:
        print(f"❌ 无法显示配置信息: {str(e)}")
    
    # 测试总结
    print("\n📊 测试结果总结")
    print("=" * 80)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过! 配置整改成功!")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，需要检查配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())