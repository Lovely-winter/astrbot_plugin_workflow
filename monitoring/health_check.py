实现健康检查工具类。

依赖 WorkflowRegistry 和 SessionManager。

提供方法：检查 workflow 状态（总数、启用数、禁用数）、检查活跃会话数量、
检查资源占用（内存、线程数，使用 psutil）。

get_full_status 方法：返回完整健康状态字典。