实现诊断工具类。

check_workflow 方法：诊断单个 workflow 配置，检查 action_id 有效性、
next 索引合法性、循环依赖，返回问题列表。

check_dependencies 方法：检查插件依赖库是否安装、AstrBot 版本兼容性。

dry_run 方法：模拟执行 workflow（不实际发送消息或调用 API），
创建模拟事件和上下文，记录每步执行但不调用真实接口，返回执行步骤和错误。