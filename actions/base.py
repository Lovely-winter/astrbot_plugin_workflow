内容：
- BaseAction抽象类
  - __init__(params)：保存动作参数
  - validate_params()：验证参数完整性和合法性
  - execute(context)：抽象方法，执行动作逻辑
  - _log(level, message, **kwargs)：日志记录
  - _handle_error(error)：统一异常处理逻辑
异常处理：定义错误处理模板，子类可自定义重试策略