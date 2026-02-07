内容：
- WorkflowException：基础异常类
  - error_code, user_message, details
- ConfigValidationError(WorkflowException)：配置验证失败
- WorkflowTimeoutError(WorkflowException)：工作流超时
- WorkflowCreationError(WorkflowException)：工作流创建失败
- ActionExecutionError(WorkflowException)：动作执行失败
- ExternalScriptError(WorkflowException)：外部脚本执行错误
- BlacklistError(WorkflowException)：黑名单拦截
- PlatformAPIError(WorkflowException)：平台API调用失败
- InvalidInputError(WorkflowException)：用户输入非法
每个异常包含：错误码（用于分类统计）、用户友好消息、详细信息（用于日志）