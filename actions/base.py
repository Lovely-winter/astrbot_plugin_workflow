"""
Action 抽象基类
定义所有 action 的通用接口和辅助方法
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import re


class BaseAction(ABC):
    """
    Action 抽象基类
    所有具体的 action 必须继承此类并实现 execute 方法
    """
    
    # 子类应该设置这些属性
    action_id: str = ""  # 由装饰器自动设置
    description: str = ""  # Action 描述
    
    def __init__(self, context: 'ExecutionContext', config: 'ActionConfig'):
        """
        初始化 Action
        
        Args:
            context: 执行上下文
            config: 动作配置
        """
        self.context = context
        self.config = config
        self.params = config.params.copy()
    
    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """
        执行 action 的核心逻辑
        
        Returns:
            执行结果字典，可包含任意键值对
            建议包含 'success': bool 和 'message': str
        """
        pass
    
    def get_required_params(self) -> List[str]:
        """
        获取必填参数列表（子类可覆盖）
        
        Returns:
            必填参数名列表
        """
        return []
    
    def validate_params(self) -> None:
        """
        验证参数（子类可覆盖）
        
        Raises:
            ActionParameterError: 参数验证失败
        """
        from ..core.exceptions import ActionParameterError
        
        required = self.get_required_params()
        for param_name in required:
            if param_name not in self.params:
                raise ActionParameterError(
                    self.action_id,
                    param_name,
                    "缺少必填参数"
                )
    
    def resolve_params(self) -> Dict[str, Any]:
        """
        解析参数中的变量插值
        将 {variable} 替换为上下文中的实际值
        
        Returns:
            解析后的参数字典
        """
        resolved = {}
        for key, value in self.params.items():
            if isinstance(value, str):
                resolved[key] = self._resolve_string(value)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_dict(value)
            elif isinstance(value, list):
                resolved[key] = self._resolve_list(value)
            else:
                resolved[key] = value
        return resolved
    
    def _resolve_string(self, text: str) -> str:
        """
        解析字符串中的变量插值
        
        Args:
            text: 待解析的文本
            
        Returns:
            解析后的文本
        """
        # 匹配 {variable} 或 {variable.nested}
        pattern = r'\{([a-zA-Z0-9_\.]+)\}'
        
        def replacer(match):
            var_path = match.group(1)
            value = self.context.get_variable(var_path)
            return str(value) if value is not None else match.group(0)
        
        return re.sub(pattern, replacer, text)
    
    def _resolve_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """递归解析字典"""
        resolved = {}
        for key, value in data.items():
            if isinstance(value, str):
                resolved[key] = self._resolve_string(value)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_dict(value)
            elif isinstance(value, list):
                resolved[key] = self._resolve_list(value)
            else:
                resolved[key] = value
        return resolved
    
    def _resolve_list(self, data: List[Any]) -> List[Any]:
        """递归解析列表"""
        resolved = []
        for item in data:
            if isinstance(item, str):
                resolved.append(self._resolve_string(item))
            elif isinstance(item, dict):
                resolved.append(self._resolve_dict(item))
            elif isinstance(item, list):
                resolved.append(self._resolve_list(item))
            else:
                resolved.append(item)
        return resolved
    
    def set_result(self, key: str, value: Any):
        """
        将结果存储到上下文变量中
        
        Args:
            key: 变量名
            value: 变量值
        """
        self.context.set_variable(key, value)
    
    def get_event(self):
        """
        获取事件对象
        
        Returns:
            AstrMessageEvent 对象
        """
        return self.context.event
    
    async def send_message(self, text: str):
        """
        发送消息的便捷方法
        
        Args:
            text: 消息文本
        """
        event = self.get_event()
        await event.send(event.plain_result(text))