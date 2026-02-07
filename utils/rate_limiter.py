内容：
- RateLimiter类
  - __init__(limit, window)：限制、时间窗口
  - check(key)：检查是否超限
  - record(key)：记录一次请求
  - cleanup()：清理过期记录
  - get_remaining(key)：获取剩余配额
用于防止用户刷请求、API调用限流
异常处理：超限时抛出RateLimitError