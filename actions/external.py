实现外部调用 action。

CallApiAction：发送 HTTP 请求，参数包括 url、method、headers、body。
使用 aiohttp 异步请求，将响应结果存入上下文变量。

捕获网络异常转换为 ActionExecutionError。

支持重试机制（使用 retry 装饰器）。