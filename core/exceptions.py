"""
工作流异常类定义
提供完整的异常层级体系，便于错误处理和用户友好提示
"""
from typing import Dict, Any, Optional
import traceback


class WorkflowError(Exception):
    """工作流基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "WORKFLOW_ERROR",
        user_message: str = None,
        details: Dict[str, Any] = None,
        trace_id: str = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.user_message = user_message or message
        self.details = details or {}
        self.trace_id = trace_id
        self.traceback = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于序列化和日志记录"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
            "trace_id": self.trace_id
        }
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"


# ==================== 配置相关异常 ====================

class ConfigError(WorkflowError):
    """配置相关错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="CONFIG_ERROR",
            user_message=f"配置错误：{message}",
            **kwargs
        )


class ConfigFormatError(ConfigError):
    """配置格式错误"""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        super().__init__(
            message,
            error_code="CONFIG_FORMAT_ERROR",
            user_message=f"配置格式不正确：{message}",
            details=details,
            **kwargs
        )


class ConfigValidationError(ConfigError):
    """配置验证错误"""
    
    def __init__(self, message: str, errors: list = None, **kwargs):
        details = kwargs.get('details', {})
        if errors:
            details['validation_errors'] = errors
        super().__init__(
            message,
            error_code="CONFIG_VALIDATION_ERROR",
            user_message=f"配置验证失败：{message}",
            details=details,
            **kwargs
        )


# ==================== 执行相关异常 ====================

class ExecutionError(WorkflowError):
    """执行相关错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="EXECUTION_ERROR",
            user_message=f"执行失败：{message}",
            **kwargs
        )


class ActionNotFoundError(ExecutionError):
    """Action 不存在"""
    
    def __init__(self, action_id: str, **kwargs):
        super().__init__(
            f"Action '{action_id}' 未注册",
            error_code="ACTION_NOT_FOUND",
            user_message=f"找不到操作：{action_id}",
            details={"action_id": action_id},
            **kwargs
        )


class ActionExecutionError(ExecutionError):
    """Action 执行错误"""
    
    def __init__(
        self,
        action_id: str,
        message: str,
        original_error: Exception = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            "action_id": action_id,
            "original_error": str(original_error) if original_error else None
        })
        super().__init__(
            f"Action '{action_id}' 执行失败: {message}",
            error_code="ACTION_EXECUTION_ERROR",
            user_message=f"操作执行失败：{message}",
            details=details,
            **kwargs
        )


class ActionParameterError(ExecutionError):
    """Action 参数错误"""
    
    def __init__(self, action_id: str, param_name: str, message: str, **kwargs):
        super().__init__(
            f"Action '{action_id}' 参数 '{param_name}' 错误: {message}",
            error_code="ACTION_PARAMETER_ERROR",
            user_message=f"参数错误：{param_name} - {message}",
            details={"action_id": action_id, "param_name": param_name},
            **kwargs
        )


class WorkflowTimeoutError(ExecutionError):
    """工作流超时"""
    
    def __init__(self, workflow_id: str, timeout: float, **kwargs):
        super().__init__(
            f"Workflow '{workflow_id}' 执行超时 ({timeout}s)",
            error_code="WORKFLOW_TIMEOUT",
            user_message=f"操作超时（{timeout}秒），请稍后再试",
            details={"workflow_id": workflow_id, "timeout": timeout},
            **kwargs
        )


class FlowControlError(ExecutionError):
    """流程控制错误（跳转索引越界等）"""
    
    def __init__(self, message: str, current_index: int = None, **kwargs):
        details = kwargs.get('details', {})
        if current_index is not None:
            details['current_index'] = current_index
        super().__init__(
            message,
            error_code="FLOW_CONTROL_ERROR",
            user_message=f"流程控制错误：{message}",
            details=details,
            **kwargs
        )


# ==================== 会话相关异常 ====================

class SessionError(WorkflowError):
    """会话相关错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="SESSION_ERROR",
            user_message=f"会话错误：{message}",
            **kwargs
        )


class SessionNotFoundError(SessionError):
    """会话不存在"""
    
    def __init__(self, session_id: str, **kwargs):
        super().__init__(
            f"Session '{session_id}' 不存在",
            error_code="SESSION_NOT_FOUND",
            user_message="会话不存在或已过期",
            details={"session_id": session_id},
            **kwargs
        )


class SessionTimeoutError(SessionError):
    """会话超时"""
    
    def __init__(self, session_id: str, timeout: float, **kwargs):
        super().__init__(
            f"Session '{session_id}' 超时 ({timeout}s)",
            error_code="SESSION_TIMEOUT",
            user_message=f"会话超时（{timeout}秒），已自动结束",
            details={"session_id": session_id, "timeout": timeout},
            **kwargs
        )


class SessionConcurrentError(SessionError):
    """会话并发冲突"""
    
    def __init__(self, session_id: str, **kwargs):
        super().__init__(
            f"Session '{session_id}' 存在并发冲突",
            error_code="SESSION_CONCURRENT_ERROR",
            user_message="请等待当前会话结束后再试",
            details={"session_id": session_id},
            **kwargs
        )


# ==================== 注册相关异常 ====================

class RegistrationError(WorkflowError):
    """注册相关错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="REGISTRATION_ERROR",
            user_message=f"注册失败：{message}",
            **kwargs
        )


class DuplicateIdError(RegistrationError):
    """ID 重复"""
    
    def __init__(self, entity_type: str, entity_id: str, **kwargs):
        super().__init__(
            f"{entity_type} '{entity_id}' 已存在",
            error_code="DUPLICATE_ID",
            user_message=f"{entity_type} ID 重复：{entity_id}",
            details={"entity_type": entity_type, "entity_id": entity_id},
            **kwargs
        )


class TriggerConflictError(RegistrationError):
    """触发器冲突"""
    
    def __init__(
        self,
        trigger_type: str,
        trigger_value: str,
        existing_workflow: str,
        new_workflow: str,
        **kwargs
    ):
        super().__init__(
            f"触发器冲突：{trigger_type} '{trigger_value}' "
            f"已被 workflow '{existing_workflow}' 使用",
            error_code="TRIGGER_CONFLICT",
            user_message=f"触发器 '{trigger_value}' 已被其他工作流占用",
            details={
                "trigger_type": trigger_type,
                "trigger_value": trigger_value,
                "existing_workflow": existing_workflow,
                "new_workflow": new_workflow
            },
            **kwargs
        )


# ==================== 工具函数 ====================

def format_error_for_user(error: Exception, include_trace: bool = False) -> str:
    """
    格式化错误信息为用户友好的字符串
    
    Args:
        error: 异常对象
        include_trace: 是否包含 trace_id
        
    Returns:
        格式化后的错误消息
    """
    if isinstance(error, WorkflowError):
        msg = error.user_message
        if include_trace and error.trace_id:
            msg += f"\n[追踪ID: {error.trace_id}]"
        return msg
    else:
        return f"发生未知错误：{str(error)}"


def create_error_result(
    error: Exception,
    trace_id: str = None,
    include_details: bool = False
) -> Dict[str, Any]:
    """
    创建标准化的错误结果字典
    
    Args:
        error: 异常对象
        trace_id: 追踪 ID
        include_details: 是否包含详细信息
        
    Returns:
        错误结果字典
    """
    if isinstance(error, WorkflowError):
        result = error.to_dict()
        if trace_id:
            result['trace_id'] = trace_id
        if not include_details:
            result.pop('details', None)
        return result
    else:
        return {
            "error_code": "UNKNOWN_ERROR",
            "message": str(error),
            "user_message": "发生未知错误",
            "trace_id": trace_id
        }