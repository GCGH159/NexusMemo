"""
全文搜索节点
在 Neo4j 中执行全文搜索
"""
from typing import Dict, List
from app.db.config import get_neo4j_session

from search_agent.state import SearchState


async def fulltext_search_node(state: SearchState) -> Dict:
    """
    执行全文搜索
    
    使用 Neo4j 的全文索引搜索匹配的内容
    
    参数：
        state: 当前状态
    
    返回：
        更新后的状态，包含全文搜索结果
    """
    user_id = state["user_id"]
    query = state["query"]
    
    results = []
    
    try:
        neo4j_session = await get_neo4j_session().__anext__()
        
        # 在 Memo 节点中搜索
        cypher = """
        CALL db.index.fulltext.queryNodes('memoFullTextIndex', $query) YIELD node, score
        WHERE node.user_id = $user_id
        RETURN node, score
        LIMIT 20
        """
        
        result = await neo4j_session.run(
            cypher,
            query=query,
            user_id=user_id
        )
        
        async for record in result:
            node = record["node"]
            score = record["score"]
            
            # 获取节点的标签
            labels = list(node.labels)
            
            # 根据节点类型提取信息
            if "Memo" in labels:
                results.append({
                    "type": "memo",
                    "id": node.get("memo_id"),
                    "title": node.get("title", ""),
                    "content": node.get("content", ""),
                    "score": score,
                    "source": "fulltext"
                })
            elif "Event" in labels:
                results.append({
                    "type": "event",
                    "id": node.get("event_id"),
                    "title": node.get("title", ""),
                    "content": node.get("content", ""),
                    "score": score,
                    "source": "fulltext"
                })
        
        await neo4j_session.close()
        
    except Exception as e:
        print(f"全文搜索失败: {str(e)}")
        # 如果全文索引不存在，尝试使用 CONTAINS 搜索
        try:
            neo4j_session = await get_neo4j_session().__anext__()
            
            cypher = """
            MATCH (m:Memo)
            WHERE m.user_id = $user_id
              AND (m.title CONTAINS $query OR m.content CONTAINS $query)
            RETURN m as node, 1.0 as score
            LIMIT 20
            """
            
            result = await neo4j_session.run(
                cypher,
                query=query,
                user_id=user_id
            )
            
            async for record in result:
                node = record["node"]
                score = record["score"]
                
                results.append({
                    "type": "memo",
                    "id": node.get("memo_id"),
                    "title": node.get("title", ""),
                    "content": node.get("content", ""),
                    "score": score,
                    "source": "fulltext"
                })
            
            await neo4j_session.close()
            
        except Exception as e2:
            print(f"备用全文搜索也失败: {str(e2)}")
    
    return {
        "fulltext_results": results
    }
