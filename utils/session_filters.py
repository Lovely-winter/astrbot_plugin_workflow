实现会话 ID 生成策略类，继承 SessionFilter。

WorkflowSessionFilter：每个 workflow 生成独立会话空间，session_id 格式为 workflow_id + sender_id。

GroupSessionFilter：整个群作为一个会话，session_id 包含 group_id。

CustomSessionFilter：根据策略参数（per_user、per_group、global）生成不同粒度的 session_id。