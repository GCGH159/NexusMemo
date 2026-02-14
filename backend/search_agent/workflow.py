"""
搜索 Agent 工作流
组装所有节点，构建智能搜索的完整流程
"""
from langgraph.graph import StateGraph, END

from search_agent.nodes.decide_strategy import decide_search_strategy_node
from search_agent.nodes.fulltext_search import fulltext_search_node
from search_agent.nodes.cypher_search import cypher_search_node
from search_agent.nodes.traversal_search import traversal_search_node
from search_agent.nodes.merge_results import merge_results_node
from search_agent.nodes.rank_results import rank_results_node
from search_agent.state import SearchState


def create_search_graph():
    """
    构建搜索的主工作流。

    流程：
    1. decide_strategy: 决策搜索策略
    2. 根据策略执行相应的搜索（fulltext/cypher/traversal）
    3. merge_results: 融合搜索结果
    4. rank_results: LLM 排序并生成最终答案
    """
    workflow = StateGraph(SearchState)
    
    # 添加所有节点
    workflow.add_node("decide_strategy", decide_search_strategy_node)
    workflow.add_node("fulltext_search", fulltext_search_node)
    workflow.add_node("cypher_search", cypher_search_node)
    workflow.add_node("traversal_search", traversal_search_node)
    workflow.add_node("merge_results", merge_results_node)
    workflow.add_node("rank_results", rank_results_node)
    
    # 设置入口
    workflow.set_entry_point("decide_strategy")
    
    # 根据搜索策略路由到不同的搜索节点
    def route_after_decide(state: SearchState):
        """根据决策的搜索策略路由"""
        strategies = state.get("search_strategy", [])
        
        # 决定执行哪些搜索节点
        nodes_to_execute = []
        if "fulltext" in strategies:
            nodes_to_execute.append("fulltext_search")
        if "cypher" in strategies:
            nodes_to_execute.append("cypher_search")
        if "traversal" in strategies:
            nodes_to_execute.append("traversal_search")
        
        # 如果没有策略，默认使用全文搜索
        if not nodes_to_execute:
            nodes_to_execute = ["fulltext_search"]
        
        return nodes_to_execute
    
    # 添加条件边
    workflow.add_conditional_edges(
        "decide_strategy",
        route_after_decide,
        {
            "fulltext_search": "fulltext_search",
            "cypher_search": "cypher_search",
            "traversal_search": "traversal_search"
        }
    )
    
    # 所有搜索节点都指向 merge_results
    workflow.add_edge("fulltext_search", "merge_results")
    workflow.add_edge("cypher_search", "merge_results")
    workflow.add_edge("traversal_search", "merge_results")
    
    # merge_results -> rank_results
    workflow.add_edge("merge_results", "rank_results")
    
    # 结束
    workflow.add_edge("rank_results", END)
    
    return workflow.compile()


async def execute_search(user_id: int, query: str):
    """
    执行搜索
    
    参数：
        user_id: 用户ID
        query: 搜索查询
    
    返回：
        搜索结果，包含最终答案和来源信息
    """
    # 创建搜索图
    graph = create_search_graph()
    
    # 初始化状态
    initial_state = SearchState(
        user_id=user_id,
        query=query,
        search_strategy=[],
        fulltext_results=[],
        cypher_results=[],
        traversal_results=[],
        merged_results=[],
        ranked_results=[],
        final_answer="",
        sources=[],
        messages=[]
    )
    
    # 执行搜索
    merged_state = {}
    async for state in graph.astream(initial_state):
        for node_name, node_output in state.items():
            if node_output:
                merged_state.update(node_output)
    
    return {
        "query": query,
        "answer": merged_state.get("final_answer", ""),
        "results": merged_state.get("ranked_results", []),
        "sources": merged_state.get("sources", [])
    }
