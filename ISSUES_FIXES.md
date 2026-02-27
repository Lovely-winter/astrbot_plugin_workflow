# AstrBot Workflow 插件 - 问题修复指南

## 快速问题参考

> 本文档提供了所有发现问题的快速查询和修复建议

---

## 🔴 P0 优先级 - 功能障碍

### 1. 会话控制装饰器应用错误

**🏷️ ID**: `WF-001`  
**📍 位置**: [core/workflow_factory.py#L253-L318](core/workflow_factory.py#L253)  
**⚠️ 严重程度**: 🔴 CRITICAL  
**📊 影响范围**: 所有启用会话的工作流无法正常工作

#### 问题描述

当前代码在 `_execute_with_session()` 方法内部定义和装饰 `session_handler` 函数，但装饰器不会生效：

```python
# ❌ 错误方式
async def _execute_with_session(self, workflow, context, plugin_context):
    @session_waiter(timeout=..., record_history_chains=...)
    async def session_handler(controller, event):
        pass
    
    await session_handler(context.event)  # 装饰器被绕过
```

#### 根本原因

- `@session_waiter` 装饰器期望被应用在真正处理消息的 handler 上
- 将装饰的函数直接调用会绕过 AstrBot 的会话管理机制
- 会话控制需要在消息事件传递的关键位置应用，而不是在 handler 内部

#### 修复方案

**方案 A**（推荐）：在 handler 创建时应用会话装饰器

```python
def create_handler(self, workflow: WorkflowDefinition, plugin_context) -> Callable:
    """创建 handler 函数"""
    
    # 基础 handler 逻辑
    async def base_handler(event: AstrMessageEvent):
        context = ExecutionContext(...)
        
        if workflow.session.enabled:
            # 会话模式逻辑
            executor = ActionExecutor(context, workflow)
            await executor.execute_all()  # 执行所有 actions
        else:
            # 无会话模式逻辑
            await self._execute_workflow(workflow, context)
    
    # 如果需要会话控制，应用装饰器
    if workflow.session.enabled:
        handler = session_waiter(
            timeout=workflow.session.timeout,
            record_history_chains=workflow.session.record_history
        )(base_handler)
    else:
        handler = base_handler
    
    return handler
```

**方案 B**：使用 AstrBot 原生会话控制

```python
# 参考文档中 session_control.md 的标准用法
from astrbot.core.utils.session_waiter import session_waiter, SessionController

@session_waiter(timeout=60, record_history_chains=False)
async def handler(controller: SessionController, event: AstrMessageEvent):
    # 第一次进入：执行初始 actions
    # 等待用户输入
    controller.keep(timeout=60, reset_timeout=True)
    
    # 用户下一条消息进入
    # 继续处理
    controller.stop()  # 结束会话
```

#### 测试验证

- [ ] 测试启用会话的工作流能否正确接收多条消息
- [ ] 验证会话超时能否正确触发
- [ ] 验证历史消息记录的完整性

---

### 2. 关键词触发器未实现

**🏷️ ID**: `WF-002`  
**📍 位置**: [core/workflow_factory.py#L346-L351](core/workflow_factory.py#L346)  
**⚠️ 严重程度**: 🔴 HIGH  
**📊 影响范围**: KEYWORD 类型触发的工作流无法触发

#### 问题描述

```python
elif trigger.type == TriggerType.KEYWORD:
    import re
    pattern = re.escape(trigger.value)
    # 这里需要使用 AstrBot 的关键词匹配装饰器
    # 暂时使用 command 代替
    decorated = handler  # ❌ 返回未装饰的 handler
```

#### 修复方案

**方案 A**：基于消息内容检查（简单实现）

```python
elif trigger.type == TriggerType.KEYWORD:
    # 创建一个包装的 handler，检查关键词
    original_handler = handler
    
    async def keyword_handler(event: AstrMessageEvent, *args, **kwargs):
        # 检查消息是否包含关键词
        if trigger.value in event.message_str:
            return await original_handler(event, *args, **kwargs)
        # 否则不调用
    
    decorated = keyword_handler
```

**方案 B**：基于事件装饰器（如果 AstrBot 提供）

```python
elif trigger.type == TriggerType.KEYWORD:
    # 如果 AstrBot 有 @filter.contains() 或类似的装饰器
    from astrbot.api.event import filter as event_filter
    
    # 需要检查 AstrBot 的 filter 模块是否有相关装饰器
    # decorated = event_filter.contains(trigger.value)(handler)
    
    # 否则使用方案 A
    decorated = keyword_wrapper(handler, trigger.value)
```

#### 测试验证

- [ ] 测试 KEYWORD 类型的工作流能否正确触发
- [ ] 验证支持多种关键词匹配方式（精确、模糊、正则）

---

### 3. 正则表达式触发器未实现

**🏷️ ID**: `WF-003`  
**📍 位置**: [core/workflow_factory.py#L352-L353](core/workflow_factory.py#L352)  
**⚠️ 严重程度**: 🔴 HIGH  
**📊 影响范围**: REGEX 类型触发的工作流无法触发

#### 问题描述

```python
else:  # TriggerType.REGEX
    decorated = handler  # ❌ 完全未实现
```

#### 修复方案

```python
elif trigger.type == TriggerType.REGEX:
    import re
    
    try:
        regex_pattern = re.compile(trigger.value)
    except re.error as e:
        logger.error(f"无效的正则表达式: {trigger.value} - {str(e)}")
        decorator = handler
    else:
        original_handler = handler
        
        async def regex_handler(event: AstrMessageEvent, *args, **kwargs):
            # 检查消息是否匹配正则表达式
            if regex_pattern.search(event.message_str):
                return await original_handler(event, *args, **kwargs)
        
        decorated = regex_handler
```

#### 测试验证

- [ ] 测试各种正则表达式都能正确编译
- [ ] 验证正则表达式匹配的准确性
- [ ] 测试无效正则表达式的错误处理

---

## 🟡 P1 优先级 - 功能不完整

### 4. 重试逻辑未实现

**🏷️ ID**: `WF-004`  
**📍 位置**: [core/workflow_factory.py#L130-L141](core/workflow_factory.py#L130)  
**⚠️ 严重程度**: 🟡 MEDIUM  
**📊 影响范围**: `retry_count` 配置无法生效

#### 问题描述

```python
# 检查是否需要重试
if action_config.retry_count > 0:
    # 这里可以实现重试逻辑
    pass  # ❌ 空实现
```

#### 修复方案

```python
async def execute_action(self, index: int) -> tuple[bool, dict, int]:
    """执行单个 action (新增重试逻辑)"""
    action_config = self.workflow.actions[index]
    start_time = time.time()
    retry_count = action_config.retry_count or 0
    last_error = None
    
    for attempt in range(retry_count + 1):
        try:
            # 获取 action 类并执行
            ActionClass = get_action_class(action_config.action_id)
            action_instance = ActionClass(self.context, action_config)
            action_instance.validate_params()
            result = await action_instance.execute()
            
            # 成功
            duration_ms = (time.time() - start_time) * 1000
            self.context.record_step(
                index,
                action_config.action_id,
                'success',
                result=result,
                duration_ms=duration_ms
            )
            
            next_index = self._get_next_index(action_config, True)
            return True, result, next_index
        
        except (ActionExecutionError, Exception) as e:
            last_error = e
            
            # 如果还有重试次数，等待后重试
            if attempt < retry_count:
                # 指数退避（2^0=1s, 2^1=2s, 2^2=4s, ...）
                retry_delay = 2 ** attempt
                await asyncio.sleep(retry_delay)
                logger.debug(
                    f"Action {action_config.action_id} 重试 "
                    f"(尝试 {attempt + 1}/{retry_count + 1})"
                )
                continue
            
            # 重试次数用尽
            break
    
    # 所有重试都失败
    duration_ms = (time.time() - start_time) * 1000
    error_msg = str(last_error) if last_error else "未知错误"
    
    self.context.record_step(
        index,
        action_config.action_id,
        'failure',
        error=error_msg,
        duration_ms=duration_ms
    )
    self.context.last_error = last_error
    
    return False, {'error': error_msg}, None
```

#### 相关配置

在工作流配置中使用：

```json
{
  "action_id": "http_request",
  "retry_count": 3,
  "params": {
    "url": "https://api.example.com/data",
    "timeout": 5
  }
}
```

#### 测试验证

- [ ] 验证 retry_count=0 时不重试
- [ ] 验证重试逻辑正确执行
- [ ] 验证指数退避延迟正确计算
- [ ] 验证所有重试都失败时的错误处理

---

### 5. 流程控制策略 RETRY 和 JUMP 未实现

**🏷️ ID**: `WF-005`  
**📍 位置**: [core/workflow_factory.py#L62-L74](core/workflow_factory.py#L62)  
**⚠️ 严重程度**: 🟡 MEDIUM  
**📊 影响范围**: `error_handling` 为 RETRY 或 JUMP 时无法生效

#### 问题描述

```python
elif action_config.error_handling == ErrorHandlingStrategy.RETRY:
    # ❌ 未实现
    
elif action_config.error_handling == ErrorHandlingStrategy.JUMP:
    # ❌ 未实现
```

#### 修复方案

在 `execute_all()` 中的错误处理部分添加：

```python
async def execute_all(self):
    """执行所有 actions"""
    action_count = len(self.workflow.actions)
    current_index = 0
    
    while current_index < action_count:
        self.context.current_action_index = current_index
        action_config = self.workflow.actions[current_index]
        
        # ... 条件检查 ...
        
        # 执行 action
        success, result, next_index = await self.execute_action(current_index)
        
        # 处理流程控制
        if success:
            # ✅ 成功情况
            if next_index is not None:
                current_index = next_index
            else:
                current_index += 1
        else:
            # ❌ 失败情况 - 处理 error_handling 策略
            if action_config.error_handling == ErrorHandlingStrategy.STOP:
                logger.warning(f"Action {current_index} 失败，停止执行")
                break
            
            elif action_config.error_handling == ErrorHandlingStrategy.CONTINUE:
                logger.warning(f"Action {current_index} 失败，继续执行")
                current_index += 1
            
            elif action_config.error_handling == ErrorHandlingStrategy.RETRY:
                # 重试当前 action（已在 execute_action 中处理）
                # 这里只需要记录已重试过
                logger.warning(f"Action {current_index} 已重试，继续执行")
                current_index += 1
            
            elif action_config.error_handling == ErrorHandlingStrategy.JUMP:
                # 跳转到指定 action
                if action_config.flow_control.on_failure is not None:
                    current_index = action_config.flow_control.on_failure
                    logger.warning(
                        f"Action {current_index - action_config.flow_control.on_failure} "
                        f"失败，跳转到 action {current_index}"
                    )
                else:
                    logger.warning(f"Action {current_index} 失败，未指定跳转位置，停止执行")
                    break
```

#### 测试验证

- [ ] 验证 RETRY 策略触发重试
- [ ] 验证 JUMP 策略正确跳转到指定 action
- [ ] 验证无效跳转位置的错误处理

---

### 6. 条件检查逻辑不完整

**🏷️ ID**: `WF-006`  
**📍 位置**: [core/workflow_factory.py#L40-L46](core/workflow_factory.py#L40)  
**⚠️ 严重程度**: 🟡 MEDIUM  
**📊 影响范围**: 条件不满足时工作流中断

#### 问题描述

```python
# 检查执行条件
if action_config.condition:
    if not validate_condition(action_config.condition, self.context.variables):
        # 条件不满足，跳过
        # ❌ 但这里没有继续到下一个 action，直接返回了
        self.context.record_step(...)
        return False  # 这会中断工作流
```

#### 修复方案

```python
async def execute_all(self):
    """执行所有 actions"""
    action_count = len(self.workflow.actions)
    current_index = 0
    
    while current_index < action_count:
        self.context.current_action_index = current_index
        action_config = self.workflow.actions[current_index]
        
        # 检查执行条件
        if action_config.condition:
            try:
                if not validate_condition(action_config.condition, self.context.variables):
                    # 条件不满足，记录并继续到下一个 action
                    self.context.record_step(
                        current_index,
                        action_config.action_id,
                        'skipped',
                        reason='执行条件不满足'
                    )
                    current_index += 1
                    continue  # ✅ 继续到下一个 action
            except Exception as e:
                logger.error(f"条件验证失败: {str(e)}")
                self.context.record_step(
                    current_index,
                    action_config.action_id,
                    'skipped',
                    reason=f'条件验证异常: {str(e)}'
                )
                current_index += 1
                continue
        
        # 条件满足或无条件，执行 action
        success, result, next_index = await self.execute_action(current_index)
        
        # 处理流程控制
        if next_index is not None:
            current_index = next_index
        else:
            current_index += 1
```

#### 测试验证

- [ ] 验证条件满足时 action 执行
- [ ] 验证条件不满足时 action 被跳过
- [ ] 验证条件检查异常的处理

---

## 🟢 P2 优先级 - 可选改进

### 7. 会话大小限制缺失

**🏷️ ID**: `WF-007`  
**📍 位置**: [core/session_manager.py#L10-L20](core/session_manager.py#L10)  
**⚠️ 严重程度**: 🟢 LOW  
**📊 影响范围**: 长时间会话可能消耗过多内存

#### 建议修复

```python
class Session:
    def __init__(
        self,
        session_id: str,
        workflow_id: str,
        user_id: str,
        context: Any,
        timeout: float = 300.0,
        max_history: int = 100  # ✅ 新增
    ):
        # ...
        self.max_history = max_history
        self.history: List[Any] = []
    
    def add_history(self, item: Any):
        """添加历史记录"""
        self.history.append(item)
        # 如果超过限制，移除最早的记录
        if len(self.history) > self.max_history:
            self.history.pop(0)
```

---

### 8. 工具类功能不完整

**🏷️ ID**: `WF-008`  
**📍 位置**: 
- [utils/formatters.py](utils/formatters.py)
- [utils/extractors.py](utils/extractors.py)  
**⚠️ 严重程度**: 🟢 LOW  
**📊 影响范围**: 相关功能无法使用

#### 建议实现

**formatters.py** - 消息格式化

```python
class MessageFormatter:
    @staticmethod
    def format_table(data: List[Dict], columns: List[str]) -> str:
        """格式化表格"""
        pass
    
    @staticmethod
    def format_list(items: List[str], title: str = None) -> str:
        """格式化列表"""
        pass
    
    @staticmethod
    def format_code_block(code: str, language: str = "text") -> str:
        """格式化代码块"""
        pass
```

**extractors.py** - 参数提取

```python
class ParameterExtractor:
    @staticmethod
    def extract_args(message: str, count: int) -> List[str]:
        """提取指定数量的参数"""
        pass
    
    @staticmethod
    def extract_kwargs(message: str) -> Dict[str, str]:
        """提取键值对参数"""
        pass
```

---

## 📋 检查清单

### 修复前的验证

- [ ] 备份所有代码
- [ ] 确认测试环境可用
- [ ] 记录当前版本

### P0 问题修复

- [ ] WF-001: 会话控制装饰器
- [ ] WF-002: 关键词触发器
- [ ] WF-003: 正则表达式触发器

### P1 问题修复

- [ ] WF-004: 重试逻辑
- [ ] WF-005: 流程控制策略
- [ ] WF-006: 条件检查逻辑

### P2 改进（可选）

- [ ] WF-007: 会话大小限制
- [ ] WF-008: 工具类实现

### 修复后的验证

- [ ] 所有单元测试通过
- [ ] 集成测试覆盖各个功能
- [ ] 文档更新
- [ ] 代码审查

---

## 📚 参考文献

- [CODE_REVIEW.md](CODE_REVIEW.md) - 详细的代码分析报告
- [WORKFLOW_PROCESS.md](WORKFLOW_PROCESS.md) - 工作流程梳理

---

**问题修复指南版本**: 1.0  
**最后更新**: 2026-02-27
