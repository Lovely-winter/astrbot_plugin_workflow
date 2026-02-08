实现工厂类，负责动态创建 handler 函数。

create_handler 方法：使用闭包捕获 workflow 配置，创建异步处理函数。
函数内生成 trace_id、创建执行上下文、判断是否需要会话控制。
如果需要会话，内部定义 session_handler 并用 session_waiter 装饰器包裹。
调用 ActionExecutor 按序执行动作列表，捕获异常统一处理。

apply_decorators 方法：根据触发器类型动态应用 AstrBot 装饰器
（command、keyword、event），返回装饰后的函数对象。