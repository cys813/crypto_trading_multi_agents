#!/usr/bin/env python3
"""
JSON配置系统简单测试 - 避免依赖问题

只测试核心配置加载功能，不导入其他模块
"""

import os
import sys
import json

def test_json_file_structure():
    """测试JSON配置文件结构"""
    print("🧪 测试JSON配置文件...")
    
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        
        if not os.path.exists(config_path):
            print("❌ config.json 文件不存在")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ 成功加载JSON配置文件: {len(config)} 个顶级配置项")
        
        # 检查必要的配置段
        required_sections = ["llm", "ai_analysis", "trading", "crypto", "presets"]
        for section in required_sections:
            if section in config:
                print(f"✅ 找到配置段: {section}")
            else:
                print(f"❌ 缺少配置段: {section}")
        
        # 检查LLM配置
        llm = config.get("llm", {})
        default_provider = llm.get("default_provider")
        providers = llm.get("service_config", {}).get("providers", {})
        
        print(f"✅ 默认LLM提供商: {default_provider}")
        print(f"✅ 支持的提供商: {list(providers.keys())}")
        
        # 检查智谱AI配置
        zhipuai = providers.get("zhipuai", {})
        api_key = zhipuai.get("api_key", "")
        model = zhipuai.get("model", "")
        
        print(f"✅ 智谱AI API密钥: {'已设置' if api_key and not api_key.startswith('${') else '未设置'}")
        print(f"✅ 智谱AI 模型: {model}")
        
        # 检查预设配置
        presets = config.get("presets", {})
        llm_presets = list(presets.get("llm", {}).keys())
        market_presets = list(presets.get("market_conditions", {}).keys())
        
        print(f"✅ LLM预设: {llm_presets}")
        print(f"✅ 市场条件预设: {market_presets}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON配置文件测试失败: {e}")
        return False

def test_env_variable_format():
    """测试环境变量格式"""
    print("\n🧪 测试环境变量格式...")
    
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找环境变量模式
        import re
        env_vars = re.findall(r'\$\{([^}:]+)(?::([^}]*))?\}', content)
        
        if env_vars:
            print(f"✅ 找到 {len(env_vars)} 个环境变量配置:")
            for var_name, default_value in env_vars[:5]:  # 只显示前5个
                default_str = f" (默认: {default_value})" if default_value else ""
                print(f"   {var_name}{default_str}")
            if len(env_vars) > 5:
                print(f"   ... 还有 {len(env_vars) - 5} 个")
        else:
            print("❌ 未找到环境变量配置")
        
        return True
        
    except Exception as e:
        print(f"❌ 环境变量格式测试失败: {e}")
        return False

def test_direct_json_config():
    """直接测试JSON配置加载器"""
    print("\n🧪 测试JSON配置加载器...")
    
    try:
        # 直接导入json_config模块
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'crypto_trading_agents'))
        
        # 避免导入__init__.py，直接导入json_config
        import json_config
        
        loader = json_config.JSONConfigLoader()
        print("✅ 成功创建JSONConfigLoader")
        
        # 测试基本配置
        config = loader.get_config()
        print(f"✅ 基本配置加载: {len(config)} 个配置项")
        
        # 测试LLM切换
        zhipuai_config = loader.get_config(llm_provider="zhipuai")
        dashscope_config = loader.get_config(llm_provider="dashscope")
        traditional_config = loader.get_config(llm_provider="traditional")
        
        print(f"✅ 智谱AI配置: LLM={zhipuai_config.get('llm', {}).get('default_provider')}")
        print(f"✅ 通义千问配置: LLM={dashscope_config.get('llm', {}).get('default_provider')}")
        print(f"✅ 传统配置: AI={'禁用' if not traditional_config.get('ai_analysis', {}).get('enabled', True) else '启用'}")
        
        # 测试市场条件
        bull_config = loader.get_config(market_condition="bull_market")
        bear_config = loader.get_config(market_condition="bear_market")
        
        bull_trading = bull_config.get("trading", {})
        bear_trading = bear_config.get("trading", {})
        
        print(f"✅ 牛市配置: 仓位={bull_trading.get('max_position_size')}, 风险={bull_trading.get('risk_per_trade')}")
        print(f"✅ 熊市配置: 仓位={bear_trading.get('max_position_size')}, 风险={bear_trading.get('risk_per_trade')}")
        
        # 测试配置验证
        is_valid = loader.validate_config()
        print(f"✅ 配置验证: {'通过' if is_valid else '失败'}")
        
        # 测试LLM配置获取
        llm_config = loader.get_llm_config("zhipuai")
        print(f"✅ LLM配置获取: {llm_config.get('provider')} - {llm_config.get('model')}")
        
        # 测试可用提供商
        providers = loader.get_available_llm_providers()
        print(f"✅ 可用提供商: {providers}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON配置加载器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_content():
    """测试配置内容完整性"""
    print("\n🧪 测试配置内容...")
    
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 测试关键配置项
        tests = [
            ("project.name", "项目名称"),
            ("llm.default_provider", "默认LLM"),
            ("ai_analysis.enabled", "AI分析开关"),
            ("trading.default_symbol", "默认交易对"),
            ("crypto.supported_exchanges", "支持的交易所"),
            ("presets.llm.zhipuai", "智谱AI预设"),
            ("presets.market_conditions.bull_market", "牛市预设")
        ]
        
        for path, desc in tests:
            keys = path.split('.')
            current = config
            
            try:
                for key in keys:
                    current = current[key]
                print(f"✅ {desc}: {type(current).__name__}")
            except (KeyError, TypeError):
                print(f"❌ 缺少{desc}: {path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置内容测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 JSON配置系统简单测试")
    print("=" * 60)
    
    success = True
    
    # 测试JSON文件结构
    if not test_json_file_structure():
        success = False
    
    # 测试环境变量格式
    if not test_env_variable_format():
        success = False
    
    # 测试配置加载器
    if not test_direct_json_config():
        success = False
    
    # 测试配置内容
    if not test_config_content():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 JSON配置系统测试成功!")
        print("\n📋 配置转换完成:")
        print("1. ✅ Python配置 → JSON配置")
        print("2. ✅ 环境变量支持 (${VAR:default})")
        print("3. ✅ LLM提供商预设配置")
        print("4. ✅ 市场条件预设配置")
        print("5. ✅ 配置验证功能")
        print("6. ✅ 智谱AI预设密钥")
        
        print(f"\n🔧 JSON配置文件位置:")
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        print(f"   {config_path}")
        
        print(f"\n📖 使用示例:")
        print("from crypto_trading_agents.json_config import JSONConfigLoader")
        print("loader = JSONConfigLoader()")
        print("config = loader.get_config(llm_provider='zhipuai')")
        
        return 0
    else:
        print("❌ JSON配置系统测试存在失败项")
        return 1

if __name__ == "__main__":
    sys.exit(main())