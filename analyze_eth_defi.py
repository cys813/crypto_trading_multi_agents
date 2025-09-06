#!/usr/bin/env python3
"""
ETH DeFi链上数据分析
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def analyze_eth_defi_data():
    """分析ETH DeFi数据"""
    print("🔍 ETH DeFi链上数据分析")
    print("=" * 60)
    
    try:
        # 直接导入DeFi数据服务
        sys.path.insert(0, os.path.join(project_root, 'src', 'crypto_trading_agents', 'services', 'onchain_data'))
        
        from defi_data_service import DeFiDataService
        
        # 创建配置（不需要API密钥进行基础测试）
        config = {
            "apis": {
                "data": {
                    "onchain_data": {
                        "glassnode": {
                            "enabled": False
                        }
                    }
                }
            }
        }
        
        # 初始化DeFi数据服务
        defi_service = DeFiDataService(config)
        print("✅ DeFi数据服务初始化成功")
        
        # 检查ETH是否支持DeFi分析
        print("\n1. ETH DeFi支持检查...")
        is_supported = defi_service.is_defi_supported("ETH")
        print(f"   ETH支持DeFi分析: {'✅ 是' if is_supported else '❌ 否'}")
        
        if not is_supported:
            print("❌ ETH不支持DeFi分析，无法继续")
            return
        
        print(f"   ETH对应链: {defi_service.DEFILLAMA_SUPPORTED_ASSETS.get('ETH', 'unknown')}")
        
        # 获取协议数据
        print("\n2. ETH DeFi协议数据分析...")
        protocol_data = defi_service.get_protocol_data("ETH")
        print(f"   协议数量: {len(protocol_data)}")
        
        if protocol_data:
            print("\n   主要协议TVL排名:")
            # 按TVL排序
            sorted_protocols = sorted(protocol_data.items(), key=lambda x: x[1].get('tvl', 0), reverse=True)
            
            total_tvl = sum(data.get('tvl', 0) for data in protocol_data.values())
            print(f"   总TVL: ${total_tvl:,.0f}")
            
            for i, (protocol, data) in enumerate(sorted_protocols[:10]):  # 显示前10个
                tvl = data.get('tvl', 0)
                tvl_change = data.get('tvl_change_24h', 0) * 100
                users = data.get('users', 0)
                revenue_24h = data.get('revenue_24h', 0)
                
                print(f"   {i+1:2d}. {protocol.upper():12s} TVL: ${tvl:>12,.0f} 24h: {tvl_change:>6.1f}% "
                      f"用户: {users:>8,} 收入: ${revenue_24h:>10,.0f}")
            
            # 分析协议分布
            print("\n   协议分布分析:")
            protocol_count_by_tvl = {
                "TVL > $10B": len([p for p in protocol_data.values() if p.get('tvl', 0) > 10e9]),
                "TVL $1B-$10B": len([p for p in protocol_data.values() if 1e9 < p.get('tvl', 0) <= 10e9]),
                "TVL $100M-$1B": len([p for p in protocol_data.values() if 100e6 < p.get('tvl', 0) <= 1e9]),
                "TVL < $100M": len([p for p in protocol_data.values() if p.get('tvl', 0) <= 100e6])
            }
            
            for category, count in protocol_count_by_tvl.items():
                percentage = count / len(protocol_data) * 100
                print(f"      {category}: {count}个协议 ({percentage:.1f}%)")
        else:
            print("   ⚠️  未获取到协议数据")
        
        # 获取流动性池数据
        print("\n3. ETH流动性池数据分析...")
        liquidity_data = defi_service.get_liquidity_pools_data("ETH")
        pools = liquidity_data.get('pools', [])
        
        if pools:
            total_pool_tvl = liquidity_data.get('total_pool_tvl', 0)
            avg_apy = liquidity_data.get('average_apy', 0)
            
            print(f"   流动性池总数: {len(pools)}")
            print(f"   总池TVL: ${total_pool_tvl:,.0f}")
            print(f"   平均APY: {avg_apy*100:.2f}%")
            
            # 按TVL排序显示前5个池
            print("\n   前五大流动性池:")
            sorted_pools = sorted(pools, key=lambda x: x.get('tvl', 0), reverse=True)
            
            for i, pool in enumerate(sorted_pools[:5]):
                pair = pool.get('pair', 'Unknown')
                tvl = pool.get('tvl', 0)
                volume = pool.get('volume_24h', 0)
                apy = pool.get('apy', 0)
                utilization = pool.get('liquidity_utilization', 0)
                
                print(f"   {i+1}. {pair:15s} TVL: ${tvl:>10,.0f} "
                      f"交易量: ${volume:>10,.0f} APY: {apy*100:5.1f}% "
                      f"利用率: {utilization*100:5.1f}%")
        else:
            print("   ⚠️  未获取到流动性池数据")
        
        # 获取收益挖矿数据
        print("\n4. ETH收益挖矿数据分析...")
        yield_data = defi_service.get_yield_farming_data("ETH")
        farms = yield_data.get('farms', [])
        
        if farms:
            total_farm_tvl = yield_data.get('total_farm_tvl', 0)
            avg_apy = yield_data.get('average_apy', 0)
            highest_apy = yield_data.get('highest_apy', 0)
            lowest_apy = yield_data.get('lowest_apy', 0)
            
            print(f"   挖矿农场总数: {len(farms)}")
            print(f"   总TVL: ${total_farm_tvl:,.0f}")
            print(f"   平均APY: {avg_apy*100:.2f}%")
            print(f"   最高APY: {highest_apy*100:.2f}%")
            print(f"   最低APY: {lowest_apy*100:.2f}%")
            
            # 按APY排序显示前3个农场
            print("\n   收益率最高的农场:")
            sorted_farms = sorted(farms, key=lambda x: x.get('apy', 0), reverse=True)
            
            for i, farm in enumerate(sorted_farms[:3]):
                farm_type = farm.get('type', 'Unknown')
                tvl = farm.get('total_tvl', 0)
                apy = farm.get('apy', 0)
                risk = farm.get('risk_level', 'Unknown')
                lock_period = farm.get('lock_period', 0)
                
                print(f"   {i+1}. {farm_type:12s} APY: {apy*100:6.1f}% "
                      f"TVL: ${tvl:>10,.0f} 风险: {risk:6s} "
                      f"锁期: {lock_period}天")
            
            # 风险分布分析
            risk_distribution = {}
            for farm in farms:
                risk = farm.get('risk_level', 'unknown')
                risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
            
            print("\n   风险等级分布:")
            for risk, count in sorted(risk_distribution.items()):
                percentage = count / len(farms) * 100
                print(f"      {risk}: {count}个农场 ({percentage:.1f}%)")
        else:
            print("   ⚠️  未获取到收益挖矿数据")
        
        # 获取治理数据
        print("\n5. ETH治理数据分析...")
        governance_data = defi_service.get_governance_data("ETH")
        
        if governance_data:
            token_holders = governance_data.get('token_holders', 0)
            active_voters = governance_data.get('active_voters', 0)
            voter_participation = governance_data.get('voter_participation', 0) * 100
            proposals_30d = governance_data.get('proposals_30d', 0)
            success_rate = governance_data.get('proposal_success_rate', 0) * 100
            governance_tvl = governance_data.get('governance_tvl', 0)
            voter_concentration = governance_data.get('voter_concentration', 0) * 100
            
            print(f"   代币持有者: {token_holders:,}")
            print(f"   活跃投票者: {active_voters:,}")
            print(f"   投票参与率: {voter_participation:.2f}%")
            print(f"   30天提案数: {proposals_30d}")
            print(f"   提案成功率: {success_rate:.2f}%")
            print(f"   治理TVL: ${governance_tvl:,.0f}")
            print(f"   投票者集中度: {voter_concentration:.2f}%")
            
            # 治理健康度评估
            governance_health = governance_data.get('governance_health', 'unknown')
            print(f"   治理健康度: {governance_health}")
            
            # 治理参与度评估
            if voter_participation > 20:
                participation_level = "非常高"
            elif voter_participation > 10:
                participation_level = "高"
            elif voter_participation > 5:
                participation_level = "中等"
            else:
                participation_level = "低"
            print(f"   参与度水平: {participation_level}")
        else:
            print("   ⚠️  未获取到治理数据")
        
        # 获取聚合器数据
        print("\n6. ETH聚合器数据分析...")
        aggregator_data = defi_service.get_aggregator_data("ETH")
        
        if aggregator_data:
            aggregators = ['1inch', 'matcha', 'paraSwap']
            total_volume = 0
            
            print("   主要聚合器24小时数据:")
            for agg in aggregators:
                if agg in aggregator_data:
                    data = aggregator_data[agg]
                    volume = data.get('volume_24h', 0)
                    trades = data.get('trades_24h', 0)
                    slippage = data.get('avg_slippage', 0) * 100
                    gas_savings = data.get('gas_savings', 0) * 100
                    market_share = data.get('market_share', 0) * 100
                    
                    total_volume += volume
                    print(f"   {agg.upper():10s} 交易量: ${volume:>12,.0f} "
                          f"交易数: {trades:>8,} 滑点: {slippage:5.3f}% "
                          f"Gas节省: {gas_savings:6.1f}% 市占: {market_share:5.1f}%")
            
            print(f"\n   总交易量: ${total_volume:,.0f}")
            
        else:
            print("   ⚠️  未获取到聚合器数据")
        
        # 综合分析
        print("\n7. ETH DeFi生态综合分析...")
        
        # 计算整体TVL
        if protocol_data:
            total_protocol_tvl = sum(data.get('tvl', 0) for data in protocol_data.values())
            print(f"   ETH DeFi总TVL: ${total_protocol_tvl:,.0f}")
        
        # 生态健康度评估
        health_score = 0
        if protocol_data:
            # 协议多样性
            health_score += min(len(protocol_data) / 20, 1.0) * 0.3
            
            # TVL增长
            avg_tvl_change = sum(data.get('tvl_change_24h', 0) for data in protocol_data.values()) / len(protocol_data)
            if avg_tvl_change > 0.05:
                health_score += 0.3
            elif avg_tvl_change > 0:
                health_score += 0.1
            
            # 流动性健康度
            if pools and len(pools) > 5:
                health_score += 0.2
            
            # 收益合理性
            if farms:
                avg_apy = yield_data.get('average_apy', 0)
                if 0.01 <= avg_apy <= 0.3:  # 1%-30%认为是合理的
                    health_score += 0.2
        
        print(f"   生态健康度评分: {health_score:.2f}/1.0")
        
        if health_score > 0.8:
            health_status = "非常健康"
        elif health_score > 0.6:
            health_status = "健康"
        elif health_score > 0.4:
            health_status = "一般"
        else:
            health_status = "需要关注"
        
        print(f"   生态状态: {health_status}")
        
        # 主要风险
        print("\n   主要风险因素:")
        if protocol_data:
            high_concentration_protocols = [p for p in protocol_data.values() if p.get('tvl', 0) > total_protocol_tvl * 0.1]
            if len(high_concentration_protocols) > 2:
                print("      ⚠️  协议集中度过高")
            
            negative_growth_protocols = [p for p in protocol_data.values() if p.get('tvl_change_24h', 0) < -0.1]
            if len(negative_growth_protocols) > len(protocol_data) * 0.3:
                print("      ⚠️  多数协议TVL下降")
        
        if farms:
            high_apy_farms = [f for f in farms if f.get('apy', 0) > 0.5]  # APY > 50%
            if len(high_apy_farms) > len(farms) * 0.2:
                print("      ⚠️  存在超高收益农场，可能不可持续")
        
        if not governance_data or governance_data.get('voter_participation', 0) < 0.05:
            print("      ⚠️  治理参与度偏低")
        
        print("\n" + "=" * 60)
        print("✅ ETH DeFi链上数据分析完成!")
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

def show_eth_defi_ecosystem_overview():
    """显示ETH DeFi生态概述"""
    print("\n\n📊 ETH DeFi生态系统概述")
    print("=" * 60)
    
    overview = """
    🌟 Ethereum DeFi生态系统是全球最大、最成熟的去中心化金融生态
    
    📈 核心指标:
    • 总锁仓价值(TVL): 数百亿美元级别
    • 协议数量: 数百个DeFi协议
    • 用户基数: 数百万活跃用户
    • 日交易量: 数十亿美元
    
    🔧 主要协议类型:
    1. 去中心化交易所(DEX):
       • Uniswap - 最大DEX
       • SushiSwap - 分叉项目
       • Curve - 稳定币交换
    
    2. 借贷协议:
       • Aave - 主流借贷
       • Compound - 利率市场
       • MakerDAO - 稳定币发行
    
    3. 衍生品:
       • Synthetix - 合成资产
       • dYdX - 去中心化衍生品
    
    4. 聚合器:
       • 1inch - DEX聚合器
       • Matcha - 交易聚合
       • ParaSwap - 路由优化
    
    5. 流动性挖矿:
       • Yearn Finance - 自动化收益
       • Convex Finance - Curve优化
       • Harvest Finance - 收益聚合
    
    🎯 生态优势:
    • 网络效应 - 最多用户和流动性
    • 安全性 - 经过时间验证的智能合约
    • 互操作性 - 协议间可组合
    • 创新活跃 - 持续推出新产品和机制
    
    ⚠️ 风险因素:
    • 智能合约风险
    • 流动性风险
    • 监管不确定性
    • Layer 2竞争
    • Gas费用波动
    
    📊 发展趋势:
    • Layer 2解决方案普及
    • 跨链桥接协议发展
    • RWA(真实世界资产)代币化
    • DeFi与传统金融融合
    """
    
    print(overview)

if __name__ == "__main__":
    show_eth_defi_ecosystem_overview()
    analyze_eth_defi_data()
    
    print("\n" + "=" * 60)
    print("🎉 ETH DeFi链上数据分析完成!")
    print("\n💡 建议:")
    print("   • 重点关注TVL排名前10的协议")
    print("   • 监控治理参与度和提案质量")
    print("   • 关注收益率的可持续性")
    print("   • 注意Layer 2生态的发展")
    print("   • 观察监管政策变化影响")