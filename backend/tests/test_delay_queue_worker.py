"""
测试延迟队列工作线程功能
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.redis_components.delay_queue import DelayQueue
from app.redis_components.broadcast import Broadcast


async def test_delay_queue_worker():
    """测试延迟队列工作线程"""
    print("=" * 50)
    print("测试延迟队列工作线程")
    print("=" * 50)
    
    delay_queue = DelayQueue(queue_name="delay_queue:reminders")
    broadcast = Broadcast()
    
    # 定义任务处理函数
    async def handle_reminder_task(task):
        """处理到期提醒任务"""
        print(f"\n🔔 收到到期提醒任务！")
        print(f"Task ID: {task.get('task_id')}")
        print(f"执行时间: {task.get('execute_time')}")
        print(f"延迟秒数: {task.get('delay_seconds')}")
        
        task_data = task.get('task_data', {})
        print(f"用户ID: {task_data.get('user_id')}")
        print(f"速记ID: {task_data.get('memo_id')}")
        print(f"标题: {task_data.get('title')}")
        print(f"内容: {task_data.get('content')}")
        print(f"提醒类型: {task_data.get('reminder_type')}")
        
        # 广播提醒通知
        await broadcast.publish(
            channel=f"user:{task_data.get('user_id')}:reminders",
            message={
                "type": "reminder_triggered",
                "memo_id": task_data.get('memo_id'),
                "title": task_data.get('title'),
                "reminder_time": task.get('execute_time'),
                "message": f"提醒：{task_data.get('title')}"
            }
        )
        print(f"✅ 已广播提醒通知到用户频道")
    
    # 添加一个短延迟任务（5秒后执行）
    print("\n添加5秒后执行的测试任务...")
    task_id = await delay_queue.push(
        task_data={
            "user_id": 1,
            "memo_id": 999,
            "memo_type": "quick_note",
            "title": "测试提醒",
            "content": "这是一个5秒后执行的测试提醒",
            "reminder_type": "test"
        },
        delay_seconds=5,
        task_id="test_reminder_5s"
    )
    print(f"✅ 任务已添加，Task ID: {task_id}")
    
    # 检查队列中的任务数量
    task_count = await delay_queue.get_task_count()
    print(f"📊 队列中的任务数量: {task_count}")
    
    # 启动工作线程
    print("\n🚀 启动工作线程...")
    await delay_queue.start_worker(handle_reminder_task, poll_interval=1.0)
    
    # 等待任务执行（最多等待10秒）
    print("⏳ 等待任务执行（最多10秒）...")
    for i in range(10):
        await asyncio.sleep(1)
        remaining_count = await delay_queue.get_task_count()
        print(f"  [{i+1}/10] 剩余任务数: {remaining_count}")
        if remaining_count == 0:
            print("✅ 所有任务已执行完成！")
            break
    
    # 停止工作线程
    print("\n🛑 停止工作线程...")
    await delay_queue.stop_worker()
    print("✅ 工作线程已停止")
    
    # 最终检查
    final_count = await delay_queue.get_task_count()
    print(f"\n📊 最终队列中的任务数量: {final_count}")


async def main():
    """主测试函数"""
    try:
        await test_delay_queue_worker()
        print("\n" + "=" * 50)
        print("测试完成！")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
