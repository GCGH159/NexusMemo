"""
测试将来事项识别功能
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from memo_agent.nodes.future_reminder import future_reminder_node, parse_datetime
from memo_agent.state import MemoProcessState


async def test_parse_datetime():
    """测试时间解析功能"""
    print("=" * 50)
    print("测试时间解析功能")
    print("=" * 50)
    
    test_cases = [
        "2026-02-20T14:30:00",
        "2026-02-20 14:30:00",
        "2026-02-20",
        "3天后",
        "2小时后",
        "30分钟后",
        "明天",
        "后天",
        "下周一",
    ]
    
    for time_str in test_cases:
        result = parse_datetime(time_str)
        print(f"输入: {time_str}")
        print(f"输出: {result}")
        print("-" * 30)


async def test_future_reminder_node():
    """测试将来事项提醒节点"""
    print("\n" + "=" * 50)
    print("测试将来事项提醒节点")
    print("=" * 50)
    
    # 测试用例1：有将来事项
    state1 = MemoProcessState(
        messages=[],
        user_id=1,
        memo_id=100,
        memo_type="quick_note",
        title="明天下午开会",
        content="明天下午3点和产品团队开会讨论新功能",
        user_graph_context={},
        classification_result={},
        extraction_result={
            "tags": [{"name": "会议", "confidence": 0.9}],
            "entities": [{"name": "产品团队", "confidence": 0.8}],
            "time_info": {
                "time_str": "明天下午3点",
                "time_type": "future",
                "datetime_str": "明天",
                "is_reminder": True,
                "reminder_type": "appointment"
            },
            "summary": "明天下午开会"
        },
        reminder_result={},
        relation_candidates=[],
        final_relations=[],
        event_links=[],
    )
    
    result1 = await future_reminder_node(state1)
    print(f"测试用例1 - 有将来事项:")
    print(f"结果: {result1}")
    print("-" * 30)
    
    # 测试用例2：无将来事项
    state2 = MemoProcessState(
        messages=[],
        user_id=1,
        memo_id=101,
        memo_type="quick_note",
        title="今天的学习笔记",
        content="今天学习了Python异步编程",
        user_graph_context={},
        classification_result={},
        extraction_result={
            "tags": [{"name": "学习", "confidence": 0.9}],
            "entities": [{"name": "Python", "confidence": 0.95}],
            "time_info": {
                "time_str": "今天",
                "time_type": "present",
                "is_reminder": False
            },
            "summary": "今天的学习笔记"
        },
        reminder_result={},
        relation_candidates=[],
        final_relations=[],
        event_links=[],
    )
    
    result2 = await future_reminder_node(state2)
    print(f"测试用例2 - 无将来事项:")
    print(f"结果: {result2}")
    print("-" * 30)
    
    # 测试用例3：将来事项但不提醒
    state3 = MemoProcessState(
        messages=[],
        user_id=1,
        memo_id=102,
        memo_type="quick_note",
        title="下周的计划",
        content="下周要完成项目文档",
        user_graph_context={},
        classification_result={},
        extraction_result={
            "tags": [{"name": "计划", "confidence": 0.9}],
            "entities": [{"name": "项目文档", "confidence": 0.8}],
            "time_info": {
                "time_str": "下周",
                "time_type": "future",
                "datetime_str": "下周一",
                "is_reminder": False
            },
            "summary": "下周的计划"
        },
        reminder_result={},
        relation_candidates=[],
        final_relations=[],
        event_links=[],
    )
    
    result3 = await future_reminder_node(state3)
    print(f"测试用例3 - 将来事项但不提醒:")
    print(f"结果: {result3}")
    print("-" * 30)


async def main():
    """主测试函数"""
    try:
        await test_parse_datetime()
        await test_future_reminder_node()
        print("\n" + "=" * 50)
        print("所有测试完成！")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
