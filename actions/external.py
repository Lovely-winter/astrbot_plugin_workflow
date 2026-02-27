"""
外部调用 Action
实现 API 调用、Webhook 等功能
"""
from typing import Dict, Any, List
import aiohttp
from .base import BaseAction
from ..core.action_registry import register_action
from ..core.exceptions import ActionExecutionError


@register_action("call_api")
class CallApiAction(BaseAction):
    """调用外部 API"""
    
    description = "调用外部 API 接口"
    
    def get_required_params(self) -> List[str]:
        return ['url']
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - url: API URL
        - method: 请求方法（默认 POST）
        - headers: 请求头
        - data: 请求体（字典或字符串）
        - json: JSON 请求体
        - timeout: 超时时间
        - result_variable: 结果存储变量名
        """
        params = self.resolve_params()
        url = params.get('url')
        method = params.get('method', 'POST').upper()
        headers = params.get('headers', {})
        data = params.get('data')
        json_data = params.get('json')
        timeout = params.get('timeout', 10.0)
        result_var = params.get('result_variable', 'api_response')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    json=json_data,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    status = response.status
                    
                    # 尝试解析 JSON
                    try:
                        result_data = await response.json()
                    except:
                        result_data = await response.text()
                    
                    # 存储到上下文
                    self.set_result(result_var, result_data)
                    
                    return {
                        'success': status < 400,
                        'message': f'API 调用完成, 状态码: {status}',
                        'status': status,
                        'data': result_data
                    }
        
        except aiohttp.ClientError as e:
            raise ActionExecutionError(
                self.action_id,
                f"API 调用失败: {str(e)}",
                original_error=e
            )
        except Exception as e:
            raise ActionExecutionError(
                self.action_id,
                f"发生错误: {str(e)}",
                original_error=e
            )


@register_action("webhook")
class WebhookAction(BaseAction):
    """发送 Webhook 通知"""
    
    description = "发送 Webhook 通知"
    
    def get_required_params(self) -> List[str]:
        return ['url']
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - url: Webhook URL
        - payload: 发送的数据字典
        - headers: 自定义请求头
        """
        params = self.resolve_params()
        url = params.get('url')
        payload = params.get('payload', {})
        headers = params.get('headers', {'Content-Type': 'application/json'})
        
        # 添加内置变量到 payload
        if isinstance(payload, dict):
            payload['workflow_id'] = self.context.workflow_id
            payload['trace_id'] = self.context.trace_id
            payload['user_id'] = self.context.get_variable('user_id')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5.0)
                ) as response:
                    status = response.status
                    
                    return {
                        'success': status < 400,
                        'message': f'Webhook 发送完成, 状态: {status}',
                        'status': status
                    }
        
        except Exception as e:
            # Webhook 失败不阻断流程，只记录
            return {
                'success': False,
                'message': f'Webhook 发送失败: {str(e)}'
            }