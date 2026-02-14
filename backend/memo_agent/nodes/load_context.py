"""
加载用户图谱上下文节点
从Neo4j和MySQL加载用户的分类、标签、活跃事件等上下文信息
"""
from memo_agent.state import MemoProcessState
from app.db.config import neo4j_conn


async def load_user_graph_context(state: MemoProcessState) -> dict:
    """
    加载用户的图谱上下文信息
    
    包括：
    - 用户现有的分类体系
    - 用户常用的标签
    - 用户当前活跃的事件
    - 用户最近创建的速记
    """
    user_id = state["user_id"]
    
    # 初始化变量
    categories = []
    tags = []
    active_events = []
    recent_memos = []
    
    session = await neo4j_conn.get_session()
    try:
            # 1. 查询用户的分类体系
            categories_result = await session.run("""
                MATCH (u:User {user_id: $uid})-[:OWNS]->(m)-[:BELONGS_TO]->(c:Category)
                WITH c, count(m) AS memo_count
                WHERE memo_count > 0
                RETURN c.name AS name, labels(c)[0] AS type, memo_count
                ORDER BY memo_count DESC
                LIMIT 20
            """, uid=user_id)
            
            if categories_result:
                async for record in categories_result:
                    categories.append({
                        "name": record["name"],
                        "type": record["type"],
                        "memo_count": record["memo_count"]
                    })
            
            # 2. 查询用户常用的标签
            tags_result = await session.run("""
                MATCH (u:User {user_id: $uid})-[:OWNS]->(m)-[:HAS_TAG]->(t:Tag)
                WITH t, count(m) AS memo_count
                WHERE memo_count > 0
                RETURN t.name AS name, memo_count
                ORDER BY memo_count DESC
                LIMIT 30
            """, uid=user_id)
            
            if tags_result:
                async for record in tags_result:
                    tags.append({
                        "name": record["name"],
                        "memo_count": record["memo_count"]
                    })
            
            # 3. 查询用户当前活跃的事件
            events_result = await session.run("""
                MATCH (u:User {user_id: $uid})-[:OWNS]->(e:Event)
                WHERE e.status = 'active'
                RETURN e.event_id AS event_id, e.title AS title,
                       e.description AS description, e.event_type AS event_type,
                       e.created_at AS created_at
                ORDER BY e.created_at DESC
                LIMIT 10
            """, uid=user_id)
            
            if events_result:
                async for record in events_result:
                    active_events.append({
                        "event_id": record["event_id"],
                        "title": record["title"],
                        "description": record["description"],
                        "event_type": record["event_type"],
                        "created_at": record["created_at"].isoformat() if record["created_at"] else None
                    })
            
            # 4. 查询用户最近创建的速记（用于关联参考）
            recent_memos_result = await session.run("""
                MATCH (u:User {user_id: $uid})-[:OWNS]->(m:Memo)
                RETURN m.memo_id AS memo_id, m.title AS title,
                       left(m.content, 300) AS content_preview,
                       m.created_at AS created_at
                ORDER BY m.created_at DESC
                LIMIT 20
            """, uid=user_id)
            
            if recent_memos_result:
                async for record in recent_memos_result:
                    recent_memos.append({
                        "memo_id": record["memo_id"],
                        "title": record["title"],
                        "content_preview": record["content_preview"],
                        "created_at": record["created_at"].isoformat() if record["created_at"] else None
                    })
    finally:
        await session.close()
    
    # 构建用户图谱上下文
    user_graph_context = {
        "categories": categories,
        "tags": tags,
        "active_events": active_events,
        "recent_memos": recent_memos,
    }
    
    return {"user_graph_context": user_graph_context}
