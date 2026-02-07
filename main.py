内容：
- WorkflowPlugin类，注册到AstrBot
- __init__：加载配置、初始化日志、创建workflow实例、注册触发器、启动清理任务
- _load_workflows()：解析config["workflows"]，根据template_key创建实例
- _register_triggers()：为每个workflow动态注册@filter.command
- _setup_logging()：配置日志系统（级别、格式、文件）
- _start_cleanup_task()：启动定时清理（清理过期会话、校验码、日志轮转）
- _validate_global_config()：验证全局配置合法性
异常处理：捕获配置加载失败、workflow创建失败，记录ERROR日志后优雅降级
请按照C:\Users\sky-winter\Desktop\program\astrbot_plugin\astrbot_plugin_workflow\doc\simple.md
这个文件中的格式生成代码