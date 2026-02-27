"""
消息相关 Action
实现消息发送、图片发送、等待输入等功能
"""
from typing import Dict, Any, List
from .base import BaseAction
from ..core.action_registry import register_action
from ..core.exceptions import ActionExecutionError
import astrbot.api.message_components as Comp


@register_action("send_message")
class SendMessageAction(BaseAction):
    """发送文本消息"""
    
    description = "发送文本消息到当前会话"
    
    def get_required_params(self) -> List[str]:
        return ['text']
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - text: 消息文本，支持变量插值
        """
        params = self.resolve_params()
        text = params.get('text', '')
        
        if not text:
            raise ActionExecutionError(
                self.action_id,
                "消息文本不能为空"
            )
        
        event = self.get_event()
        try:
            await event.send(event.plain_result(text))
            return {
                'success': True,
                'message': '消息发送成功',
                'text': text
            }
        except Exception as e:
            raise ActionExecutionError(
                self.action_id,
                f"消息发送失败: {str(e)}",
                original_error=e
            )


@register_action("send_image")
class SendImageAction(BaseAction):
    """发送图片消息"""
    
    description = "发送图片消息"
    
    def get_required_params(self) -> List[str]:
        return ['url']
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - url: 图片 URL 或本地路径
        - caption: 图片描述（可选）
        """
        params = self.resolve_params()
        url = params.get('url', '')
        caption = params.get('caption', '')
        
        if not url:
            raise ActionExecutionError(
                self.action_id,
                "图片 URL 不能为空"
            )
        
        event = self.get_event()
        try:
            # 构建消息链
            chain = []
            if caption:
                chain.append(Comp.Plain(caption))
            
            # 判断是 URL 还是本地路径
            if url.startswith('http://') or url.startswith('https://'):
                chain.append(Comp.Image.fromURL(url))
            else:
                chain.append(Comp.Image.fromFileSystem(url))
            
            await event.send(event.chain_result(chain))
            return {
                'success': True,
                'message': '图片发送成功',
                'url': url
            }
        except Exception as e:
            raise ActionExecutionError(
                self.action_id,
                f"图片发送失败: {str(e)}",
                original_error=e
            )


@register_action("wait_input")
class WaitInputAction(BaseAction):
    """等待用户输入（会话控制）"""
    
    description = "等待用户输入，需要启用会话控制"
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - prompt: 提示文本（可选）
        - timeout: 超时时间（可选）
        - variable_name: 存储用户输入的变量名（默认 'user_input'）
        
        注意：实际等待逻辑在 workflow_factory 的 session_handler 中处理
        此 action 仅作为标记
        """
        params = self.resolve_params()
        prompt = params.get('prompt', '')
        variable_name = params.get('variable_name', 'user_input')
        
        # 如果有提示文本，发送给用户
        if prompt:
            event = self.get_event()
            await event.send(event.plain_result(prompt))
        
        return {
            'success': True,
            'message': '等待用户输入',
            'variable_name': variable_name,
            'waiting': True
        }


@register_action("send_at")
class SendAtAction(BaseAction):
    """@ 提及用户"""
    
    description = "@ 提及指定用户"
    
    def get_required_params(self) -> List[str]:
        return ['user_id']
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - user_id: 用户 ID，可以是 'sender' 表示 @ 发送者
        - text: @ 后的文本（可选）
        """
        params = self.resolve_params()
        user_id = params.get('user_id', '')
        text = params.get('text', '')
        
        event = self.get_event()
        
        # 处理 'sender' 特殊值
        if user_id == 'sender':
            user_id = event.get_sender_id()
        
        try:
            chain = [Comp.At(qq=user_id)]
            if text:
                chain.append(Comp.Plain(" " + text))
            
            await event.send(event.chain_result(chain))
            return {
                'success': True,
                'message': '@发送成功',
                'user_id': user_id
            }
        except Exception as e:
            raise ActionExecutionError(
                self.action_id,
                f"@发送失败: {str(e)}",
                original_error=e
            )


@register_action("send_chain")
class SendChainAction(BaseAction):
    """发送消息链（富媒体消息）"""
    
    description = "发送富媒体消息链"
    
    def get_required_params(self) -> List[str]:
        return ['chain']
    
    async def execute(self) -> Dict[str, Any]:
        """
        参数：
        - chain: 消息链配置列表
          格式: [{"type": "plain", "text": "..."}, {"type": "image", "url": "..."}]
        """
        params = self.resolve_params()
        chain_config = params.get('chain', [])
        
        if not chain_config:
            raise ActionExecutionError(
                self.action_id,
                "消息链不能为空"
            )
        
        event = self.get_event()
        try:
            chain = []
            for item in chain_config:
                item_type = item.get('type', 'plain').lower()
                
                if item_type == 'plain':
                    chain.append(Comp.Plain(item.get('text', '')))
                elif item_type == 'image':
                    url = item.get('url', '')
                    if url.startswith('http'):
                        chain.append(Comp.Image.fromURL(url))
                    else:
                        chain.append(Comp.Image.fromFileSystem(url))
                elif item_type == 'at':
                    chain.append(Comp.At(qq=item.get('user_id', '')))
                # 可以扩展更多类型...
            
            await event.send(event.chain_result(chain))
            return {
                'success': True,
                'message': '消息链发送成功',
                'chain_length': len(chain)
            }
        except Exception as e:
            raise ActionExecutionError(
                self.action_id,
                f"消息链发送失败: {str(e)}",
                original_error=e
            )