实现参数提取和插值解析工具。

extract_params_from_message：使用正则从消息中提取参数，支持命名组。

resolve_template_string：替换 {variable} 为实际值，支持点号访问、默认值、转义。

resolve_params：递归处理字典、列表、字符串，调用模板字符串解析。

找不到变量时使用默认值或保留原样，不抛异常。