内容：
- BilibiliVerifyWorkflow(BaseWorkflow)
  - execute(event)主流程：
    步骤1：检查是否在审核群，不是则忽略
    步骤2：发送提示"请发送B站UID"
    步骤3：@session_waiter等待用户输入
      - 提取UID（extract_uid）
      - 格式验证
      - 检测退出指令
    步骤4：根据verify_method选择验证方式
      - api：调用B站API
      - screenshot：OCR识别截图
    步骤5：检查黑名单
    步骤6：生成入群校验码
    步骤7：保存到KV存储
    步骤8：发送成功消息
  - _verify_bilibili_api(uid)：调用B站API验证粉丝数
  - _verify_screenshot(image_url, verify_code)：OCR+爬虫双重验证
  - _generate_entry_code(user_id)：生成并保存校验码
  - _handle_formal_group_request(event, code)：正式群校验码验证
异常处理：
- API超时 → 重试3次 → 失败后降级到人工审核
- 格式错误 → 提示用户重新输入，不中断会话
- 超时 → TimeoutError → 发送超时提示，清理状态
- 黑名单 → 抛出BlacklistError → 拒绝并记录
所有异常都记录详细日志，包含user_id、步骤、原因