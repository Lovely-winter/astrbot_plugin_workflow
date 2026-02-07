内容：
- GroupSessionFilter：按群隔离会话（返回group_id）
- GroupUserSessionFilter：群+用户复合隔离（返回f"{group_id}_{user_id}"）
- GlobalSessionFilter：全局单例（返回固定字符串）
- CustomSessionFilter：自定义规则基类