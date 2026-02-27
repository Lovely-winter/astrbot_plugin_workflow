# AstrBot Workflow 插件工作流程详解

## 🎯 核心工作流概览

该插件实现了一个 **事件驱动的工作流引擎**，接收 AstrBot 消息事件，根据配置的触发器动态执行一系列 Actions。

---

## 🔄 完整工作流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户发送消息事件                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    main.py: WorkflowPlugin                      │
│  1. 加载工作流配置 (_load_workflows)                           │
│  2. 为每个工作流创建 handler 并动态绑定到插件实例              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   workflow_factory.py                           │
│                  WorkflowHandlerFactory                         │
│                                                                 │
│  create_handler(workflow, plugin_context)                      │
│    └─→ 创建异步 handler 函数                                   │
│                                                                 │
│  apply_decorators(handler, workflow)                           │
│    └─→ 根据 trigger 类型应用 @filter 装饰器                    │
│        ├─→ COMMAND: @filter.command('xxx')                    │
│        ├─→ KEYWORD: 关键词匹配 (❌ 未实现)                     │
│        ├─→ REGEX: 正则表达式 (❌ 未实现)                       │
│        └─→ EVENT: @filter.event_message_type()               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
                ▼                 ▼
        ┌───────────────┐   ┌──────────────────┐
        │ 无会话模式    │   │   有会话模式     │
        │               │   │   (启用的情况)   │
        │  execute()    │   │  execute_with    │
        │  (直接执行)   │   │  _session()      │
        └───────┬───────┘   └────────┬─────────┘
                │                    │
                └────────┬───────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   execution_context.py                          │
│                   ExecutionContext                              │
│                                                                 │
│  ✅ 初始化执行上下文                                            │
│  ├─→ trace_id: 唯一追踪 ID                                    │
│  ├─→ variables: 变量存储                                       │
│  │   ├─→ 内置变量: user_id, message, group_id 等             │
│  │   └─→ 用户定义变量                                         │
│  ├─→ execution_trace: 执行轨迹记录                            │
│  └─→ last_error: 错误记录                                      │
│                                                                 │
│  关键方法:                                                      │
│  • set_variable(key, value): 设置变量                          │
│  • get_variable(key): 获取变量 (支持点号访问: 'user.name')    │
│  • resolve_string(template): 模板变量插值 {variable}          │
│  • record_step(...): 记录执行步骤                              │
│  • get_execution_summary(): 获取执行摘要                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   workflow_factory.py                           │
│                    ActionExecutor                               │
│                                                                 │
│  execute_all()  ← 按顺序执行所有 actions                      │
│    │                                                             │
│    └─→ 循环遍历 workflow.actions:                               │
│        │                                                         │
│        ├─→ [✓] 检查执行条件 (condition)                        │
│        │      if condition not satisfied: skip to next        │
│        │                                                         │
│        ├─→ [✓] 获取 Action 类并实例化                          │
│        │      ActionClass = get_action_class(action_id)      │
│        │      instance = ActionClass(context, config)        │
│        │                                                         │
│        ├─→ [✓] 验证参数                                        │
│        │      instance.validate_params()                      │
│        │                                                         │
│        ├─→ [✓] 执行 Action                                     │
│        │      result = await instance.execute()               │
│        │                                                         │
│        ├─→ [✓] 记录执行步骤                                    │
│        │      context.record_step(...)                        │
│        │                                                         │
│        └─→ [❌] 处理流程控制:                                   │
│               current_index = _get_next_index(config, success)│
│               ├─→ on_success (成功时跳转)                      │
│               ├─→ on_failure (失败时跳转)                      │
│               └─→ next (默认跳转)                              │
│                                                                 │
│  [⚠️] 错误处理策略 (未完全实现):                                │
│      ├─→ STOP: 停止执行 ✓                                     │
│      ├─→ CONTINUE: 继续执行 ✓                                 │
│      ├─→ RETRY: 重试 ❌ (未实现)                               │
│      └─→ JUMP: 跳转 ❌ (未实现)                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    actions/ 模块                                │
│                    Action 执行                                  │
│                                                                 │
│  每个 Action 实现 BaseAction.execute()                         │
│                                                                 │
│  执行前:                                                         │
│  1. resolve_params(): 参数变量插值                             │
│  2. validate_params(): 验证必填参数                            │
│  3. get_event(): 获取当前事件                                  │
│                                                                 │
│  执行中:                                                         │
│  4. 具体业务逻辑 (send_message, http_request, save_to_kv 等) │
│  5. set_result(): 将结果存储到上下文                           │
│                                                                 │
│  执行后:                                                         │
│  6. 返回 Dict[str, Any] 型结果                                 │
│     ├─→ 'success': bool                                       │
│     ├─→ 'message': str                                        │
│     └─→ 其他业务数据                                           │
│                                                                 │
│  存在的 Actions:                                               │
│  ✓ send_message: 发送文本消息                                 │
│  ✓ send_image: 发送图片                                       │
│  ✓ send_at: @ 提及用户                                        │
│  ✓ send_chain: 发送消息链                                     │
│  ✓ http_request: HTTP 请求                                   │
│  ✓ web_scrape: 网页爬取                                       │
│  ✓ call_api: 调用外部 API                                    │
│  ✓ webhook: 发送 Webhook                                      │
│  ✓ save_to_kv: 保存数据                                       │
│  ✓ load_from_kv: 加载数据                                     │
│  ✓ delete_from_kv: 删除数据                                   │
│  ✓ set_variable: 手动设置变量                                 │
│  ✓ condition_check: 条件判断                                  │
│  ❌ wait_input: 等待输入 (会话相关)                             │
│  ❌ kick_user: 踢出群成员 (框架未完成)                         │
│  ❌ group_ban: 禁言 (框架未完成)                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              结果处理和返回                                      │
│                                                                 │
│  无会话模式:                                                    │
│  └─→ 所有 actions 执行完毕                                     │
│      ├─→ Debug 模式下发送执行摘要                             │
│      └─→ 错误情况下发送错误消息                               │
│                                                                 │
│  有会话模式:                                                    │
│  └─→ @session_waiter 处理                                     │
│      ├─→ 首次执行到 wait_input                                │
│      ├─→ controller.keep() 保持会话                           │
│      ├─→ 等待下一条用户消息                                   │
│      └─→ 继续执行剩余 actions                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 会话流程（详细）

### 会话启用时的工作流

当 `workflow.session.enabled = True` 时：

```
用户: /workflow_cmd
     ▼
Handler 执行
     ▼
ExecutionContext 创建
     ▼
_execute_with_session() 调用
     │
     ├─→ @session_waiter 装饰 session_handler
     │   ├─→ timeout: workflow.session.timeout (默认 300s)
     │   └─→ record_history: 记录消息历史
     │
     ├─→ ActionExecutor.execute_all()
     │   │
     │   └─→ 遍历 actions 直到遇到 wait_input
     │       ├─→ action 0: 发送欢迎信息
     │       ├─→ action 1: wait_input
     │       │   └─→ 执行 wait_input action (发送提示)
     │       │   └─→ controller.keep(timeout=300, reset_timeout=True)
     │       │   └─→ context.current_action_index = 2
     │       │   └─→ return (会话保持，等待用户输入)
     │
     └─→ 会话生命周期管理:
         ├─→ 会话创建
         │   └─→ SessionManager.create_session()
         │   └─→ session_id = f"{workflow_id}_{user_id}_{uuid}"
         │
         ├─→ 用户发送消息 (在会话有效期内)
         │   └─→ session_waiter 截获消息
         │   └─→ 更新内置变量: message, user_input
         │   └─→ 继续从 current_action_index 执行
         │       ├─→ action 2: 处理用户输入
         │       ├─→ action 3: 验证...
         │       └─→ action 4: 可能再次 wait_input (循环继续)
         │
         └─→ 会话终止方式:
             ├─→ 推荐: controller.stop() 显式结束
             ├─→ 隐含: 所有 actions 执行完毕
             ├─→ 超时: 没有新消息超过 timeout 秒
             └─→ 错误: 异常导致会话中断
```

### 会话可能存在的问题

⚠️ **问题**: `@session_waiter` 装饰器应用方式

当前代码：
```python
async def _execute_with_session(...):
    @session_waiter(...)              # 在方法内部定义和装饰
    async def session_handler(...):
        pass
    await session_handler(context.event)  # 直接调用（装饰器无效）
```

预期用法（根据文档）：
```python
@session_waiter(...)               # 在 handler 层应用
async def handler(event: AstrMessageEvent, ...):
    # 会话逻辑在这里
    pass
```

---

## 🔗 数据流向

### 变量流转

```
1. ExecutionContext 初始化
   ├─→ 内置变量: user_id, message, group_id, platform, timestamp, trace_id
   └─→ 初始变量: workflow.variables

2. 用户定义初始变量
   └─→ workflow 配置中的 variables 字段

3. Action 执行中
   ├─→ 接收参数: action_config.params
   ├─→ 参数变量插值: resolve_params() → {variable} 被替换
   ├─→ 执行 Action
   └─→ 存储结果: set_result() 或修改上下文变量

4. 后续 Action 访问
   └─→ context.get_variable(key) 获取前面的变量

5. 模板变量插值
   └─→ {user_id}, {message}, {action_result} 等都可以引用
```

### 示例：成语接龙工作流

```
工作流配置:
{
  "id": "idiom_game",
  "name": "成语接龙",
  "trigger": {"type": "command", "value": "成语接龙"},
  "variables": {"history": []},
  "session": {"enabled": true, "timeout": 300},
  "actions": [
    {
      "action_id": "send_message",
      "params": {"text": "开始成语接龙，请发送第一个成语"}
    },
    {
      "action_id": "wait_input"
    },
    {
      "action_id": "condition_check",
      "condition": "len({message}) == 4",  # 检查长度
      "error_handling": "continue"
    },
    {
      "action_id": "http_request",
      "params": {
        "url": "https://api.example.com/idiom/{message}"
      }
    },
    {
      "action_id": "send_message",
      "params": {"text": "下一个成语: {http_response.data}"}
    },
    {
      "action_id": "wait_input"  # 继续等待
    }
  ]
}

执行流程:
用户: /成语接龙
  ▼
action 0: 发送 "开始成语接龙..."
  ▼
action 1: wait_input (保持会话)
  ▼
用户: 一马当先
  ▼
context.variables['message'] = '一马当先'
  ▼
action 2: 检查长度 (✓ 4个字)
  ▼
action 3: 调用 API http://api.example.com/idiom/一马当先
  ⤾ context.variables['http_response'] = {status: 200, data: '先见之明'}
  ▼
action 4: 发送 "下一个成语: 先见之明"
  ▼
action 5: wait_input (继续会话)
  ▼
... 循环继续 ...
```

---

## 🔊 管理指令流程

### /workflow 命令体系

```
/workflow
├─→ list
│   └─→ 列出所有已注册的工作流
│       ├─→ 工作流状态 (启用/禁用)
│       ├─→ 触发器信息
│       └─→ 动作数量
│
├─→ status
│   └─→ 显示工作流统计信息
│       ├─→ 总工作流数
│       ├─→ 启用数量
│       ├─→ 总执行次数
│       ├─→ 成功次数
│       ├─→ 整体成功率
│       └─→ 各工作流详细统计
│
├─→ reload
│   └─→ 重载工作流配置
│       └─→ 从插件配置重新读取
│
├─→ debug
│   └─→ 切换调试模式
│       └─→ 执行时发送详细信息
│
├─→ sessions
│   └─→ 显示活跃会话
│       ├─→ 会话总数/活跃数
│       ├─→ 各会话详细信息
│       └─→ SessionManager.get_active_sessions()
│
└─→ help
    └─→ 显示帮助信息
```

---

## 📊 状态机视图

### 工作流状态转换

```
未登记 → 已注册 (WorkflowRegistry.register)
          │
          ├─→ 已启用 (workflow.enabled = True)
          │   └─→ 可触发执行
          │       ├─→ 执行中
          │       │   ├─→ 成功 → 统计记录
          │       │   └─→ 失败 → 错误处理 → 统计记录
          │       └─→ [会话等待]
          │           ├─→ 用户输入
          │           ├─→ 继续执行
          │           └─→ 超时或控制停止
          │
          └─→ 已禁用 (workflow.enabled = False)
              └─→ 不可触发
```

### Action 执行状态

```
初始化
  ├─→ 解析参数 (resolve_params)
  ├─→ 验证参数 (validate_params)
  └─→ 检查条件 (condition)
      ├─→ ✓ 条件满足 → 执行
      │   ├─→ 成功
      │   │   ├─→ 返回结果
      │   │   ├─→ 根据 on_success 流程控制
      │   │   └─→ 记录步骤
      │   └─→ 失败
      │       ├─→ 错误处理策略
      │       │   ├─→ STOP: 中断
      │       │   ├─→ CONTINUE: 继续
      │       │   ├─→ RETRY: 重试
      │       │   └─→ JUMP: 跳转
      │       ├─→ 根据 on_failure 流程控制
      │       └─→ 记录步骤和错误
      └─→ ✗ 条件不满足 → 简单跳过
          └─→  记录 skipped 状态
```

---

## 🎛️ 配置与执行的映射关系

### 配置对象 → Python 类映射

| 配置字段 | Python 类 | 位置 |
|---------|---------|------|
| workflow | WorkflowDefinition | workflow_definition.py |
| trigger | TriggerConfig | workflow_definition.py |
| actions[*] | ActionConfig | workflow_definition.py |
| action flow_control | FlowControl | workflow_definition.py |
| session | SessionConfig | workflow_definition.py |
| 执行上下文 | ExecutionContext | execution_context.py |
| Action 实例 | BaseAction 子类 | actions/*.py |

### 注册表管理

```
plugin_config (WebUI 配置)
    └─→ ConfigParser.parse_templates()
        └─→ WorkflowRegistry.register()
            ├─→ self.workflows[id] = WorkflowDefinition
            ├─→ self.stats[id] = WorkflowStats
            └─→ self._trigger_map[key] = workflow_id
```

---

## ⚡ 性能和资源考虑

### 内存使用

1. **工作流注册**
   - 每个工作流 ~1KB (配置数据)
   - 总数据取决于工作流数量

2. **会话存储**
   - 每个会话 ~500B - 10KB (取决于是否记录历史)
   - 最坏情况：1000 并发用户 = ~10MB

3. **执行轨迹**
   - 每个 action 步骤 ~100B
   - 单个工作流执行轨迹 = step_count × 100B

### 并发考虑

- ✅ AsyncIO 原生支持并发
- ✅ SessionManager 使用 asyncio.Lock 保护会话
- ⚠️ 缺少 Action 级别的并发限制

---

## 📝 关键数据结构

### WorkflowDefinition

```python
@dataclass
class WorkflowDefinition:
    id: str
    name: str
    description: str
    enabled: bool
    priority: int
    trigger: TriggerConfig
    actions: List[ActionConfig]
    variables: Dict[str, Any]
    session: SessionConfig
    rate_limit: RateLimitConfig
    error_notifications: bool
```

### ExecutionContext

```python
{
    'trace_id': '8a9c3x1f',
    'workflow_id': 'idiom_game',
    'variables': {
        'user_id': '12345678',
        'user_name': 'Alice',
        'message': '一马当先',
        'group_id': '987654321',
        'platform': 'onebot',
        'timestamp': 1698123456,
        'http_response': {...},
        'custom_var': 'value'
    },
    'execution_trace': [
        {'index': 0, 'action_id': 'send_message', 'status': 'success', ...},
        {'index': 1, 'action_id': 'wait_input', 'status': 'skipped', ...},
        ...
    ]
}
```

---

## 🚀 总体工作流总结

1. **加载阶段** (插件启动时)
   - ConfigParser 解析配置
   - WorkflowRegistry 注册工作流
   - WorkflowHandlerFactory 创建 handlers

2. **触发阶段** (用户消息到达)
   - filter 装饰器匹配触发器
   - 调用对应的 handler

3. **执行阶段** (handler 运行)
   - ExecutionContext 初始化变量
   - ActionExecutor 按顺序执行 actions
   - 处理流程控制和错误

4. **结果阶段** (执行完毕)
   - 发送消息给用户
   - 记录统计信息
   - 清理会话（如果有）

---

**工作流程梳理版本**: 1.0  
**最后更新**：2026-02-27
