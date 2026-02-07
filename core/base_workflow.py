内容：
- BaseWorkflow抽象类
  - __init__(config, plugin)：保存配置、插件引用、初始化logger
  - execute(event)：抽象方法，子类必须实现
  - _log(level, message, **context)：统一日志记录接口
  - _send_message(event, text)：辅助发送消息
  - _validate_config()：验证workflow配置合法性
  - _cleanup()：清理资源（关闭文件、释放锁等）
  - on_start(), on_complete(), on_error(error), on_timeout()：生命周期钩子
异常处理：定义异常处理模板，子类可override on_error钩子