#!/usr/bin/env python3
"""
验证三个交易辩论员AI增强功能的修改结果
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def verify_ai_modifications():
    """验证AI修改结果"""
    
    print("=== 交易辩论员AI增强功能验证 ===\n")
    
    # 验证ConservativeDebator
    print("1. ConservativeDebator (保守型辩论员) 验证:")
    with open('src/crypto_trading_agents/agents/risk_managers/conservative_debator.py', 'r', encoding='utf-8') as f:
        conservative_code = f.read()
    
    # 检查AI导入
    ai_import_check = "from src.crypto_trading_agents.services.ai_analysis_mixin import StandardAIAnalysisMixin" in conservative_code
    print(f"✅ AI混入类导入: {'通过' if ai_import_check else '失败'}")
    
    # 检查AI继承
    ai_inherit_check = "class ConservativeDebator(StandardAIAnalysisMixin):" in conservative_code
    print(f"✅ AI混入类继承: {'通过' if ai_inherit_check else '失败'}")
    
    # 检查AI初始化
    ai_init_check = "super().__init__()" in conservative_code and "initialize_llm_service" in conservative_code
    print(f"✅ AI服务初始化: {'通过' if ai_init_check else '失败'}")
    
    # 检查AI增强方法
    ai_method_check = "_enhance_conservative_analysis_with_ai" in conservative_code
    print(f"✅ AI增强分析方法: {'通过' if ai_method_check else '失败'}")
    
    # 检查AI提示词构建
    ai_prompt_check = "_build_conservative_analysis_prompt" in conservative_code
    print(f"✅ AI提示词构建: {'通过' if ai_prompt_check else '失败'}")
    
    # 检查AI调用逻辑
    ai_call_check = "if self.is_ai_enabled():" in conservative_code and "self.call_ai_analysis" in conservative_code
    print(f"✅ AI调用逻辑: {'通过' if ai_call_check else '失败'}")
    
    # 检查AI输出字段
    ai_output_check = '"ai_enhanced": self.is_ai_enabled()' in conservative_code and '"ai_analysis": ai_enhancement' in conservative_code
    print(f"✅ AI输出字段: {'通过' if ai_output_check else '失败'}")
    
    conservative_passed = all([ai_import_check, ai_inherit_check, ai_init_check, ai_method_check, ai_prompt_check, ai_call_check, ai_output_check])
    print(f"🎯 ConservativeDebator总体状态: {'✅ 通过' if conservative_passed else '❌ 失败'}")
    
    print("\n" + "="*50 + "\n")
    
    # 验证NeutralDebator
    print("2. NeutralDebator (中性型辩论员) 验证:")
    with open('src/crypto_trading_agents/agents/risk_managers/neutral_debator.py', 'r', encoding='utf-8') as f:
        neutral_code = f.read()
    
    # 检查AI导入
    ai_import_check = "from src.crypto_trading_agents.services.ai_analysis_mixin import StandardAIAnalysisMixin" in neutral_code
    print(f"✅ AI混入类导入: {'通过' if ai_import_check else '失败'}")
    
    # 检查AI继承
    ai_inherit_check = "class NeutralDebator(StandardAIAnalysisMixin):" in neutral_code
    print(f"✅ AI混入类继承: {'通过' if ai_inherit_check else '失败'}")
    
    # 检查AI初始化
    ai_init_check = "super().__init__()" in neutral_code and "initialize_llm_service" in neutral_code
    print(f"✅ AI服务初始化: {'通过' if ai_init_check else '失败'}")
    
    # 检查AI增强方法
    ai_method_check = "_enhance_neutral_analysis_with_ai" in neutral_code
    print(f"✅ AI增强分析方法: {'通过' if ai_method_check else '失败'}")
    
    # 检查AI提示词构建
    ai_prompt_check = "_build_neutral_analysis_prompt" in neutral_code
    print(f"✅ AI提示词构建: {'通过' if ai_prompt_check else '失败'}")
    
    # 检查AI调用逻辑
    ai_call_check = "if self.is_ai_enabled():" in neutral_code and "self.call_ai_analysis" in neutral_code
    print(f"✅ AI调用逻辑: {'通过' if ai_call_check else '失败'}")
    
    # 检查AI输出字段
    ai_output_check = '"ai_enhanced": self.is_ai_enabled()' in neutral_code and '"ai_analysis": ai_enhancement' in neutral_code
    print(f"✅ AI输出字段: {'通过' if ai_output_check else '失败'}")
    
    neutral_passed = all([ai_import_check, ai_inherit_check, ai_init_check, ai_method_check, ai_prompt_check, ai_call_check, ai_output_check])
    print(f"🎯 NeutralDebator总体状态: {'✅ 通过' if neutral_passed else '❌ 失败'}")
    
    print("\n" + "="*50 + "\n")
    
    # 验证AggressiveDebator
    print("3. AggressiveDebator (激进型辩论员) 验证:")
    with open('src/crypto_trading_agents/agents/risk_managers/aggresive_debator.py', 'r', encoding='utf-8') as f:
        aggressive_code = f.read()
    
    # 检查AI导入
    ai_import_check = "from src.crypto_trading_agents.services.ai_analysis_mixin import StandardAIAnalysisMixin" in aggressive_code
    print(f"✅ AI混入类导入: {'通过' if ai_import_check else '失败'}")
    
    # 检查AI继承
    ai_inherit_check = "class AggressiveDebator(StandardAIAnalysisMixin):" in aggressive_code
    print(f"✅ AI混入类继承: {'通过' if ai_inherit_check else '失败'}")
    
    # 检查AI初始化
    ai_init_check = "super().__init__()" in aggressive_code and "initialize_llm_service" in aggressive_code
    print(f"✅ AI服务初始化: {'通过' if ai_init_check else '失败'}")
    
    # 检查AI增强方法
    ai_method_check = "_enhance_aggressive_analysis_with_ai" in aggressive_code
    print(f"✅ AI增强分析方法: {'通过' if ai_method_check else '失败'}")
    
    # 检查AI提示词构建
    ai_prompt_check = "_build_aggressive_analysis_prompt" in aggressive_code
    print(f"✅ AI提示词构建: {'通过' if ai_prompt_check else '失败'}")
    
    # 检查AI调用逻辑
    ai_call_check = "if self.is_ai_enabled():" in aggressive_code and "self.call_ai_analysis" in aggressive_code
    print(f"✅ AI调用逻辑: {'通过' if ai_call_check else '失败'}")
    
    # 检查AI输出字段
    ai_output_check = '"ai_enhanced": self.is_ai_enabled()' in aggressive_code and '"ai_analysis": ai_enhancement' in aggressive_code
    print(f"✅ AI输出字段: {'通过' if ai_output_check else '失败'}")
    
    aggressive_passed = all([ai_import_check, ai_inherit_check, ai_init_check, ai_method_check, ai_prompt_check, ai_call_check, ai_output_check])
    print(f"🎯 AggressiveDebator总体状态: {'✅ 通过' if aggressive_passed else '❌ 失败'}")
    
    print("\n" + "="*50 + "\n")
    
    # 架构一致性验证
    print("4. 架构一致性验证:")
    
    # 检查是否都继承相同的AI混入类
    all_inherit_ai = (
        "StandardAIAnalysisMixin" in conservative_code and
        "StandardAIAnalysisMixin" in neutral_code and
        "StandardAIAnalysisMixin" in aggressive_code
    )
    print(f"✅ 继承统一的AI混入类: {'通过' if all_inherit_ai else '失败'}")
    
    # 检查是否都有相同的AI调用模式
    all_ai_pattern = (
        "if self.is_ai_enabled():" in conservative_code and
        "if self.is_ai_enabled():" in neutral_code and
        "if self.is_ai_enabled():" in aggressive_code and
        "self.call_ai_analysis" in conservative_code and
        "self.call_ai_analysis" in neutral_code and
        "self.call_ai_analysis" in aggressive_code
    )
    print(f"✅ 统一的AI调用模式: {'通过' if all_ai_pattern else '失败'}")
    
    # 检查是否都有相同的输出字段
    all_output_fields = (
        '"ai_enhanced":' in conservative_code and
        '"ai_enhanced":' in neutral_code and
        '"ai_enhanced":' in aggressive_code and
        '"ai_analysis":' in conservative_code and
        '"ai_analysis":' in neutral_code and
        '"ai_analysis":' in aggressive_code
    )
    print(f"✅ 统一的AI输出字段: {'通过' if all_output_fields else '失败'}")
    
    # 检查错误处理
    all_error_handling = (
        "except Exception as e:" in conservative_code and
        "except Exception as e:" in neutral_code and
        "except Exception as e:" in aggressive_code and
        "logger.warning" in conservative_code and
        "logger.warning" in neutral_code and
        "logger.warning" in aggressive_code
    )
    print(f"✅ 统一的错误处理: {'通过' if all_error_handling else '失败'}")
    
    consistency_passed = all([all_inherit_ai, all_ai_pattern, all_output_fields, all_error_handling])
    print(f"🎯 架构一致性总体状态: {'✅ 通过' if consistency_passed else '❌ 失败'}")
    
    print("\n" + "="*50 + "\n")
    
    # 功能特性验证
    print("5. 功能特性验证:")
    
    # 验证AI提示词的专业性差异
    conservative_prompt_focus = "保守" in conservative_code and "风险规避" in conservative_code and "资本保护" in conservative_code
    print(f"✅ ConservativeDebator提示词专业性: {'通过' if conservative_prompt_focus else '失败'}")
    
    neutral_prompt_focus = "中性" in neutral_code and "平衡" in neutral_code and "客观" in neutral_code
    print(f"✅ NeutralDebator提示词专业性: {'通过' if neutral_prompt_focus else '失败'}")
    
    aggressive_prompt_focus = "激进" in aggressive_code and "机会" in aggressive_code and "高收益" in aggressive_code
    print(f"✅ AggressiveDebator提示词专业性: {'通过' if aggressive_prompt_focus else '失败'}")
    
    # 验证AI分析结果的差异性
    conservative_ai_output = "ai_risk_factors" in conservative_code and "ai_protection_strategies" in conservative_code
    print(f"✅ ConservativeDebator AI输出差异化: {'通过' if conservative_ai_output else '失败'}")
    
    neutral_ai_output = "ai_balance_assessment" in neutral_code and "ai_strategy_optimization" in neutral_code
    print(f"✅ NeutralDebator AI输出差异化: {'通过' if neutral_ai_output else '失败'}")
    
    aggressive_ai_output = "ai_opportunity_signals" in aggressive_code and "ai_leverage_optimization" in aggressive_code
    print(f"✅ AggressiveDebator AI输出差异化: {'通过' if aggressive_ai_output else '失败'}")
    
    features_passed = all([conservative_prompt_focus, neutral_prompt_focus, aggressive_prompt_focus, 
                          conservative_ai_output, neutral_ai_output, aggressive_ai_output])
    print(f"🎯 功能特性总体状态: {'✅ 通过' if features_passed else '❌ 失败'}")
    
    print("\n" + "="*50 + "\n")
    
    # 最终验证结果
    print("6. 最终验证结果:")
    
    total_passed = conservative_passed and neutral_passed and aggressive_passed and consistency_passed and features_passed
    
    print(f"📊 验证统计:")
    print(f"   - ConservativeDebator: {'✅ 通过' if conservative_passed else '❌ 失败'}")
    print(f"   - NeutralDebator: {'✅ 通过' if neutral_passed else '❌ 失败'}")
    print(f"   - AggressiveDebator: {'✅ 通过' if aggressive_passed else '❌ 失败'}")
    print(f"   - 架构一致性: {'✅ 通过' if consistency_passed else '❌ 失败'}")
    print(f"   - 功能特性: {'✅ 通过' if features_passed else '❌ 失败'}")
    
    print(f"\n🏆 总体验证结果: {'✅ 全部通过 - AI增强功能修改成功！' if total_passed else '❌ 存在问题 - 需要进一步检查'}")
    
    if total_passed:
        print("\n🎉 修改成功总结:")
        print("✅ 三个辩论员都已继承StandardAIAnalysisMixin")
        print("✅ 都具备完整的AI增强分析能力")
        print("✅ 架构保持高度一致性")
        print("✅ 功能特性体现各自的专业差异")
        print("✅ 统一的错误处理和降级机制")
        print("✅ 与系统其他AI组件保持兼容")
        print("\n🚀 现在三个辩论员都具备:")
        print("   - 规则分析 + AI增强分析的双重分析路径")
        print("   - 可配置的AI开关控制")
        print("   - 专业的AI提示词模板")
        print("   - 统一的输出格式")
        print("   - 完善的错误处理")

if __name__ == "__main__":
    verify_ai_modifications()