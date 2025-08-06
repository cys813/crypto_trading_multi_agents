"""
智能会话管理器
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import uuid
from datetime import datetime, timedelta

class SmartSessionManager:
    """智能会话管理器"""
    
    def __init__(self):
        """初始化会话管理器"""
        self.session_dir = Path.home() / ".crypto_trading_agents" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)
    
    def save_analysis_state(self, analysis_id: str, state_data: Dict[str, Any]) -> bool:
        """
        保存分析状态
        
        Args:
            analysis_id: 分析ID
            state_data: 状态数据
            
        Returns:
            是否保存成功
        """
        try:
            session_file = self.session_dir / f"{analysis_id}.json"
            
            # 添加元数据
            state_data['analysis_id'] = analysis_id
            state_data['saved_at'] = datetime.now().isoformat()
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"保存分析状态失败: {e}")
            return False
    
    def load_analysis_state(self, analysis_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        加载分析状态
        
        Args:
            analysis_id: 分析ID（可选，如果为None则加载最新的）
            
        Returns:
            状态数据或None
        """
        try:
            if analysis_id:
                session_file = self.session_dir / f"{analysis_id}.json"
            else:
                # 加载最新的会话文件
                session_files = list(self.session_dir.glob("*.json"))
                if not session_files:
                    return None
                
                # 按修改时间排序，获取最新的
                latest_file = max(session_files, key=lambda f: f.stat().st_mtime)
                session_file = latest_file
            
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            print(f"加载分析状态失败: {e}")
            return None
    
    def cleanup_old_sessions(self, max_age_hours: int = 48):
        """
        清理旧的会话数据
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        try:
            current_time = datetime.now()
            
            for session_file in self.session_dir.glob("*.json"):
                try:
                    # 获取文件修改时间
                    file_time = datetime.fromtimestamp(session_file.stat().st_mtime)
                    age_hours = (current_time - file_time).total_seconds() / 3600
                    
                    # 如果文件超过最大保留时间，删除它
                    if age_hours > max_age_hours:
                        session_file.unlink()
                        print(f"已清理旧的会话文件: {session_file.name}")
                        
                except Exception as e:
                    print(f"清理会话文件失败 {session_file.name}: {e}")
                    
        except Exception as e:
            print(f"清理会话数据失败: {e}")

# 全局实例
smart_session_manager = SmartSessionManager()

def get_persistent_analysis_id() -> Optional[str]:
    """
    获取持久的分析ID
    
    Returns:
        分析ID或None
    """
    try:
        # 首先尝试从文件中获取
        id_file = Path.home() / ".crypto_trading_agents" / "current_analysis_id.txt"
        
        if id_file.exists():
            with open(id_file, 'r', encoding='utf-8') as f:
                analysis_id = f.read().strip()
                
                # 检查对应的进度数据是否存在
                from .async_progress_tracker import get_progress_by_id
                progress_data = get_progress_by_id(analysis_id)
                
                if progress_data:
                    return analysis_id
                else:
                    # 如果进度数据不存在，删除ID文件
                    id_file.unlink()
        
        return None
        
    except Exception as e:
        print(f"获取持久分析ID失败: {e}")
        return None

def set_persistent_analysis_id(
    analysis_id: str,
    status: str = "running",
    crypto_symbol: str = "",
    exchange: str = "",
    form_config: Optional[Dict[str, Any]] = None
) -> bool:
    """
    设置持久的分析ID
    
    Args:
        analysis_id: 分析ID
        status: 状态
        crypto_symbol: 加密货币符号
        exchange: 交易所
        form_config: 表单配置
        
    Returns:
        是否设置成功
    """
    try:
        # 创建目录
        id_dir = Path.home() / ".crypto_trading_agents"
        id_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存分析ID到文件
        id_file = id_dir / "current_analysis_id.txt"
        with open(id_file, 'w', encoding='utf-8') as f:
            f.write(analysis_id)
        
        # 保存会话状态
        session_data = {
            'analysis_id': analysis_id,
            'status': status,
            'crypto_symbol': crypto_symbol,
            'exchange': exchange,
            'form_config': form_config or {},
            'created_at': datetime.now().isoformat()
        }
        
        smart_session_manager.save_analysis_state(analysis_id, session_data)
        
        return True
        
    except Exception as e:
        print(f"设置持久分析ID失败: {e}")
        return False

def clear_persistent_analysis_id() -> bool:
    """
    清除持久的分析ID
    
    Returns:
        是否清除成功
    """
    try:
        id_file = Path.home() / ".crypto_trading_agents" / "current_analysis_id.txt"
        
        if id_file.exists():
            id_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"清除持久分析ID失败: {e}")
        return False