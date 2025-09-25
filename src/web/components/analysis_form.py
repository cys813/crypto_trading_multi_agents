"""
分析表单组件
"""

import streamlit as st
from datetime import datetime, date
from typing import Dict, Any, List

def render_analysis_form() -> Dict[str, Any]:
    """渲染分析表单并返回表单数据"""
    
    # 创建表单
    with st.form("crypto_analysis_form", clear_on_submit=False):
        st.subheader("🎯 加密货币分析配置")
        
        # 加密货币符号输入
        col1, col2 = st.columns(2)
        
        with col1:
            crypto_symbol = st.text_input(
                "加密货币符号 *",
                value=st.session_state.get('last_crypto_symbol', 'BTC/USDT'),
                help="输入交易对符号，如 BTC/USDT, ETH/USDT 等",
                key="crypto_symbol_input"
            )
        
        with col2:
            exchange = st.selectbox(
                "交易所 *",
                ["binance", "coinbase", "okx", "bybit", "kucoin"],
                help="选择主要数据源交易所",
                index=0
            )
        
        # 分析日期
        analysis_date = st.date_input(
            "分析日期",
            value=date.today(),
            help="选择要分析的日期，默认为今天"
        )
        
        # 代理选择
        st.subheader("👥 选择分析代理")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            technical_analyst = st.checkbox("技术分析师", value=True)
            onchain_analyst = st.checkbox("链上分析师", value=True)
        
        with col2:
            sentiment_analyst = st.checkbox("情绪分析师", value=True)
            defi_analyst = st.checkbox("DeFi分析师", value=False)
        
        with col3:
            market_maker_analyst = st.checkbox("市场庄家分析师", value=False)
        
        # 构建选中的代理列表
        selected_agents = []
        if technical_analyst:
            selected_agents.append("technical_analyst")
        if onchain_analyst:
            selected_agents.append("onchain_analyst")
        if sentiment_analyst:
            selected_agents.append("sentiment_analyst")
        if defi_analyst:
            selected_agents.append("defi_analyst")
        if market_maker_analyst:
            selected_agents.append("market_maker_analyst")
        
        # 分析级别
        analysis_level = st.select_slider(
            "分析级别",
            options=["quick", "basic", "standard", "deep", "comprehensive"],
            value="standard",
            help="选择分析深度级别"
        )
        
        # 高级选项
        with st.expander("🔧 高级选项"):
            col1, col2 = st.columns(2)
            
            with col1:
                # 时间范围
                time_horizon = st.selectbox(
                    "时间范围",
                    ["short_term", "medium_term", "long_term"],
                    help="分析的时间范围"
                )
                
                # 交易策略
                trading_strategy = st.selectbox(
                    "交易策略",
                    ["conservative", "balanced", "aggressive"],
                    help="选择交易策略偏好"
                )
            
            with col2:
                # 启用风险管理
                enable_risk_management = st.checkbox(
                    "启用风险管理",
                    value=True,
                    help="是否进行风险管理分析"
                )
                
                # 启用信号生成
                enable_signal_generation = st.checkbox(
                    "启用信号生成",
                    value=True,
                    help="是否生成交易信号"
                )
        
        # 提交按钮
        submit_button = st.form_submit_button(
            "🚀 开始分析",
            type="primary",
            use_container_width=True
        )
        
        # 表单验证
        if submit_button:
            errors = []
            
            # 验证必填字段
            if not crypto_symbol.strip():
                errors.append("请输入加密货币符号")
            
            if not selected_agents:
                errors.append("请至少选择一个分析代理")
            
            # 显示错误
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
                return {'submitted': False}
            
            # 返回表单数据
            form_data = {
                'submitted': True,
                'crypto_symbol': crypto_symbol.strip().upper(),
                'exchange': exchange,
                'analysis_date': analysis_date,
                'agents': selected_agents,
                'analysis_level': analysis_level,
                'time_horizon': time_horizon,
                'trading_strategy': trading_strategy,
                'enable_risk_management': enable_risk_management,
                'enable_signal_generation': enable_signal_generation
            }
            
            return form_data
        
        # 如果没有提交，返回未提交状态
        return {'submitted': False}