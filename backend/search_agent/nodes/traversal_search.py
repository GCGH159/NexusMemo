"""
多跳遍历节点
探索关系链，查找相关内容
"""
from typing import Dict
from app.db.config import get_neo4j_session

from search_agent.state import SearchState


async def traversal_search_node(state: SearchState) -> Dict:
    """
    执行多跳遍历搜索
    
    探索关系链，查找与查询相关的内容
    
    参数：
        state: 当前状态
    
    返回：
        更新后的状态，包含多跳遍历结果
    """
    user_id = state["user_id"]
    query = state["query"]
    
    results = []
    
    try:
        neo4j_session = await get_neo4j_session().__anext__()
        
        # 首先找到匹配查询的起始节点
        start_cypher = """
        MATCH (m:Memo)
        WHERE m.user_id = $user_id
          AND (m.title CONTAINS $query OR m.content CONTAINS $query)
        RETURN m as start_node
        LIMIT 5
        """
        
        start_result = await neo4j_session.run(
            start_cypher,
            query=query,
            user_id=user_id
        )
        
        start_nodes = []
        async for record in start_result:
            start_nodes.append(record["start_node"])
        
        # 从每个起始节点进行多跳遍历
        for start_node in start_nodes:
            # 2跳遍历
            cypher = """
            MATCH path = (start)-[*1..3]-(related)
            WHERE id(start) = $start_id
              AND start.user_id = $user_id
            RETURN related as node, length(path) as hops, [r in relationships(path) | type(r)] as relations
            LIMIT 10
            """
            
            result = await neo4j_session.run(
                cypher,
                start_id=start_node.element_id,
                user_id=user_id
            )
            
            async for record in result:
                node = record["node"]
                hops = record["hops"]
                relations = record["relations"]
                
                # 获取节点的标签
                labels = list(node.labels)
                
                if "Memo" in labels:
                    results.append({
                        "type": "memo",
                        "id": node.get("memo_id"),
                        "title": node.get("title", ""),
                        "content": node.get("content", ""),
                        "hops": hops,
                        "relations": relations,
                        "score": 1.0 / hops,  # 跳数越多，分数越低
                        "source": "traversal"
                    })
                elif "Event" in labels:
                    results.append({
                        "type": "event",
                        "id": node.get("event_id"),
                        "title": node.get("title", ""),
                        "content": node.get("content", ""),
                        "hops": hops,
                        "relations": relations,
                        "score": 1.0 / hops,
                        "source": "traversal"
                    })
        
        await neo4j_session.close()
        
    except Exception as e:
        print(f"多跳遍历失败: {str(e)}")
    
    return {
        "traversal_results": results
    }
