"""
端到端测试：将来事项识别Agent完整工作流
模拟用户创建包含将来事项的速记，验证整个流程
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from memo_agent.workflow import create_memo_processing_graph
from memo_agent.state import MemoProcessState
from app.db.config import redis_conn


async def test_end_to_end_future_reminder():
    """端到端测试：将来事项识别Agent完整工作流"""
    print("=" * 60)
    print("端到端测试：将来事项识别Agent完整工作流")
    print("=" * 60)
    
    # 创建工作流
    print("\n📝 创建Agent工作流...")
    workflow = create_memo_processing_graph()
    print("✅ 工作流创建成功")
    
    # 测试用例1：包含将来事项的速记
    print("\n" + "=" * 60)
    print("测试用例1：包含将来事项的速记")
    print("=" * 60)
    
    state1 = MemoProcessState(
        messages=[],
        user_id=1,
        memo_id=200,
        memo_type="quick_note",
        title="下周三下午2点开会",
        content="下周三下午2点和开发团队讨论新功能开发计划",
        user_graph_context={},
        classification_result={},
        extraction_result={},
        reminder_result={},
        relation_candidates=[],
        final_relations=[],
        event_links=[],
    )
    
    print(f"用户ID: {state1['user_id']}")
    print(f"速记ID: {state1['memo_id']}")
    print(f"标题: {state1['title']}")
    print(f"内容: {state1['content']}")
    
    # 执行工作流
    print("\n🚀 执行工作流...")
    result1 = await workflow.ainvoke(state1)
    
    print("\n📊 工作流执行结果:")
    print(f"  分类结果: {result1.get('classification_result', {})}")
    print(f"  提取结果: {result1.get('extraction_result', {})}")
    print(f"  提醒结果: {result1.get('reminder_result', {})}")
    print(f"  关系候选数量: {len(result1.get('relation_candidates', []))}")
    
    # 验证Redis数据
    print("\n🔍 验证Redis数据...")
    redis_client = await redis_conn.get_client()
    
    # 检查将来事项存储
    future_events_key = f"future_events:user:{state1['user_id']}"
    future_events = await redis_client.hgetall(future_events_key)
    print(f"  将来事项存储: {len(future_events)} 条")
    for field, value in future_events.items():
        import json
        event = json.loads(value)
        if event.get('memo_id') == state1['memo_id']:
            print(f"    - 标题: {event.get('title')}")
            print(f"    - 提醒时间: {event.get('reminder_time')}")
            print(f"    - 提醒类型: {event.get('reminder_type')}")
            print(f"    - 延迟秒数: {event.get('delay_seconds')}")
    
    # 检查延迟队列
    delay_queue_key = "delay_queue:reminders"
    delay_items = await redis_client.zrange(delay_queue_key, 0, -1, withscores=True)
    print(f"  延迟队列任务: {len(delay_items)} 条")
    for item_json, score in delay_items:
        import json
        task = json.loads(item_json)
        task_data = task.get('task_data', {})
        if task_data.get('memo_id') == state1['memo_id']:
            print(f"    - Task ID: {task.get('task_id')}")
            print(f"    - 执行时间: {task.get('execute_time')}")
            print(f"    - 延迟秒数: {task.get('delay_seconds')}")
    
    # 测试用例2：不包含将来事项的速记
    print("\n" + "=" * 60)
    print("测试用例2：不包含将来事项的速记")
    print("=" * 60)
    
    state2 = MemoProcessState(
        messages=[],
        user_id=1,
        memo_id=201,
        memo_type="quick_note",
        title="今天的学习笔记",
        content="今天学习了Python异步编程和FastAPI框架",
        user_graph_context={},
        classification_result={},
        extraction_result={},
        reminder_result={},
        relation_candidates=[],
        final_relations=[],
        event_links=[],
    )
    
    print(f"用户ID: {state2['user_id']}")
    print(f"速记ID: {state2['memo_id']}")
    print(f"标题: {state2['title']}")
    print(f"内容: {state2['content']}")
    
    # 执行工作流
    print("\n🚀 执行工作流...")
    result2 = await workflow.ainvoke(state2)
    
    print("\n📊 工作流执行结果:")
    print(f"  分类结果: {result2.get('classification_result', {})}")
    print(f"  提取结果: {result2.get('extraction_result', {})}")
    print(f"  提醒结果: {result2.get('reminder_result', {})}")
    
    # 验证不应该有将来事项
    reminder_result = result2.get('reminder_result', {})
    if reminder_result.get('has_reminder'):
        print("  ❌ 错误：不应该有将来事项提醒")
    else:
        print(f"  ✅ 正确：无将来事项提醒 - {reminder_result.get('message', '')}")
    
    # 测试用例3：包含多个将来事项的速记
    print("\n" + "=" * 60)
    print("测试用例3：包含截止日期的速记")
    print("=" * 60)
    
    state3 = MemoProcessState(
        messages=[],
        user_id=1,
        memo_id=202,
        memo_type="quick_note",
        title="项目截止日期",
        content="项目需要在下周五之前完成，包括文档和代码",
        user_graph_context={},
        classification_result={},
        extraction_result={},
        reminder_result={},
        relation_candidates=[],
        final_relations=[],
        event_links=[],
    )
    
    print(f"用户ID: {state3['user_id']}")
    print(f"速记ID: {state3['memo_id']}")
    print(f"标题: {state3['title']}")
    print(f"内容: {state3['content']}")
    
    # 执行工作流
    print("\n🚀 执行工作流...")
    result3 = await workflow.ainvoke(state3)
    
    print("\n📊 工作流执行结果:")
    print(f"  分类结果: {result3.get('classification_result', {})}")
    print(f"  提取结果: {result3.get('extraction_result', {})}")
    print(f"  提醒结果: {result3.get('reminder_result', {})}")
    
    # 验证提醒类型
    reminder_result = result3.get('reminder_result', {})
    if reminder_result.get('has_reminder'):
        print(f"  ✅ 有将来事项提醒")
        print(f"  提醒类型: {reminder_result.get('reminder_type')}")
        print(f"  提醒时间: {reminder_result.get('reminder_time')}")
    
    # 最终统计
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    # 统计Redis中的数据
    all_future_events = await redis_client.hgetall(f"future_events:user:1")
    all_delay_tasks = await redis_client.zrange("delay_queue:reminders", 0, -1, withscores=True)
    
    print(f"📊 Redis数据统计:")
    print(f"  将来事项总数: {len(all_future_events)}")
    print(f"  延迟队列任务总数: {len(all_delay_tasks)}")
    
    print("\n✅ 端到端测试完成！")


async def main():
    """主测试函数"""
    try:
        await test_end_to_end_future_reminder()
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
