内容：
- ActionRegistry单例类
  - _actions = {}：action_type -> ActionClass映射
  - register(action_type)：装饰器注册动作
  - execute(action_type, params, context)：执行指定动作
  - get_action_list()：返回所有可用动作列表
  - validate_action(action_type)：检查动作是否存在
异常处理：execute时捕获动作执行失败，抛出ActionExecutionError并记录详细日志