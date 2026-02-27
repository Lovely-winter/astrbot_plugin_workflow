"""
Workflow 注册表
管理所有已注册的工作流及其执行统计
"""
from typing import Dict, List, Optional
from datetime import datetime
from .workflow_definition import WorkflowDefinition
from .exceptions import DuplicateIdError, TriggerConflictError


class WorkflowStats:
    """工作流执行统计"""
    
    def __init__(self):
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_duration_ms = 0
        self.last_execution_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
    
    def record_execution(self, success: bool, duration_ms: float, error: Optional[str] = None):
        """记录一次执行"""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
            self.last_error = error
        self.total_duration_ms += duration_ms
        self.last_execution_time = datetime.now()
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    def get_avg_duration_ms(self) -> float:
        """获取平均执行时长"""
        if self.total_executions == 0:
            return 0.0
        return self.total_duration_ms / self.total_executions
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': round(self.get_success_rate(), 3),
            'avg_duration_ms': round(self.get_avg_duration_ms(), 2),
            'last_execution_time': self.last_execution_time.isoformat() if self.last_execution_time else None,
            'last_error': self.last_error
        }


class WorkflowRegistry:
    """
    Workflow 注册表
    管理所有已注册的工作流定义和执行统计
    """
    
    def __init__(self):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.stats: Dict[str, WorkflowStats] = {}
        self._trigger_map: Dict[str, str] = {}  # trigger_key -> workflow_id
    
    def register(self, workflow: WorkflowDefinition, allow_override: bool = False):
        """
        注册工作流
        
        Args:
            workflow: 工作流定义
            allow_override: 是否允许覆盖已存在的 workflow
            
        Raises:
            DuplicateIdError: ID 重复且不允许覆盖
            TriggerConflictError: 触发器冲突
        """
        # 1. 检查 ID 冲突
        if workflow.id in self.workflows and not allow_override:
            raise DuplicateIdError("Workflow", workflow.id)
        
        # 2. 检查触发器冲突
        if workflow.trigger:
            trigger_key = self._get_trigger_key(workflow.trigger.type.value, workflow.trigger.value)
            existing_workflow_id = self._trigger_map.get(trigger_key)
            
            if existing_workflow_id and existing_workflow_id != workflow.id:
                # 记录警告但不阻止注册
                print(f"⚠️  触发器冲突: {workflow.trigger.value} 已被 {existing_workflow_id} 使用")
        
        # 3. 注册
        self.workflows[workflow.id] = workflow
        if workflow.id not in self.stats:
            self.stats[workflow.id] = WorkflowStats()
        
        # 4. 更新触发器映射
        if workflow.trigger:
            trigger_key = self._get_trigger_key(workflow.trigger.type.value, workflow.trigger.value)
            self._trigger_map[trigger_key] = workflow.id
    
    def _get_trigger_key(self, trigger_type: str, trigger_value: str) -> str:
        """生成触发器键"""
        return f"{trigger_type}:{trigger_value}"
    
    def get(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        获取工作流定义
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            工作流定义或 None
        """
        return self.workflows.get(workflow_id)
    
    def get_all(self) -> List[WorkflowDefinition]:
        """
        获取所有工作流定义
        
        Returns:
            工作流列表
        """
        return list(self.workflows.values())
    
    def get_enabled(self) -> List[WorkflowDefinition]:
        """
        获取所有已启用的工作流
        
        Returns:
            已启用的工作流列表
        """
        return [wf for wf in self.workflows.values() if wf.enabled]
    
    def unregister(self, workflow_id: str) -> bool:
        """
        注销工作流
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            是否成功注销
        """
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            
            # 移除触发器映射
            if workflow.trigger:
                trigger_key = self._get_trigger_key(
                    workflow.trigger.type.value,
                    workflow.trigger.value
                )
                if self._trigger_map.get(trigger_key) == workflow_id:
                    del self._trigger_map[trigger_key]
            
            del self.workflows[workflow_id]
            return True
        return False
    
    def clear(self):
        """清空所有注册"""
        self.workflows.clear()
        self.stats.clear()
        self._trigger_map.clear()
    
    def record_execution(
        self,
        workflow_id: str,
        success: bool,
        duration_ms: float,
        error: Optional[str] = None
    ):
        """
        记录执行统计
        
        Args:
            workflow_id: 工作流 ID
            success: 是否成功
            duration_ms: 执行时长（毫秒）
            error: 错误信息
        """
        if workflow_id not in self.stats:
            self.stats[workflow_id] = WorkflowStats()
        self.stats[workflow_id].record_execution(success, duration_ms, error)
    
    def get_stats(self, workflow_id: Optional[str] = None) -> Dict:
        """
        获取统计信息
        
        Args:
            workflow_id: 工作流 ID（可选，None 则返回所有统计）
            
        Returns:
            统计信息字典
        """
        if workflow_id:
            if workflow_id in self.stats:
                return {workflow_id: self.stats[workflow_id].to_dict()}
            return {}
        else:
            return {wf_id: stat.to_dict() for wf_id, stat in self.stats.items()}
    
    def get_summary(self) -> Dict:
        """
        获取注册表摘要
        
        Returns:
            摘要信息字典
        """
        total_workflows = len(self.workflows)
        enabled_workflows = len(self.get_enabled())
        
        total_executions = sum(stat.total_executions for stat in self.stats.values())
        total_successes = sum(stat.successful_executions for stat in self.stats.values())
        
        return {
            'total_workflows': total_workflows,
            'enabled_workflows': enabled_workflows,
            'disabled_workflows': total_workflows - enabled_workflows,
            'total_executions': total_executions,
            'total_successes': total_successes,
            'overall_success_rate': round(total_successes / total_executions, 3) if total_executions > 0 else 0.0
        }