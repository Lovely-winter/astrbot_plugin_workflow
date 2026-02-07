内容：
- WorkflowRegistry单例类
  - _registry = {}：存储template_key -> WorkflowClass的映射
  - register(template_key)：装饰器，注册workflow类
  - create(template_key, config, plugin)：工厂方法创建workflow实例
  - get_all_templates()：返回所有注册的template信息
  - validate_template(template_key)：检查template是否存在
异常处理：create时捕获实例化失败，抛出WorkflowCreationError