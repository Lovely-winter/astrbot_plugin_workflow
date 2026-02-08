实现指标收集器类。

维护字典存储 workflow 和 action 的执行统计、耗时列表。

提供方法：记录 workflow 执行（成功/失败、耗时）、记录 action 执行。

get_stats 方法：返回指定 workflow 或全局的统计数据，包括总次数、成功率、平均耗时。