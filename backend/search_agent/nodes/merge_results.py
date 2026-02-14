"""
结果融合节点
合并来自不同搜索策略的结果
"""
from typing import Dict
from collections import defaultdict

from search_agent.state import SearchState


async def merge_results_node(state: SearchState) -> Dict:
    """
    融合搜索结果
    
    合并来自全文搜索、图查询和多跳遍历的结果，去重并计算综合分数
    
    参数：
        state: 当前状态
    
    返回：
        更新后的状态，包含合并后的结果
    """
    fulltext_results = state.get("fulltext_results", [])
    cypher_results = state.get("cypher_results", [])
    traversal_results = state.get("traversal_results", [])
    
    # 使用字典去重（基于 id 和 type）
    merged_dict = {}
    
    # 合并全文搜索结果
    for result in fulltext_results:
        key = f"{result['type']}_{result['id']}"
        if key not in merged_dict:
            merged_dict[key] = {
                "type": result["type"],
                "id": result["id"],
                "title": result["title"],
                "content": result["content"],
                "score": 0,
                "sources": []
            }
        merged_dict[key]["score"] += result["score"] * 1.0  # 全文搜索权重 1.0
        merged_dict[key]["sources"].append("fulltext")
    
    # 合并图查询结果
    for result in cypher_results:
        key = f"{result['type']}_{result['id']}"
        if key not in merged_dict:
            merged_dict[key] = {
                "type": result["type"],
                "id": result["id"],
                "title": result["title"],
                "content": result["content"],
                "score": 0,
                "sources": []
            }
        merged_dict[key]["score"] += result["score"] * 1.2  # 图查询权重 1.2
        merged_dict[key]["sources"].append("cypher")
        # 如果有额外的关系信息，保留
        if "relation" in result:
            merged_dict[key]["relation"] = result["relation"]
    
    # 合并多跳遍历结果
    for result in traversal_results:
        key = f"{result['type']}_{result['id']}"
        if key not in merged_dict:
            merged_dict[key] = {
                "type": result["type"],
                "id": result["id"],
                "title": result["title"],
                "content": result["content"],
                "score": 0,
                "sources": []
            }
        merged_dict[key]["score"] += result["score"] * 0.8  # 多跳遍历权重 0.8
        merged_dict[key]["sources"].append("traversal")
        # 如果有额外的跳数和关系信息，保留
        if "hops" in result:
            merged_dict[key]["hops"] = result["hops"]
        if "relations" in result:
            merged_dict[key]["relations"] = result["relations"]
    
    # 转换为列表
    merged_results = list(merged_dict.values())
    
    # 去重 sources
    for result in merged_results:
        result["sources"] = list(set(result["sources"]))
    
    return {
        "merged_results": merged_results
    }
