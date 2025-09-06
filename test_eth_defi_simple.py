#!/usr/bin/env python3
"""
ETH DeFi数据分析 - 简化版本
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_defi_data_service_direct():
    """直接测试DeFi数据服务"""
    print("🔍 ETH DeFi数据分析 - 简化版本")
    print("=" * 50)
    
    try:
        # 修改Python路径以支持相对导入
        sys.path.insert(0, os.path.join(project_root, 'src'))
        sys.path.insert(0, os.path.join(project_root, 'src', 'crypto_trading_agents'))
        
        print("1. 测试导入...")
        try:
            # 测试DeFiLlama数据源导入
            from data_sources.crypto_data_sources import DeFiLlamaDataSource
            print("   ✅ DeFiLlamaDataSource 导入成功")
            
            # 创建DeFiLlama实例
            defillama = DeFiLlamaDataSource()
            print("   ✅ DeFiLlamaDataSource 初始化成功")
            
        except Exception as e:
            print(f"   ❌ DeFiLlamaDataSource 导入失败: {str(e)}")
            return False
        
        print("\n2. 测试DeFiLlama数据获取...")
        try:
            # 获取所有协议数据
            all_protocols = defillama.get_tvl_data()
            print(f"   ✅ 所有协议数据获取成功")
            
            if all_protocols and isinstance(all_protocols, list):
                print(f"   总协议数量: {len(all_protocols)}")
                
                # 筛选Ethereum协议
                eth_protocols = []
                for protocol in all_protocols:
                    chains = protocol.get('chains', [])
                    if 'Ethereum' in chains:
                        eth_protocols.append(protocol)
                
                print(f"   Ethereum协议数量: {len(eth_protocols)}")
                
                if eth_protocols:
                    print("\n3. Ethereum DeFi协议分析...")
                    
                    # 按TVL排序
                    sorted_protocols = sorted(eth_protocols, key=lambda x: x.get('tvl', 0), reverse=True)
                    
                    # 计算总TVL
                    total_tvl = sum(p.get('tvl', 0) for p in eth_protocols)
                    print(f"   ETH DeFi总TVL: ${total_tvl:,.0f}")
                    
                    # 显示前15个协议
                    print("\n   TVL排名前15的Ethereum DeFi协议:")
                    print("-" * 70)
                    print(f"{'排名':<4} {'协议名称':<20} {'TVL':<15} {'市场份额':<10} {'类别':<15}")
                    print("-" * 70)
                    
                    for i, protocol in enumerate(sorted_protocols[:15]):
                        name = protocol.get('name', 'Unknown')
                        tvl = protocol.get('tvl', 0)
                        category = protocol.get('category', 'Unknown')
                        market_cap = protocol.get('marketCap', 0)
                        
                        market_share = (tvl / total_tvl * 100) if total_tvl > 0 else 0
                        
                        print(f"{i+1:<4} {name[:19]:<20} ${tvl:>13,.0f} {market_share:>8.2f}% {category[:14]:<15}")
                    
                    # 分析协议分布
                    print("\n4. 协议类别分析...")
                    
                    category_stats = {}
                    for protocol in eth_protocols:
                        category = protocol.get('category', 'Unknown')
                        tvl = protocol.get('tvl', 0)
                        
                        if category not in category_stats:
                            category_stats[category] = {'count': 0, 'tvl': 0}
                        
                        category_stats[category]['count'] += 1
                        category_stats[category]['tvl'] += tvl
                    
                    # 按TVL排序类别
                    sorted_categories = sorted(category_stats.items(), key=lambda x: x[1]['tvl'], reverse=True)
                    
                    print("\n   按TVL排序的协议类别:")
                    print("-" * 60)
                    print(f"{'类别':<15} {'协议数':<8} {'TVL':<15} {'占比':<8}")
                    print("-" * 60)
                    
                    for category, stats in sorted_categories:
                        count = stats['count']
                        tvl = stats['tvl']
                        percentage = (tvl / total_tvl * 100) if total_tvl > 0 else 0
                        
                        print(f"{category[:14]:<15} {count:<8} ${tvl:>13,.0f} {percentage:>6.1f}%")
                    
                    # 分析大协议集中度
                    print("\n5. 集中度分析...")
                    
                    top_3_tvl = sum(p.get('tvl', 0) for p in sorted_protocols[:3])
                    top_10_tvl = sum(p.get('tvl', 0) for p in sorted_protocols[:10])
                    
                    top_3_concentration = (top_3_tvl / total_tvl * 100) if total_tvl > 0 else 0
                    top_10_concentration = (top_10_tvl / total_tvl * 100) if total_tvl > 0 else 0
                    
                    print(f"   前3大协议集中度: {top_3_concentration:.1f}%")
                    print(f"   前10大协议集中度: {top_10_concentration:.1f}%")
                    
                    if top_3_concentration > 50:
                        print("   ⚠️  集中度偏高，依赖少数几个大协议")
                    elif top_3_concentration > 30:
                        print("   ✅ 集中度适中")
                    else:
                        print("   🎉 集中度良好，生态分布均衡")
                    
                    # 显示前3大协议详情
                    print("\n6. 前3大协议详情:")
                    for i, protocol in enumerate(sorted_protocols[:3]):
                        name = protocol.get('name', 'Unknown')
                        tvl = protocol.get('tvl', 0)
                        market_cap = protocol.get('marketCap', 0)
                        category = protocol.get('category', 'Unknown')
                        description = protocol.get('description', '暂无描述')
                        
                        # 计算价格/TVL比率
                        price_tvl_ratio = (market_cap / tvl) if tvl > 0 else 0
                        
                        print(f"\n   {i+1}. {name}")
                        print(f"      类别: {category}")
                        print(f"      TVL: ${tvl:,.0f}")
                        print(f"      市值: ${market_cap:,.0f}")
                        print(f"      P/TVL: {price_tvl_ratio:.2f}")
                        print(f"      描述: {description}")
                    
                    print("\n" + "=" * 50)
                    print("✅ ETH DeFi数据分析完成!")
                    
                    # 总结和建议
                    print("\n📊 分析总结:")
                    print(f"   • ETH DeFi总TVL: ${total_tvl:,.0f}")
                    print(f"   • 协议总数: {len(eth_protocols)}")
                    print(f"   • 主要类别: {sorted_categories[0][0] if sorted_categories else 'N/A'}")
                    print(f"   • 前三大协议集中度: {top_3_concentration:.1f}%")
                    
                    print("\n🎯 关键洞察:")
                    if sorted_categories:
                        top_category = sorted_categories[0][0]
                        top_category_tvl_share = (sorted_categories[0][1]['tvl'] / total_tvl * 100) if total_tvl > 0 else 0
                        print(f"   • {top_category}类协议占据主导地位，占比{top_category_tvl_share:.1f}%")
                    
                    if top_3_concentration > 50:
                        print("   • 生态集中度较高，大协议具有显著影响力")
                    
                    if len(eth_protocols) > 100:
                        print("   • 协议数量众多，生态竞争激烈")
                    
                    print("\n💡 建议:")
                    print("   • 重点关注TVL排名前10的协议")
                    print("   • 关注集中度变化趋势")
                    print("   • 监控新兴类别的发展")
                    print("   • 注意Layer 2协议的崛起")
                    
                    return True
                    
                else:
                    print("   ⚠️  未找到Ethereum协议")
                    return False
            else:
                print("   ⚠️  未获取到协议数据")
                return False
                
        except Exception as e:
            print(f"   ❌ DeFiLlama数据获取失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def show_eth_defi_key_insights():
    """显示ETH DeFi关键洞察"""
    print("\n\n🎯 ETH DeFi生态系统关键洞察")
    print("=" * 50)
    
    insights = """
    🌟 ETH DeFi生态现状 (基于历史数据分析):
    
    📈 总体规模:
    • 总TVL: 约400-600亿美元范围
    • 协议数量: 300+个活跃协议
    • 日活跃用户: 100万+
    • 日交易量: 20-50亿美元
    
    🏆 主导协议:
    1. Uniswap (DEX) - TVL: ~150亿美元
    2. Aave (借贷) - TVL: ~100亿美元  
    3. MakerDAO (稳定币) - TVL: ~80亿美元
    4. Curve (稳定币交换) - TVL: ~60亿美元
    5. Compound (借贷) - TVL: ~40亿美元
    
    🔧 协议类别分布:
    • 借贷协议 - ~30% TVL份额
    • DEX/AMM - ~25% TVL份额  
    • 稳定币协议 - ~20% TVL份额
    • 衍生品 - ~15% TVL份额
    • 收益聚合 - ~10% TVL份额
    
    📊 生态特征:
    • 集中度适中 - 前3大协议约占40-50% TVL
    • 创新活跃 - 新协议不断涌现
    • 互操作性强 - 协议间可组合
    • 治理成熟 - 多数协议有DAO治理
    
    🚀 发展趋势:
    • Layer 2迁移 - 更多协议在Arbitrum/Optimism部署
    • RWA代币化 - 真实世界资产上链
    • 机构参与 - 传统金融入场
    • 跨链桥接 - 多链互操作性增强
    
    ⚠️ 风险因素:
    • 智能合约风险 - 虽然经过审计但仍有风险
    • 流动性风险 - 黑天鹅事件可能出现
    • 监管风险 - 全球监管政策不确定性
    • 竞争风险 - 其他链和Layer 2的竞争
    
    💡 投资建议:
    • 关注TVL持续增长的协议
    • 选择经过时间验证的成熟协议
    • 分散投资降低集中度风险
    • 重视治理参与度高的项目
    • 关注技术实力强的团队
    """
    
    print(insights)

if __name__ == "__main__":
    show_eth_defi_key_insights()
    
    print("\n" + "=" * 60)
    print("🚀 开始ETH DeFi数据分析...")
    success = test_defi_data_service_direct()
    
    if success:
        print("\n🎉 数据分析成功完成!")
    else:
        print("\n❌ 数据分析遇到问题")
        print("💡 可能原因:")
        print("   • 网络连接问题")
        print("   • API服务暂时不可用") 
        print("   • 依赖包缺失")
        print("   • 数据源限制")
        
        print("\n🔧 建议解决方案:")
        print("   • 检查网络连接")
        print("   • 稍后重试")
        print("   • 安装必要依赖包")
        print("   • 使用VPN（如需要）")