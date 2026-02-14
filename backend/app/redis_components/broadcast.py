"""
广播通知组件
使用 Redis Pub/Sub 实现广播通知
"""
import json
import asyncio
from typing import Callable, Any, Optional
import redis.asyncio as aioredis

from app.db.config import settings, redis_conn


class Broadcast:
    """
    广播通知
    
    使用 Redis Pub/Sub 实现实时广播通知。
    
    特性：
    - 支持多频道订阅
    - 支持消息广播
    - 支持异步消息处理
    - 支持频道模式匹配
    """
    
    def __init__(self):
        """初始化广播组件"""
        self.subscribers = {}  # {channel: [handlers]}
        self.listening = False
        self.listener_task: Optional[asyncio.Task] = None
        self.pubsub: Optional[aioredis.PubSub] = None
    
    async def publish(self, channel: str, message: dict) -> int:
        """
        发布消息到指定频道
        
        参数：
            channel: 频道名称
            message: 消息内容（字典）
        
        返回：
            接收到消息的订阅者数量
        """
        redis_client = await redis_conn.get_client()
        
        # 序列化消息
        message_json = json.dumps(message)
        
        # 发布消息
        count = await redis_client.publish(channel, message_json)
        
        return count
    
    async def subscribe(
        self,
        channel: str,
        handler: Callable[[str, dict], Any]
    ):
        """
        订阅频道
        
        参数：
            channel: 频道名称
            handler: 消息处理函数，接收 (channel, message) 参数
        """
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        
        self.subscribers[channel].append(handler)
        
        # 如果还没有开始监听，启动监听
        if not self.listening:
            await self.start_listening()
    
    async def unsubscribe(self, channel: str, handler: Optional[Callable] = None):
        """
        取消订阅频道
        
        参数：
            channel: 频道名称
            handler: 要取消的处理函数（如果为 None，则取消该频道的所有订阅）
        """
        if channel not in self.subscribers:
            return
        
        if handler is None:
            # 取消该频道的所有订阅
            del self.subscribers[channel]
        else:
            # 取消指定的处理函数
            self.subscribers[channel] = [
                h for h in self.subscribers[channel] if h != handler
            ]
            
            # 如果该频道没有订阅者了，删除频道
            if not self.subscribers[channel]:
                del self.subscribers[channel]
    
    async def start_listening(self):
        """启动消息监听"""
        if self.listening:
            return
        
        self.listening = True
        
        async def listener():
            redis_client = await redis_conn.get_client()
            self.pubsub = redis_client.pubsub()
            
            # 订阅所有频道
            if self.subscribers:
                channels = list(self.subscribers.keys())
                await self.pubsub.subscribe(*channels)
            
            try:
                while self.listening:
                    # 获取消息
                    message = await self.pubsub.get_message(
                        timeout=1.0,
                        ignore_subscribe_messages=True
                    )
                    
                    if message and message["type"] == "message":
                        channel = message["channel"]
                        data = message["data"]
                        
                        # 解析消息
                        try:
                            message_dict = json.loads(data)
                        except json.JSONDecodeError:
                            message_dict = {"raw": data}
                        
                        # 调用该频道的所有处理函数
                        if channel in self.subscribers:
                            for handler in self.subscribers[channel]:
                                try:
                                    await handler(channel, message_dict)
                                except Exception as e:
                                    print(f"消息处理失败: {str(e)}")
                    
                    # 检查是否有新的频道需要订阅
                    current_channels = set(self.subscribers.keys())
                    subscribed_channels = set(self.pubsub.channels)
                    
                    new_channels = current_channels - subscribed_channels
                    if new_channels:
                        await self.pubsub.subscribe(*new_channels)
                    
                    # 检查是否有频道需要取消订阅
                    removed_channels = subscribed_channels - current_channels
                    if removed_channels:
                        await self.pubsub.unsubscribe(*removed_channels)
                    
                    await asyncio.sleep(0.01)
            
            except Exception as e:
                print(f"监听异常: {str(e)}")
            finally:
                if self.pubsub:
                    await self.pubsub.close()
        
        self.listener_task = asyncio.create_task(listener())
    
    async def stop_listening(self):
        """停止消息监听"""
        self.listening = False
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
            self.listener_task = None
        
        if self.pubsub:
            await self.pubsub.close()
            self.pubsub = None
    
    def get_subscribed_channels(self) -> list:
        """
        获取已订阅的频道列表
        
        返回：
            频道名称列表
        """
        return list(self.subscribers.keys())
    
    def get_subscriber_count(self, channel: str) -> int:
        """
        获取指定频道的订阅者数量
        
        参数：
            channel: 频道名称
        
        返回：
            订阅者数量
        """
        return len(self.subscribers.get(channel, []))
