#!/usr/bin/env python3
"""
完整的Solana链上数据分析报告（传统分析 vs AI增强分析）
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def generate_complete_analysis_report():
    """生成完整的Solana链上数据分析报告"""
    print("📊 生成完整的Solana链上数据分析报告")
    print("=" * 60)
    
    try:
        # 导入相关模块
        from src.crypto_trading_agents.services.onchain_data.onchain_data_service import OnchainDataService
        from src.crypto_trading_agents.services.llm_service import initialize_llm_service, call_llm_analysis
        from src.crypto_trading_agents.unified_config import get_unified_config
        
        # 获取配置
        config = get_unified_config()
        
        print("1. 初始化服务...")
        # 初始化LLM服务
        llm_config = config.get('llm', {})
        init_result = initialize_llm_service(llm_config)
        llm_available = init_result
        
        if llm_available:
            print("   ✅ LLM服务初始化成功")
        else:
            print("   ⚠️  LLM服务初始化失败，将只进行传统分析")
        
        # 初始化链上数据服务
        onchain_service = OnchainDataService(config)
        print("   ✅ 链上数据服务初始化成功")
        
        print("\n2. 获取Solana链上数据...")
        # 获取网络健康数据
        network_health = onchain_service.get_network_health("SOL", "solana", "2025-08-08")
        print(f"   网络健康数据获取完成")
        
        # 获取活跃账户数据
        active_accounts = onchain_service.get_active_addresses("SOL", "solana", "2025-08-08")
        print(f"   活跃账户数据获取完成")
        
        # 获取交易指标数据
        transaction_metrics = onchain_service.get_transaction_metrics("SOL", "solana", "2025-08-08")
        print(f"   交易指标数据获取完成")
        
        print("\n3. 生成传统分析报告...")
        # 从Solana数据中提取关键指标
        solana_data_nh = network_health.get("solana_data", {})
        solana_data_aa = active_accounts.get("solana_data", {})
        solana_data_tm = transaction_metrics.get("solana_data", {})
        
        # 计算TPS（使用性能样本数据）
        tps = "N/A"
        confirmation_time = "N/A"
        performance_samples = solana_data_nh.get("performance_samples", [])
        if performance_samples:
            # 使用第一个样本计算TPS
            sample = performance_samples[0]
            num_transactions = sample.get("numTransactions", 0)
            sample_period_secs = sample.get("samplePeriodSecs", 1)
            if sample_period_secs > 0:
                tps = round(num_transactions / sample_period_secs, 2)
            
            # 计算确认时间（假设每个slot约0.4秒）
            num_slots = sample.get("numSlots", 1)
            if num_slots > 0:
                confirmation_time = round((sample_period_secs / num_slots) * 1000, 2)  # 毫秒
        
        # 传统分析报告
        traditional_report = {
            "timestamp": datetime.now().isoformat(),
            "currency": "SOL",
            "chain": "solana",
            "traditional_analysis": {
                "network_health": {
                    "tps": tps,
                    "confirmation_time_ms": confirmation_time,
                    "epoch": solana_data_nh.get("epoch_info", {}).get("epoch", "N/A"),
                    "epoch_progress": f"{solana_data_nh.get('epoch_info', {}).get('slotIndex', 'N/A')}/{solana_data_nh.get('epoch_info', {}).get('slotsInEpoch', 'N/A')}",
                    "total_transactions": solana_data_nh.get("transaction_count", "N/A")
                },
                "user_activity": {
                    "daily_active_users": solana_data_aa.get("daily_active", "N/A"),
                    "weekly_active_users": solana_data_aa.get("weekly_active", "N/A"),
                    "monthly_active_users": solana_data_aa.get("monthly_active", "N/A"),
                    "user_growth_7d": f"{solana_data_aa.get('growth_rate_7d', 'N/A')*100:.1f}%" if solana_data_aa.get('growth_rate_7d') != "N/A" else "N/A",
                    "user_growth_30d": f"{solana_data_aa.get('growth_rate_30d', 'N/A')*100:.1f}%" if solana_data_aa.get('growth_rate_30d') != "N/A" else "N/A"
                },
                "transaction_metrics": {
                    "total_transactions": solana_data_nh.get("transaction_count", "N/A"),
                    "avg_transaction_fee": "N/A",  # 模拟数据中未提供
                    "program_calls": "N/A"  # 模拟数据中未提供
                }
            }
        }
        
        print("   ✅ 传统分析报告生成完成")
        
        ai_analysis_result = None
        if llm_available:
            print("\n4. 生成AI增强分析...")
            
            # 构建分析提示词
            analysis_prompt = f"""
作为区块链分析专家，请基于以下Solana链上数据进行综合分析：

## 网络健康数据
{json.dumps(network_health, indent=2, ensure_ascii=False)}

## 活跃账户数据
{json.dumps(active_accounts, indent=2, ensure_ascii=False)}

## 交易指标数据  
{json.dumps(transaction_metrics, indent=2, ensure_ascii=False)}

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
                
                # 尝试解析JSON响应
                try:
                    ai_analysis_result = json.loads(ai_analysis)
                    print("   ✅ AI响应解析成功")
                except json.JSONDecodeError:
                    print("   ⚠️  AI响应不是标准JSON格式")
                    ai_analysis_result = {"raw_response": ai_analysis}
                    
            except Exception as e:
                print(f"   ❌ AI增强分析失败: {str(e)}")
        else:
            print("\n4. 跳过AI增强分析（LLM服务不可用）")
        
        print("\n5. 生成完整报告...")
        # 生成完整报告
        complete_report = {
            **traditional_report,
            "ai_enhanced_analysis": ai_analysis_result
        }
        
        # 保存报告到文件
        report_file = "solana_analysis_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(complete_report, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ 完整报告已保存到 {report_file}")
        
        # 打印报告摘要
        print("\n📊 报告摘要:")
        print("-" * 40)
        print(f"分析时间: {complete_report['timestamp']}")
        print(f"分析币种: {complete_report['currency']}")
        print(f"分析链: {complete_report['chain']}")
        print(f"AI增强分析: {'✅ 可用' if llm_available else '❌ 不可用'}")
        
        # 打印传统分析关键指标
        traditional = complete_report['traditional_analysis']
        print(f"\n📈 传统分析关键指标:")
        print(f"  TPS: {traditional['network_health']['tps']}")
        print(f"  确认时间(毫秒): {traditional['network_health']['confirmation_time_ms']}")
        print(f"  当前Epoch: {traditional['network_health']['epoch']}")
        print(f"  Epoch进度: {traditional['network_health']['epoch_progress']}")
        print(f"  日活跃用户: {traditional['user_activity']['daily_active_users']:,}")
        print(f"  周活跃用户: {traditional['user_activity']['weekly_active_users']:,}")
        print(f"  月活跃用户: {traditional['user_activity']['monthly_active_users']:,}")
        print(f"  7日用户增长率: {traditional['user_activity']['user_growth_7d']}")
        print(f"  30日用户增长率: {traditional['user_activity']['user_growth_30d']}")
        print(f"  总交易数: {traditional['transaction_metrics']['total_transactions']:,}")
        
        if ai_analysis_result:
            print(f"\n🤖 AI增强分析摘要:")
            if "network_status" in ai_analysis_result:
                print(f"  网络状态评级: {ai_analysis_result['network_status']}")
            if "tps_analysis" in ai_analysis_result:
                tps_analysis = ai_analysis_result['tps_analysis']
                print(f"  TPS分析: {tps_analysis[:100]}..." if len(tps_analysis) > 100 else f"  TPS分析: {tps_analysis}")
            if "user_activity" in ai_analysis_result:
                user_activity = ai_analysis_result['user_activity']
                print(f"  用户活跃度: {user_activity[:100]}..." if len(user_activity) > 100 else f"  用户活跃度: {user_activity}")
            if "short_term_prediction" in ai_analysis_result:
                print(f"  短期预测: {ai_analysis_result['short_term_prediction']}")
            if "investment_recommendation" in ai_analysis_result:
                recommendation = ai_analysis_result['investment_recommendation']
                print(f"  投资建议: {recommendation[:100]}..." if len(recommendation) > 100 else f"  投资建议: {recommendation}")
        
        print(f"\n🎉 完整的Solana链上数据分析报告生成完成")
        print(f"   报告文件: {report_file}")
        
    except Exception as e:
        print(f"生成完整分析报告时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_complete_analysis_report()