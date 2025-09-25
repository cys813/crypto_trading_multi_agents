#!/usr/bin/env python3
"""
测试Solana链上数据AI增强分析
"""

import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_solana_ai_analysis():
    """测试Solana链上数据AI增强分析"""
    print("🔍 测试Solana链上数据AI增强分析")
    print("=" * 50)
    
    try:
        # 导入相关模块
        from src.crypto_trading_agents.services.onchain_data.onchain_data_service import OnchainDataService
        from src.crypto_trading_agents.services.llm_service import initialize_llm_service, call_llm_analysis
        from src.crypto_trading_agents.unified_config import get_unified_config
        
        # 获取配置
        config = get_unified_config()
        
        print("1. 初始化LLM服务...")
        llm_config = config.get('llm', {})
        init_result = initialize_llm_service(llm_config)
        
        if init_result:
            print("   ✅ LLM服务初始化成功")
        else:
            print("   ❌ LLM服务初始化失败")
            return
        
        print("\n2. 初始化链上数据服务...")
        onchain_service = OnchainDataService(config)
        print("   ✅ 链上数据服务初始化成功")
        
        print("\n3. 获取Solana链上数据...")
        # 获取网络健康数据
        network_health = onchain_service.get_network_health("SOL", "solana", "2025-08-08")
        print(f"   网络健康数据: {list(network_health.keys())}")
        
        # 获取活跃账户数据
        active_accounts = onchain_service.get_active_addresses("SOL", "solana", "2025-08-08")
        print(f"   活跃账户数据: {list(active_accounts.keys())}")
        
        # 获取交易指标数据
        transaction_metrics = onchain_service.get_transaction_metrics("SOL", "solana", "2025-08-08")
        print(f"   交易指标数据: {list(transaction_metrics.keys())}")
        
        print("\n4. 生成AI增强分析...")
        
        # 构建分析提示词
        analysis_prompt = f"""
作为区块链分析专家，请基于以下Solana链上数据进行综合分析：

## 网络健康数据
{network_health}

## 活跃账户数据
{active_accounts}

## 交易指标数据  
{transaction_metrics}

请从以下几个维度进行分析：

1. **网络状态评估**
   - TPS表现和网络健康状况
   - 确认时间和网络效率
   - 验证者参与度和质押情况

2. **用户活跃度分析**
   - 活跃账户增长趋势
   - 用户参与度变化
   - 网络采用情况

3. **交易行为洞察**
   - 交易费用趋势
   - 交易成功率
   - 程序调用活跃度

4. **投资建议**
   - 当前网络健康状况评级（优秀/良好/一般/较差）
   - 短期（7天）价格走势预测
   - 中期（30天）发展趋势判断
   - 风险提示和关注要点

请以JSON格式返回分析结果，包含以下字段：
{{
  "network_status": "网络状态评级",
  "tps_analysis": "TPS分析",
  "user_activity": "用户活跃度分析", 
  "transaction_insights": "交易行为洞察",
  "short_term_prediction": "短期预测",
  "medium_term_outlook": "中期展望",
  "risk_factors": "风险因素",
  "investment_recommendation": "投资建议"
}}
"""
        
        try:
            ai_analysis = call_llm_analysis(
                prompt=analysis_prompt,
                temperature=0.1,
                max_tokens=2000
            )
            
            print("   ✅ AI增强分析生成成功")
            print(f"   分析结果（前500字符）: {ai_analysis[:500]}...")
            
            # 尝试解析JSON响应
            import json
            try:
                parsed_result = json.loads(ai_analysis)
                print(f"\n   📊 解析后的分析结果:")
                for key, value in parsed_result.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"     {key}: {value[:100]}...")
                    else:
                        print(f"     {key}: {value}")
            except json.JSONDecodeError:
                print("   ⚠️  AI响应不是标准JSON格式，显示原始内容")
                
        except Exception as e:
            print(f"   ❌ AI增强分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n5. 分析完成")
        print("   🎉 Solana链上数据AI增强分析测试完成")
        
    except Exception as e:
        print(f"测试Solana AI分析时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_solana_ai_analysis()