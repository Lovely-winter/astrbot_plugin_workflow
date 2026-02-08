定义异常类层级体系。

基类 WorkflowError，包含：错误消息、错误码、用户友好消息、详情字典、trace_id。

派生类：ConfigError（配置相关）、ExecutionError（执行相关）、
SessionError（会话相关）、RegistrationError（注册相关）。

每个派生类进一步细分：ConfigFormatError、ConfigValidationError、
ActionNotFoundError、ActionExecutionError 等。

每个异常类提供便捷构造方法，自动生成错误码和用户消息。