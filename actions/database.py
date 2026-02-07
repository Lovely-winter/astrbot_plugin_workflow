内容：
- SaveKVDataAction：保存KV数据（plugin.put_kv_data）
- QueryKVDataAction：查询KV数据
- DeleteKVDataAction：删除KV数据
- CheckBlacklistAction：检查用户是否在黑名单
- AddBlacklistAction：添加到黑名单
- RemoveBlacklistAction：从黑名单移除
- SaveToSQLiteAction：保存到SQLite（可选，用于复杂查询）
异常处理：数据库操作失败抛出ActionExecutionError，不自动重试