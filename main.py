实现插件入口类 WorkflowPlugin，继承 Star。

初始化方法：读取 workflow_templates 配置，解析每个模板的 config_code（JSON），
调用工厂创建 handler，动态注册到插件实例。配置错误时回退到空配置不中断加载。

terminate 方法：清理所有会话和资源。

管理指令：reload（重载配置）、status（显示状态统计）、debug（切换调试）、
diagnose（诊断配置问题）、metrics（显示执行指标）、sessions（查看活跃会话）。

所有异常捕获并返回友好错误消息。