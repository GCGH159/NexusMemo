"""
速记Agent的状态定义
定义LangGraph工作流中传递的状态结构
"""
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class MemoProcessState(TypedDict):
    """
    速记处理流程的状态
    
    包含：
    - messages: 消息历史（用于LLM交互）
    - user_id: 用户ID
    - memo_id: 速记/事件ID
    - memo_type: 类型（quick_note | event）
    - title: 标题
    - content: 内容
    - user_graph_context: 用户图谱上下文（分类、标签、活跃事件等）
    - classification_result: 分类结果
    - extraction_result: 提取结果（标签、实体、时间信息）
    - reminder_result: 提醒结果
    - relation_candidates: 关联候选列表
    - final_relations: 最终关联关系
    - event_links: 事件绑定关系
    """
    messages: Annotated[list, add_messages]
    user_id: int
    memo_id: int
    memo_type: str  # "quick_note" | "event"
    title: str
    content: str
    user_graph_context: dict
    classification_result: dict
    extraction_result: dict
    reminder_result: dict
    relation_candidates: list[dict]
    final_relations: list[dict]
    event_links: list[dict]
