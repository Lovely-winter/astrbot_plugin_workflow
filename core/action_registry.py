实现全局 action 注册表。

提供注册表字典和装饰器函数。装饰器将 action 类注册到字典中。

提供辅助函数：获取 action 类（不存在抛异常）、列出所有 action_id、
验证 action_id 有效性。

配合 actions/__init__.py 实现自动注册机制。