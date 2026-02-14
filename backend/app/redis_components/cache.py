"""
缓存组件
使用 Redis 实现缓存功能
"""
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import redis.asyncio as aioredis

from app.db.config import settings, redis_conn


class Cache:
    """
    缓存组件
    
    使用 Redis 实现缓存功能，支持多种数据类型和序列化方式。
    
    特性：
    - 支持字符串、JSON、Pickle 序列化
    - 支持过期时间
    - 支持批量操作
    - 支持缓存前缀
    - 支持缓存统计
    """
    
    def __init__(self, prefix: str = "cache"):
        """
        初始化缓存组件
        
        参数：
            prefix: 缓存键前缀
        """
        self.prefix = prefix
    
    def _make_key(self, key: str) -> str:
        """
        生成完整的缓存键
        
        参数：
            key: 原始键
        
        返回：
            带前缀的完整键
        """
        return f"{self.prefix}:{key}"
    
    async def get(
        self,
        key: str,
        deserialize: str = "json"
    ) -> Optional[Any]:
        """
        获取缓存
        
        参数：
            key: 缓存键
            deserialize: 反序列化方式（json | pickle | raw）
        
        返回：
            缓存值，如果不存在则返回 None
        """
        redis_client = await redis_conn.get_client()
        full_key = self._make_key(key)
        
        value = await redis_client.get(full_key)
        
        if value is None:
            return None
        
        # 根据反序列化方式处理
        if deserialize == "json":
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        elif deserialize == "pickle":
            try:
                return pickle.loads(value)
            except pickle.PickleError:
                return value
        else:  # raw
            return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
        serialize: str = "json"
    ) -> bool:
        """
        设置缓存
        
        参数：
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒数或 timedelta 对象）
            serialize: 序列化方式（json | pickle | raw）
        
        返回：
            是否成功设置
        """
        redis_client = await redis_conn.get_client()
        full_key = self._make_key(key)
        
        # 根据序列化方式处理
        if serialize == "json":
            try:
                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                serialized_value = str(value)
        elif serialize == "pickle":
            serialized_value = pickle.dumps(value)
        else:  # raw
            serialized_value = str(value)
        
        # 设置缓存
        if ttl is not None:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            return await redis_client.setex(full_key, ttl, serialized_value)
        else:
            return await redis_client.set(full_key, serialized_value)
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存
        
        参数：
            key: 缓存键
        
        返回：
            是否成功删除
        """
        redis_client = await redis_conn.get_client()
        full_key = self._make_key(key)
        
        result = await redis_client.delete(full_key)
        return result > 0
    
    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        参数：
            key: 缓存键
        
        返回：
            是否存在
        """
        redis_client = await redis_conn.get_client()
        full_key = self._make_key(key)
        
        result = await redis_client.exists(full_key)
        return result > 0
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """
        设置缓存过期时间
        
        参数：
            key: 缓存键
            ttl: 过期时间（秒数或 timedelta 对象）
        
        返回：
            是否成功设置
        """
        redis_client = await redis_conn.get_client()
        full_key = self._make_key(key)
        
        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())
        
        result = await redis_client.expire(full_key, ttl)
        return result > 0
    
    async def ttl(self, key: str) -> int:
        """
        获取缓存剩余过期时间
        
        参数：
            key: 缓存键
        
        返回：
            剩余秒数，-1 表示没有过期时间，-2 表示键不存在
        """
        redis_client = await redis_conn.get_client()
        full_key = self._make_key(key)
        
        return await redis_client.ttl(full_key)
    
    async def get_many(
        self,
        keys: list[str],
        deserialize: str = "json"
    ) -> dict[str, Any]:
        """
        批量获取缓存
        
        参数：
            keys: 缓存键列表
            deserialize: 反序列化方式
        
        返回：
            键值对字典
        """
        redis_client = await redis_conn.get_client()
        full_keys = [self._make_key(key) for key in keys]
        
        values = await redis_client.mget(full_keys)
        
        result = {}
        for key, value in zip(keys, values):
            if value is not None:
                if deserialize == "json":
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
                elif deserialize == "pickle":
                    try:
                        result[key] = pickle.loads(value)
                    except pickle.PickleError:
                        result[key] = value
                else:  # raw
                    result[key] = value
        
        return result
    
    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[Union[int, timedelta]] = None,
        serialize: str = "json"
    ) -> bool:
        """
        批量设置缓存
        
        参数：
            mapping: 键值对字典
            ttl: 过期时间（秒数或 timedelta 对象）
            serialize: 序列化方式
        
        返回：
            是否成功设置
        """
        redis_client = await redis_conn.get_client()
        
        # 序列化所有值
        serialized_mapping = {}
        for key, value in mapping.items():
            full_key = self._make_key(key)
            
            if serialize == "json":
                try:
                    serialized_value = json.dumps(value)
                except (TypeError, ValueError):
                    serialized_value = str(value)
            elif serialize == "pickle":
                serialized_value = pickle.dumps(value)
            else:  # raw
                serialized_value = str(value)
            
            serialized_mapping[full_key] = serialized_value
        
        # 批量设置
        if ttl is not None:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            # 需要逐个设置过期时间
            for key, value in serialized_mapping.items():
                await redis_client.setex(key, ttl, value)
        else:
            await redis_client.mset(serialized_mapping)
        
        return True
    
    async def delete_many(self, keys: list[str]) -> int:
        """
        批量删除缓存
        
        参数：
            keys: 缓存键列表
        
        返回：
            删除的数量
        """
        redis_client = await redis_conn.get_client()
        full_keys = [self._make_key(key) for key in keys]
        
        return await redis_client.delete(*full_keys)
    
    async def clear(self) -> bool:
        """
        清空所有缓存（只删除带前缀的键）
        
        返回：
            是否成功清空
        """
        redis_client = await redis_conn.get_client()
        
        # 获取所有带前缀的键
        pattern = f"{self.prefix}:*"
        keys = []
        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await redis_client.delete(*keys)
        
        return True
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        增加计数器
        
        参数：
            key: 缓存键
            amount: 增加的数量
        
        返回：
            增加后的值
        """
        redis_client = await redis_conn.get_client()
        full_key = self._make_key(key)
        
        return await redis_client.incrby(full_key, amount)
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """
        减少计数器
        
        参数：
            key: 缓存键
            amount: 减少的数量
        
        返回：
            减少后的值
        """
        redis_client = await redis_conn.get_client()
        full_key = self._make_key(key)
        
        return await redis_client.decrby(full_key, amount)
    
    async def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息
        
        返回：
            统计信息字典
        """
        redis_client = await redis_conn.get_client()
        
        # 获取所有带前缀的键
        pattern = f"{self.prefix}:*"
        keys = []
        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)
        
        # 计算总大小（近似）
        total_size = 0
        for key in keys:
            size = await redis_client.memory_usage(key)
            total_size += size if size else 0
        
        return {
            "prefix": self.prefix,
            "key_count": len(keys),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2)
        }
