"""
将来事项提醒节点
识别将来要做的事情，并通过Redis广播通知关系发现Agent
"""
from datetime import datetime, timedelta
from typing import Optional
import re
import json

from memo_agent.state import MemoProcessState
from app.redis_components.broadcast import Broadcast
from app.redis_components.delay_queue import DelayQueue
from app.services.future_event_storage import FutureEventStorage


async def future_reminder_node(state: MemoProcessState) -> dict:
    """
    处理将来事项提醒，并通过Redis广播通知关系发现Agent
    
    流程：
    1. 检查提取结果中的时间信息
    2. 如果是将来时间且需要提醒，计算延迟时间
    3. 通过Redis广播消息通知关系发现Agent
    4. 返回提醒结果
    """
    extraction_result = state.get("extraction_result", {})
    time_info = extraction_result.get("time_info")
    
    # 如果没有时间信息或不是将来时间，直接返回
    if not time_info or time_info.get("time_type") != "future":
        return {
            "reminder_result": {
                "has_reminder": False,
                "message": "无将来事项需要提醒"
            }
        }
    
    # 检查是否需要提醒
    if not time_info.get("is_reminder"):
        return {
            "reminder_result": {
                "has_reminder": False,
                "message": "将来事项不需要提醒"
            }
        }
    
    # 解析时间字符串
    datetime_str = time_info.get("datetime_str")
    if not datetime_str:
        return {
            "reminder_result": {
                "has_reminder": False,
                "message": "无法解析时间字符串"
            }
        }
    
    try:
        # 尝试解析时间
        reminder_time = parse_datetime(datetime_str)
        if not reminder_time:
            return {
                "reminder_result": {
                    "has_reminder": False,
                    "message": "时间解析失败"
                }
            }
        
        # 计算延迟时间（秒）
        now = datetime.now()
        delay_seconds = int((reminder_time - now).total_seconds())
        
        # 如果时间已过，不添加提醒
        if delay_seconds <= 0:
            return {
                "reminder_result": {
                    "has_reminder": False,
                    "message": "提醒时间已过"
                }
            }
        
        # 存储将来事项信息到Redis
        event_data = {
            "user_id": state["user_id"],
            "memo_id": state["memo_id"],
            "memo_type": state["memo_type"],
            "title": state["title"],
            "content": state["content"],
            "reminder_time": reminder_time.isoformat(),
            "delay_seconds": delay_seconds,
            "reminder_type": time_info.get("reminder_type", "task"),
            "time_str": time_info.get("time_str"),
            "tags": [tag.get("name") for tag in extraction_result.get("tags", [])],
            "entities": [entity.get("name") for entity in extraction_result.get("entities", [])]
        }
        
        await FutureEventStorage.store_future_event(
            user_id=state["user_id"],
            memo_id=state["memo_id"],
            event_data=event_data
        )
        
        # 添加到延迟队列
        delay_queue = DelayQueue(queue_name="delay_queue:reminders")
        task_id = await delay_queue.push(
            task_data=event_data,
            delay_seconds=delay_seconds,
            task_id=f"reminder_user_{state['user_id']}_memo_{state['memo_id']}"
        )
        
        # 通过Redis广播消息通知关系发现Agent
        broadcast = Broadcast()
        
        # 广播到关系发现Agent的频道
        await broadcast.publish(
            channel="agent:find_relations:future_events",
            message=event_data
        )
        
        # 同时广播到用户提醒频道
        await broadcast.publish(
            channel=f"user:{state['user_id']}:reminders",
            message={
                "type": "reminder_scheduled",
                "memo_id": state["memo_id"],
                "title": state["title"],
                "reminder_time": reminder_time.isoformat(),
                "delay_seconds": delay_seconds,
                "task_id": task_id
            }
        )
        
        return {
            "reminder_result": {
                "has_reminder": True,
                "reminder_time": reminder_time.isoformat(),
                "delay_seconds": delay_seconds,
                "reminder_type": time_info.get("reminder_type"),
                "message": f"已识别将来事项，将在 {delay_seconds} 秒后提醒，已通知关系发现Agent"
            }
        }
        
    except Exception as e:
        return {
            "reminder_result": {
                "has_reminder": False,
                "message": f"提醒设置失败: {str(e)}"
            }
        }


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """
    解析日期时间字符串
    
    支持多种格式：
    - ISO 格式: 2026-02-15T14:30:00
    - 简单格式: 2026-02-15 14:30:00
    - 相对时间: 3天后, 2小时后, 明天上午
    """
    # 尝试 ISO 格式
    try:
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except ValueError:
        pass
    
    # 尝试简单格式
    try:
        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass
    
    # 尝试日期格式
    try:
        return datetime.strptime(datetime_str, "%Y-%m-%d")
    except ValueError:
        pass
    
    # 处理相对时间
    now = datetime.now()
    
    # 匹配 "X天后"
    match = re.match(r'(\d+)天后?', datetime_str)
    if match:
        days = int(match.group(1))
        return now + timedelta(days=days)
    
    # 匹配 "X小时后"
    match = re.match(r'(\d+)小时后?', datetime_str)
    if match:
        hours = int(match.group(1))
        return now + timedelta(hours=hours)
    
    # 匹配 "X分钟后"
    match = re.match(r'(\d+)分钟后?', datetime_str)
    if match:
        minutes = int(match.group(1))
        return now + timedelta(minutes=minutes)
    
    # 匹配 "明天"
    if datetime_str == "明天":
        return now + timedelta(days=1)
    
    # 匹配 "后天"
    if datetime_str == "后天":
        return now + timedelta(days=2)
    
    # 匹配 "下周一" 等
    weekdays = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6}
    for day_name, day_num in weekdays.items():
        if day_name in datetime_str:
            current_weekday = now.weekday()
            days_ahead = day_num - current_weekday
            if days_ahead <= 0:
                days_ahead += 7
            return now + timedelta(days=days_ahead)
    
    return None
