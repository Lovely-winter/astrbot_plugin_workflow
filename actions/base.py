定义 action 抽象基类。

包含：初始化方法接收执行上下文、抽象方法 execute（执行逻辑，返回结果字典）。

可选方法：validate_params（参数验证）、get_required_params（返回必填参数列表）。

提供辅助方法：解析参数插值、记录执行结果到上下文。

所有具体 action 类继承此基类。