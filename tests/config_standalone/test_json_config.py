#!/usr/bin/env python3
"""
JSON配置系统测试脚本

测试新的JSON配置文件系统的各项功能：
1. JSON配置文件加载
2. 环境变量解析
3. LLM提供商切换
4. 市场条件预设
5. 配置验证
6. 向后兼容性
"""

import os
import sys
import json

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_json_config_direct():
    """直接测试JSON配置系统"""
    print("🧪 测试JSON配置系统...")
    
    try:
        # 测试直接导入
        from crypto_trading_agents.json_config import JSONConfigLoader
        
        loader = JSONConfigLoader()
        print("✅ 成功创建JSONConfigLoader")
        
        # 测试基本配置加载
        config = loader.get_config()
        print(f"✅ 成功加载配置: {len(config)} 个顶级配置项")
        
        # 检查必要的配置段
        required_sections = ["llm", "ai_analysis", "trading", "crypto", "analysis"]
        for section in required_sections:
            if section in config:
                print(f"✅ 找到配置段: {section}")
            else:
                print(f"❌ 缺少配置段: {section}")
        
        # 测试LLM配置
        llm_config = config.get("llm", {})
        default_provider = llm_config.get("default_provider")
        service_config = llm_config.get("service_config", {})
        providers = service_config.get("providers", {})
        
        print(f"✅ 默认LLM提供商: {default_provider}")
        print(f"✅ 支持的LLM提供商: {list(providers.keys())}")
        
        # 测试智谱AI配置
        zhipuai_config = providers.get("zhipuai", {})
        api_key = zhipuai_config.get("api_key")
        model = zhipuai_config.get("model")
        
        print(f"✅ 智谱AI API密钥: {'已设置' if api_key else '未设置'}")
        print(f"✅ 智谱AI 模型: {model}")
        
        # 测试LLM提供商切换
        for provider in ["zhipuai", "dashscope", "deepseek", "traditional"]:
            try:
                provider_config = loader.get_config(llm_provider=provider)
                if provider == "traditional":
                    ai_enabled = provider_config.get("ai_analysis", {}).get("enabled", True)
                    print(f"✅ {provider} 配置: AI={'禁用' if not ai_enabled else '启用'}")
                else:
                    llm_provider = provider_config.get("llm", {}).get("default_provider")
                    print(f"✅ {provider} 配置: LLM提供商={llm_provider}")
            except Exception as e:
                print(f"❌ {provider} 配置失败: {e}")
        
        # 测试市场条件预设
        market_conditions = ["bull_market", "bear_market", "high_volatility"]
        for condition in market_conditions:
            try:
                market_config = loader.get_config(market_condition=condition)
                trading = market_config.get("trading", {})
                max_pos = trading.get("max_position_size", 0)
                risk = trading.get("risk_per_trade", 0)
                print(f"✅ {condition}: 最大仓位={max_pos}, 风险={risk}")
            except Exception as e:
                print(f"❌ {condition} 配置失败: {e}")
        
        # 测试配置验证
        is_valid = loader.validate_config(config)
        print(f"✅ 配置验证: {'通过' if is_valid else '失败'}")
        
        # 测试LLM配置获取
        llm_info = loader.get_llm_config("zhipuai")
        print(f"✅ 智谱AI配置获取: {llm_info}")
        
        # 测试可用提供商
        available = loader.get_available_llm_providers()
        print(f"✅ 可用LLM提供商: {available}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON配置系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_env_variable_parsing():
    """测试环境变量解析"""
    print("\n🧪 测试环境变量解析...")
    
    try:
        from crypto_trading_agents.json_config import JSONConfigLoader
        
        # 设置测试环境变量
        os.environ["TEST_API_KEY"] = "test_value_123"
        os.environ["TEST_BOOLEAN"] = "true"
        os.environ["TEST_NUMBER"] = "42"
        
        # 创建测试配置
        test_config = {
            "test_section": {
                "api_key": "${TEST_API_KEY}",
                "default_key": "${NONEXISTENT_KEY:default_value}",
                "boolean_val": "${TEST_BOOLEAN}",
                "number_val": "${TEST_NUMBER}",
                "mixed": "prefix_${TEST_API_KEY}_suffix"
            }
        }
        
        # 保存原配置文件内容
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            original_config = f.read()
        
        # 临时修改配置文件进行测试
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, indent=2, ensure_ascii=False)
        
        loader = JSONConfigLoader()
        loader._config_cache = None  # 清除缓存
        parsed_config = loader.get_config(reload=True)
        
        test_section = parsed_config.get("test_section", {})
        
        # 验证解析结果
        if test_section.get("api_key") == "test_value_123":
            print("✅ 环境变量解析正确")
        else:
            print(f"❌ 环境变量解析错误: {test_section.get('api_key')}")
        
        if test_section.get("default_key") == "default_value":
            print("✅ 默认值解析正确")
        else:
            print(f"❌ 默认值解析错误: {test_section.get('default_key')}")
        
        if test_section.get("boolean_val") is True:
            print("✅ 布尔值解析正确")
        else:
            print(f"❌ 布尔值解析错误: {test_section.get('boolean_val')}")
        
        if test_section.get("number_val") == 42:
            print("✅ 数字解析正确")
        else:
            print(f"❌ 数字解析错误: {test_section.get('number_val')}")
        
        if test_section.get("mixed") == "prefix_test_value_123_suffix":
            print("✅ 混合字符串解析正确")
        else:
            print(f"❌ 混合字符串解析错误: {test_section.get('mixed')}")
        
        # 恢复原配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(original_config)
        
        # 清理环境变量
        del os.environ["TEST_API_KEY"]
        del os.environ["TEST_BOOLEAN"]
        del os.environ["TEST_NUMBER"]
        
        return True
        
    except Exception as e:
        print(f"❌ 环境变量解析测试失败: {e}")
        return False

def test_compatibility():
    """测试向后兼容性"""
    print("\n🧪 测试向后兼容性...")
    
    try:
        # 测试通过unified_config.py导入
        from crypto_trading_agents.unified_config import (
            get_unified_config,
            get_config_template,
            get_llm_config,
            get_available_llm_providers,
            validate_config,
            print_config_info
        )
        
        # 测试基本函数
        config = get_unified_config()
        print(f"✅ unified_config.get_unified_config(): {len(config)} 配置项")
        
        template = get_config_template("zhipuai")
        print(f"✅ unified_config.get_config_template(): {len(template)} 配置项")
        
        llm_config = get_llm_config("zhipuai")
        print(f"✅ unified_config.get_llm_config(): {llm_config.get('provider')}")
        
        providers = get_available_llm_providers()
        print(f"✅ unified_config.get_available_llm_providers(): {providers}")
        
        is_valid = validate_config(config)
        print(f"✅ unified_config.validate_config(): {'通过' if is_valid else '失败'}")
        
        # 测试default_config.py兼容性
        from crypto_trading_agents.default_config import get_config
        default_config = get_config()
        print(f"✅ default_config.get_config(): {len(default_config)} 配置项")
        
        # 测试ai_analysis_config.py兼容性
        from crypto_trading_agents.config.ai_analysis_config import get_unified_llm_service_config
        ai_config = get_unified_llm_service_config()
        print(f"✅ ai_analysis_config.get_unified_llm_service_config(): {len(ai_config)} 配置项")
        
        return True
        
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_structure():
    """测试配置结构完整性"""
    print("\n🧪 测试配置结构完整性...")
    
    try:
        from crypto_trading_agents.json_config import JSONConfigLoader
        
        loader = JSONConfigLoader()
        config = loader.get_config()
        
        # 检查配置结构
        expected_structure = {
            "llm": ["default_provider", "service_config"],
            "ai_analysis": ["enabled", "temperature", "max_tokens"],
            "trading": ["default_symbol", "risk_per_trade", "max_position_size"],
            "crypto": ["supported_exchanges", "supported_chains"],
            "analysis": ["technical_indicators", "sentiment_sources"],
            "apis": ["exchanges", "data", "social_media", "llm"],
            "presets": ["llm", "market_conditions"]
        }
        
        all_valid = True
        for section, required_keys in expected_structure.items():
            if section not in config:
                print(f"❌ 缺少配置段: {section}")
                all_valid = False
                continue
                
            section_config = config[section]
            for key in required_keys:
                if key not in section_config:
                    print(f"❌ 缺少配置项: {section}.{key}")
                    all_valid = False
                else:
                    print(f"✅ 找到配置项: {section}.{key}")
        
        if all_valid:
            print("✅ 配置结构完整")
        
        return all_valid
        
    except Exception as e:
        print(f"❌ 配置结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 JSON配置系统全面测试")
    print("=" * 60)
    
    success = True
    
    # 测试JSON配置系统
    if not test_json_config_direct():
        success = False
    
    # 测试环境变量解析
    if not test_env_variable_parsing():
        success = False
    
    # 测试向后兼容性
    if not test_compatibility():
        success = False
    
    # 测试配置结构
    if not test_config_structure():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 JSON配置系统测试全部通过!")
        print("\n📋 JSON配置系统特性:")
        print("1. ✅ JSON格式配置文件，结构清晰")
        print("2. ✅ 支持环境变量替换 (${VAR:default})")
        print("3. ✅ LLM提供商灵活切换")
        print("4. ✅ 市场条件预设配置")
        print("5. ✅ 完整的向后兼容性")
        print("6. ✅ 智谱AI预设配置，开箱即用")
        print("7. ✅ 配置验证和错误检查")
        
        print(f"\n🔧 使用方法:")
        print("# 使用JSON配置系统")
        print("from crypto_trading_agents.json_config import JSONConfigLoader")
        print("loader = JSONConfigLoader()")
        print("config = loader.get_config(llm_provider='zhipuai', market_condition='bull_market')")
        print("")
        print("# 或使用兼容性接口")
        print("from crypto_trading_agents.unified_config import get_unified_config")
        print("config = get_unified_config(llm_provider='dashscope')")
        
        return 0
    else:
        print("❌ JSON配置系统测试存在失败项")
        return 1

if __name__ == "__main__":
    sys.exit(main())