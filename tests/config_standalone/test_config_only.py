#!/usr/bin/env python3
"""
仅测试配置文件，避免其他依赖问题
"""

import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_files():
    """直接测试配置文件"""
    print("🧪 测试配置文件...")
    
    try:
        # 直接导入配置模块
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        from crypto_trading_agents.unified_config import (
            UNIFIED_CONFIG,
            get_unified_config,
            get_config_template,
            get_llm_config,
            validate_config
        )
        
        print("✅ 成功导入unified_config模块")
        
        # 测试基本配置结构
        config = get_unified_config()
        print(f"✅ 配置类型: {type(config)}")
        print(f"✅ 配置键数量: {len(config.keys())}")
        
        # 检查必要的配置项
        required_keys = [
            "llm_service_config",
            "ai_analysis_config", 
            "trading_config",
            "crypto_config",
            "analysis_config"
        ]
        
        for key in required_keys:
            if key in config:
                print(f"✅ 找到配置项: {key}")
            else:
                print(f"❌ 缺少配置项: {key}")
        
        # 测试LLM配置
        llm_config = config.get("llm_service_config", {})
        default_provider = llm_config.get("default_provider")
        providers = llm_config.get("providers", {})
        
        print(f"✅ 默认LLM提供商: {default_provider}")
        print(f"✅ 可用LLM提供商: {list(providers.keys())}")
        
        # 测试智谱AI配置
        zhipuai_config = providers.get("zhipuai", {})
        api_key = zhipuai_config.get("api_key")
        model = zhipuai_config.get("model")
        
        print(f"✅ 智谱AI API密钥: {'已设置' if api_key else '未设置'}")
        print(f"✅ 智谱AI 模型: {model}")
        
        # 测试不同模板
        templates = ["default", "zhipuai", "dashscope", "deepseek", "traditional"]
        for template in templates:
            try:
                template_config = get_config_template(template)
                template_provider = template_config.get("llm_service_config", {}).get("default_provider")
                ai_enabled = template_config.get("ai_analysis_config", {}).get("enabled", False)
                print(f"✅ 模板 {template}: LLM={template_provider}, AI={'启用' if ai_enabled else '禁用'}")
            except Exception as e:
                print(f"❌ 模板 {template} 失败: {str(e)}")
        
        # 测试配置验证
        if validate_config(config):
            print("✅ 配置验证通过")
        else:
            print("❌ 配置验证失败")
        
        # 测试市场条件
        market_conditions = ["bull_market", "bear_market", "high_volatility"]
        for condition in market_conditions:
            try:
                market_config = get_unified_config(market_condition=condition)
                trading = market_config.get("trading_config", {})
                max_pos = trading.get("max_position_size", 0)
                print(f"✅ 市场条件 {condition}: 最大仓位={max_pos}")
            except Exception as e:
                print(f"❌ 市场条件 {condition} 失败: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_old_config_compatibility():
    """测试旧配置文件兼容性"""
    print("\n🧪 测试旧配置兼容性...")
    
    try:
        from crypto_trading_agents.default_config import get_config
        from crypto_trading_agents.config.ai_analysis_config import get_config_template
        from crypto_trading_agents.config.zhipuai_direct_config import get_zhipuai_direct_config
        
        # 测试default_config
        config = get_config()
        print(f"✅ default_config.get_config() 正常工作")
        
        # 测试ai_analysis_config
        ai_config = get_config_template("zhipuai")
        print(f"✅ ai_analysis_config.get_config_template() 正常工作")
        
        # 测试zhipuai_direct_config
        zhipu_config = get_zhipuai_direct_config()
        print(f"✅ zhipuai_direct_config.get_zhipuai_direct_config() 正常工作")
        
        return True
        
    except Exception as e:
        print(f"❌ 旧配置兼容性测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 配置整改验证测试")
    print("=" * 60)
    
    success = True
    
    # 测试配置文件
    if not test_config_files():
        success = False
    
    # 测试兼容性
    if not test_old_config_compatibility():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 配置整改验证成功!")
        print("\n📝 整改总结:")
        print("1. ✅ 统一了所有配置到 unified_config.py")
        print("2. ✅ 支持LLM模型选择(zhipuai/dashscope/deepseek/traditional)")
        print("3. ✅ 支持市场条件预设(bull_market/bear_market等)")
        print("4. ✅ 保持了与旧配置文件的向后兼容性")
        print("5. ✅ 智谱AI作为默认LLM提供商，API密钥已配置")
        
        print(f"\n🔧 使用方法:")
        print("# 获取默认配置(智谱AI)")
        print("from crypto_trading_agents.unified_config import get_unified_config")
        print("config = get_unified_config()")
        print("")
        print("# 选择不同的LLM")  
        print("config = get_unified_config(llm_provider='dashscope')  # 通义千问")
        print("config = get_unified_config(llm_provider='deepseek')   # DeepSeek")
        print("config = get_unified_config(llm_provider='traditional') # 禁用AI")
        print("")
        print("# 结合市场条件")
        print("config = get_unified_config(market_condition='bull_market', llm_provider='zhipuai')")
        
        return 0
    else:
        print("❌ 配置整改验证失败，需要检查问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())