"""
执行上下文
存储工作流执行的运行时状态和变量
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import re


class ExecutionContext:
    """
    执行上下文，存储 workflow 执行过程中的状态和变量
    """
    
    def __init__(
        self,
        workflow_id: str,
        event: 'AstrMessageEvent',
        initial_variables: Dict[str, Any] = None,
        debug_mode: bool = False,
        trace_id: str = None
    ):
        """
        初始化执行上下文
        
        Args:
            workflow_id: 工作流 ID
            event: AstrBot 消息事件
            initial_variables: 初始变量
            debug_mode: 调试模式
            trace_id: 追踪 ID
        """
        self.trace_id = trace_id or str(uuid.uuid4())[:8]
        self.workflow_id = workflow_id
        self.event = event
        self.debug_mode = debug_mode
        
        # 变量存储
        self.variables: Dict[str, Any] = initial_variables.copy() if initial_variables else {}
        
        # 设置内置变量
        self._set_builtin_variables()
        
        # 执行状态
        self.current_action_index: int = 0
        self.start_time = datetime.now()
        self.execution_trace: List[Dict[str, Any]] = []  # 执行轨迹
        
        # 错误信息
        self.last_error: Optional[Exception] = None
    
    def _set_builtin_variables(self):
        """设置内置变量"""
        self.variables.update({
            'user_id': self.event.get_sender_id(),
            'user_name': self.event.get_sender_name(),
            'message': self.event.message_str,
            'group_id': self.event.get_group_id() or '',
            'platform': self.event.message_obj.type.value if hasattr(self.event.message_obj.type, 'value') else 'unknown',
            'timestamp': int(datetime.now().timestamp()),
            'trace_id': self.trace_id
        })
    
    def set_variable(self, key: str, value: Any):
        """
        设置变量
        
        Args:
            key: 变量名，支持点号访问如 'data.result'
            value: 变量值
        """
        if '.' in key:
            # 嵌套设置
            parts = key.split('.')
            current = self.variables
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            self.variables[key] = value
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """
        获取变量
        
        Args:
            key: 变量名，支持点号访问如 'data.result'
            default: 默认值
            
        Returns:
            变量值
        """
        if '.' in key:
            # 嵌套获取
            parts = key.split('.')
            current = self.variables
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current
        else:
            return self.variables.get(key, default)
    
    def resolve_string(self, template: str) -> str:
        """
        解析字符串模板中的变量插值
        将 {variable} 替换为实际值
        
        Args:
            template: 模板字符串
            
        Returns:
            解析后的字符串
        """
        pattern = r'\{([a-zA-Z0-9_\.]+)\}'
        
        def replacer(match):
            var_name = match.group(1)
            value = self.get_variable(var_name)
            return str(value) if value is not None else match.group(0)
        
        return re.sub(pattern, replacer, template)
    
    def record_step(
        self,
        action_index: int,
        action_id: str,
        status: str,
        result: Dict[str, Any] = None,
        error: str = None,
        duration_ms: int = 0
    ):
        """
        记录执行步骤
        
        Args:
            action_index: action 索引
            action_id: action ID
            status: 状态（success/failure/skipped）
            result: 执行结果
            error: 错误信息
            duration_ms: 执行耗时（毫秒）
        """
        step_record = {
            'index': action_index,
            'action_id': action_id,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'duration_ms': duration_ms
        }
        
        if self.debug_mode:
            # 调试模式下记录更详细信息
            step_record['result'] = result
            step_record['error'] = error
            step_record['variables_snapshot'] = self.variables.copy()
        
        self.execution_trace.append(step_record)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        获取执行摘要
        
        Returns:
            执行摘要字典
        """
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        success_count = sum(
            1 for step in self.execution_trace if step['status'] == 'success'
        )
        failure_count = sum(
            1 for step in self.execution_trace if step['status'] == 'failure'
        )
        
        return {
            'trace_id': self.trace_id,
            'workflow_id': self.workflow_id,
            'elapsed_seconds': round(elapsed, 3),
            'total_steps': len(self.execution_trace),
            'success_count': success_count,
            'failure_count': failure_count,
            'final_variables': self.variables if self.debug_mode else None
        }
    
    def get_trace(self) -> List[Dict[str, Any]]:
        """
        获取完整执行轨迹
        
        Returns:
            执行轨迹列表
        """
        return self.execution_trace.copy()
    
    def should_continue(self) -> bool:
        """
        判断是否应该继续执行
        
        Returns:
            是否继续
        """
        # 可以根据需要添加更多判断逻辑
        return True