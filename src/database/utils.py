"""
数据库工具模块
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from .models import DatabaseManager, AnalysisResult, SessionConfig

# 创建数据库管理器实例
db_manager = DatabaseManager()


class AnalysisStorage:
    """分析结果存储管理"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化分析存储
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
    
    def save_analysis(self, analysis: AnalysisResult) -> bool:
        """
        保存分析结果
        
        Args:
            analysis: 分析结果对象
            
        Returns:
            是否保存成功
        """
        return self.db_manager.save_analysis_result(analysis.analysis_id, analysis.to_dict())
    
    def load_analysis(self, analysis_id: str) -> Optional[AnalysisResult]:
        """
        加载分析结果
        
        Args:
            analysis_id: 分析ID
            
        Returns:
            分析结果对象或None
        """
        data = self.db_manager.load_analysis_result(analysis_id)
        if data:
            return AnalysisResult.from_dict(data)
        return None
    
    def get_recent_analyses(self, limit: int = 10) -> List[AnalysisResult]:
        """
        获取最近的分析结果
        
        Args:
            limit: 限制数量
            
        Returns:
            分析结果列表
        """
        results_data = self.db_manager.list_analysis_results(limit)
        return [AnalysisResult.from_dict(data) for data in results_data]
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """
        删除分析结果
        
        Args:
            analysis_id: 分析ID
            
        Returns:
            是否删除成功
        """
        return self.db_manager.delete_analysis_result(analysis_id)
    
    def get_analyses_by_symbol(self, symbol: str, limit: int = 20) -> List[AnalysisResult]:
        """
        按交易对获取分析结果
        
        Args:
            symbol: 交易对符号
            limit: 限制数量
            
        Returns:
            分析结果列表
        """
        all_analyses = self.get_recent_analyses(100)  # 获取更多结果进行筛选
        return [analysis for analysis in all_analyses if analysis.symbol == symbol][:limit]
    
    def get_analyses_by_agent(self, agent_name: str, limit: int = 20) -> List[AnalysisResult]:
        """
        按代理获取分析结果
        
        Args:
            agent_name: 代理名称
            limit: 限制数量
            
        Returns:
            分析结果列表
        """
        all_analyses = self.get_recent_analyses(100)  # 获取更多结果进行筛选
        return [analysis for analysis in all_analyses if agent_name in analysis.agents][:limit]


class SessionStorage:
    """会话配置存储管理"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化会话存储
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
    
    def save_session(self, session: SessionConfig) -> bool:
        """
        保存会话配置
        
        Args:
            session: 会话配置对象
            
        Returns:
            是否保存成功
        """
        return self.db_manager.save_session_config(session.session_id, session.to_dict())
    
    def load_session(self, session_id: str) -> Optional[SessionConfig]:
        """
        加载会话配置
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话配置对象或None
        """
        data = self.db_manager.load_session_config(session_id)
        if data:
            return SessionConfig.from_dict(data)
        return None
    
    def create_session(self, session_id: str = None) -> SessionConfig:
        """
        创建新会话
        
        Args:
            session_id: 会话ID（可选）
            
        Returns:
            会话配置对象
        """
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = SessionConfig(session_id)
        self.save_session(session)
        return session
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """
        更新会话配置
        
        Args:
            session_id: 会话ID
            **kwargs: 更新的配置项
            
        Returns:
            是否更新成功
        """
        session = self.load_session(session_id)
        if session:
            session.update_config(**kwargs)
            return self.save_session(session)
        return False


class UserPreferencesManager:
    """用户偏好设置管理"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化用户偏好管理器
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
    
    def save_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        保存用户偏好设置
        
        Args:
            preferences: 偏好设置
            
        Returns:
            是否保存成功
        """
        return self.db_manager.save_user_preferences(preferences)
    
    def load_preferences(self) -> Dict[str, Any]:
        """
        加载用户偏好设置
        
        Returns:
            偏好设置
        """
        return self.db_manager.load_user_preferences()
    
    def update_preferences(self, **kwargs) -> bool:
        """
        更新用户偏好设置
        
        Args:
            **kwargs: 更新的偏好项
            
        Returns:
            是否更新成功
        """
        preferences = self.load_preferences()
        preferences.update(kwargs)
        return self.save_preferences(preferences)
    
    def get_preference(self, key: str, default_value: Any = None) -> Any:
        """
        获取特定偏好设置
        
        Args:
            key: 偏好键
            default_value: 默认值
            
        Returns:
            偏好值
        """
        preferences = self.load_preferences()
        return preferences.get(key, default_value)
    
    def set_preference(self, key: str, value: Any) -> bool:
        """
        设置特定偏好设置
        
        Args:
            key: 偏好键
            value: 偏好值
            
        Returns:
            是否设置成功
        """
        return self.update_preferences(**{key: value})


class DataExportManager:
    """数据导出管理"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化数据导出管理器
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
    
    def export_analysis_to_json(self, analysis_id: str, output_path: str = None) -> str:
        """
        导出分析结果到JSON文件
        
        Args:
            analysis_id: 分析ID
            output_path: 输出路径（可选）
            
        Returns:
            导出文件路径
        """
        analysis = self.db_manager.load_analysis_result(analysis_id)
        if not analysis:
            raise ValueError(f"分析结果 {analysis_id} 不存在")
        
        if output_path is None:
            output_path = f"analysis_{analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def export_analysis_to_markdown(self, analysis_id: str, output_path: str = None) -> str:
        """
        导出分析结果到Markdown文件
        
        Args:
            analysis_id: 分析ID
            output_path: 输出路径（可选）
            
        Returns:
            导出文件路径
        """
        analysis = self.db_manager.load_analysis_result(analysis_id)
        if not analysis:
            raise ValueError(f"分析结果 {analysis_id} 不存在")
        
        if output_path is None:
            output_path = f"analysis_{analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        # 生成Markdown内容
        markdown_content = self._generate_markdown_content(analysis)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return output_path
    
    def _generate_markdown_content(self, analysis: Dict[str, Any]) -> str:
        """
        生成Markdown内容
        
        Args:
            analysis: 分析结果数据
            
        Returns:
            Markdown内容
        """
        content = f"""# 加密货币交易分析报告

## 基本信息
- **交易对**: {analysis.get('symbol', 'N/A')}
- **分析ID**: {analysis.get('analysis_id', 'N/A')}
- **创建时间**: {analysis.get('created_at', 'N/A')}
- **更新时间**: {analysis.get('updated_at', 'N/A')}
- **状态**: {analysis.get('status', 'N/A')}
- **进度**: {analysis.get('progress', 0)}%

## 使用的代理
"""
        
        for agent in analysis.get('agents', []):
            content += f"- {agent}\n"
        
        content += "\n## 分析结果\n"
        
        for agent_name, result in analysis.get('results', {}).items():
            content += f"### {agent_name}\n\n"
            
            if isinstance(result, dict):
                for key, value in result.items():
                    content += f"**{key}**: {value}\n\n"
            else:
                content += f"{result}\n\n"
        
        if analysis.get('error'):
            content += f"## 错误信息\n\n{analysis['error']}\n"
        
        return content
    
    def export_analyses_summary(self, output_path: str = None, days: int = 7) -> str:
        """
        导出分析结果摘要
        
        Args:
            output_path: 输出路径（可选）
            days: 导出最近几天的数据
            
        Returns:
            导出文件路径
        """
        if output_path is None:
            output_path = f"analyses_summary_{datetime.now().strftime('%Y%m%d')}.json"
        
        # 获取最近的分析结果
        recent_analyses = self.db_manager.list_analysis_results(100)
        
        # 按日期筛选
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_analyses = []
        
        for analysis in recent_analyses:
            created_at = datetime.fromisoformat(analysis.get('created_at', ''))
            if created_at >= cutoff_date:
                filtered_analyses.append(analysis)
        
        # 生成摘要数据
        summary = {
            'export_date': datetime.now().isoformat(),
            'period_days': days,
            'total_analyses': len(filtered_analyses),
            'analyses': filtered_analyses
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return output_path


# 全局存储管理器实例
analysis_storage = AnalysisStorage(db_manager)
session_storage = SessionStorage(db_manager)
preferences_manager = UserPreferencesManager(db_manager)
export_manager = DataExportManager(db_manager)