实现配置解析器类。

parse_templates 方法：遍历 template_list，检查 enabled 字段，
解析 config_code（JSON 字符串），调用验证器验证，转换为 WorkflowDefinition 对象。

捕获解析和验证异常，记录错误但继续处理其他模板，返回成功解析的列表。

load_from_file 方法：从文件读取 JSON 配置并解析。
