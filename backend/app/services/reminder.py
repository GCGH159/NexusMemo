"""
提醒服务
处理延迟队列中的提醒任务，并发送通知
"""
import asyncio
from typing import Optional
from datetime import datetime

from app.redis_components.delay_queue import DelayQueue
from app.redis_components.broadcast import Broadcast


class ReminderService:
    """
    提醒服务
    
    功能：
    - 启动延迟队列工作线程
    - 处理到期的提醒任务
    - 通过广播组件发送通知
    """
    
    def __init__(self):
        """初始化提醒服务"""
        self.delay_queue: Optional[DelayQueue] = None
        self.broadcast: Optional[Broadcast] = None
        self.worker_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """启动提醒服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.delay_queue = DelayQueue(queue_name="reminder_queue")
        self.broadcast = Broadcast()
        
        # 启动延迟队列工作线程
        await self.delay_queue.start_worker(
            handler=self._handle_reminder_task,
            poll_interval=1.0
        )
        
        print("提醒服务已启动")
    
    async def stop(self):
        """停止提醒服务"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.delay_queue:
            await self.delay_queue.stop_worker()
        
        if self.broadcast:
            await self.broadcast.stop_listening()
        
        print("提醒服务已停止")
    
    async def _handle_reminder_task(self, task: dict):
        """
        处理到期的提醒任务
        
        参数：
            task: 任务数据
        """
        try:
            task_data = task.get("task_data", {})
            user_id = task_data.get("user_id")
            memo_id = task_data.get("memo_id")
            title = task_data.get("title")
            content = task_data.get("content")
            reminder_type = task_data.get("reminder_type", "task")
            
            # 通过广播发送提醒通知
            await self.broadcast.publish(
                channel=f"user:{user_id}:reminders",
                message={
                    "type": "reminder_triggered",
                    "task_id": task.get("task_id"),
                    "memo_id": memo_id,
                    "title": title,
                    "content": content,
                    "reminder_type": reminder_type,
                    "triggered_at": datetime.now().isoformat()
                }
            )
            
            print(f"提醒已发送: 用户 {user_id}, 速记 {memo_id}, 标题: {title}")
            
        except Exception as e:
            print(f"处理提醒任务失败: {str(e)}")
    
    async def get_pending_count(self) -> int:
        """
        获取待处理的提醒数量
        
        返回：
            待处理数量
        """
        if self.delay_queue:
            return await self.delay_queue.get_task_count()
        return 0
    
    async def cancel_reminder(self, task_id: str) -> bool:
        """
        取消提醒
        
        参数：
            task_id: 任务ID
        
        返回：
            是否成功取消
        """
        if self.delay_queue:
            return await self.delay_queue.cancel(task_id)
        return False


# 全局提醒服务实例
reminder_service = ReminderService()
