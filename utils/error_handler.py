实现统一错误处理函数。

handle_config_error：格式化配置错误消息，记录日志，返回 None 跳过模板。

handle_execution_error：根据 on_error 策略处理执行错误（abort、retry、continue），
调用格式化器生成用户友好消息并发送。

handle_session_error：清理会话资源，发送超时提示。

所有函数不再抛异常，而是优雅处理并记录日志。