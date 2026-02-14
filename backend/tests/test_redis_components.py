"""
Redis 组件测试
测试延迟队列、广播通知和缓存组件
"""
import pytest
import asyncio
from datetime import timedelta

from app.redis_components.delay_queue import DelayQueue
from app.redis_components.broadcast import Broadcast
from app.redis_components.cache import Cache


class TestDelayQueue:
    """延迟队列测试"""
    
    @pytest.mark.asyncio
    async def test_push_and_pop(self):
        """测试添加和获取任务"""
        queue = DelayQueue("test_queue")
        
        # 添加延迟任务（延迟 1 秒）
        task_data = {"action": "test", "value": 123}
        task_id = await queue.push(task_data, delay_seconds=1)
        
        assert task_id is not None
        assert task_id.startswith("task_")
        
        # 立即获取，应该没有到期任务
        task = await queue.pop()
        assert task is None
        
        # 等待 1.5 秒后获取
        await asyncio.sleep(1.5)
        task = await queue.pop()
        
        assert task is not None
        assert task["task_id"] == task_id
        assert task["task_data"] == task_data
        
        # 清理
        await queue.clear()
    
    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """测试取消任务"""
        queue = DelayQueue("test_queue_cancel")
        
        # 添加延迟任务（延迟 10 秒）
        task_data = {"action": "cancel_test"}
        task_id = await queue.push(task_data, delay_seconds=10)
        
        # 取消任务
        result = await queue.cancel(task_id)
        assert result is True
        
        # 等待后获取，应该没有任务
        await asyncio.sleep(0.5)
        task = await queue.pop()
        assert task is None
        
        # 清理
        await queue.clear()
    
    @pytest.mark.asyncio
    async def test_get_task_count(self):
        """测试获取任务数量"""
        queue = DelayQueue("test_queue_count")
        
        # 添加多个任务
        for i in range(5):
            await queue.push({"index": i}, delay_seconds=10)
        
        count = await queue.get_task_count()
        assert count == 5
        
        # 清理
        await queue.clear()
    
    @pytest.mark.asyncio
    async def test_worker(self):
        """测试工作线程"""
        queue = DelayQueue("test_queue_worker")
        
        # 记录执行的任务
        executed_tasks = []
        
        async def handler(task):
            executed_tasks.append(task)
        
        # 启动工作线程
        await queue.start_worker(handler, poll_interval=0.5)
        
        # 添加延迟任务（延迟 1 秒）
        await queue.push({"action": "worker_test"}, delay_seconds=1)
        
        # 等待任务执行
        await asyncio.sleep(2)
        
        # 停止工作线程
        await queue.stop_worker()
        
        # 验证任务已执行
        assert len(executed_tasks) == 1
        assert executed_tasks[0]["task_data"]["action"] == "worker_test"
        
        # 清理
        await queue.clear()


class TestBroadcast:
    """广播通知测试"""
    
    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self):
        """测试发布和订阅"""
        broadcast = Broadcast()
        
        # 记录接收到的消息
        received_messages = []
        
        async def handler(channel, message):
            received_messages.append((channel, message))
        
        # 订阅频道
        await broadcast.subscribe("test_channel", handler)
        
        # 等待监听器启动
        await asyncio.sleep(1.0)
        
        # 发布消息
        message = {"type": "notification", "content": "Hello"}
        count = await broadcast.publish("test_channel", message)
        
        # 等待消息处理
        await asyncio.sleep(1.0)
        
        # 验证消息已接收
        assert len(received_messages) == 1
        assert received_messages[0][0] == "test_channel"
        assert received_messages[0][1] == message
        
        # 停止监听
        await broadcast.stop_listening()
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        """测试多个订阅者"""
        broadcast = Broadcast()
        
        # 记录接收到的消息
        received_messages = []
        
        async def handler1(channel, message):
            received_messages.append(("handler1", channel, message))
        
        async def handler2(channel, message):
            received_messages.append(("handler2", channel, message))
        
        # 订阅同一频道
        await broadcast.subscribe("test_channel", handler1)
        await broadcast.subscribe("test_channel", handler2)
        
        # 等待监听器启动
        await asyncio.sleep(1.0)
        
        # 发布消息
        message = {"type": "notification", "content": "Hello"}
        await broadcast.publish("test_channel", message)
        
        # 等待消息处理
        await asyncio.sleep(1.0)
        
        # 验证两个订阅者都收到了消息
        assert len(received_messages) == 2
        assert received_messages[0][0] == "handler1"
        assert received_messages[1][0] == "handler2"
        
        # 停止监听
        await broadcast.stop_listening()
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """测试取消订阅"""
        broadcast = Broadcast()
        
        # 记录接收到的消息
        received_messages = []
        
        async def handler(channel, message):
            received_messages.append((channel, message))
        
        # 订阅频道
        await broadcast.subscribe("test_channel", handler)
        
        # 取消订阅
        await broadcast.unsubscribe("test_channel", handler)
        
        # 发布消息
        message = {"type": "notification", "content": "Hello"}
        await broadcast.publish("test_channel", message)
        
        # 等待消息处理
        await asyncio.sleep(0.5)
        
        # 验证没有收到消息
        assert len(received_messages) == 0
        
        # 停止监听
        await broadcast.stop_listening()
    
    @pytest.mark.asyncio
    async def test_get_subscriber_count(self):
        """测试获取订阅者数量"""
        broadcast = Broadcast()
        
        async def handler1(channel, message):
            pass
        
        async def handler2(channel, message):
            pass
        
        # 订阅频道
        await broadcast.subscribe("test_channel", handler1)
        await broadcast.subscribe("test_channel", handler2)
        
        # 获取订阅者数量
        count = broadcast.get_subscriber_count("test_channel")
        assert count == 2
        
        # 停止监听
        await broadcast.stop_listening()


class TestCache:
    """缓存组件测试"""
    
    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """测试设置和获取缓存"""
        cache = Cache("test_cache")
        
        # 设置缓存
        value = {"key": "value", "number": 123}
        result = await cache.set("test_key", value)
        assert result is True
        
        # 获取缓存
        cached_value = await cache.get("test_key")
        assert cached_value == value
        
        # 清理
        await cache.clear()
    
    @pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """测试设置带过期时间的缓存"""
        cache = Cache("test_cache_ttl")
        
        # 设置缓存（过期时间 1 秒）
        value = {"key": "value"}
        await cache.set("test_key", value, ttl=1)
        
        # 立即获取，应该存在
        cached_value = await cache.get("test_key")
        assert cached_value == value
        
        # 等待 1.5 秒后获取，应该不存在
        await asyncio.sleep(1.5)
        cached_value = await cache.get("test_key")
        assert cached_value is None
        
        # 清理
        await cache.clear()
    
    @pytest.mark.asyncio
    async def test_delete(self):
        """测试删除缓存"""
        cache = Cache("test_cache_delete")
        
        # 设置缓存
        await cache.set("test_key", {"key": "value"})
        
        # 删除缓存
        result = await cache.delete("test_key")
        assert result is True
        
        # 获取缓存，应该不存在
        cached_value = await cache.get("test_key")
        assert cached_value is None
        
        # 清理
        await cache.clear()
    
    @pytest.mark.asyncio
    async def test_exists(self):
        """测试检查缓存是否存在"""
        cache = Cache("test_cache_exists")
        
        # 检查不存在的缓存
        exists = await cache.exists("test_key")
        assert exists is False
        
        # 设置缓存
        await cache.set("test_key", {"key": "value"})
        
        # 检查存在的缓存
        exists = await cache.exists("test_key")
        assert exists is True
        
        # 清理
        await cache.clear()
    
    @pytest.mark.asyncio
    async def test_get_many_and_set_many(self):
        """测试批量操作"""
        cache = Cache("test_cache_batch")
        
        # 批量设置
        mapping = {
            "key1": {"value": 1},
            "key2": {"value": 2},
            "key3": {"value": 3}
        }
        await cache.set_many(mapping)
        
        # 批量获取
        result = await cache.get_many(["key1", "key2", "key3"])
        assert len(result) == 3
        assert result["key1"]["value"] == 1
        assert result["key2"]["value"] == 2
        assert result["key3"]["value"] == 3
        
        # 清理
        await cache.clear()
    
    @pytest.mark.asyncio
    async def test_increment_and_decrement(self):
        """测试计数器"""
        cache = Cache("test_cache_counter")
        
        # 增加计数器
        value = await cache.increment("counter", 5)
        assert value == 5
        
        # 再次增加
        value = await cache.increment("counter", 3)
        assert value == 8
        
        # 减少计数器
        value = await cache.decrement("counter", 2)
        assert value == 6
        
        # 清理
        await cache.clear()
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计信息"""
        cache = Cache("test_cache_stats")
        
        # 设置一些缓存
        for i in range(5):
            await cache.set(f"key{i}", {"value": i})
        
        # 获取统计信息
        stats = await cache.get_stats()
        assert stats["prefix"] == "test_cache_stats"
        assert stats["key_count"] == 5
        assert stats["total_size_bytes"] > 0
        
        # 清理
        await cache.clear()
