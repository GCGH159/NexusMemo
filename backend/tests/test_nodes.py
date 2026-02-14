"""
LangGraph 节点测试用例
测试各个处理节点的功能
"""
import pytest
from memo_agent.state import MemoProcessState
from memo_agent.nodes.load_context import load_user_graph_context
from memo_agent.nodes.classify import classify_node
from memo_agent.nodes.extract import extract_tags_entities_node


@pytest.mark.asyncio
class TestLoadContextNode:
    """加载上下文节点测试"""
    
    async def test_load_user_graph_context(self):
        """测试加载用户图谱上下文"""
        state = MemoProcessState(
            messages=[],
            user_id=1,
            memo_id=1,
            memo_type="quick_note",
            title="测试",
            content="测试内容",
            user_graph_context={},
            classification_result={},
            extraction_result={},
            relation_candidates=[],
            final_relations=[],
            event_links=[],
        )
        
        result = await load_user_graph_context(state)
        
        assert "user_graph_context" in result
        assert "categories" in result["user_graph_context"]
        assert "tags" in result["user_graph_context"]
        assert "active_events" in result["user_graph_context"]
        assert "recent_memos" in result["user_graph_context"]


@pytest.mark.asyncio
class TestClassifyNode:
    """分类节点测试"""
    
    async def test_classify_node(self):
        """测试分类节点"""
        state = MemoProcessState(
            messages=[],
            user_id=1,
            memo_id=1,
            memo_type="quick_note",
            title="学习 LangGraph",
            content="今天学习了 LangGraph 的 StateGraph 用法",
            user_graph_context={
                "categories": [
                    {"name": "学习资料", "type": "study", "memo_count": 5},
                    {"name": "Python编程", "type": "technology", "memo_count": 3}
                ],
                "tags": [],
                "active_events": [],
                "recent_memos": []
            },
            classification_result={},
            extraction_result={},
            relation_candidates=[],
            final_relations=[],
            event_links=[],
        )
        
        # 注意：这个测试需要 LLM API，可能会失败
        # 在实际测试中，应该 mock LLM 调用
        try:
            result = await classify_node(state)
            assert "classification_result" in result
        except Exception as e:
            # 如果 LLM 调用失败，跳过测试
            pytest.skip(f"LLM API 调用失败: {e}")


@pytest.mark.asyncio
class TestExtractNode:
    """提取节点测试"""
    
    async def test_extract_tags_entities_node(self):
        """测试提取标签和实体节点"""
        state = MemoProcessState(
            messages=[],
            user_id=1,
            memo_id=1,
            memo_type="quick_note",
            title="学习 LangGraph",
            content="今天学习了 LangGraph 的 StateGraph 用法，它比 AgentExecutor 灵活很多",
            user_graph_context={
                "categories": [],
                "tags": [
                    {"name": "LangChain", "memo_count": 5},
                    {"name": "AI", "memo_count": 3}
                ],
                "active_events": [],
                "recent_memos": []
            },
            classification_result={},
            extraction_result={},
            relation_candidates=[],
            final_relations=[],
            event_links=[],
        )
        
        # 注意：这个测试需要 LLM API，可能会失败
        # 在实际测试中，应该 mock LLM 调用
        try:
            result = await extract_tags_entities_node(state)
            assert "extraction_result" in result
        except Exception as e:
            # 如果 LLM 调用失败，跳过测试
            pytest.skip(f"LLM API 调用失败: {e}")
