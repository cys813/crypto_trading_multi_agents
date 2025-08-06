"""
线程跟踪器 - 管理分析线程
"""

import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

# 全局线程注册表
_thread_registry = {}
_registry_lock = threading.Lock()

def register_analysis_thread(analysis_id: str, thread: threading.Thread):
    """
    注册分析线程
    
    Args:
        analysis_id: 分析ID
        thread: 线程对象
    """
    with _registry_lock:
        _thread_registry[analysis_id] = {
            'thread': thread,
            'start_time': datetime.now(),
            'status': 'running',
            'last_check': datetime.now()
        }
        
        # 保存到文件
        _save_thread_registry()

def unregister_analysis_thread(analysis_id: str):
    """
    注销分析线程
    
    Args:
        analysis_id: 分析ID
    """
    with _registry_lock:
        if analysis_id in _thread_registry:
            thread_info = _thread_registry[analysis_id]
            thread_info['status'] = 'completed'
            thread_info['end_time'] = datetime.now()
            
            # 保存到文件
            _save_thread_registry()

def check_analysis_status(analysis_id: str) -> str:
    """
    检查分析状态
    
    Args:
        analysis_id: 分析ID
        
    Returns:
        状态: 'running', 'completed', 'failed', 'not_found'
    """
    with _registry_lock:
        # 首先检查内存中的注册表
        if analysis_id in _thread_registry:
            thread_info = _thread_registry[analysis_id]
            thread = thread_info['thread']
            
            # 更新检查时间
            thread_info['last_check'] = datetime.now()
            
            # 检查线程是否还在运行
            if thread.is_alive():
                return 'running'
            else:
                # 检查是否有错误
                if hasattr(thread, '_error') and thread._error:
                    return 'failed'
                return 'completed'
        
        # 如果内存中没有，检查文件
        return _check_thread_status_from_file(analysis_id)

def _check_thread_status_from_file(analysis_id: str) -> str:
    """从文件检查线程状态"""
    try:
        registry_file = Path.home() / ".crypto_trading_agents" / "thread_registry.json"
        
        if registry_file.exists():
            with open(registry_file, 'r', encoding='utf-8') as f:
                registry_data = json.load(f)
            
            if analysis_id in registry_data:
                thread_info = registry_data[analysis_id]
                return thread_info.get('status', 'not_found')
        
        return 'not_found'
        
    except Exception as e:
        print(f"检查线程状态失败: {e}")
        return 'not_found'

def _save_thread_registry():
    """保存线程注册表到文件"""
    try:
        registry_dir = Path.home() / ".crypto_trading_agents"
        registry_dir.mkdir(parents=True, exist_ok=True)
        
        registry_file = registry_dir / "thread_registry.json"
        
        # 转换为可序列化的格式
        serializable_registry = {}
        for analysis_id, thread_info in _thread_registry.items():
            serializable_registry[analysis_id] = {
                'start_time': thread_info['start_time'].isoformat(),
                'status': thread_info['status'],
                'last_check': thread_info['last_check'].isoformat()
            }
            
            if 'end_time' in thread_info:
                serializable_registry[analysis_id]['end_time'] = thread_info['end_time'].isoformat()
        
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_registry, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"保存线程注册表失败: {e}")

def load_thread_registry():
    """从文件加载线程注册表"""
    try:
        registry_file = Path.home() / ".crypto_trading_agents" / "thread_registry.json"
        
        if registry_file.exists():
            with open(registry_file, 'r', encoding='utf-8') as f:
                registry_data = json.load(f)
            
            # 转换回内存格式
            for analysis_id, thread_info in registry_data.items():
                if thread_info['status'] == 'running':
                    # 如果状态是运行中，但实际上线程可能已经结束
                    _thread_registry[analysis_id] = {
                        'thread': None,  # 线程对象已经丢失
                        'start_time': datetime.fromisoformat(thread_info['start_time']),
                        'status': 'unknown',  # 标记为未知状态
                        'last_check': datetime.fromisoformat(thread_info['last_check'])
                    }
                    
                    if 'end_time' in thread_info:
                        _thread_registry[analysis_id]['end_time'] = datetime.fromisoformat(thread_info['end_time'])
                        
    except Exception as e:
        print(f"加载线程注册表失败: {e}")

def cleanup_dead_analysis_threads():
    """清理死亡的分析线程"""
    with _registry_lock:
        dead_threads = []
        
        for analysis_id, thread_info in _thread_registry.items():
            thread = thread_info['thread']
            
            # 如果线程对象存在但已经死亡
            if thread and not thread.is_alive():
                dead_threads.append(analysis_id)
            elif thread is None and thread_info['status'] == 'running':
                # 如果线程对象丢失但状态还是运行中，可能是重启导致的
                dead_threads.append(analysis_id)
        
        # 清理死亡线程
        for analysis_id in dead_threads:
            thread_info = _thread_registry[analysis_id]
            thread_info['status'] = 'failed'
            thread_info['end_time'] = datetime.now()
            thread_info['error'] = 'Thread died unexpectedly'
            
            print(f"清理死亡分析线程: {analysis_id}")
        
        if dead_threads:
            _save_thread_registry()

def get_thread_statistics() -> Dict[str, Any]:
    """获取线程统计信息"""
    with _registry_lock:
        total_threads = len(_thread_registry)
        running_threads = sum(1 for info in _thread_registry.values() if info['status'] == 'running')
        completed_threads = sum(1 for info in _thread_registry.values() if info['status'] == 'completed')
        failed_threads = sum(1 for info in _thread_registry.values() if info['status'] == 'failed')
        
        return {
            'total_threads': total_threads,
            'running_threads': running_threads,
            'completed_threads': completed_threads,
            'failed_threads': failed_threads,
            'thread_details': {
                analysis_id: {
                    'status': info['status'],
                    'start_time': info['start_time'].isoformat(),
                    'runtime_seconds': (datetime.now() - info['start_time']).total_seconds()
                }
                for analysis_id, info in _thread_registry.items()
            }
        }

# 初始化时加载线程注册表
load_thread_registry()