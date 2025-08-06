"""
代理状态管理 - 管理各个代理的状态和交互

基于原版代理状态管理，针对加密货币多代理系统优化
"""

from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class AgentState(Enum):
    """代理状态枚举"""
    IDLE = "idle"
    COLLECTING_DATA = "collecting_data"
    ANALYZING = "analyzing"
    DEBATING = "debating"
    DECIDING = "deciding"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"

class AgentType(Enum):
    """代理类型枚举"""
    TECHNICAL_ANALYST = "technical_analyst"
    ONCHAIN_ANALYST = "onchain_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    MARKET_MAKER_ANALYST = "market_maker_analyst"
    DEFI_ANALYST = "defi_analyst"
    BULL_RESEARCHER = "bull_researcher"
    BEAR_RESEARCHER = "bear_researcher"
    AGGRESSIVE_DEBATOR = "aggressive_debator"
    CONSERVATIVE_DEBATOR = "conservative_debator"
    NEUTRAL_DEBATOR = "neutral_debator"
    RESEARCH_MANAGER = "research_manager"
    RISK_MANAGER = "risk_manager"
    CRYPTO_TRADER = "crypto_trader"

class AgentStateManager:
    """代理状态管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化代理状态管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.agent_states: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        self.current_workflow_id: Optional[str] = None
        
    def initialize_agent_state(self, agent_type: AgentType, agent_id: str) -> Dict[str, Any]:
        """
        初始化代理状态
        
        Args:
            agent_type: 代理类型
            agent_id: 代理ID
            
        Returns:
            初始化的代理状态
        """
        state = {
            "agent_id": agent_id,
            "agent_type": agent_type.value,
            "current_state": AgentState.IDLE.value,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "progress": 0.0,
            "results": {},
            "errors": [],
            "metrics": {
                "execution_time": 0,
                "memory_usage": 0,
                "api_calls": 0,
                "data_processed": 0
            },
            "dependencies": [],
            "outputs": [],
            "logs": []
        }
        
        self.agent_states[agent_id] = state
        return state
    
    def update_agent_state(self, agent_id: str, new_state: AgentState, 
                          progress: float = None, results: Dict[str, Any] = None,
                          error: str = None) -> bool:
        """
        更新代理状态
        
        Args:
            agent_id: 代理ID
            new_state: 新状态
            progress: 进度（0-1）
            results: 结果数据
            error: 错误信息
            
        Returns:
            是否更新成功
        """
        if agent_id not in self.agent_states:
            logger.warning(f"Agent {agent_id} not found in state manager")
            return False
        
        agent_state = self.agent_states[agent_id]
        
        # 更新状态
        agent_state["current_state"] = new_state.value
        agent_state["last_updated"] = datetime.now().isoformat()
        
        # 更新进度
        if progress is not None:
            agent_state["progress"] = max(0.0, min(1.0, progress))
        
        # 更新结果
        if results is not None:
            agent_state["results"].update(results)
        
        # 记录错误
        if error is not None:
            agent_state["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "error": error
            })
        
        # 记录状态变更日志
        agent_state["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "event": "state_change",
            "from_state": agent_state.get("current_state"),
            "to_state": new_state.value,
            "progress": agent_state["progress"]
        })
        
        # 如果是完成或错误状态，记录结束时间
        if new_state in [AgentState.COMPLETED, AgentState.ERROR]:
            agent_state["end_time"] = datetime.now().isoformat()
            
            # 计算执行时间
            if agent_state.get("start_time"):
                start_time = datetime.fromisoformat(agent_state["start_time"])
                end_time = datetime.fromisoformat(agent_state["end_time"])
                execution_time = (end_time - start_time).total_seconds()
                agent_state["metrics"]["execution_time"] = execution_time
        
        return True
    
    def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取代理状态
        
        Args:
            agent_id: 代理ID
            
        Returns:
            代理状态或None
        """
        return self.agent_states.get(agent_id)
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[Dict[str, Any]]:
        """
        根据类型获取代理列表
        
        Args:
            agent_type: 代理类型
            
        Returns:
            代理状态列表
        """
        return [
            state for state in self.agent_states.values()
            if state.get("agent_type") == agent_type.value
        ]
    
    def get_agents_by_state(self, state: AgentState) -> List[Dict[str, Any]]:
        """
        根据状态获取代理列表
        
        Args:
            state: 代理状态
            
        Returns:
            代理状态列表
        """
        return [
            state for state in self.agent_states.values()
            if state.get("current_state") == state.value
        ]
    
    def start_workflow(self, workflow_id: str, symbol: str, analysis_type: str) -> str:
        """
        开始工作流
        
        Args:
            workflow_id: 工作流ID
            symbol: 交易对
            analysis_type: 分析类型
            
        Returns:
            工作流ID
        """
        self.current_workflow_id = workflow_id
        
        workflow = {
            "workflow_id": workflow_id,
            "symbol": symbol,
            "analysis_type": analysis_type,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "agent_states": {},
            "global_state": {
                "symbol": symbol,
                "market_report": None,
                "sentiment_report": None,
                "news_report": None,
                "fundamentals_report": None,
                "bull_research": None,
                "bear_research": None,
                "research_debate": None,
                "aggressive_risk_analysis": None,
                "conservative_risk_analysis": None,
                "neutral_risk_analysis": None,
                "risk_debate": None,
                "final_risk_decision": None,
                "trading_decision": None
            },
            "metrics": {
                "total_execution_time": 0,
                "agents_completed": 0,
                "agents_failed": 0,
                "total_api_calls": 0,
                "total_data_processed": 0
            }
        }
        
        self.workflow_history.append(workflow)
        return workflow_id
    
    def update_workflow_state(self, workflow_id: str, agent_id: str, 
                             agent_results: Dict[str, Any] = None) -> bool:
        """
        更新工作流状态
        
        Args:
            workflow_id: 工作流ID
            agent_id: 代理ID
            agent_results: 代理结果
            
        Returns:
            是否更新成功
        """
        workflow = self._get_workflow(workflow_id)
        if not workflow:
            return False
        
        # 更新代理在工作流中的状态
        if agent_id in self.agent_states:
            workflow["agent_states"][agent_id] = self.agent_states[agent_id].copy()
        
        # 更新全局状态
        if agent_results:
            agent_state = self.agent_states.get(agent_id, {})
            agent_type = agent_state.get("agent_type")
            
            if agent_type and agent_results:
                # 根据代理类型更新对应的全局状态
                if agent_type == AgentType.TECHNICAL_ANALYST.value:
                    workflow["global_state"]["market_report"] = agent_results
                elif agent_type == AgentType.SENTIMENT_ANALYST.value:
                    workflow["global_state"]["sentiment_report"] = agent_results
                elif agent_type == AgentType.ONCHAIN_ANALYST.value:
                    workflow["global_state"]["fundamentals_report"] = agent_results
                elif agent_type == AgentType.BULL_RESEARCHER.value:
                    workflow["global_state"]["bull_research"] = agent_results
                elif agent_type == AgentType.BEAR_RESEARCHER.value:
                    workflow["global_state"]["bear_research"] = agent_results
                elif agent_type == AgentType.RESEARCH_MANAGER.value:
                    workflow["global_state"]["research_debate"] = agent_results
                elif agent_type == AgentType.AGGRESSIVE_DEBATOR.value:
                    workflow["global_state"]["aggressive_risk_analysis"] = agent_results
                elif agent_type == AgentType.CONSERVATIVE_DEBATOR.value:
                    workflow["global_state"]["conservative_risk_analysis"] = agent_results
                elif agent_type == AgentType.NEUTRAL_DEBATOR.value:
                    workflow["global_state"]["neutral_risk_analysis"] = agent_results
                elif agent_type == AgentType.RISK_MANAGER.value:
                    workflow["global_state"]["risk_debate"] = agent_results
                elif agent_type == AgentType.CRYPTO_TRADER.value:
                    workflow["global_state"]["trading_decision"] = agent_results
        
        return True
    
    def complete_workflow(self, workflow_id: str, success: bool = True) -> bool:
        """
        完成工作流
        
        Args:
            workflow_id: 工作流ID
            success: 是否成功
            
        Returns:
            是否完成成功
        """
        workflow = self._get_workflow(workflow_id)
        if not workflow:
            return False
        
        workflow["end_time"] = datetime.now().isoformat()
        workflow["status"] = "completed" if success else "failed"
        
        # 计算总执行时间
        if workflow.get("start_time"):
            start_time = datetime.fromisoformat(workflow["start_time"])
            end_time = datetime.fromisoformat(workflow["end_time"])
            execution_time = (end_time - start_time).total_seconds()
            workflow["metrics"]["total_execution_time"] = execution_time
        
        # 统计代理完成情况
        completed_agents = 0
        failed_agents = 0
        total_api_calls = 0
        total_data_processed = 0
        
        for agent_state in workflow["agent_states"].values():
            if agent_state.get("current_state") == AgentState.COMPLETED.value:
                completed_agents += 1
            elif agent_state.get("current_state") == AgentState.ERROR.value:
                failed_agents += 1
            
            # 累计指标
            metrics = agent_state.get("metrics", {})
            total_api_calls += metrics.get("api_calls", 0)
            total_data_processed += metrics.get("data_processed", 0)
        
        workflow["metrics"]["agents_completed"] = completed_agents
        workflow["metrics"]["agents_failed"] = failed_agents
        workflow["metrics"]["total_api_calls"] = total_api_calls
        workflow["metrics"]["total_data_processed"] = total_data_processed
        
        return True
    
    def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流状态
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流状态或None
        """
        return self._get_workflow(workflow_id)
    
    def get_current_global_state(self) -> Dict[str, Any]:
        """
        获取当前全局状态
        
        Returns:
            全局状态
        """
        if self.current_workflow_id:
            workflow = self._get_workflow(self.current_workflow_id)
            if workflow:
                return workflow.get("global_state", {})
        
        return {}
    
    def check_workflow_progress(self, workflow_id: str) -> Dict[str, Any]:
        """
        检查工作流进度
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            进度信息
        """
        workflow = self._get_workflow(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}
        
        agent_states = workflow.get("agent_states", {})
        total_agents = len(agent_states)
        completed_agents = len([s for s in agent_states.values() if s.get("current_state") == AgentState.COMPLETED.value])
        failed_agents = len([s for s in agent_states.values() if s.get("current_state") == AgentState.ERROR.value])
        
        progress = completed_agents / total_agents if total_agents > 0 else 0.0
        
        return {
            "workflow_id": workflow_id,
            "total_agents": total_agents,
            "completed_agents": completed_agents,
            "failed_agents": failed_agents,
            "progress": progress,
            "status": workflow.get("status", "unknown"),
            "execution_time": workflow.get("metrics", {}).get("total_execution_time", 0),
        }
    
    def export_workflow_summary(self, workflow_id: str) -> Dict[str, Any]:
        """
        导出工作流摘要
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流摘要
        """
        workflow = self._get_workflow(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}
        
        return {
            "workflow_id": workflow_id,
            "symbol": workflow.get("symbol"),
            "analysis_type": workflow.get("analysis_type"),
            "start_time": workflow.get("start_time"),
            "end_time": workflow.get("end_time"),
            "status": workflow.get("status"),
            "duration": workflow.get("metrics", {}).get("total_execution_time", 0),
            "agents_participated": len(workflow.get("agent_states", {})),
            "agents_completed": workflow.get("metrics", {}).get("agents_completed", 0),
            "agents_failed": workflow.get("metrics", {}).get("agents_failed", 0),
            "total_api_calls": workflow.get("metrics", {}).get("total_api_calls", 0),
            "final_decision": workflow.get("global_state", {}).get("trading_decision", {}).get("trading_decision", "unknown"),
        }
    
    def _get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流"""
        for workflow in self.workflow_history:
            if workflow.get("workflow_id") == workflow_id:
                return workflow
        return None
    
    def cleanup_old_workflows(self, max_workflows: int = 100):
        """
        清理旧工作流记录
        
        Args:
            max_workflows: 最大保留数量
        """
        if len(self.workflow_history) > max_workflows:
            # 保留最新的工作流
            self.workflow_history = self.workflow_history[-max_workflows:]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息
        
        Returns:
            系统统计信息
        """
        total_workflows = len(self.workflow_history)
        active_agents = len([s for s in self.agent_states.values() if s.get("current_state") not in [AgentState.COMPLETED.value, AgentState.ERROR.value]])
        
        return {
            "total_workflows": total_workflows,
            "active_agents": active_agents,
            "total_agents": len(self.agent_states),
            "current_workflow": self.current_workflow_id,
            "memory_usage": len(json.dumps(self.agent_states)) + len(json.dumps(self.workflow_history)),
        }