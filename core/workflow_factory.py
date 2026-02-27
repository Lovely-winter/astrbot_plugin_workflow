"""
Workflow 处理器工厂
动态创建 handler 函数并应用装饰器
"""
from typing import Callable, Any
import uuid
import time
import asyncio
from datetime import datetime
from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.utils.session_waiter import session_waiter, SessionController

from .workflow_definition import WorkflowDefinition, TriggerType, ErrorHandlingStrategy
from .execution_context import ExecutionContext
from .action_registry import get_action_class
from .exceptions import (
    ActionExecutionError,
    ActionNotFoundError,
    FlowControlError,
    format_error_for_user
)
from .validators import validate_condition


class ActionExecutor:
    """Action 执行器"""
    
    def __init__(self, context: ExecutionContext, workflow: WorkflowDefinition):
        self.context = context
        self.workflow = workflow
    
    async def execute_all(self):
        """
        按顺序执行所有 action
        根据 flow_control 控制执行流程
        """
        action_count = len(self.workflow.actions)
        current_index = 0
        
        while current_index < action_count:
            self.context.current_action_index = current_index
            action_config = self.workflow.actions[current_index]
            
            # 检查执行条件
            if action_config.condition:
                try:
                    if not validate_condition(action_config.condition, self.context.variables):
                        # 条件不满足，跳过
                        self.context.record_step(
                            current_index,
                            action_config.action_id,
                            'skipped',
                            result={'reason': 'condition not met'}
                        )
                        current_index += 1
                        continue
                except Exception as e:
                    # 条件校验异常时也跳过，避免中断整个流程
                    self.context.record_step(
                        current_index,
                        action_config.action_id,
                        'skipped',
                        result={'reason': f'condition error: {str(e)}'}
                    )
                    current_index += 1
                    continue
            
            # 执行 action
            success, result, next_index = await self.execute_action(current_index)
            
            # 根据结果决定下一步
            if next_index is not None:
                current_index = next_index
            elif success:
                current_index += 1
            else:
                # 失败处理
                if action_config.error_handling == ErrorHandlingStrategy.STOP:
                    break
                elif action_config.error_handling == ErrorHandlingStrategy.CONTINUE:
                    current_index += 1
                elif action_config.error_handling == ErrorHandlingStrategy.RETRY:
                    # 重试已在 execute_action 内完成，这里直接继续
                    current_index += 1
                elif action_config.error_handling == ErrorHandlingStrategy.JUMP:
                    if action_config.flow_control.on_failure is not None:
                        current_index = action_config.flow_control.on_failure
                    else:
                        break
    
    async def execute_action(self, index: int) -> tuple[bool, dict, int]:
        """
        执行单个 action
        
        Returns:
            (success, result, next_index)
        """
        action_config = self.workflow.actions[index]
        start_time = time.time()
        retry_count = max(0, action_config.retry_count or 0)
        attempt = 0
        
        while True:
            try:
                # 获取 action 类
                ActionClass = get_action_class(action_config.action_id)
                
                # 创建 action 实例
                action_instance = ActionClass(self.context, action_config)
                
                # 验证参数
                action_instance.validate_params()
                
                # 执行
                result = await action_instance.execute()
                
                # 记录执行步骤
                duration_ms = (time.time() - start_time) * 1000
                self.context.record_step(
                    index,
                    action_config.action_id,
                    'success',
                    result=result,
                    duration_ms=duration_ms
                )
                
                # 判断下一步
                next_index = self._get_next_index(action_config, True)
                
                return True, result, next_index
            
            except ActionNotFoundError as e:
                duration_ms = (time.time() - start_time) * 1000
                self.context.record_step(
                    index,
                    action_config.action_id,
                    'failure',
                    error=str(e),
                    duration_ms=duration_ms
                )
                self.context.last_error = e
                return False, {'error': str(e)}, None
            
            except ActionExecutionError as e:
                if attempt < retry_count:
                    attempt += 1
                    delay = 2 ** (attempt - 1)
                    logger.warning(
                        "Action %s failed, retrying (%s/%s)",
                        action_config.action_id,
                        attempt,
                        retry_count
                    )
                    await asyncio.sleep(delay)
                    continue
                
                duration_ms = (time.time() - start_time) * 1000
                self.context.record_step(
                    index,
                    action_config.action_id,
                    'failure',
                    error=e.user_message,
                    duration_ms=duration_ms
                )
                self.context.last_error = e
                return False, {'error': e.user_message}, None
            
            except Exception as e:
                if attempt < retry_count:
                    attempt += 1
                    delay = 2 ** (attempt - 1)
                    logger.warning(
                        "Action %s failed, retrying (%s/%s)",
                        action_config.action_id,
                        attempt,
                        retry_count
                    )
                    await asyncio.sleep(delay)
                    continue
                
                duration_ms = (time.time() - start_time) * 1000
                error_msg = f"未知错误: {str(e)}"
                self.context.record_step(
                    index,
                    action_config.action_id,
                    'failure',
                    error=error_msg,
                    duration_ms=duration_ms
                )
                self.context.last_error = e
                return False, {'error': error_msg}, None
    
    def _get_next_index(self, action_config, success: bool) -> int:
        """
        根据 flow_control 获取下一个 action 索引
        
        Returns:
            下一个索引或 None（表示使用默认流程）
        """
        fc = action_config.flow_control
        
        if success and fc.on_success is not None:
            return fc.on_success
        elif not success and fc.on_failure is not None:
            return fc.on_failure
        elif fc.next is not None:
            return fc.next
        
        return None


class WorkflowHandlerFactory:
    """
    Workflow Handler 工厂
    负责创建动态 handler 函数
    """
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
    
    def create_handler(self, workflow: WorkflowDefinition, plugin_context) -> Callable:
        """
        创建 handler 函数
        
        Args:
            workflow: 工作流定义
            plugin_context: 插件上下文（用于访问插件方法）
            
        Returns:
            handler 函数
        """
        # 使用闭包捕获 workflow 配置
        async def handler(event: AstrMessageEvent, *args, **kwargs):
            """动态生成的 workflow handler"""
            trace_id = str(uuid.uuid4())[:8]
            
            # 创建执行上下文
            context = ExecutionContext(
                workflow_id=workflow.id,
                event=event,
                initial_variables=workflow.variables.copy(),
                debug_mode=self.debug_mode,
                trace_id=trace_id
            )
            
            # 判断是否需要会话控制
            if workflow.session.enabled:
                @session_waiter(
                    timeout=workflow.session.timeout,
                    record_history_chains=workflow.session.record_history
                )
                async def session_handler(controller: SessionController, sess_event: AstrMessageEvent):
                    await self._execute_with_session(
                        workflow,
                        context,
                        plugin_context,
                        controller,
                        sess_event
                    )
                
                try:
                    await session_handler(event)
                except TimeoutError:
                    await context.event.send(
                        context.event.plain_result("⏱️ 会话超时，已自动结束")
                    )
                except Exception as e:
                    error_msg = format_error_for_user(e, include_trace=True)
                    await context.event.send(context.event.plain_result(f"❌ {error_msg}"))
            else:
                # 直接执行
                await self._execute_workflow(workflow, context)
        
        return handler
    
    async def _execute_workflow(self, workflow: WorkflowDefinition, context: ExecutionContext):
        """
        执行工作流（无会话）
        
        Args:
            workflow: 工作流定义
            context: 执行上下文
        """
        try:
            executor = ActionExecutor(context, workflow)
            await executor.execute_all()
            
            # 发送执行摘要（如果开启调试）
            if self.debug_mode:
                summary = context.get_execution_summary()
                await context.event.send(
                    context.event.plain_result(
                        f"✅ 执行完成 [trace: {context.trace_id}]\n"
                        f"耗时: {summary['elapsed_seconds']}s | "
                        f"步骤: {summary['success_count']}/{summary['total_steps']}"
                    )
                )
        
        except Exception as e:
            error_msg = format_error_for_user(e, include_trace=True)
            await context.event.send(context.event.plain_result(f"❌ {error_msg}"))
    
    async def _execute_with_session(
        self,
        workflow: WorkflowDefinition,
        context: ExecutionContext,
        plugin_context,
        controller: SessionController,
        event: AstrMessageEvent
    ):
        """
        执行工作流（会话模式）
        
        Args:
            workflow: 工作流定义
            context: 执行上下文
            plugin_context: 插件上下文
        """
        # 更新 context 的 event
        context.event = event
        
        # 更新内置变量
        context.set_variable('message', event.message_str)
        context.set_variable('user_input', event.message_str)
        
        # 执行 actions
        executor = ActionExecutor(context, workflow)
        current_index = context.current_action_index
        
        # 从当前位置继续执行
        while current_index < len(workflow.actions):
            action_config = workflow.actions[current_index]
            
            # 检查是否是 wait_input action
            if action_config.action_id == 'wait_input':
                # 执行 wait_input（发送提示）
                await executor.execute_action(current_index)
                
                # 保持会话，等待下一次输入
                controller.keep(
                    timeout=workflow.session.timeout,
                    reset_timeout=True
                )
                
                # 更新当前索引为下一个
                context.current_action_index = current_index + 1
                return
            
            # 执行普通 action
            success, result, next_index = await executor.execute_action(current_index)
            
            if next_index is not None:
                current_index = next_index
            else:
                current_index += 1
        
        # 所有 actions 执行完毕，结束会话
        controller.stop()
    
    def apply_decorators(
        self,
        handler: Callable,
        workflow: WorkflowDefinition
    ) -> Callable:
        """
        根据触发器类型应用装饰器
        
        Args:
            handler: 原始 handler 函数
            workflow: 工作流定义
            
        Returns:
            装饰后的 handler
        """
        if not workflow.trigger:
            return handler
        
        trigger = workflow.trigger
        
        # 应用触发器装饰器
        if trigger.type == TriggerType.COMMAND:
            # 指令触发
            alias = set(trigger.alias) if trigger.alias else None
            decorated = filter.command(
                trigger.value,
                alias=alias,
                priority=workflow.priority
            )(handler)
        
        elif trigger.type == TriggerType.KEYWORD:
            # 关键词触发（消息内容包含）
            original_handler = handler
            
            async def keyword_handler(event: AstrMessageEvent, *args, **kwargs):
                if trigger.value and trigger.value in event.message_str:
                    return await original_handler(event, *args, **kwargs)
                return None
            
            event_type = trigger.filters.get('message_type', 'all') if trigger.filters else 'all'
            if event_type == 'group':
                decorated = filter.event_message_type(
                    filter.EventMessageType.GROUP_MESSAGE
                )(keyword_handler)
            elif event_type == 'private':
                decorated = filter.event_message_type(
                    filter.EventMessageType.PRIVATE_MESSAGE
                )(keyword_handler)
            else:
                decorated = filter.event_message_type(
                    filter.EventMessageType.ALL
                )(keyword_handler)
        
        elif trigger.type == TriggerType.EVENT:
            # 事件触发
            from astrbot.api.event import filter
            event_type = trigger.filters.get('message_type', 'all')
            
            if event_type == 'group':
                decorated = filter.event_message_type(
                    filter.EventMessageType.GROUP_MESSAGE
                )(handler)
            elif event_type == 'private':
                decorated = filter.event_message_type(
                    filter.EventMessageType.PRIVATE_MESSAGE
                )(handler)
            else:
                decorated = filter.event_message_type(
                    filter.EventMessageType.ALL
                )(handler)
        
        elif trigger.type == TriggerType.REGEX:
            import re
            try:
                regex_pattern = re.compile(trigger.value)
            except re.error as e:
                logger.error("Invalid regex pattern: %s (%s)", trigger.value, str(e))
                decorated = handler
            else:
                original_handler = handler
                
                async def regex_handler(event: AstrMessageEvent, *args, **kwargs):
                    if regex_pattern.search(event.message_str):
                        return await original_handler(event, *args, **kwargs)
                    return None
                
                event_type = trigger.filters.get('message_type', 'all') if trigger.filters else 'all'
                if event_type == 'group':
                    decorated = filter.event_message_type(
                        filter.EventMessageType.GROUP_MESSAGE
                    )(regex_handler)
                elif event_type == 'private':
                    decorated = filter.event_message_type(
                        filter.EventMessageType.PRIVATE_MESSAGE
                    )(regex_handler)
                else:
                    decorated = filter.event_message_type(
                        filter.EventMessageType.ALL
                    )(regex_handler)
        else:
            decorated = handler
        
        return decorated