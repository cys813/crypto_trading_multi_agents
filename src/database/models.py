"""
数据库模型和工具
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import time
from pathlib import Path


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        """
        初始化数据库管理器
        
        Args:
            data_dir: 数据目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.analysis_dir = self.data_dir / "analysis"
        self.sessions_dir = self.data_dir / "sessions"
        self.config_dir = self.data_dir / "config"
        
        for directory in [self.analysis_dir, self.sessions_dir, self.config_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_analysis_result(self, analysis_id: str, result: Dict[str, Any]) -> bool:
        """
        保存分析结果
        
        Args:
            analysis_id: 分析ID
            result: 分析结果
            
        Returns:
            是否保存成功
        """
        try:
            file_path = self.analysis_dir / f"{analysis_id}.json"
            
            # 添加时间戳
            result['saved_at'] = datetime.now().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存分析结果失败: {e}")
            return False
    
    def load_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        加载分析结果
        
        Args:
            analysis_id: 分析ID
            
        Returns:
            分析结果或None
        """
        try:
            file_path = self.analysis_dir / f"{analysis_id}.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载分析结果失败: {e}")
            return None
    
    def list_analysis_results(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        列出分析结果
        
        Args:
            limit: 限制数量
            
        Returns:
            分析结果列表
        """
        try:
            results = []
            
            for file_path in self.analysis_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                        result['file_path'] = str(file_path)
                        results.append(result)
                except Exception:
                    continue
            
            # 按时间排序
            results.sort(key=lambda x: x.get('saved_at', ''), reverse=True)
            
            return results[:limit]
        except Exception as e:
            print(f"列出分析结果失败: {e}")
            return []
    
    def delete_analysis_result(self, analysis_id: str) -> bool:
        """
        删除分析结果
        
        Args:
            analysis_id: 分析ID
            
        Returns:
            是否删除成功
        """
        try:
            file_path = self.analysis_dir / f"{analysis_id}.json"
            
            if file_path.exists():
                file_path.unlink()
                return True
            
            return False
        except Exception as e:
            print(f"删除分析结果失败: {e}")
            return False
    
    def save_session_config(self, session_id: str, config: Dict[str, Any]) -> bool:
        """
        保存会话配置
        
        Args:
            session_id: 会话ID
            config: 配置数据
            
        Returns:
            是否保存成功
        """
        try:
            file_path = self.sessions_dir / f"{session_id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存会话配置失败: {e}")
            return False
    
    def load_session_config(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        加载会话配置
        
        Args:
            session_id: 会话ID
            
        Returns:
            配置数据或None
        """
        try:
            file_path = self.sessions_dir / f"{session_id}.json"
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载会话配置失败: {e}")
            return None
    
    def save_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        保存用户偏好设置
        
        Args:
            preferences: 偏好设置
            
        Returns:
            是否保存成功
        """
        try:
            file_path = self.config_dir / "user_preferences.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存用户偏好设置失败: {e}")
            return False
    
    def load_user_preferences(self) -> Dict[str, Any]:
        """
        加载用户偏好设置
        
        Returns:
            偏好设置
        """
        try:
            file_path = self.config_dir / "user_preferences.json"
            
            if not file_path.exists():
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载用户偏好设置失败: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """
        清理旧数据
        
        Args:
            days: 保留天数
            
        Returns:
            清理的文件数量
        """
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            cleaned_count = 0
            
            # 清理分析结果
            for file_path in self.analysis_dir.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            
            # 清理会话配置
            for file_path in self.sessions_dir.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            
            return cleaned_count
        except Exception as e:
            print(f"清理旧数据失败: {e}")
            return 0


class AnalysisResult:
    """分析结果模型"""
    
    def __init__(self, analysis_id: str, symbol: str, agents: List[str]):
        """
        初始化分析结果
        
        Args:
            analysis_id: 分析ID
            symbol: 交易对符号
            agents: 使用的代理列表
        """
        self.analysis_id = analysis_id
        self.symbol = symbol
        self.agents = agents
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.status = "pending"
        self.progress = 0
        self.results = {}
        self.error = None
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'analysis_id': self.analysis_id,
            'symbol': self.symbol,
            'agents': self.agents,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'status': self.status,
            'progress': self.progress,
            'results': self.results,
            'error': self.error,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """从字典创建实例"""
        result = cls(
            analysis_id=data['analysis_id'],
            symbol=data['symbol'],
            agents=data['agents']
        )
        
        result.created_at = datetime.fromisoformat(data['created_at'])
        result.updated_at = datetime.fromisoformat(data['updated_at'])
        result.status = data['status']
        result.progress = data['progress']
        result.results = data['results']
        result.error = data['error']
        result.metadata = data['metadata']
        
        return result
    
    def update_progress(self, progress: int, status: str = None):
        """更新进度"""
        self.progress = progress
        if status:
            self.status = status
        self.updated_at = datetime.now()
    
    def add_result(self, agent_name: str, result: Dict[str, Any]):
        """添加代理结果"""
        self.results[agent_name] = result
        self.updated_at = datetime.now()
    
    def set_error(self, error: str):
        """设置错误"""
        self.error = error
        self.status = "error"
        self.updated_at = datetime.now()
    
    def is_complete(self) -> bool:
        """检查是否完成"""
        return self.status == "completed"
    
    def is_failed(self) -> bool:
        """检查是否失败"""
        return self.status == "error"


class LayeredDataStorage:
    """分层数据存储模型"""
    
    def __init__(self, data_dir: str = "./data"):
        """
        初始化分层数据存储
        
        Args:
            data_dir: 数据目录
        """
        self.data_dir = Path(data_dir)
        self.layered_data_dir = self.data_dir / "layered_data"
        self.layered_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 分层数据缓存
        self.cache = {}
        self.cache_ttl = 300  # 5分钟缓存
    
    def save_layered_data(self, symbol: str, layered_data: Dict[str, Any]) -> bool:
        """
        保存分层数据
        
        Args:
            symbol: 交易对符号
            layered_data: 分层数据
            
        Returns:
            是否保存成功
        """
        try:
            # 创建符号专用目录
            symbol_dir = self.layered_data_dir / symbol.replace('/', '_')
            symbol_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = symbol_dir / f"layered_30d_{timestamp}.json"
            
            # 添加元数据
            layered_data['saved_at'] = datetime.now().isoformat()
            layered_data['file_path'] = str(file_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(layered_data, f, ensure_ascii=False, indent=2)
            
            # 更新缓存
            cache_key = f"{symbol}_latest"
            self.cache[cache_key] = (layered_data, time.time())
            
            return True
        except Exception as e:
            print(f"保存分层数据失败: {e}")
            return False
    
    def load_latest_layered_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        加载最新的分层数据
        
        Args:
            symbol: 交易对符号
            
        Returns:
            分层数据或None
        """
        try:
            # 检查缓存
            cache_key = f"{symbol}_latest"
            if cache_key in self.cache:
                data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    return data
                else:
                    del self.cache[cache_key]
            
            # 从文件加载
            symbol_dir = self.layered_data_dir / symbol.replace('/', '_')
            if not symbol_dir.exists():
                return None
            
            # 查找最新的文件
            files = list(symbol_dir.glob("layered_30d_*.json"))
            if not files:
                return None
            
            latest_file = max(files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['file_path'] = str(latest_file)
                
                # 更新缓存
                self.cache[cache_key] = (data, time.time())
                
                return data
        except Exception as e:
            print(f"加载分层数据失败: {e}")
            return None
    
    def get_layered_data_history(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取分层数据历史
        
        Args:
            symbol: 交易对符号
            limit: 限制数量
            
        Returns:
            历史数据列表
        """
        try:
            symbol_dir = self.layered_data_dir / symbol.replace('/', '_')
            if not symbol_dir.exists():
                return []
            
            results = []
            for file_path in symbol_dir.glob("layered_30d_*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data['file_path'] = str(file_path)
                        data['file_mtime'] = file_path.stat().st_mtime
                        results.append(data)
                except Exception:
                    continue
            
            # 按修改时间排序
            results.sort(key=lambda x: x['file_mtime'], reverse=True)
            
            return results[:limit]
        except Exception as e:
            print(f"获取分层数据历史失败: {e}")
            return []
    
    def cleanup_old_layered_data(self, symbol: str = None, days: int = 7) -> int:
        """
        清理旧的分层数据
        
        Args:
            symbol: 交易对符号，None表示所有符号
            days: 保留天数
            
        Returns:
            清理的文件数量
        """
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            cleaned_count = 0
            
            if symbol:
                # 清理特定符号的数据
                symbol_dir = self.layered_data_dir / symbol.replace('/', '_')
                if symbol_dir.exists():
                    for file_path in symbol_dir.glob("layered_30d_*.json"):
                        if file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            cleaned_count += 1
            else:
                # 清理所有符号的数据
                for symbol_dir in self.layered_data_dir.iterdir():
                    if symbol_dir.is_dir():
                        for file_path in symbol_dir.glob("layered_30d_*.json"):
                            if file_path.stat().st_mtime < cutoff_time:
                                file_path.unlink()
                                cleaned_count += 1
            
            return cleaned_count
        except Exception as e:
            print(f"清理分层数据失败: {e}")
            return 0
    
    def get_data_statistics(self, symbol: str = None) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Args:
            symbol: 交易对符号，None表示所有符号
            
        Returns:
            统计信息
        """
        try:
            stats = {
                'total_symbols': 0,
                'total_files': 0,
                'total_size_mb': 0,
                'symbols': {}
            }
            
            if symbol:
                symbol_dirs = [self.layered_data_dir / symbol.replace('/', '_')]
            else:
                symbol_dirs = [d for d in self.layered_data_dir.iterdir() if d.is_dir()]
            
            for symbol_dir in symbol_dirs:
                if not symbol_dir.exists():
                    continue
                
                symbol_name = symbol_dir.name.replace('_', '/')
                symbol_files = list(symbol_dir.glob("layered_30d_*.json"))
                
                symbol_stats = {
                    'file_count': len(symbol_files),
                    'size_mb': sum(f.stat().st_size for f in symbol_files) / (1024 * 1024),
                    'latest_file': None
                }
                
                if symbol_files:
                    latest_file = max(symbol_files, key=lambda x: x.stat().st_mtime)
                    symbol_stats['latest_file'] = latest_file.stat().st_mtime
                
                stats['symbols'][symbol_name] = symbol_stats
                stats['total_files'] += symbol_stats['file_count']
                stats['total_size_mb'] += symbol_stats['size_mb']
            
            stats['total_symbols'] = len(stats['symbols'])
            stats['total_size_mb'] = round(stats['total_size_mb'], 2)
            
            return stats
        except Exception as e:
            print(f"获取数据统计失败: {e}")
            return {}


class SessionConfig:
    """会话配置模型"""
    
    def __init__(self, session_id: str):
        """
        初始化会话配置
        
        Args:
            session_id: 会话ID
        """
        self.session_id = session_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.symbol = "BTC/USDT"
        self.selected_agents = []
        self.analysis_config = {}
        self.user_preferences = {}
        self.analysis_history = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'symbol': self.symbol,
            'selected_agents': self.selected_agents,
            'analysis_config': self.analysis_config,
            'user_preferences': self.user_preferences,
            'analysis_history': self.analysis_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionConfig':
        """从字典创建实例"""
        config = cls(session_id=data['session_id'])
        
        config.created_at = datetime.fromisoformat(data['created_at'])
        config.updated_at = datetime.fromisoformat(data['updated_at'])
        config.symbol = data['symbol']
        config.selected_agents = data['selected_agents']
        config.analysis_config = data['analysis_config']
        config.user_preferences = data['user_preferences']
        config.analysis_history = data['analysis_history']
        
        return config
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
    
    def add_analysis_history(self, analysis_id: str):
        """添加分析历史"""
        self.analysis_history.append({
            'analysis_id': analysis_id,
            'timestamp': datetime.now().isoformat()
        })
        self.updated_at = datetime.now()


# 全局数据库管理器实例
db_manager = DatabaseManager()

# 全局分层数据存储实例
layered_data_storage = LayeredDataStorage()