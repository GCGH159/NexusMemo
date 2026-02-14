"""
持久化图谱节点
将所有Agent决策结果写入Neo4j知识图谱
"""
from memo_agent.state import MemoProcessState
from app.db.config import neo4j_conn


async def persist_graph_node(state: MemoProcessState) -> dict:
    """
    将所有处理结果写入 Neo4j 知识图谱。
    包括：Memo/Event 节点、分类关系、标签关系、实体节点、关联关系、事件绑定。
    """
    user_id = state["user_id"]
    memo_id = state["memo_id"]
    memo_type = state["memo_type"]
    title = state["title"]
    content = state["content"]
    
    classification = state["classification_result"] or {}
    extraction = state["extraction_result"] or {}
    relations = state["final_relations"] or []
    event_links = state["event_links"] or []
    
    session = await neo4j_conn.get_session()
    try:
        # 使用事务批量执行
        tx = await session.begin_transaction()
        try:
            # 1. 创建 Memo/Event 节点
            if memo_type == "event":
                event_type = extraction.get("event_type", "general")
                await tx.run("""
                    MERGE (u:User {user_id: $user_id})
                    MERGE (e:Event {event_id: $id})
                    ON CREATE SET e.title = $title, e.description = $content,
                                   e.event_type = $event_type,
                                   e.status = 'active',
                                   e.created_at = datetime()
                    ON MATCH SET e.updated_at = datetime()
                    MERGE (u)-[:OWNS]->(e)
                """, user_id=user_id, id=memo_id, title=title,
                    content=content, event_type=event_type)
            else:
                await tx.run("""
                    MERGE (u:User {user_id: $user_id})
                    MERGE (m:Memo {memo_id: $id})
                    ON CREATE SET m.title = $title, m.content = $content,
                                   m.type = 'quick_note',
                                   m.created_at = datetime()
                    ON MATCH SET m.updated_at = datetime()
                    MERGE (u)-[:OWNS]->(m)
                """, user_id=user_id, id=memo_id, title=title, content=content)
            
            # 2. 建立分类关系
            primary_cat = classification.get("primary_category")
            secondary_cat = classification.get("secondary_category")
            
            if primary_cat and secondary_cat:
                await tx.run("""
                    MATCH (u:User {user_id: $uid})-[:OWNS]->(x)
                    WHERE x.memo_id = $id OR x.event_id = $id
                    MERGE (c1:Category {name: $primary})
                    MERGE (c2:Category {name: $secondary})
                    MERGE (c2)-[:CHILD_OF]->(c1)
                    MERGE (x)-[:BELONGS_TO]->(c2)
                """, uid=user_id, id=memo_id, primary=primary_cat, secondary=secondary_cat)
            
            # 3. 创建/关联标签
            for tag in extraction.get("tags", []):
                tag_name = tag.get("name")
                if tag_name:
                    await tx.run("""
                        MATCH (u:User {user_id: $uid})-[:OWNS]->(x)
                        WHERE x.memo_id = $id OR x.event_id = $id
                        MERGE (t:Tag {name: $name})
                        MERGE (x)-[:HAS_TAG]->(t)
                    """, uid=user_id, id=memo_id, name=tag_name)
            
            # 4. 创建/关联实体
            for entity in extraction.get("entities", []):
                entity_name = entity.get("name")
                entity_type = entity.get("entity_type")
                if entity_name and entity_type:
                    await tx.run("""
                        MATCH (u:User {user_id: $uid})-[:OWNS]->(x)
                        WHERE x.memo_id = $id OR x.event_id = $id
                        MERGE (en:Entity {name: $name, type: $type})
                        ON CREATE SET en.created_at = datetime()
                        MERGE (x)-[:MENTIONS]->(en)
                    """, uid=user_id, id=memo_id, name=entity_name, type=entity_type)
            
            # 5. 创建关联关系（速记-速记 / 事件-事件）
            for rel in relations:
                target_id = rel.get("target_id")
                rel_type = rel.get("relation_type")
                score = rel.get("score")
                reason = rel.get("reason")
                
                if target_id and rel_type:
                    # 使用APOC创建动态关系类型
                    await tx.run("""
                        MATCH (u:User {user_id: $uid})
                        MATCH (s) WHERE (s.memo_id = $src_id OR s.event_id = $src_id)
                        MATCH (t) WHERE (t.memo_id = $tgt_id OR t.event_id = $tgt_id)
                        CALL apoc.create.relationship(s, $rel_type, {
                            score: $score, 
                            reason: $reason,
                            created_at: datetime()
                        }, t) YIELD rel
                        RETURN rel
                    """, uid=user_id, src_id=memo_id, tgt_id=target_id,
                        rel_type=rel_type, score=score, reason=reason)
            
            # 6. 创建事件绑定关系（仅速记）
            if memo_type == "quick_note" and event_links:
                for link in event_links:
                    event_id = link.get("event_id")
                    binding_strength = link.get("binding_strength")
                    reason = link.get("binding_reason")
                    
                    if event_id:
                        await tx.run("""
                            MATCH (u:User {user_id: $uid})
                            MATCH (m:Memo {memo_id: $memo_id})
                            MATCH (e:Event {event_id: $event_id})
                            MERGE (m)-[:LINKED_TO {
                                strength: $strength,
                                reason: $reason,
                                created_at: datetime()
                            }]->(e)
                        """, uid=user_id, memo_id=memo_id, event_id=event_id,
                            strength=binding_strength, reason=reason)
            
            await tx.commit()
        finally:
            await tx.close()
    finally:
        await session.close()
    
    return {}
