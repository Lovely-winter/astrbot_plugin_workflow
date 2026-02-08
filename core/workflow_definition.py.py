定义数据模型类。

WorkflowDefinition 包含：id、名称、描述、启用状态、触发器配置、动作列表、
会话配置、优先级。

TriggerConfig 包含：类型（枚举）、触发值、别名列表、过滤器。

ActionConfig 包含：action_id、参数字典、跳转配置（next、on_success、on_failure）、
错误处理策略、重试次数。

使用 dataclass 或 pydantic，支持从字典反序列化。