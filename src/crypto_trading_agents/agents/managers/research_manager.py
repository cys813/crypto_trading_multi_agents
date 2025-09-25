"""
研究管理器 - 协调和管理所有研究活动

基于原版研究管理架构，针对加密货币研究需求优化
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class ResearchPriority(Enum):
    """研究优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ResearchStatus(Enum):
    """研究状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ResearchType(Enum):
    """研究类型"""
    MARKET_ANALYSIS = "market_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    OPPORTUNITY_IDENTIFICATION = "opportunity_identification"
    TREND_ANALYSIS = "trend_analysis"
    FUNDAMENTAL_RESEARCH = "fundamental_research"
    TECHNICAL_RESEARCH = "technical_research"

class ResearchManager:
    """研究管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化研究管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.research_config = config.get("research_config", {})
        
        # 研究参数
        self.max_concurrent_research = self.research_config.get("max_concurrent_research", 3)
        self.research_timeout = self.research_config.get("research_timeout", 300)  # 秒
        self.research_priorities = self.research_config.get("research_priorities", {})
        
        # 研究队列和状态
        self.research_queue = []
        self.active_research = {}
        self.completed_research = []
        self.research_results = {}
        
        # 研究协调
        self.research_coordinators = {}
        self.research_dependencies = {}
        
    def collect_data(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        收集研究管理数据
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            研究管理数据
        """
        try:
            base_currency = symbol.split('/')[0]
            
            return {
                "symbol": symbol,
                "base_currency": base_currency,
                "end_date": end_date,
                "research_queue": self.research_queue,
                "active_research": self.active_research,
                "research_priorities": self.research_priorities,
                "research_capacity": self._assess_research_capacity(),
                "research_dependencies": self.research_dependencies,
                "resource_availability": self._assess_resource_availability(),
            }
            
        except Exception as e:
            logger.error(f"Error collecting research management data for {symbol}: {str(e)}")
            return {"error": str(e)}
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析研究管理数据
        
        Args:
            data: 研究管理数据
            
        Returns:
            研究管理分析结果
        """
        try:
            if "error" in data:
                return {"error": data["error"]}
            
            # 分析研究队列
            queue_analysis = self._analyze_research_queue(data.get("research_queue", []))
            
            # 分析活跃研究
            active_analysis = self._analyze_active_research(data.get("active_research", {}))
            
            # 分析研究依赖关系
            dependency_analysis = self._analyze_research_dependencies(data.get("research_dependencies", {}))
            
            # 分析资源可用性
            resource_analysis = self._analyze_resource_availability(data.get("resource_availability", {}))
            
            # 优化研究调度
            scheduling_optimization = self._optimize_research_scheduling(
                queue_analysis, active_analysis, resource_analysis
            )
            
            # 协调研究活动
            research_coordination = self._coordinate_research_activities(
                scheduling_optimization, dependency_analysis
            )
            
            # 生成研究计划
            research_plan = self._generate_research_plan(
                research_coordination, resource_analysis
            )
            
            # 评估研究效率
            efficiency_metrics = self._assess_research_efficiency(
                active_analysis, queue_analysis, research_coordination
            )
            
            return {
                "queue_analysis": queue_analysis,
                "active_analysis": active_analysis,
                "dependency_analysis": dependency_analysis,
                "resource_analysis": resource_analysis,
                "scheduling_optimization": scheduling_optimization,
                "research_coordination": research_coordination,
                "research_plan": research_plan,
                "efficiency_metrics": efficiency_metrics,
                "confidence": self._calculate_confidence(efficiency_metrics, resource_analysis),
                "research_dashboard": self._generate_research_dashboard(
                    queue_analysis, active_analysis, efficiency_metrics
                ),
            }
            
        except Exception as e:
            logger.error(f"Error analyzing research management data: {str(e)}")
            return {"error": str(e)}
    
    def submit_research_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        提交研究任务
        
        Args:
            task: 研究任务
            
        Returns:
            提交结果
        """
        try:
            task_id = f"research_{datetime.now().timestamp()}"
            
            # 验证任务
            validation_result = self._validate_research_task(task)
            if not validation_result.get("valid", True):
                return {"error": validation_result.get("error", "Invalid task")}
            
            # 添加任务到队列
            queued_task = {
                "task_id": task_id,
                "symbol": task.get("symbol"),
                "research_type": task.get("research_type"),
                "priority": task.get("priority", ResearchPriority.MEDIUM.value),
                "parameters": task.get("parameters", {}),
                "dependencies": task.get("dependencies", []),
                "estimated_duration": task.get("estimated_duration", 300),
                "submitted_at": datetime.now().isoformat(),
                "status": ResearchStatus.PENDING.value,
            }
            
            self.research_queue.append(queued_task)
            
            # 排序队列
            self._sort_research_queue()
            
            return {
                "task_id": task_id,
                "status": "queued",
                "queue_position": len(self.research_queue),
                "estimated_start_time": self._estimate_start_time(task_id),
            }
            
        except Exception as e:
            logger.error(f"Error submitting research task: {str(e)}")
            return {"error": str(e)}
    
    def start_research_task(self, task_id: str) -> Dict[str, Any]:
        """
        启动研究任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            启动结果
        """
        try:
            # 查找任务
            task = self._find_task_in_queue(task_id)
            if not task:
                return {"error": "Task not found"}
            
            # 检查依赖关系
            if not self._check_dependencies(task.get("dependencies", [])):
                return {"error": "Dependencies not satisfied"}
            
            # 检查资源可用性
            if not self._check_resource_availability():
                return {"error": "Insufficient resources"}
            
            # 启动任务
            task["status"] = ResearchStatus.IN_PROGRESS.value
            task["started_at"] = datetime.now().isoformat()
            
            # 移动到活跃研究
            self.active_research[task_id] = task
            self.research_queue = [t for t in self.research_queue if t["task_id"] != task_id]
            
            return {
                "task_id": task_id,
                "status": "started",
                "started_at": task["started_at"],
                "estimated_completion": self._estimate_completion_time(task_id),
            }
            
        except Exception as e:
            logger.error(f"Error starting research task {task_id}: {str(e)}")
            return {"error": str(e)}
    
    def complete_research_task(self, task_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        完成研究任务
        
        Args:
            task_id: 任务ID
            results: 研究结果
            
        Returns:
            完成结果
        """
        try:
            if task_id not in self.active_research:
                return {"error": "Task not active"}
            
            task = self.active_research[task_id]
            
            # 更新任务状态
            task["status"] = ResearchStatus.COMPLETED.value
            task["completed_at"] = datetime.now().isoformat()
            task["results"] = results
            
            # 移动到已完成研究
            self.completed_research.append(task)
            del self.active_research[task_id]
            
            # 保存结果
            self.research_results[task_id] = results
            
            # 释放资源
            self._release_resources(task_id)
            
            # 触发依赖任务
            self._trigger_dependent_tasks(task_id)
            
            return {
                "task_id": task_id,
                "status": "completed",
                "completed_at": task["completed_at"],
                "duration": self._calculate_task_duration(task),
            }
            
        except Exception as e:
            logger.error(f"Error completing research task {task_id}: {str(e)}")
            return {"error": str(e)}
    
    def _assess_research_capacity(self) -> Dict[str, Any]:
        """评估研究能力"""
        active_count = len(self.active_research)
        capacity_ratio = active_count / self.max_concurrent_research
        
        return {
            "current_load": active_count,
            "max_capacity": self.max_concurrent_research,
            "capacity_ratio": capacity_ratio,
            "available_slots": self.max_concurrent_research - active_count,
            "capacity_status": "overloaded" if capacity_ratio > 0.9 else "busy" if capacity_ratio > 0.7 else "available",
        }
    
    def _assess_resource_availability(self) -> Dict[str, Any]:
        """评估资源可用性"""
        return {
            "cpu_available": 0.75,
            "memory_available": 0.68,
            "network_bandwidth": 0.82,
            "api_rate_limit": 0.85,
            "overall_availability": 0.77,
            "resource_status": "good",
        }
    
    def _analyze_research_queue(self, research_queue: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析研究队列"""
        if not research_queue:
            return {"queue_status": "empty", "total_tasks": 0}
        
        priority_counts = {}
        for task in research_queue:
            priority = task.get("priority", ResearchPriority.MEDIUM.value)
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        wait_times = []
        for task in research_queue:
            wait_time = self._calculate_wait_time(task)
            wait_times.append(wait_time)
        
        avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
        
        return {
            "queue_status": "active",
            "total_tasks": len(research_queue),
            "priority_distribution": priority_counts,
            "average_wait_time": avg_wait_time,
            "queue_length": len(research_queue),
            "queue_efficiency": "good" if avg_wait_time < 300 else "moderate" if avg_wait_time < 600 else "poor",
        }
    
    def _analyze_active_research(self, active_research: Dict[str, Any]) -> Dict[str, Any]:
        """分析活跃研究"""
        if not active_research:
            return {"active_status": "idle", "active_count": 0}
        
        running_times = []
        for task_id, task in active_research.items():
            if "started_at" in task:
                running_time = self._calculate_running_time(task)
                running_times.append(running_time)
        
        avg_running_time = sum(running_times) / len(running_times) if running_times else 0
        
        return {
            "active_status": "busy",
            "active_count": len(active_research),
            "average_running_time": avg_running_time,
            "research_types": [task.get("research_type") for task in active_research.values()],
            "resource_utilization": len(active_research) / self.max_concurrent_research,
        }
    
    def _analyze_research_dependencies(self, dependencies: Dict[str, Any]) -> Dict[str, Any]:
        """分析研究依赖关系"""
        if not dependencies:
            return {"dependency_status": "independent", "dependency_count": 0}
        
        total_dependencies = sum(len(deps) for deps in dependencies.values())
        resolved_dependencies = sum(
            1 for deps in dependencies.values() 
            if all(self._is_dependency_resolved(dep) for dep in deps)
        )
        
        return {
            "dependency_status": "complex" if total_dependencies > 5 else "simple",
            "dependency_count": total_dependencies,
            "resolved_dependencies": resolved_dependencies,
            "pending_dependencies": total_dependencies - resolved_dependencies,
            "dependency_resolution_rate": resolved_dependencies / total_dependencies if total_dependencies > 0 else 0,
        }
    
    def _analyze_resource_availability(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析资源可用性"""
        overall_avail = resource_data.get("overall_availability", 0.0)
        
        return {
            "resource_status": "adequate" if overall_avail > 0.7 else "limited" if overall_avail > 0.4 else "critical",
            "resource_efficiency": overall_avail,
            "bottleneck_resources": self._identify_bottlenecks(resource_data),
            "resource_optimization_opportunities": self._identify_optimization_opportunities(resource_data),
        }
    
    def _optimize_research_scheduling(self, queue_analysis: Dict[str, Any], 
                                   active_analysis: Dict[str, Any], 
                                   resource_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """优化研究调度"""
        optimization_recommendations = []
        
        # 基于队列长度的优化
        if queue_analysis.get("queue_length", 0) > 10:
            optimization_recommendations.append("增加并发研究数量")
        
        # 基于资源利用率的优化
        if active_analysis.get("resource_utilization", 0) < 0.5:
            optimization_recommendations.append("提高资源利用率")
        
        # 基于等待时间的优化
        if queue_analysis.get("average_wait_time", 0) > 600:
            optimization_recommendations.append("优化任务优先级")
        
        return {
            "optimization_needed": len(optimization_recommendations) > 0,
            "recommendations": optimization_recommendations,
            "priority": "high" if len(optimization_recommendations) > 2 else "medium" if len(optimization_recommendations) > 0 else "low",
        }
    
    def _coordinate_research_activities(self, scheduling_optimization: Dict[str, Any], 
                                      dependency_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """协调研究活动"""
        coordination_strategies = []
        
        # 基于依赖关系的协调
        if dependency_analysis.get("pending_dependencies", 0) > 0:
            coordination_strategies.append("优先解决依赖关系")
        
        # 基于调度的协调
        if scheduling_optimization.get("optimization_needed", False):
            coordination_strategies.append("实施调度优化")
        
        return {
            "coordination_strategy": "active" if coordination_strategies else "passive",
            "coordination_actions": coordination_strategies,
            "workflow_efficiency": 0.75,  # 模拟效率评分
        }
    
    def _generate_research_plan(self, research_coordination: Dict[str, Any], 
                               resource_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成研究计划"""
        plan = {
            "immediate_actions": [],
            "scheduled_tasks": [],
            "resource_allocation": {},
            "timeline": {},
        }
        
        # 基于协调策略生成计划
        if research_coordination.get("coordination_strategy") == "active":
            plan["immediate_actions"].extend(research_coordination.get("coordination_actions", []))
        
        # 基于资源分析分配资源
        if resource_analysis.get("resource_status") == "adequate":
            plan["resource_allocation"] = {
                "cpu": 0.6,
                "memory": 0.5,
                "network": 0.4,
            }
        
        return plan
    
    def _assess_research_efficiency(self, active_analysis: Dict[str, Any], 
                                  queue_analysis: Dict[str, Any], 
                                  research_coordination: Dict[str, Any]) -> Dict[str, Any]:
        """评估研究效率"""
        efficiency_factors = []
        
        # 活跃研究效率
        if active_analysis.get("average_running_time", 0) < 300:
            efficiency_factors.append("活跃研究效率高")
        
        # 队列效率
        if queue_analysis.get("queue_efficiency") == "good":
            efficiency_factors.append("队列管理效率高")
        
        # 协调效率
        if research_coordination.get("workflow_efficiency", 0) > 0.7:
            efficiency_factors.append("工作流程效率高")
        
        overall_efficiency = len(efficiency_factors) / 3.0
        
        return {
            "overall_efficiency": overall_efficiency,
            "efficiency_level": "high" if overall_efficiency > 0.8 else "medium" if overall_efficiency > 0.6 else "low",
            "efficiency_factors": efficiency_factors,
            "improvement_areas": self._identify_improvement_areas(
                active_analysis, queue_analysis, research_coordination
            ),
        }
    
    def _validate_research_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """验证研究任务"""
        required_fields = ["symbol", "research_type"]
        
        for field in required_fields:
            if field not in task:
                return {"valid": False, "error": f"Missing required field: {field}"}
        
        # 验证研究类型
        valid_types = [rt.value for rt in ResearchType]
        if task["research_type"] not in valid_types:
            return {"valid": False, "error": f"Invalid research type: {task['research_type']}"}
        
        return {"valid": True}
    
    def _sort_research_queue(self):
        """排序研究队列"""
        priority_order = {
            ResearchPriority.HIGH.value: 3,
            ResearchPriority.MEDIUM.value: 2,
            ResearchPriority.LOW.value: 1,
        }
        
        self.research_queue.sort(
            key=lambda x: (
                -priority_order.get(x.get("priority", ResearchPriority.MEDIUM.value), 2),
                x.get("submitted_at", "")
            )
        )
    
    def _find_task_in_queue(self, task_id: str) -> Optional[Dict[str, Any]]:
        """在队列中查找任务"""
        for task in self.research_queue:
            if task["task_id"] == task_id:
                return task
        return None
    
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查依赖关系"""
        for dep_id in dependencies:
            if dep_id not in self.research_results:
                return False
        return True
    
    def _check_resource_availability(self) -> bool:
        """检查资源可用性"""
        return len(self.active_research) < self.max_concurrent_research
    
    def _estimate_start_time(self, task_id: str) -> str:
        """估计开始时间"""
        # 简化的开始时间估计
        queue_position = next((i for i, task in enumerate(self.research_queue) if task["task_id"] == task_id), 0)
        estimated_minutes = queue_position * 10  # 假设每个任务平均10分钟
        
        start_time = datetime.now() + timedelta(minutes=estimated_minutes)
        return start_time.isoformat()
    
    def _estimate_completion_time(self, task_id: str) -> str:
        """估计完成时间"""
        if task_id in self.active_research:
            task = self.active_research[task_id]
            duration = task.get("estimated_duration", 300)
            completion_time = datetime.now() + timedelta(seconds=duration)
            return completion_time.isoformat()
        return "unknown"
    
    def _calculate_wait_time(self, task: Dict[str, Any]) -> float:
        """计算等待时间"""
        submitted_at = datetime.fromisoformat(task.get("submitted_at", datetime.now().isoformat()))
        return (datetime.now() - submitted_at).total_seconds()
    
    def _calculate_running_time(self, task: Dict[str, Any]) -> float:
        """计算运行时间"""
        started_at = datetime.fromisoformat(task.get("started_at", datetime.now().isoformat()))
        return (datetime.now() - started_at).total_seconds()
    
    def _calculate_task_duration(self, task: Dict[str, Any]) -> float:
        """计算任务持续时间"""
        if "started_at" in task and "completed_at" in task:
            started_at = datetime.fromisoformat(task["started_at"])
            completed_at = datetime.fromisoformat(task["completed_at"])
            return (completed_at - started_at).total_seconds()
        return 0.0
    
    def _release_resources(self, task_id: str):
        """释放资源"""
        # 模拟资源释放
        pass
    
    def _trigger_dependent_tasks(self, task_id: str):
        """触发依赖任务"""
        # 查找依赖此任务的任务
        for task in self.research_queue:
            if task_id in task.get("dependencies", []):
                # 检查是否所有依赖都已完成
                if self._check_dependencies(task.get("dependencies", [])):
                    # 可以启动任务
                    pass
    
    def _is_dependency_resolved(self, dep_id: str) -> bool:
        """检查依赖是否已解决"""
        return dep_id in self.research_results
    
    def _identify_bottlenecks(self, resource_data: Dict[str, Any]) -> List[str]:
        """识别瓶颈资源"""
        bottlenecks = []
        
        if resource_data.get("cpu_available", 1.0) < 0.5:
            bottlenecks.append("CPU")
        
        if resource_data.get("memory_available", 1.0) < 0.5:
            bottlenecks.append("内存")
        
        if resource_data.get("network_bandwidth", 1.0) < 0.5:
            bottlenecks.append("网络带宽")
        
        return bottlenecks
    
    def _identify_optimization_opportunities(self, resource_data: Dict[str, Any]) -> List[str]:
        """识别优化机会"""
        opportunities = []
        
        if resource_data.get("cpu_available", 1.0) > 0.8:
            opportunities.append("CPU利用率不足")
        
        if resource_data.get("memory_available", 1.0) > 0.8:
            opportunities.append("内存利用率不足")
        
        return opportunities
    
    def _identify_improvement_areas(self, active_analysis: Dict[str, Any], 
                                   queue_analysis: Dict[str, Any], 
                                   research_coordination: Dict[str, Any]) -> List[str]:
        """识别改进领域"""
        improvements = []
        
        if active_analysis.get("average_running_time", 0) > 600:
            improvements.append("任务执行时间过长")
        
        if queue_analysis.get("average_wait_time", 0) > 600:
            improvements.append("队列等待时间过长")
        
        if research_coordination.get("workflow_efficiency", 0) < 0.6:
            improvements.append("工作流程效率需要提升")
        
        return improvements
    
    def _calculate_confidence(self, efficiency_metrics: Dict[str, Any], 
                            resource_analysis: Dict[str, Any]) -> float:
        """计算分析置信度"""
        efficiency = efficiency_metrics.get("overall_efficiency", 0.5)
        resource_avail = resource_analysis.get("overall_availability", 0.5)
        
        return (efficiency + resource_avail) / 2
    
    def _generate_research_dashboard(self, queue_analysis: Dict[str, Any], 
                                   active_analysis: Dict[str, Any], 
                                   efficiency_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """生成研究仪表板"""
        return {
            "queue_status": queue_analysis.get("queue_status", "empty"),
            "active_count": active_analysis.get("active_count", 0),
            "efficiency_score": efficiency_metrics.get("overall_efficiency", 0.0),
            "system_load": len(self.active_research) / self.max_concurrent_research,
            "total_tasks_today": len(self.completed_research),
            "average_completion_time": 300,  # 模拟平均完成时间
            "last_updated": datetime.now().isoformat(),
        }

    def synthesize(self, bull_analysis: Dict[str, Any], bear_analysis: Dict[str, Any], 
                  debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """
        综合看涨和看跌研究分析结果
        
        Args:
            bull_analysis: 看涨研究员分析结果
            bear_analysis: 看跌研究员分析结果
            debate_material: 辩论材料
            
        Returns:
            综合研究分析结果
        """
        try:
            # 提取关键指标
            bull_confidence = bull_analysis.get("confidence", 0.5)
            bear_confidence = bear_analysis.get("confidence", 0.5)
            
            bull_signals = bull_analysis.get("bull_signals", [])
            bear_signals = bear_analysis.get("bear_signals", [])
            
            # 计算综合置信度
            combined_confidence = (bull_confidence + bear_confidence) / 2
            
            # 分析信号一致性
            signal_consensus = self._analyze_signal_consensus(bull_signals, bear_signals)
            
            # 生成综合建议
            synthesis_recommendation = self._generate_synthesis_recommendation(
                bull_analysis, bear_analysis, signal_consensus
            )
            
            # 整合研究材料
            integrated_material = self._integrate_research_material(debate_material)
            
            return {
                "synthesis_timestamp": datetime.now().isoformat(),
                "bull_analysis_summary": {
                    "confidence": bull_confidence,
                    "key_signals": bull_signals[:3],  # 前3个关键信号
                    "primary_conclusion": bull_analysis.get("conclusion", "bullish")
                },
                "bear_analysis_summary": {
                    "confidence": bear_confidence,
                    "key_signals": bear_signals[:3],  # 前3个关键信号
                    "primary_conclusion": bear_analysis.get("conclusion", "bearish")
                },
                "signal_consensus": signal_consensus,
                "combined_confidence": combined_confidence,
                "synthesis_recommendation": synthesis_recommendation,
                "integrated_research": integrated_material,
                "research_quality": self._assess_research_quality(bull_analysis, bear_analysis),
                "key_insights": self._extract_key_insights(bull_analysis, bear_analysis),
                "research_citation": {
                    "bull_researcher": "BullResearcher",
                    "bear_researcher": "BearResearcher",
                    "synthesis_method": "weighted_consensus",
                    "confidence_weighting": "equal"
                }
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing research analysis: {str(e)}")
            return {
                "synthesis_timestamp": datetime.now().isoformat(),
                "error": f"Research synthesis failed: {str(e)}",
                "bull_analysis_summary": {"confidence": 0.0, "key_signals": [], "primary_conclusion": "unknown"},
                "bear_analysis_summary": {"confidence": 0.0, "key_signals": [], "primary_conclusion": "unknown"},
                "signal_consensus": "unknown",
                "combined_confidence": 0.0,
                "synthesis_recommendation": {"action": "hold", "reasoning": "synthesis_error"},
                "integrated_research": {},
                "research_quality": "poor",
                "key_insights": ["Research synthesis encountered an error"],
                "research_citation": {}
            }
    
    def _analyze_signal_consensus(self, bull_signals: List[str], bear_signals: List[str]) -> str:
        """分析信号一致性"""
        try:
            # 计算信号强度
            bull_strength = len(bull_signals)
            bear_strength = len(bear_signals)
            
            if bull_strength > bear_strength * 1.5:
                return "strong_bullish"
            elif bear_strength > bull_strength * 1.5:
                return "strong_bearish"
            elif abs(bull_strength - bear_strength) <= 1:
                return "balanced"
            elif bull_strength > bear_strength:
                return "moderate_bullish"
            else:
                return "moderate_bearish"
                
        except Exception as e:
            logger.error(f"Error analyzing signal consensus: {str(e)}")
            return "unknown"
    
    def _generate_synthesis_recommendation(self, bull_analysis: Dict[str, Any], 
                                         bear_analysis: Dict[str, Any], 
                                         consensus: str) -> Dict[str, Any]:
        """生成综合建议"""
        try:
            # 基于共识生成建议
            if "strong_bullish" in consensus:
                action = "buy"
                reasoning = "Strong bullish consensus from research analysis"
            elif "strong_bearish" in consensus:
                action = "sell"
                reasoning = "Strong bearish consensus from research analysis"
            elif "balanced" in consensus:
                action = "hold"
                reasoning = "Balanced research signals, maintain current position"
            elif "moderate_bullish" in consensus:
                action = "buy"
                reasoning = "Moderate bullish bias in research analysis"
            elif "moderate_bearish" in consensus:
                action = "sell"
                reasoning = "Moderate bearish bias in research analysis"
            else:
                action = "hold"
                reasoning = "Insufficient consensus for clear recommendation"
            
            # 计算综合置信度
            bull_conf = bull_analysis.get("confidence", 0.5)
            bear_conf = bear_analysis.get("confidence", 0.5)
            confidence = (bull_conf + bear_conf) / 2
            
            return {
                "action": action,
                "confidence": confidence,
                "reasoning": reasoning,
                "consensus_level": consensus,
                "risk_adjustment": "moderate" if "moderate" in consensus else "strong" if "strong" in consensus else "neutral"
            }
            
        except Exception as e:
            logger.error(f"Error generating synthesis recommendation: {str(e)}")
            return {
                "action": "hold",
                "confidence": 0.3,
                "reasoning": "Error in recommendation generation",
                "consensus_level": "unknown",
                "risk_adjustment": "neutral"
            }
    
    def _integrate_research_material(self, debate_material: Dict[str, Any]) -> Dict[str, Any]:
        """整合研究材料"""
        try:
            integrated = {}
            
            # 整合各种分析结果
            for key, value in debate_material.items():
                if isinstance(value, dict) and "error" not in value:
                    integrated[key] = {
                        "summary": self._generate_analysis_summary(value),
                        "key_metrics": self._extract_key_metrics(value),
                        "data_quality": self._assess_data_quality(value)
                    }
                else:
                    integrated[key] = value
            
            return integrated
            
        except Exception as e:
            logger.error(f"Error integrating research material: {str(e)}")
            return {"error": f"Material integration failed: {str(e)}"}
    
    def _generate_analysis_summary(self, analysis: Dict[str, Any]) -> str:
        """生成分析摘要"""
        try:
            confidence = analysis.get("confidence", 0.5)
            risk_level = analysis.get("risk_level", "medium")
            
            if confidence > 0.7:
                confidence_desc = "high confidence"
            elif confidence > 0.4:
                confidence_desc = "moderate confidence"
            else:
                confidence_desc = "low confidence"
            
            return f"Analysis with {confidence_desc}, {risk_level} risk assessment"
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {str(e)}")
            return "Analysis summary unavailable"
    
    def _extract_key_metrics(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """提取关键指标"""
        try:
            metrics = {}
            
            # 提取通用指标
            common_metrics = ["confidence", "risk_level", "strength", "momentum"]
            for metric in common_metrics:
                if metric in analysis:
                    metrics[metric] = analysis[metric]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error extracting key metrics: {str(e)}")
            return {}
    
    def _assess_data_quality(self, analysis: Dict[str, Any]) -> str:
        """评估数据质量"""
        try:
            confidence = analysis.get("confidence", 0.5)
            
            if confidence > 0.7:
                return "high"
            elif confidence > 0.4:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"Error assessing data quality: {str(e)}")
            return "unknown"
    
    def _assess_research_quality(self, bull_analysis: Dict[str, Any], bear_analysis: Dict[str, Any]) -> str:
        """评估研究质量"""
        try:
            bull_confidence = bull_analysis.get("confidence", 0.5)
            bear_confidence = bear_analysis.get("confidence", 0.5)
            
            avg_confidence = (bull_confidence + bear_confidence) / 2
            
            if avg_confidence > 0.7:
                return "excellent"
            elif avg_confidence > 0.5:
                return "good"
            elif avg_confidence > 0.3:
                return "fair"
            else:
                return "poor"
                
        except Exception as e:
            logger.error(f"Error assessing research quality: {str(e)}")
            return "unknown"
    
    def _extract_key_insights(self, bull_analysis: Dict[str, Any], bear_analysis: Dict[str, Any]) -> List[str]:
        """提取关键洞察"""
        try:
            insights = []
            
            # 从看涨分析中提取洞察
            bull_conclusion = bull_analysis.get("conclusion", "")
            if bull_conclusion:
                insights.append(f"Bullish perspective: {bull_conclusion}")
            
            # 从看跌分析中提取洞察
            bear_conclusion = bear_analysis.get("conclusion", "")
            if bear_conclusion:
                insights.append(f"Bearish perspective: {bear_conclusion}")
            
            # 添加其他关键洞察
            bull_signals = bull_analysis.get("bull_signals", [])
            bear_signals = bear_analysis.get("bear_signals", [])
            
            if bull_signals:
                insights.append(f"Key bullish factors: {', '.join(bull_signals[:2])}")
            
            if bear_signals:
                insights.append(f"Key bearish factors: {', '.join(bear_signals[:2])}")
            
            return insights[:5]  # 限制为前5个洞察
            
        except Exception as e:
            logger.error(f"Error extracting key insights: {str(e)}")
            return ["Unable to extract insights due to error"]
