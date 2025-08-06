"""
页面头部组件
"""

import streamlit as st
from datetime import datetime

def render_header():
    """渲染页面头部"""
    
    st.markdown("""
    <div class="main-header">
        <h1>₿ Crypto Trading Agents</h1>
        <p>智能加密货币多代理分析系统</p>
        <small>基于AI技术的加密货币市场分析与投资决策支持平台</small>
    </div>
    """, unsafe_allow_html=True)
    
    # 显示当前时间和市场状态
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="当前时间",
            value=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    with col2:
        # 模拟市场状态
        market_status = "🟢 开放" if datetime.now().hour % 24 < 24 else "🟢 开放"
        st.metric(
            label="市场状态",
            value=market_status
        )
    
    with col3:
        # 模拟系统状态
        system_status = "✅ 正常"
        st.metric(
            label="系统状态",
            value=system_status
        )
    
    with col4:
        # 显示分析状态
        if st.session_state.get('analysis_running', False):
            analysis_status = "🔄 分析中"
        elif st.session_state.get('analysis_results'):
            analysis_status = "✅ 已完成"
        else:
            analysis_status = "⏳ 待分析"
        
        st.metric(
            label="分析状态",
            value=analysis_status
        )
    
    st.markdown("---")