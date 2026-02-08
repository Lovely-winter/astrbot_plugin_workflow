实现消息相关 action 类。

SendMessageAction：发送文本消息，参数为 text，调用 event.send 发送。

WaitInputAction：标记等待用户输入，参数为 timeout，实际等待逻辑在工厂的 session_handler 中。

SendImageAction：发送图片消息，参数为 url，调用 event.image_result 发送。

使用装饰器自动注册到 ACTION_REGISTRY。