"""
会话管理器
管理多用户并发会话和生命周期
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
import uuid


class Session:
    """会话对象"""
    
    def __init__(
        self,
        session_id: str,
        workflow_id: str,
        user_id: str,
        context: Any,
        timeout: float = 300.0
    ):
        self.session_id = session_id
        self.workflow_id = workflow_id
        self.user_id = user_id
        self.context = context
        self.timeout = timeout
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.data: Dict[str, Any] = {}  # 会话数据
        self.history: List[Any] = []  # 历史记录
    
    def is_expired(self) -> bool:
        """判断会话是否超时"""
        elapsed = (datetime.now() - self.last_activity).total_seconds()
        return elapsed > self.timeout
    
    def touch(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()
    
    def add_history(self, item: Any):
        """添加历史记录"""
        self.history.append(item)
    
    def get_age(self) -> float:
        """获取会话年龄（秒）"""
        return (datetime.now() - self.created_at).total_seconds()


class SessionManager:
    """
    会话管理器
    管理所有活跃会话的生命周期
    """
    
    def __init__(self, cleanup_interval: int = 60):
        """
        初始化会话管理器
        
        Args:
            cleanup_interval: 清理任务间隔（秒）
        """
        self.sessions: Dict[str, Session] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
        self.cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """启动会话管理器，开始后台清理任务"""
        if not self._running:
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """停止会话管理器"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """后台清理循环"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # 记录错误但不中断清理循环
                print(f"Session cleanup error: {e}")
    
    def create_session(
        self,
        workflow_id: str,
        user_id: str,
        context: Any,
        timeout: float = 300.0,
        session_id: Optional[str] = None
    ) -> Session:
        """
        创建新会话
        
        Args:
            workflow_id: 工作流 ID
            user_id: 用户 ID
            context: 执行上下文
            timeout: 超时时间
            session_id: 指定会话 ID（可选）
            
        Returns:
            会话对象
        """
        if not session_id:
            session_id = f"{workflow_id}_{user_id}_{uuid.uuid4().hex[:8]}"
        
        session = Session(session_id, workflow_id, user_id, context, timeout)
        self.sessions[session_id] = session
        self.locks[session_id] = asyncio.Lock()
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话对象或 None
        """
        session = self.sessions.get(session_id)
        if session and not session.is_expired():
            session.touch()
            return session
        return None
    
    async def get_lock(self, session_id: str) -> asyncio.Lock:
        """
        获取会话锁
        
        Args:
            session_id: 会话 ID
            
        Returns:
            异步锁
        """
        if session_id not in self.locks:
            self.locks[session_id] = asyncio.Lock()
        return self.locks[session_id]
    
    def remove_session(self, session_id: str) -> bool:
        """
        移除会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否成功移除
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.locks:
                del self.locks[session_id]
            return True
        return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        清理超时会话
        
        Returns:
            清理的会话数量
        """
        expired_ids = [
            sid for sid, session in self.sessions.items()
            if session.is_expired()
        ]
        
        for session_id in expired_ids:
            self.remove_session(session_id)
        
        return len(expired_ids)
    
    def clear_all_sessions(self):
        """清空所有会话"""
        self.sessions.clear()
        self.locks.clear()
    
    def get_active_sessions(
        self,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取活跃会话列表
        
        Args:
            workflow_id: 过滤条件：workflow ID
            user_id: 过滤条件：用户 ID
            
        Returns:
            会话信息列表
        """
        result = []
        
        for session in self.sessions.values():
            if session.is_expired():
                continue
            
            # 应用过滤条件
            if workflow_id and session.workflow_id != workflow_id:
                continue
            if user_id and session.user_id != user_id:
                continue
            
            result.append({
                'session_id': session.session_id,
                'workflow_id': session.workflow_id,
                'user_id': session.user_id,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'age_seconds': session.get_age(),
                'timeout': session.timeout
            })
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        active_count = sum(
            1 for s in self.sessions.values() if not s.is_expired()
        )
        expired_count = len(self.sessions) - active_count
        
        workflows = set(s.workflow_id for s in self.sessions.values())
        users = set(s.user_id for s in self.sessions.values())
        
        return {
            'total_sessions': len(self.sessions),
            'active_sessions': active_count,
            'expired_sessions': expired_count,
            'unique_workflows': len(workflows),
            'unique_users': len(users)
        }