内容：
- CallPlatformAPIAction：通用平台API调用封装
- DeleteMessageAction：撤回消息
  - 需要message_id
  - 调用delete_msg API
- MuteUserAction：禁言用户
  - 参数：group_id, user_id, duration
  - 调用set_group_ban API
- KickUserAction：踢出用户
  - 参数：group_id, user_id, reject_add_request
  - 调用set_group_kick API
- SetGroupCardAction：设置群名片
  - 参数：group_id, user_id, card
  - 调用set_group_card API
- GetGroupMemberListAction：获取群成员列表
异常处理：
- 权限不足 → 抛出PlatformAPIError，提示管理员设置权限
- API超时 → 重试1次
- 目标用户是管理员 → 拒绝执行，返回错误
所有平台API调用都记录INFO日志：API名称、参数、结果