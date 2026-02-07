内容：
- validate_qq(qq_str)：QQ号格式验证（5-11位数字）
- validate_uid(uid_str)：通用UID验证（纯数字）
- validate_email(email)：邮箱格式验证
- validate_url(url)：URL格式验证
- validate_positive_int(value, name)：验证正整数
- validate_config_schema(config, required_fields)：配置完整性验证
- sanitize_input(text, max_length)：输入清理、长度限制、转义特殊字符
- validate_group_permission(event, required_role)：验证用户群权限
异常处理：验证失败抛出InvalidInputError，包含具体字段信息