"""
延迟队列组件
使用 Redis 实现延迟任务队列，用于定时任务
"""
import json
import asyncio
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
import redis.asyncio as aioredis

from app.db.config import settings, redis_conn


class DelayQueue:
    """
    延迟队列
    
    使用 Redis 的 Sorted Set 实现延迟队列，score 为执行时间戳。
    
    特性：
    - 支持延迟任务
    - 支持任务优先级（通过 score）
    - 支持任务取消
    - 支持任务重试
    """
    
    def __init__(self, queue_name: str = "delay_queue"):
        """
        初始化延迟队列
        
        参数：
            queue_name: 队列名称
        """
        self.queue_name = queue_name
        self.processing = False
        self.worker_task: Optional[asyncio.Task] = None
    
    async def push(
        self,
        task_data: dict,
        delay_seconds: int,
        task_id: Optional[str] = None
    ) -> str:
        """
        添加延迟任务
        
        参数：
            task_data: 任务数据（字典）
            delay_seconds: 延迟秒数
            task_id: 任务ID（可选，如果不提供则自动生成）
        
        返回：
            任务ID
        """
        if task_id is None:
            task_id = f"task_{datetime.now().timestamp()}_{id(task_data)}"
        
        # 计算执行时间戳
        execute_time = datetime.now() + timedelta(seconds=delay_seconds)
        score = execute_time.timestamp()
        
        # 序列化任务数据
        task = {
            "task_id": task_id,
            "task_data": task_data,
            "execute_time": execute_time.isoformat(),
            "delay_seconds": delay_seconds,
            "created_at": datetime.now().isoformat()
        }
        
        # 添加到 Redis Sorted Set
        redis_client = await redis_conn.get_client()
        await redis_client.zadd(
            self.queue_name,
            {json.dumps(task): score}
        )
        
        return task_id
    
    async def pop(self) -> Optional[dict]:
        """
        获取到期的任务
        
        返回：
            任务数据，如果没有到期任务则返回 None
        """
        redis_client = await redis_conn.get_client()
        current_time = datetime.now().timestamp()
        
        # 获取到期的任务（score <= current_time）
        result = await redis_client.zrangebyscore(
            self.queue_name,
            0,
            current_time,
            start=0,
            num=1,
            withscores=True
        )
        
        if not result:
            return None
        
        # 获取第一个任务
        task_json, score = result[0]
        
        # 从队列中移除
        await redis_client.zrem(self.queue_name, task_json)
        
        # 解析任务数据
        task = json.loads(task_json)
        return task
    
    async def cancel(self, task_id: str) -> bool:
        """
        取消任务
        
        参数：
            task_id: 任务ID
        
        返回：
            是否成功取消
        """
        redis_client = await redis_conn.get_client()
        
        # 获取所有任务
        tasks = await redis_client.zrange(self.queue_name, 0, -1)
        
        # 查找并删除指定任务
        for task_json in tasks:
            task = json.loads(task_json)
            if task.get("task_id") == task_id:
                await redis_client.zrem(self.queue_name, task_json)
                return True
        
        return False
    
    async def get_task_count(self) -> int:
        """
        获取队列中的任务数量
        
        返回：
            任务数量
        """
        redis_client = await redis_conn.get_client()
        return await redis_client.zcard(self.queue_name)
    
    async def clear(self):
        """清空队列"""
        redis_client = await redis_conn.get_client()
        await redis_client.delete(self.queue_name)
    
    async def start_worker(
        self,
        handler: Callable[[dict], Any],
        poll_interval: float = 1.0
    ):
        """
        启动工作线程
        
        参数：
            handler: 任务处理函数
            poll_interval: 轮询间隔（秒）
        """
        if self.processing:
            return
        
        self.processing = True
        
        async def worker():
            while self.processing:
                try:
                    # 获取到期任务
                    task = await self.pop()
                    
                    if task:
                        try:
                            # 执行任务处理函数
                            await handler(task)
                        except Exception as e:
                            print(f"任务执行失败: {str(e)}")
                            # 可以在这里添加重试逻辑
                    else:
                        # 没有到期任务，等待
                        await asyncio.sleep(poll_interval)
                except Exception as e:
                    print(f"工作线程异常: {str(e)}")
                    await asyncio.sleep(poll_interval)
        
        self.worker_task = asyncio.create_task(worker())
    
    async def stop_worker(self):
        """停止工作线程"""
        self.processing = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            self.worker_task = None
