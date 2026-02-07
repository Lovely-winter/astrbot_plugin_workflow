内容：
- generate_code(length, charset)：生成随机校验码
- validate_code_format(code)：格式验证
- check_collision(code, plugin)：检查KV存储中是否已存在
- save_code(code, user_id, data, expires_in, plugin)：保存到KV
- verify_code(code, user_id, plugin)：验证码校验（检查存在、user_id匹配、未过期）
- cleanup_expired_codes(plugin)：清理过期校验码
异常处理：碰撞时自动重试生成，最多10次，失败则抛出异常