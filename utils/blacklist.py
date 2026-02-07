内容：
- BlacklistManager类
  - add(identifier, reason, expires_in)：添加黑名单
  - remove(identifier)：移除
  - check(identifier)：检查是否在黑名单
  - get_all()：获取所有黑名单
  - cleanup_expired()：清理过期黑名单
  - 数据存储在plugin的KV存储中