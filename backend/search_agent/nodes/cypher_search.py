"""
图查询节点
使用 LLM 生成 Cypher 查询并执行
"""
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from search_agent.state import SearchState
from app.db.config import settings, get_neo4j_session


async def cypher_search_node(state: SearchState) -> Dict:
    """
    执行图查询
    
    使用 LLM 生成 Cypher 查询并执行
    
    参数：
        state: 当前状态
    
    返回：
        更新后的状态，包含图查询结果
    """
    user_id = state["user_id"]
    query = state["query"]
    
    results = []
    
    try:
        # 使用 LLM 生成 Cypher 查询
        llm = ChatOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
            temperature=0
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个 Cypher 查询专家。根据用户的自然语言查询，生成对应的 Cypher 查询语句。

数据库结构：
- Memo 节点：memo_id, user_id, title, content, type
- Event 节点：event_id, user_id, title, content, type
- Category 节点：name, level
- Tag 节点：name
- 关系：HAS_TAG, MENTIONS, RELATED_TO, LINKED_TO, PREFERS, CHILD_OF

要求：
1. 只返回 Cypher 查询语句，不要有任何解释
2. 查询必须包含 user_id = $user_id 条件
3. 查询结果应该返回节点信息
4. 使用参数化查询，使用 $user_id 和 $query 作为参数
5. 限制返回结果数量为 20 条

示例：
用户查询："查找所有与Python相关的速记"
Cypher: MATCH (m:Memo) WHERE m.user_id = $user_id AND (m.title CONTAINS $query OR m.content CONTAINS $query) RETURN m LIMIT 20
"""),
            ("user", "用户查询：{query}")
        ])
        
        chain = prompt | llm | StrOutputParser()
        cypher_query = await chain.ainvoke({"query": query})
        
        # 清理生成的 Cypher 查询
        cypher_query = cypher_query.strip()
        if cypher_query.startswith("```"):
            cypher_query = cypher_query.split("```")[1]
            if cypher_query.startswith("cypher"):
                cypher_query = cypher_query[6:].strip()
        
        # 执行 Cypher 查询
        neo4j_session = await get_neo4j_session().__anext__()
        result = await neo4j_session.run(
            cypher_query,
            user_id=user_id,
            query=query
        )
        
        async for record in result:
            # 尝试从记录中提取节点信息
            for key, value in record.items():
                if hasattr(value, 'labels'):
                    node = value
                    labels = list(node.labels)
                    
                    if "Memo" in labels:
                        results.append({
                            "type": "memo",
                            "id": node.get("memo_id"),
                            "title": node.get("title", ""),
                            "content": node.get("content", ""),
                            "score": 1.0,
                            "source": "cypher"
                        })
                    elif "Event" in labels:
                        results.append({
                            "type": "event",
                            "id": node.get("event_id"),
                            "title": node.get("title", ""),
                            "content": node.get("content", ""),
                            "score": 1.0,
                            "source": "cypher"
                        })
        
        await neo4j_session.close()
        
    except Exception as e:
        print(f"图查询失败: {str(e)}")
        # 使用备用的简单查询
        try:
            neo4j_session = await get_neo4j_session().__anext__()
            
            # 简单的关系查询
            cypher = """
            MATCH (m:Memo)
            WHERE m.user_id = $user_id
              AND (m.title CONTAINS $query OR m.content CONTAINS $query)
            RETURN m as node
            LIMIT 20
            """
            
            result = await neo4j_session.run(
                cypher,
                query=query,
                user_id=user_id
            )
            
            async for record in result:
                node = record["node"]
                
                results.append({
                    "type": "memo",
                    "id": node.get("memo_id"),
                    "title": node.get("title", ""),
                    "content": node.get("content", ""),
                    "score": 1.0,
                    "source": "cypher"
                })
            
            await neo4j_session.close()
            
        except Exception as e2:
            print(f"备用图查询也失败: {str(e2)}")
    
    return {
        "cypher_results": results
    }
