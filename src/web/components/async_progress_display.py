"""
异步进度显示组件
"""

import streamlit as st
import time
from typing import Optional
from .async_progress_tracker import get_progress_by_id

def display_unified_progress(analysis_id: str, show_refresh_controls: bool = True) -> bool:
    """
    显示统一进度
    
    Args:
        analysis_id: 分析ID
        show_refresh_controls: 是否显示刷新控件
        
    Returns:
        是否完成
    """
    try:
        # 获取进度数据
        progress_data = get_progress_by_id(analysis_id)
        
        if not progress_data:
            st.warning("⚠️ 找不到进度数据")
            return False
        
        status = progress_data.get('status', 'unknown')
        current_step = progress_data.get('current_step', 0)
        total_steps = progress_data.get('total_steps', 1)
        current_message = progress_data.get('current_message', '正在分析...')
        progress_percentage = progress_data.get('progress_percentage', 0)
        
        # 显示进度条
        progress_bar = st.progress(progress_percentage / 100)
        
        # 显示状态信息
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**状态**: {current_message}")
        
        with col2:
            st.write(f"**步骤**: {current_step}/{total_steps}")
        
        with col3:
            st.write(f"**进度**: {progress_percentage:.1f}%")
        
        # 显示详细进度消息
        if 'progress_messages' in progress_data:
            with st.expander("📋 详细进度", expanded=False):
                messages = progress_data['progress_messages'][-10:]  # 显示最近10条消息
                for msg in messages:
                    timestamp = msg.get('timestamp', 'N/A')[-8:]  # 只显示时间部分
                    message = msg.get('message', 'N/A')
                    st.write(f"`{timestamp}` {message}")
        
        # 显示刷新控件
        if show_refresh_controls and status == 'running':
            st.markdown("---")
            auto_refresh_key = f"auto_refresh_unified_{analysis_id}"
            
            # 自动刷新选项
            auto_refresh = st.checkbox(
                "🔄 自动刷新进度",
                value=st.session_state.get(auto_refresh_key, True),
                key=auto_refresh_key,
                help="自动刷新页面显示最新进度"
            )
            
            if auto_refresh:
                # 设置自动刷新
                refresh_seconds = st.slider(
                    "刷新间隔（秒）",
                    min_value=3,
                    max_value=30,
                    value=5,
                    key=f"refresh_interval_{analysis_id}"
                )
                
                # 显示刷新倒计时
                if f"refresh_countdown_{analysis_id}" not in st.session_state:
                    st.session_state[f"refresh_countdown_{analysis_id}"] = refresh_seconds
                
                # 倒计时显示
                countdown = st.session_state[f"refresh_countdown_{analysis_id}"]
                st.write(f"⏱️ {countdown} 秒后自动刷新...")
                
                # 倒计时逻辑
                if countdown <= 0:
                    st.session_state[f"refresh_countdown_{analysis_id}"] = refresh_seconds
                    time.sleep(0.1)  # 短暂延迟
                    st.rerun()
                else:
                    st.session_state[f"refresh_countdown_{analysis_id}"] = countdown - 1
                    time.sleep(1)
                    st.rerun()
            
            # 手动刷新按钮
            if st.button("🔄 手动刷新", key=f"manual_refresh_{analysis_id}"):
                st.rerun()
        
        # 如果有错误，显示错误信息
        if progress_data.get('error'):
            st.error(f"❌ 分析错误: {progress_data['error']}")
        
        # 返回是否完成
        return status == 'completed'
        
    except Exception as e:
        st.error(f"❌ 显示进度时发生错误: {str(e)}")
        return False