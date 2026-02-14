"""
搜索 Agent 状态定义
"""
from typing import TypedDict, List, Dict, Optional, Literal
from langgraph.graph import add_messages


class SearchState(TypedDict):
    """搜索 Agent 状态"""
    
    # 用户输入
    user_id: int
    query: str  # 用户搜索查询
    
    # Agent 决策
    search_strategy: List[str]  # 选择的搜索策略列表
    
    # 搜索结果
    fulltext_results: List[Dict]  # 全文搜索结果
    cypher_results: List[Dict]  # 图查询结果
    traversal_results: List[Dict]  # 多跳遍历结果
    
    # 融合和排序
    merged_results: List[Dict]  # 合并后的结果
    ranked_results: List[Dict]  # 排序后的结果
    
    # 最终输出
    final_answer: str  # 最终答案
    sources: List[Dict]  # 来源信息
    
    # 消息历史（用于 LangGraph）
    messages: list
