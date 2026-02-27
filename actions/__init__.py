"""
Actions 模块初始化
自动导入所有 action 模块，确保装饰器被执行并注册
"""

# 导入所有 action 模块以触发装饰器注册
from . import base  # 基类
from . import message  # 消息相关
from . import http  # HTTP 请求
from . import external  # 外部调用
from . import database  # 数据存储
from . import platform_advanced  # 平台高级功能

# 从 registry 导出以供外部使用
from ..core.action_registry import (
    ACTION_REGISTRY,
    register_action,
    get_action_class,
    list_action_ids,
    get_registered_action_ids,
    is_action_registered
)

__all__ = [
    'ACTION_REGISTRY',
    'register_action',
    'get_action_class',
    'list_action_ids',
    'get_registered_action_ids',
    'is_action_registered',
    'base',
    'message',
    'http',
    'external',
    'database',
    'platform_advanced'
]