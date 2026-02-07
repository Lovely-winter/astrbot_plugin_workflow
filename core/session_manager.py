内容：
- SessionContext类：会话上下文数据结构
  - workflow_name, user_id, group_id, step_index, data, created_at, last_active_at
- SessionManager类（单例）
  - _sessions = {}：user_id -> SessionContext映射
  - create_session(user_id, workflow_name)：创建会话
  - get_session(user_id)：获取会话
  - update_session(user_id, data)：更新会话数据
  - close_session(user_id)：关闭会话
  - get_active_sessions()：获取所有活跃会话（用于统计）
  - cleanup_expired(timeout)：清理过期会话
异常处理：会话不存在时返回None而非抛异常，由调用者判断