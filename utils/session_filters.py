"""
会话 ID 生成策略
提供不同粒度的会话区分
"""
from astrbot.api.event import AstrMessageEvent
from astrbot.core.utils.session_waiter import SessionFilter


class WorkflowSessionFilter(SessionFilter):
    """
    每个 workflow 生成独立会话空间
    session_id 格式: workflow_id + sender_id
    """
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
    
    def filter(self, event: AstrMessageEvent) -> str:
        """生成会话 ID"""
        sender_id = event.get_sender_id()
        return f"workflow_{self.workflow_id}_{sender_id}"


class GroupSessionFilter(SessionFilter):
    """
    整个群作为一个会话
    session_id 包含 group_id
    """
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
    
    def filter(self, event: AstrMessageEvent) -> str:
        """生成会话 ID"""
        group_id = event.get_group_id()
        if group_id:
            return f"workflow_{self.workflow_id}_group_{group_id}"
        else:
            sender_id = event.get_sender_id()
            return f"workflow_{self.workflow_id}_user_{sender_id}"


class CustomSessionFilter(SessionFilter):
    """
    自定义会话策略
    根据策略参数生成不同粒度的 session_id
    """
    
    def __init__(self, workflow_id: str, strategy: str = "per_user"):
        """
        Args:
            workflow_id: 工作流 ID
            strategy: 策略（per_user/per_group/global）
        """
        self.workflow_id = workflow_id
        self.strategy = strategy
    
    def filter(self, event: AstrMessageEvent) -> str:
        """生成会话 ID"""
        if self.strategy == "per_user":
            sender_id = event.get_sender_id()
            return f"workflow_{self.workflow_id}_user_{sender_id}"
        
        elif self.strategy == "per_group":
            group_id = event.get_group_id()
            if group_id:
                return f"workflow_{self.workflow_id}_group_{group_id}"
            else:
                sender_id = event.get_sender_id()
                return f"workflow_{self.workflow_id}_user_{sender_id}"
        
        elif self.strategy == "global":
            # 全局共享会话（慎用）
            return f"workflow_{self.workflow_id}_global"
        
        else:
            sender_id = event.get_sender_id()
            return f"workflow_{self.workflow_id}_user_{sender_id}"