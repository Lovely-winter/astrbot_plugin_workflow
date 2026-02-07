内容：
- KeywordFilterWorkflow(BaseWorkflow)
  - 使用@filter.event_message_type(GROUP_MESSAGE)而非command
  - execute(event)流程：
    步骤1：提取消息纯文本
    步骤2：匹配关键词列表（支持正则）
    步骤3：记录触发日志
    步骤4：执行配置的action_type
      - warn：仅发送警告消息
      - mute：调用平台API禁言
      - kick：调用平台API踢出
    步骤5：添加黑名单（可选）
  - _match_keywords(text, patterns)：关键词匹配逻辑
  - _execute_punishment(action_type, event)：执行惩罚动作
异常处理：
- 平台API失败 → 记录ERROR日志 → 降级到仅记录
- 权限不足 → 提示管理员设置权限
- 不影响其他消息处理