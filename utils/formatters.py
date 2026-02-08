实现错误消息格式化工具。

format_user_error：根据异常类型生成用户友好错误消息，包含工作流名称、
Action 位置、问题描述、建议。使用 emoji 和分隔线增强可读性。

format_diagnostic_report：格式化诊断报告，列出问题和建议。

format_metrics_report：格式化执行指标，包含次数、成功率、耗时。