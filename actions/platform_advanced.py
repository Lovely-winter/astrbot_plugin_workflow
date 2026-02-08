实现平台高级功能 action。

KickUserAction：踢出群成员，参数为 user_id，调用平台协议端 API。

GroupBanAction：禁言群成员，参数为 user_id 和 duration，调用平台 API。

所有操作需要权限检查，失败时抛出 ActionExecutionError。