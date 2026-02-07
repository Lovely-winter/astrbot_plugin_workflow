内容：
- SendMessageAction：发送消息
- SendPrivateMessageAction：发送私聊
- SendGroupMessageAction：发送群消息
- WaitInputAction：等待用户输入（封装session_waiter模式）
- ApproveRequestAction：同意入群申请
- RejectRequestAction：拒绝申请
异常处理：消息发送失败记录WARNING，不抛异常（消息发送是尽力而为）