"""
异步进度跟踪器
"""

import json
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
from pathlib import Path

class AsyncProgressTracker:
    """异步进度跟踪器"""
    
    def __init__(self, analysis_id: str, agents: List[str], analysis_level: str, llm_provider: str):
        """
        初始化进度跟踪器
        
        Args:
            analysis_id: 分析ID
            agents: 代理列表
            analysis_level: 分析级别
            llm_provider: LLM提供商
        """
        self.analysis_id = analysis_id
        self.agents = agents
        self.analysis_level = analysis_level
        self.llm_provider = llm_provider
        self.lock = threading.Lock()
        
        # 初始化进度数据
        self.progress_data = {
            'analysis_id': analysis_id,
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'agents': agents,
            'analysis_level': analysis_level,
            'llm_provider': llm_provider,
            'current_step': 0,
            'total_steps': len(agents) + 3,  # 数据收集 + 代理分析 + 综合分析 + 生成报告
            'progress_messages': [],
            'current_message': '正在初始化分析...',
            'raw_results': None,
            'error': None
        }
        
        # 保存初始状态
        self._save_progress()
    
    def update_progress(self, message: str, step: Optional[int] = None):
        """
        更新进度
        
        Args:
            message: 进度消息
            step: 当前步骤（可选）
        """
        with self.lock:
            self.progress_data['current_message'] = message
            self.progress_data['progress_messages'].append({
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
            if step is not None:
                self.progress_data['current_step'] = step
            
            # 计算进度百分比
            total_steps = self.progress_data['total_steps']
            current_step = self.progress_data['current_step']
            progress_percentage = (current_step / total_steps) * 100 if total_steps > 0 else 0
            
            self.progress_data['progress_percentage'] = progress_percentage
            
            # 保存进度
            self._save_progress()
    
    def mark_completed(self, message: str, results: Optional[Dict[str, Any]] = None):
        """
        标记分析完成
        
        Args:
            message: 完成消息
            results: 分析结果
        """
        with self.lock:
            self.progress_data['status'] = 'completed'
            self.progress_data['end_time'] = datetime.now().isoformat()
            self.progress_data['current_message'] = message
            self.progress_data['current_step'] = self.progress_data['total_steps']
            self.progress_data['progress_percentage'] = 100.0
            self.progress_data['raw_results'] = results
            
            self.progress_data['progress_messages'].append({
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # 保存最终状态
            self._save_progress()
    
    def mark_failed(self, error_message: str):
        """
        标记分析失败
        
        Args:
            error_message: 错误消息
        """
        with self.lock:
            self.progress_data['status'] = 'failed'
            self.progress_data['end_time'] = datetime.now().isoformat()
            self.progress_data['current_message'] = f"分析失败: {error_message}"
            self.progress_data['error'] = error_message
            
            self.progress_data['progress_messages'].append({
                'message': f"❌ 分析失败: {error_message}",
                'timestamp': datetime.now().isoformat()
            })
            
            # 保存失败状态
            self._save_progress()
    
    def _save_progress(self):
        """保存进度到文件"""
        try:
            # 创建进度数据目录
            progress_dir = Path.home() / ".crypto_trading_agents" / "progress"
            progress_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存进度数据
            progress_file = progress_dir / f"{self.analysis_id}.json"
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存进度数据失败: {e}")
    
    def get_progress(self) -> Dict[str, Any]:
        """获取当前进度数据"""
        with self.lock:
            return self.progress_data.copy()

# 全局函数
def get_progress_by_id(analysis_id: str) -> Optional[Dict[str, Any]]:
    """
    根据分析ID获取进度数据
    
    Args:
        analysis_id: 分析ID
        
    Returns:
        进度数据或None
    """
    try:
        progress_file = Path.home() / ".crypto_trading_agents" / "progress" / f"{analysis_id}.json"
        
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
        
    except Exception as e:
        print(f"获取进度数据失败: {e}")
        return None

def get_latest_analysis_id() -> Optional[str]:
    """
    获取最新的分析ID
    
    Returns:
        最新的分析ID或None
    """
    try:
        progress_dir = Path.home() / ".crypto_trading_agents" / "progress"
        
        if not progress_dir.exists():
            return None
        
        # 获取所有进度文件
        progress_files = list(progress_dir.glob("*.json"))
        
        if not progress_files:
            return None
        
        # 按修改时间排序，获取最新的
        latest_file = max(progress_files, key=lambda f: f.stat().st_mtime)
        
        # 从文件名提取分析ID
        analysis_id = latest_file.stem
        
        # 检查是否已完成
        progress_data = get_progress_by_id(analysis_id)
        if progress_data and progress_data.get('status') == 'completed':
            return analysis_id
        
        return None
        
    except Exception as e:
        print(f"获取最新分析ID失败: {e}")
        return None

def cleanup_old_progress_data(max_age_hours: int = 24):
    """
    清理旧的进度数据
    
    Args:
        max_age_hours: 最大保留时间（小时）
    """
    try:
        progress_dir = Path.home() / ".crypto_trading_agents" / "progress"
        
        if not progress_dir.exists():
            return
        
        current_time = datetime.now()
        
        for progress_file in progress_dir.glob("*.json"):
            try:
                # 获取文件修改时间
                file_time = datetime.fromtimestamp(progress_file.stat().st_mtime)
                age_hours = (current_time - file_time).total_seconds() / 3600
                
                # 如果文件超过最大保留时间，删除它
                if age_hours > max_age_hours:
                    progress_file.unlink()
                    print(f"已清理旧的进度文件: {progress_file.name}")
                    
            except Exception as e:
                print(f"清理进度文件失败 {progress_file.name}: {e}")
                
    except Exception as e:
        print(f"清理进度数据失败: {e}")