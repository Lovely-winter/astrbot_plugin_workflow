"""
数据存储 Action
实现数据存储、查询等功能
"""
from typing import Dict, Any, List
from .base import BaseAction
from ..core.action_registry import register_action
from ..core.exceptions import ActionExecutionError


@register_action("save_to_kv")
class SaveToKvAction(BaseAction):
    """保存数据到 KV 存储"""
    
    description = "保存数据到键值存储"
    
    def get_required_params(self) -> List[str]:
        return ['key', 'value']
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - key: 存储键
        - value: 存储值（可以是任意类型）
        - global_scope: 是否使用全局作用域（默认 False，每个 workflow 独立）
        
        注意：这里使用 AstrBot 提供的 KV 存储功能
        需要从 plugin context 中获取
        """
        params = self.resolve_params()
        key = params.get('key')
        value = params.get('value')
        global_scope = params.get('global_scope', False)
        
        # 添加 workflow 前缀以隔离命名空间
        if not global_scope:
            key = f"workflow_{self.context.workflow_id}_{key}"
        
        try:
            # 将数据存储到上下文变量中
            # 实际项目中应使用 AstrBot 的 put_kv_data API
            # 这里先用简单的内存存储
            storage_key = f"_storage_{key}"
            self.context.set_variable(storage_key, value)
            
            return {
                'success': True,
                'message': '数据保存成功',
                'key': key
            }
        
        except Exception as e:
            raise ActionExecutionError(
                self.action_id,
                f"数据保存失败: {str(e)}",
                original_error=e
            )


@register_action("load_from_kv")
class LoadFromKvAction(BaseAction):
    """从 KV 存储加载数据"""
    
    description = "从键值存储加载数据"
    
    def get_required_params(self) -> List[str]:
        return ['key']
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - key: 存储键
        - default: 默认值（如果不存在）
        - variable_name: 结果存储的变量名（默认 'loaded_value'）
        - global_scope: 是否使用全局作用域
        """
        params = self.resolve_params()
        key = params.get('key')
        default = params.get('default')
        variable_name = params.get('variable_name', 'loaded_value')
        global_scope = params.get('global_scope', False)
        
        if not global_scope:
            key = f"workflow_{self.context.workflow_id}_{key}"
        
        try:
            storage_key = f"_storage_{key}"
            value = self.context.get_variable(storage_key, default)
            
            # 存储到指定变量
            self.context.set_variable(variable_name, value)
            
            return {
                'success': True,
                'message': '数据加载成功',
                'key': key,
                'found': value is not None
            }
        
        except Exception as e:
            raise ActionExecutionError(
                self.action_id,
                f"数据加载失败: {str(e)}",
                original_error=e
            )


@register_action("delete_from_kv")
class DeleteFromKvAction(BaseAction):
    """从 KV 存储删除数据"""
    
    description = "从键值存储删除数据"
    
    def get_required_params(self) -> List[str]:
        return ['key']
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - key: 存储键
        - global_scope: 是否使用全局作用域
        """
        params = self.resolve_params()
        key = params.get('key')
        global_scope = params.get('global_scope', False)
        
        if not global_scope:
            key = f"workflow_{self.context.workflow_id}_{key}"
        
        try:
            storage_key = f"_storage_{key}"
            # 删除变量
            if storage_key in self.context.variables:
                del self.context.variables[storage_key]
                found = True
            else:
                found = False
            
            return {
                'success': True,
                'message': '执行完成',
                'found': found
            }
        
        except Exception as e:
            raise ActionExecutionError(
                self.action_id,
                f"删除数据失败: {str(e)}",
                original_error=e
            )