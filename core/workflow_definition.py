"""
工作流数据模型定义
使用 dataclass 定义工作流、触发器、动作的配置结构
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class TriggerType(str, Enum):
    """触发器类型枚举"""
    COMMAND = "command"  # 指令触发 /xxx
    KEYWORD = "keyword"  # 关键词触发
    EVENT = "event"  # 事件触发（群消息、私聊消息等）
    REGEX = "regex"  # 正则表达式匹配


class SessionStrategy(str, Enum):
    """会话策略枚举"""
    PER_USER = "per_user"  # 每个用户独立会话
    PER_GROUP = "per_group"  # 整个群作为一个会话
    GLOBAL = "global"  # 全局共享会话（慎用）


class ErrorHandlingStrategy(str, Enum):
    """错误处理策略枚举"""
    STOP = "stop"  # 停止执行
    CONTINUE = "continue"  # 继续执行下一个
    RETRY = "retry"  # 重试当前操作
    JUMP = "jump"  # 跳转到指定 action


@dataclass
class TriggerConfig:
    """触发器配置"""
    type: TriggerType  # 触发器类型
    value: str  # 触发值（指令名、关键词、正则等）
    alias: List[str] = field(default_factory=list)  # 别名列表
    filters: Dict[str, Any] = field(default_factory=dict)  # 额外过滤器配置
    # filters 可包含：message_type（private/group），platform_type 等
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TriggerConfig':
        """从字典创建触发器配置"""
        return cls(
            type=TriggerType(data.get('type', 'command')),
            value=data.get('value', ''),
            alias=data.get('alias', []),
            filters=data.get('filters', {})
        )


@dataclass
class FlowControl:
    """流程控制配置"""
    next: Optional[int] = None  # 默认下一个 action 索引
    on_success: Optional[int] = None  # 成功后跳转索引
    on_failure: Optional[int] = None  # 失败后跳转索引
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlowControl':
        """从字典创建流程控制配置"""
        return cls(
            next=data.get('next'),
            on_success=data.get('on_success'),
            on_failure=data.get('on_failure')
        )


@dataclass
class ActionConfig:
    """动作配置"""
    action_id: str  # Action 类型标识
    params: Dict[str, Any] = field(default_factory=dict)  # 参数字典
    flow_control: FlowControl = field(default_factory=FlowControl)  # 流程控制
    error_handling: ErrorHandlingStrategy = ErrorHandlingStrategy.STOP  # 错误处理策略
    retry_count: int = 0  # 重试次数
    timeout: Optional[float] = None  # 超时时间（秒）
    condition: Optional[str] = None  # 执行条件表达式（如 "{score} > 60"）
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionConfig':
        """从字典创建动作配置"""
        flow_control_data = data.get('flow_control', {})
        if isinstance(flow_control_data, dict):
            flow_control = FlowControl.from_dict(flow_control_data)
        else:
            flow_control = FlowControl()
        
        return cls(
            action_id=data.get('action_id', ''),
            params=data.get('params', {}),
            flow_control=flow_control,
            error_handling=ErrorHandlingStrategy(
                data.get('error_handling', 'stop')
            ),
            retry_count=data.get('retry_count', 0),
            timeout=data.get('timeout'),
            condition=data.get('condition')
        )


@dataclass
class SessionConfig:
    """会话配置"""
    enabled: bool = False  # 是否启用会话控制
    timeout: float = 300.0  # 会话超时时间（秒）
    strategy: SessionStrategy = SessionStrategy.PER_USER  # 会话策略
    record_history: bool = False  # 是否记录历史消息链
    max_history: int = 50  # 最大历史记录数
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionConfig':
        """从字典创建会话配置"""
        return cls(
            enabled=data.get('enabled', False),
            timeout=data.get('timeout', 300.0),
            strategy=SessionStrategy(data.get('strategy', 'per_user')),
            record_history=data.get('record_history', False),
            max_history=data.get('max_history', 50)
        )


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    id: str  # 工作流唯一标识
    name: str  # 工作流名称
    description: str = ""  # 描述
    enabled: bool = True  # 是否启用
    trigger: Optional[TriggerConfig] = None  # 触发器配置
    actions: List[ActionConfig] = field(default_factory=list)  # 动作列表
    session: SessionConfig = field(default_factory=SessionConfig)  # 会话配置
    priority: int = 0  # 优先级（数值越大越优先）
    variables: Dict[str, Any] = field(default_factory=dict)  # 初始变量
    rate_limit: Optional[Dict[str, Any]] = None  # 频率限制配置
    # rate_limit 格式：{"max_calls": 10, "time_window": 60}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowDefinition':
        """从字典创建工作流定义"""
        # 解析触发器
        trigger_data = data.get('trigger')
        trigger = TriggerConfig.from_dict(trigger_data) if trigger_data else None
        
        # 解析动作列表
        actions_data = data.get('actions', [])
        actions = [ActionConfig.from_dict(action) for action in actions_data]
        
        # 解析会话配置
        session_data = data.get('session', {})
        session = SessionConfig.from_dict(session_data)
        
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            enabled=data.get('enabled', True),
            trigger=trigger,
            actions=actions,
            session=session,
            priority=data.get('priority', 0),
            variables=data.get('variables', {}),
            rate_limit=data.get('rate_limit')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'trigger': {
                'type': self.trigger.type.value if self.trigger else None,
                'value': self.trigger.value if self.trigger else None,
                'alias': self.trigger.alias if self.trigger else [],
                'filters': self.trigger.filters if self.trigger else {}
            } if self.trigger else None,
            'actions': [
                {
                    'action_id': action.action_id,
                    'params': action.params,
                    'flow_control': {
                        'next': action.flow_control.next,
                        'on_success': action.flow_control.on_success,
                        'on_failure': action.flow_control.on_failure
                    },
                    'error_handling': action.error_handling.value,
                    'retry_count': action.retry_count,
                    'timeout': action.timeout,
                    'condition': action.condition
                }
                for action in self.actions
            ],
            'session': {
                'enabled': self.session.enabled,
                'timeout': self.session.timeout,
                'strategy': self.session.strategy.value,
                'record_history': self.session.record_history,
                'max_history': self.session.max_history
            },
            'priority': self.priority,
            'variables': self.variables,
            'rate_limit': self.rate_limit
        }