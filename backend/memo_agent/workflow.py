"""
LangGraph主工作流
组装所有节点，构建速记处理的完整流程
"""
from langgraph.graph import StateGraph, END

from memo_agent.nodes.load_context import load_user_graph_context
from memo_agent.nodes.classify import classify_node
from memo_agent.nodes.extract import extract_tags_entities_node
from memo_agent.nodes.find_relations import find_relations_node
from memo_agent.nodes.judge_relations import judge_relations_node
from memo_agent.nodes.bind_events import bind_events_node
from memo_agent.nodes.persist_graph import persist_graph_node
from memo_agent.state import MemoProcessState


def create_memo_processing_graph():
    """
    构建速记处理的主工作流。

    流程：
    1. load_context: 加载用户图谱上下文
    2. classify: 匹配分类
    3. extract: 提取标签和实体
    4. find_relations: 查找相关内容（速记=被动匹配，事件=ReAct Agent 主动搜索）
    5. judge_relations: 判定关联关系（仅速记需要，事件由 Agent 内部完成）
    6. bind_events: 绑定事件（仅速记需要）
    7. persist_graph: 写入 Neo4j
    """
    workflow = StateGraph(MemoProcessState)
    
    # 添加所有节点
    workflow.add_node("load_context", load_user_graph_context)
    workflow.add_node("classify", classify_node)
    workflow.add_node("extract", extract_tags_entities_node)
    workflow.add_node("find_relations", find_relations_node)
    workflow.add_node("judge_relations", judge_relations_node)
    workflow.add_node("bind_events", bind_events_node)
    workflow.add_node("persist_graph", persist_graph_node)
    
    # 设置入口
    workflow.set_entry_point("load_context")
    
    # 标准路径：
    workflow.add_edge("load_context", "classify")
    workflow.add_edge("classify", "extract")
    
    # 从 extract 开始分流
    workflow.add_edge("extract", "find_relations")
    
    # find_relations 后分流
    # 对于速记：需要 judge_relations 和 bind_events
    # 对于事件：Agent 内部已完成所有判定，直接 persist
    
    def route_after_find_relations(state: MemoProcessState):
        """根据 memo_type 决定后续流程"""
        if state["memo_type"] == "event":
            return "event_path"
        else:
            return "quicknote_path"
    
    workflow.add_conditional_edges(
        "find_relations",
        route_after_find_relations,
        {
            "quicknote_path": "judge_relations",
            "event_path": "persist_graph",
        }
    )
    
    # 速记路径：judge_relations -> bind_events -> persist_graph
    workflow.add_edge("judge_relations", "bind_events")
    workflow.add_edge("bind_events", "persist_graph")
    
    # 结束
    workflow.add_edge("persist_graph", END)
    
    return workflow.compile()


# ============================================================
# 使用示例
# ============================================================

async def process_new_memo(user_id: int, memo_type: str, title: str, content: str):
    """
    处理新的速记或事件
    
    参数：
        user_id: 用户ID
        memo_type: 类型（quick_note | event）
        title: 标题
        content: 内容
    
    返回：
        处理结果，包含分类、提取、关联等信息
    """
    from app.db.config import AsyncSessionLocal
    from app.models import Memo
    
    # 1. 先写入 MySQL，获取 memo_id
    async with AsyncSessionLocal() as session:
        memo = Memo(
            user_id=user_id,
            type=memo_type,
            title=title,
            content=content,
            status="active"
        )
        session.add(memo)
        await session.commit()
        await session.refresh(memo)
        memo_id = memo.id
    
    # 2. 运行 LangGraph 工作流
    graph = create_memo_processing_graph()
    
    initial_state = MemoProcessState(
        messages=[],
        user_id=user_id,
        memo_id=memo_id,
        memo_type=memo_type,
        title=title,
        content=content,
        user_graph_context={},
        classification_result={},
        extraction_result={},
        relation_candidates=[],
        final_relations=[],
        event_links=[],
    )
    
    final_state = None
    async for state in graph.astream(initial_state):
        final_state = state
    
    # 3. 更新 MySQL 中的处理状态
    async with AsyncSessionLocal() as session:
        memo = await session.get(Memo, memo_id)
        if memo:
            memo.processed = True
            await session.commit()
    
    return {
        "memo_id": memo_id,
        "classification": final_state.get("classification_result"),
        "extraction": final_state.get("extraction_result"),
        "relations": final_state.get("final_relations"),
        "event_links": final_state.get("event_links"),
    }
