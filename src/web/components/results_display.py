"""
分析结果展示组件
"""

import streamlit as st
from typing import Dict, Any
import json

def render_results(analysis_results: Dict[str, Any]):
    """渲染分析结果"""
    
    if not analysis_results:
        st.warning("⚠️ 没有可显示的分析结果")
        return
    
    try:
        # 显示基本信息
        st.subheader("📊 分析概览")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            symbol = analysis_results.get('crypto_symbol', 'N/A')
            st.metric("交易对", symbol)
        
        with col2:
            decision = analysis_results.get('trading_decision', {}).get('trading_decision', 'N/A')
            decision_emoji = {
                'buy': '🟢',
                'sell': '🔴', 
                'hold': '🟡'
            }.get(decision, '⚪')
            st.metric("交易决策", f"{decision_emoji} {decision.upper()}")
        
        with col3:
            confidence = analysis_results.get('trading_decision', {}).get('confidence', 0)
            st.metric("置信度", f"{confidence:.1%}")
        
        with col4:
            expected_return = analysis_results.get('trading_decision', {}).get('expected_return', 'N/A')
            st.metric("预期收益", expected_return)
        
        st.markdown("---")
        
        # 显示详细分析
        st.subheader("🔍 详细分析")
        
        # 技术分析
        if 'market_trend' in analysis_results:
            with st.expander("📈 技术分析", expanded=True):
                market_trend = analysis_results['market_trend']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**市场趋势**")
                    st.write(f"主要趋势: {market_trend.get('primary_trend', 'N/A')}")
                    st.write(f"趋势强度: {market_trend.get('trend_strength', 'N/A')}")
                    st.write(f"波动性: {market_trend.get('volatility', 'N/A')}")
                
                with col2:
                    st.markdown("**关键价位**")
                    support_levels = market_trend.get('support_levels', [])
                    resistance_levels = market_trend.get('resistance_levels', [])
                    
                    if support_levels:
                        st.write("支撑位:", ", ".join(map(str, support_levels)))
                    if resistance_levels:
                        st.write("阻力位:", ", ".join(map(str, resistance_levels)))
        
        # 情绪分析
        if 'sentiment_analysis' in analysis_results:
            with st.expander("💭 情绪分析", expanded=True):
                sentiment_analysis = analysis_results['sentiment_analysis']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**情绪指标**")
                    fgi = sentiment_analysis.get('fear_greed_index', 50)
                    st.write(f"恐惧贪婪指数: {fgi}")
                    
                    # 情绪可视化
                    if fgi < 25:
                        st.error("😱 极度恐惧")
                    elif fgi < 45:
                        st.warning("😟 恐惧")
                    elif fgi < 55:
                        st.info("😐 中性")
                    elif fgi < 75:
                        st.success("😊 贪婪")
                    else:
                        st.error("🤪 极度贪婪")
                
                with col2:
                    st.markdown("**市场情绪**")
                    st.write(f"整体情绪: {sentiment_analysis.get('overall_sentiment', 'N/A')}")
                    st.write(f"情绪强度: {sentiment_analysis.get('sentiment_strength', 'N/A')}")
                    st.write(f"社交媒体情绪: {sentiment_analysis.get('social_sentiment', 'N/A')}")
        
        # 链上分析
        if 'onchain_analysis' in analysis_results:
            with st.expander("🔗 链上分析", expanded=True):
                onchain_analysis = analysis_results['onchain_analysis']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**网络活动**")
                    st.write(f"活跃地址: {onchain_analysis.get('active_addresses', 'N/A')}")
                    st.write(f"交易量: {onchain_analysis.get('transaction_volume', 'N/A')}")
                    st.write(f"哈希率: {onchain_analysis.get('hash_rate', 'N/A')}")
                
                with col2:
                    st.markdown("**市场指标**")
                    st.write(f"鲸鱼活动: {onchain_analysis.get('whale_activity', 'N/A')}")
                    st.write(f"交易所流入: {onchain_analysis.get('exchange_inflow', 'N/A')}")
                    st.write(f"交易所流出: {onchain_analysis.get('exchange_outflow', 'N/A')}")
        
        # 基本面分析
        if 'fundamentals_analysis' in analysis_results:
            with st.expander("📊 基本面分析", expanded=True):
                fundamentals = analysis_results['fundamentals_analysis']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**资产健康度**")
                    st.write(f"健康状况: {fundamentals.get('asset_health', 'N/A')}")
                    st.write(f"采用指标: {fundamentals.get('adoption_metrics', 'N/A')}")
                    st.write(f"技术发展: {fundamentals.get('technology_development', 'N/A')}")
                
                with col2:
                    st.markdown("**市场指标**")
                    st.write(f"市值排名: {fundamentals.get('market_cap_rank', 'N/A')}")
                    st.write(f"交易量: {fundamentals.get('trading_volume', 'N/A')}")
                    st.write(f"流动性: {fundamentals.get('liquidity_profile', 'N/A')}")
        
        # 交易策略
        if 'trading_strategy' in analysis_results:
            with st.expander("🎯 交易策略", expanded=True):
                strategy = analysis_results['trading_strategy']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**策略配置**")
                    st.write(f"策略类型: {strategy.get('strategy_type', 'N/A')}")
                    st.write(f"入场策略: {strategy.get('entry_strategy', 'N/A')}")
                    st.write(f"时间范围: {strategy.get('time_horizon', 'N/A')}")
                
                with col2:
                    st.markdown(**"风险收益"**)
                    st.write(f"利润目标: {strategy.get('profit_target', 'N/A')}")
                    st.write(f"每笔风险: {strategy.get('risk_per_trade', 'N/A')}")
                    st.write(f"仓位管理: {strategy.get('position_sizing', 'N/A')}")
        
        # 风险控制
        if 'risk_controls' in analysis_results:
            with st.expander("⚠️ 风险控制", expanded=True):
                risk_controls = analysis_results['risk_controls']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**止损止盈**")
                    stop_loss = risk_controls.get('stop_loss', 0)
                    take_profit = risk_controls.get('take_profit', 0)
                    
                    if stop_loss > 0:
                        st.write(f"止损: {stop_loss:.1%}")
                    if take_profit > 0:
                        st.write(f"止盈: {take_profit:.1%}")
                    
                    st.write(f"移动止损: {'是' if risk_controls.get('trailing_stop') else '否'}")
                
                with col2:
                    st.markdown("**风险限制**")
                    st.write(f"最大损失/笔: {risk_controls.get('max_loss_per_trade', 0):.1%}")
                    st.write(f"仓位限制: {risk_controls.get('position_size_limit', 0):.1%}")
                    st.write(f"杠杆限制: {risk_controls.get('leverage_limit', 0):.0f}x")
        
        # 执行计划
        if 'execution_plan' in analysis_results:
            with st.expander("📋 执行计划", expanded=True):
                execution_plan = analysis_results['execution_plan']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**仓位大小**")
                    st.write(f"建议仓位: {execution_plan.get('position_size', 'N/A')}")
                    st.write(f"执行方式: {execution_plan.get('execution_method', 'N/A')}")
                    st.write(f"时间框架: {execution_plan.get('time_frame', 'N/A')}")
                
                with col2:
                    st.markdown("**入场点位**")
                    entry_points = execution_plan.get('entry_points', [])
                    exit_points = execution_plan.get('exit_points', [])
                    
                    if entry_points:
                        st.write("建议入场点:")
                        for point in entry_points:
                            st.write(f"  - 价格: {point.get('price', 'N/A')}, 比例: {point.get('allocation', 'N/A')}")
                    
                    if exit_points:
                        st.write("建议出场点:")
                        for point in exit_points:
                            st.write(f"  - 价格: {point.get('price', 'N/A')}, 比例: {point.get('allocation', 'N/A')}")
        
        # 推理说明
        if 'trading_decision' in analysis_results and 'reasoning' in analysis_results['trading_decision']:
            with st.expander("🧠 决策推理", expanded=True):
                reasoning = analysis_results['trading_decision']['reasoning']
                st.markdown("**推理过程**")
                st.write(reasoning)
        
        # 导出功能
        st.markdown("---")
        st.subheader("💾 导出报告")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 导出为JSON", use_container_width=True):
                # 导出JSON格式
                json_data = json.dumps(analysis_results, indent=2, ensure_ascii=False)
                st.download_button(
                    label="下载JSON报告",
                    data=json_data,
                    file_name=f"crypto_analysis_{analysis_results.get('crypto_symbol', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📋 导出为Markdown", use_container_width=True):
                # 生成Markdown报告
                markdown_report = generate_markdown_report(analysis_results)
                st.download_button(
                    label="下载Markdown报告",
                    data=markdown_report,
                    file_name=f"crypto_analysis_{analysis_results.get('crypto_symbol', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
        
        with col3:
            if st.button("🔄 重新分析", use_container_width=True):
                # 清理当前结果，准备重新分析
                st.session_state.analysis_results = None
                st.session_state.analysis_running = False
                st.session_state.current_analysis_id = None
                st.rerun()
        
    except Exception as e:
        st.error(f"❌ 显示分析结果时发生错误: {str(e)}")
        st.error("请检查分析结果格式是否正确")

def generate_markdown_report(analysis_results: Dict[str, Any]) -> str:
    """生成Markdown格式的分析报告"""
    
    try:
        report = f"""# 加密货币分析报告

## 基本信息
- **交易对**: {analysis_results.get('crypto_symbol', 'N/A')}
- **交易决策**: {analysis_results.get('trading_decision', {}).get('trading_decision', 'N/A')}
- **置信度**: {analysis_results.get('trading_decision', {}).get('confidence', 0):.1%}
- **预期收益**: {analysis_results.get('trading_decision', {}).get('expected_return', 'N/A')}

## 技术分析
"""
        
        if 'market_trend' in analysis_results:
            market_trend = analysis_results['market_trend']
            report += f"""
- **主要趋势**: {market_trend.get('primary_trend', 'N/A')}
- **趋势强度**: {market_trend.get('trend_strength', 'N/A')}
- **波动性**: {market_trend.get('volatility', 'N/A')}
"""
        
        report += "\n## 风险提示\n"
        report += "⚠️ 本报告仅供参考，不构成投资建议。\n"
        report += "⚠️ 加密货币市场波动极大，投资风险极高。\n"
        report += "⚠️ 请根据自身风险承受能力谨慎投资。\n"
        
        return report
        
    except Exception as e:
        return f"# 报告生成错误\n\n生成Markdown报告时发生错误: {str(e)}"