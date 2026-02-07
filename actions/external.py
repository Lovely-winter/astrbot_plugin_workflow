内容：
- ExternalScriptAction：调用外部Python脚本
  - 通过asyncio.create_subprocess_exec异步执行
  - 通过stdin传入JSON参数
  - 读取stdout获取返回值（JSON格式）
  - 读取stderr获取错误信息
  - 超时控制（默认30秒）
  - 环境隔离（可选：虚拟环境）
异常处理：
- 超时 → 强制kill进程 → 抛出ExternalScriptError
- 返回码非0 → 读取stderr → 抛出异常
- JSON解析失败 → 提示脚本返回格式错误
记录完整的stdout/stderr到DEBUG日志