"""
侧边栏组件
"""

import streamlit as st
import os
from typing import Dict, Any

def render_sidebar() -> Dict[str, Any]:
    """渲染侧边栏并返回配置"""
    
    # AI模型配置
    st.sidebar.markdown("**🤖 AI模型配置**")
    
    llm_provider = st.sidebar.selectbox(
        "选择AI提供商",
        ["openai", "dashscope", "deepseek"],
        help="选择用于分析的AI模型提供商"
    )
    
    # 根据提供商选择模型
    if llm_provider == "openai":
        llm_model = st.sidebar.selectbox(
            "选择模型",
            ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            help="选择AI模型版本"
        )
    elif llm_provider == "dashscope":
        llm_model = st.sidebar.selectbox(
            "选择模型",
            ["qwen-turbo", "qwen-plus", "qwen-max"],
            help="选择阿里云模型版本"
        )
    else:  # deepseek
        llm_model = st.sidebar.selectbox(
            "选择模型",
            ["deepseek-chat", "deepseek-coder"],
            help="选择DeepSeek模型版本"
        )
    
    # 分析配置
    st.sidebar.markdown("---")
    st.sidebar.markdown("**⚙️ 分析配置**")
    
    # 风险偏好
    risk_tolerance = st.sidebar.selectbox(
        "风险偏好",
        ["low", "medium", "high"],
        help="选择投资风险偏好"
    )
    
    # 最大分析时间
    max_analysis_time = st.sidebar.slider(
        "最大分析时间（分钟）",
        min_value=1,
        max_value=10,
        value=5,
        help="设置分析的最长时间限制"
    )
    
    # 数据源配置
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 数据源配置**")
    
    # 启用实时数据
    enable_realtime = st.sidebar.checkbox(
        "启用实时数据",
        value=True,
        help="是否使用实时市场数据"
    )
    
    # 启用链上数据
    enable_onchain = st.sidebar.checkbox(
        "启用链上数据",
        value=True,
        help="是否包含链上数据分析"
    )
    
    # 启用情绪数据
    enable_sentiment = st.sidebar.checkbox(
        "启用情绪数据",
        value=True,
        help="是否包含市场情绪分析"
    )
    
    # 高级选项
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔧 高级选项**")
    
    # 启用详细日志
    enable_debug = st.sidebar.checkbox(
        "启用详细日志",
        value=os.getenv('DEBUG_MODE', 'false').lower() == 'true',
        help="是否显示详细的调试信息"
    )
    
    # 启用缓存
    enable_cache = st.sidebar.checkbox(
        "启用缓存",
        value=True,
        help="是否启用分析结果缓存"
    )
    
    # 保存配置到session state
    if 'form_config' not in st.session_state:
        st.session_state.form_config = {}
    
    st.session_state.form_config.update({
        'llm_provider': llm_provider,
        'llm_model': llm_model,
        'risk_tolerance': risk_tolerance,
        'max_analysis_time': max_analysis_time,
        'enable_realtime': enable_realtime,
        'enable_onchain': enable_onchain,
        'enable_sentiment': enable_sentiment,
        'enable_debug': enable_debug,
        'enable_cache': enable_cache
    })
    
    return {
        'llm_provider': llm_provider,
        'llm_model': llm_model,
        'risk_tolerance': risk_tolerance,
        'max_analysis_time': max_analysis_time,
        'enable_realtime': enable_realtime,
        'enable_onchain': enable_onchain,
        'enable_sentiment': enable_sentiment,
        'enable_debug': enable_debug,
        'enable_cache': enable_cache
    }