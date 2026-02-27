"""
Action 注册表
提供全局 action 注册机制和查询功能
"""
from typing import Dict, Type, List, Set
from .exceptions import ActionNotFoundError


# 全局 action 注册表
ACTION_REGISTRY: Dict[str, Type] = {}


def register_action(action_id: str):
    """
    Action 注册装饰器
    
    Args:
        action_id: Action 的唯一标识
        
    Example:
        @register_action("send_message")
        class SendMessageAction(BaseAction):
            pass
    """
    def decorator(cls: Type):
        if action_id in ACTION_REGISTRY:
            # 允许覆盖注册（用于热重载）
            pass
        ACTION_REGISTRY[action_id] = cls
        # 将 action_id 存储到类属性中
        cls.action_id = action_id
        return cls
    return decorator


def get_action_class(action_id: str) -> Type:
    """
    获取 action 类
    
    Args:
        action_id: Action 标识
        
    Returns:
        Action 类
        
    Raises:
        ActionNotFoundError: Action 不存在
    """
    if action_id not in ACTION_REGISTRY:
        raise ActionNotFoundError(action_id)
    return ACTION_REGISTRY[action_id]


def list_action_ids() -> List[str]:
    """
    列出所有已注册的 action_id
    
    Returns:
        action_id 列表
    """
    return list(ACTION_REGISTRY.keys())


def get_registered_action_ids() -> Set[str]:
    """
    获取已注册的 action_id 集合（用于验证）
    
    Returns:
        action_id 集合
    """
    return set(ACTION_REGISTRY.keys())


def is_action_registered(action_id: str) -> bool:
    """
    检查 action 是否已注册
    
    Args:
        action_id: Action 标识
        
    Returns:
        是否已注册
    """
    return action_id in ACTION_REGISTRY


def unregister_action(action_id: str) -> bool:
    """
    注销 action（用于热重载）
    
    Args:
        action_id: Action 标识
        
    Returns:
        是否成功注销
    """
    if action_id in ACTION_REGISTRY:
        del ACTION_REGISTRY[action_id]
        return True
    return False


def clear_registry():
    """
    清空注册表（用于测试或重置）
    """
    ACTION_REGISTRY.clear()


def get_action_info() -> Dict[str, Dict[str, any]]:
    """
    获取所有 action 的信息
    
    Returns:
        action 信息字典
    """
    info = {}
    for action_id, action_cls in ACTION_REGISTRY.items():
        info[action_id] = {
            'class_name': action_cls.__name__,
            'module': action_cls.__module__,
            'doc': action_cls.__doc__ or '无描述'
        }
    return info