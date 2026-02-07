内容：
- extract_uid(text)：正则提取UID（支持多种格式）
- extract_email(text)：提取邮箱
- extract_url(text)：提取URL
- extract_qq(text)：提取QQ号
- extract_image_url(event)：从消息链提取图片URL
- parse_command_args(message_str)：解析指令参数
异常处理：提取失败返回None，不抛异常