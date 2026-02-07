内容：
- HttpRequestAction：通用HTTP请求
  - 支持GET/POST/PUT/DELETE
  - 超时控制（默认10秒）
  - 重试机制（3次，指数退避）
  - headers自定义
  - 使用aiohttp异步
- WebScrapeAction：网页爬取（简单HTML解析）
异常处理：
- 超时 → 重试 → 失败后抛出ActionExecutionError
- 网络错误 → 重试
- HTTP 4xx/5xx → 记录错误，抛出异常
每次重试都记录WARNING日志