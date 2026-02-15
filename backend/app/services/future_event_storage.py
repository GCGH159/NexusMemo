"""
将来事项存储服务
存储将来事项信息，供关系发现Agent查询
"""
import json
from typing import Optional, List
from datetime import datetime

from app.db.config import redis_conn


class FutureEventStorage:
    """
    将来事项存储服务
    
    功能：
    - 存储将来事项信息到Redis
    - 查询用户的将来事项
    - 删除已过期的将来事项
    """
    
    @staticmethod
    async def store_future_event(user_id: int, memo_id: int, event_data: dict):
        """
        存储将来事项信息
        
        参数：
            user_id: 用户ID
            memo_id: 速记ID
            event_data: 事件数据
        """
        redis_client = await redis_conn.get_client()
        
        # 存储到Redis Hash
        key = f"future_events:user:{user_id}"
        field = f"memo:{memo_id}"
        
        # 添加过期时间戳
        event_data["stored_at"] = datetime.now().isoformat()
        
        await redis_client.hset(key, field, json.dumps(event_data))
        
        # 设置过期时间（30天）
        await redis_client.expire(key, 30 * 24 * 3600)
    
    @staticmethod
    async def get_future_events(user_id: int) -> List[dict]:
        """
        获取用户的所有将来事项
        
        参数：
            user_id: 用户ID
        
        返回：
            将来事项列表
        """
        redis_client = await redis_conn.get_client()
        
        key = f"future_events:user:{user_id}"
        events = await redis_client.hgetall(key)
        
        result = []
        for field, value in events.items():
            try:
                event_data = json.loads(value)
                result.append(event_data)
            except json.JSONDecodeError:
                continue
        
        return result
    
    @staticmethod
    async def get_future_event(user_id: int, memo_id: int) -> Optional[dict]:
        """
        获取指定的将来事项
        
        参数：
            user_id: 用户ID
            memo_id: 速记ID
        
        返回：
            事件数据，如果不存在则返回None
        """
        redis_client = await redis_conn.get_client()
        
        key = f"future_events:user:{user_id}"
        field = f"memo:{memo_id}"
        
        value = await redis_client.hget(key, field)
        
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        
        return None
    
    @staticmethod
    async def delete_future_event(user_id: int, memo_id: int):
        """
        删除指定的将来事项
        
        参数：
            user_id: 用户ID
            memo_id: 速记ID
        """
        redis_client = await redis_conn.get_client()
        
        key = f"future_events:user:{user_id}"
        field = f"memo:{memo_id}"
        
        await redis_client.hdel(key, field)
    
    @staticmethod
    async def cleanup_expired_events(user_id: int):
        """
        清理已过期的将来事项
        
        参数：
            user_id: 用户ID
        """
        redis_client = await redis_conn.get_client()
        
        key = f"future_events:user:{user_id}"
        events = await redis_client.hgetall(key)
        
        now = datetime.now()
        
        for field, value in events.items():
            try:
                event_data = json.loads(value)
                reminder_time_str = event_data.get("reminder_time")
                
                if reminder_time_str:
                    reminder_time = datetime.fromisoformat(reminder_time_str)
                    
                    # 如果提醒时间已过，删除该事件
                    if reminder_time < now:
                        await redis_client.hdel(key, field)
            except (json.JSONDecodeError, ValueError):
                continue
