"""
查找关联关系节点
根据速记或事件类型，采用不同的策略查找相关内容
"""
import json
from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from memo_agent.state import MemoProcessState
from memo_agent.schemas import EventAnalysis
from app.db.config import neo4j_conn, settings


# ============================================================
# 速记的被动匹配函数
# ============================================================

async def find_relations_quicknote(state: MemoProcessState) -> dict:
    """
    速记的关联查找：被动匹配策略
    
    流程：
    1. 基于标签查找相关速记
    2. 基于实体查找相关速记
    3. 基于分类查找相关速记
    4. 基于时间范围查找最近速记
    """
    user_id = state["user_id"]
    memo_id = state["memo_id"]
    extraction = state["extraction_result"]
    
    tags = [tag["name"] for tag in extraction.get("tags", [])]
    entities = [entity["name"] for entity in extraction.get("entities", [])]
    classification = state["classification_result"]
    
    candidates = []
    
    async with neo4j_conn.get_session() as session:
        # 1. 基于标签查找
        if tags:
            tag_result = await session.run("""
                MATCH (u:User {user_id: $uid})-[:OWNS]->(m:Memo)
                WHERE m.memo_id <> $mid
                AND (m)-[:HAS_TAG]->(t:Tag)
                WHERE t.name IN $tags
                WITH m, collect(t.name) AS matched_tags
                RETURN m.memo_id AS id, m.title AS title,
                       left(m.content, 200) AS content_preview,
                       'memo' AS type,
                       size(matched_tags) AS match_count
                ORDER BY match_count DESC
                LIMIT 10
            """, uid=user_id, mid=memo_id, tags=tags)
            
            async for record in tag_result:
                candidates.append({
                    "id": record["id"],
                    "title": record["title"],
                    "content_preview": record["content_preview"],
                    "type": record["type"],
                    "match_reason": f"标签匹配: {record['match_count']}个共同标签"
                })
        
        # 2. 基于实体查找
        if entities:
            entity_result = await session.run("""
                MATCH (u:User {user_id: $uid})-[:OWNS]->(m:Memo)
                WHERE m.memo_id <> $mid
                AND (m)-[:MENTIONS]->(en:Entity)
                WHERE en.name IN $entities
                WITH m, collect(en.name) AS matched_entities
                RETURN m.memo_id AS id, m.title AS title,
                       left(m.content, 200) AS content_preview,
                       'memo' AS type,
                       size(matched_entities) AS match_count
                ORDER BY match_count DESC
                LIMIT 10
            """, uid=user_id, mid=memo_id, entities=entities)
            
            async for record in entity_result:
                # 避免重复
                if not any(c["id"] == record["id"] for c in candidates):
                    candidates.append({
                        "id": record["id"],
                        "title": record["title"],
                        "content_preview": record["content_preview"],
                        "type": record["type"],
                        "match_reason": f"实体匹配: {record['match_count']}个共同实体"
                    })
        
        # 3. 基于分类查找
        primary_cat = classification.get("primary_category")
        secondary_cat = classification.get("secondary_category")
        
        if primary_cat:
            cat_result = await session.run("""
                MATCH (u:User {user_id: $uid})-[:OWNS]->(m:Memo)-[:BELONGS_TO]->(c:Category)
                WHERE m.memo_id <> $mid
                AND (c.name = $primary OR c.name = $secondary)
                RETURN DISTINCT m.memo_id AS id, m.title AS title,
                       left(m.content, 200) AS content_preview,
                       'memo' AS type,
                       '分类匹配' AS match_reason
                LIMIT 10
            """, uid=user_id, mid=memo_id, primary=primary_cat, secondary=secondary_cat)
            
            async for record in cat_result:
                # 避免重复
                if not any(c["id"] == record["id"] for c in candidates):
                    candidates.append({
                        "id": record["id"],
                        "title": record["title"],
                        "content_preview": record["content_preview"],
                        "type": record["type"],
                        "match_reason": record["match_reason"]
                    })
        
        # 4. 基于时间查找最近速记
        time_result = await session.run("""
            MATCH (u:User {user_id: $uid})-[:OWNS]->(m:Memo)
            WHERE m.memo_id <> $mid
            RETURN m.memo_id AS id, m.title AS title,
                   left(m.content, 200) AS content_preview,
                   'memo' AS type,
                   '最近创建' AS match_reason,
                   m.created_at AS created_at
            ORDER BY m.created_at DESC
            LIMIT 5
        """, uid=user_id, mid=memo_id)
        
        async for record in time_result:
            # 避免重复
            if not any(c["id"] == record["id"] for c in candidates):
                candidates.append({
                    "id": record["id"],
                    "title": record["title"],
                    "content_preview": record["content_preview"],
                    "type": record["type"],
                    "match_reason": record["match_reason"]
                })
    
    return {"relation_candidates": candidates}


# ============================================================
# 事件关联 Agent 的工具集定义
# ============================================================

@tool
async def vector_search_memos(query: str, user_id: int, top_k: int = 15) -> str:
    """
    通过语义向量相似度搜索用户的速记和事件。
    适用于：模糊语义匹配，比如搜索"关于成本优化的讨论"。
    参数：
        query: 搜索查询文本
        user_id: 用户 ID
        top_k: 返回结果数量
    """
    # 注意：实际使用时需要配置embedding模型
    # 这里简化实现，使用全文搜索代替向量搜索
    async with neo4j_conn.get_session() as session:
        result = await session.run("""
            CALL db.index.fulltext.queryNodes('memo_fulltext', $query)
            YIELD node, score
            WHERE node.user_id = $uid
            RETURN node.memo_id AS id, node.title AS title,
                   left(node.content, 200) AS content_preview,
                   labels(node)[0] AS type, score
            ORDER BY score DESC
            LIMIT $top_k
        """, query=query, uid=user_id, top_k=top_k)
        
        items = []
        async for record in result:
            items.append(dict(record))
        return json.dumps(items, ensure_ascii=False)


@tool
async def search_by_entity_graph(entity_name: str, user_id: int, hops: int = 2) -> str:
    """
    通过实体名称在知识图谱中进行多跳搜索。
    从一个实体出发，沿关系边遍历，找出 N 跳内的所有相关内容。
    适用于：找出与某个人/组织/技术相关的所有笔记。
    参数：
        entity_name: 实体名称（人名、组织名、技术名等）
        user_id: 用户 ID
        hops: 最大跳数（1-3）
    """
    async with neo4j_conn.get_session() as session:
        result = await session.run("""
            MATCH (en:Entity)
            WHERE en.name CONTAINS $name
            WITH en LIMIT 3
            CALL {
                WITH en
                MATCH path = (en)<-[:MENTIONS]-(m)<-[:OWNS]-(u:User {user_id: $uid})
                RETURN m.memo_id AS id, m.title AS title,
                       left(m.content, 200) AS content_preview,
                       labels(m)[0] AS type,
                       1 AS distance
                UNION
                WITH en
                MATCH (en)-[:RELATED_TO]-(en2:Entity)<-[:MENTIONS]-(m)<-[:OWNS]-(u:User {user_id: $uid})
                RETURN m.memo_id AS id, m.title AS title,
                       left(m.content, 200) AS content_preview,
                       labels(m)[0] AS type,
                       2 AS distance
            }
            RETURN DISTINCT id, title, content_preview, type, min(distance) AS distance
            ORDER BY distance ASC
            LIMIT 20
        """, name=entity_name, uid=user_id)
        
        items = []
        async for record in result:
            items.append(dict(record))
        return json.dumps(items, ensure_ascii=False)


@tool
async def search_by_tags(tag_names: list[str], user_id: int) -> str:
    """
    通过标签组合搜索内容。找出包含指定标签（任意匹配）的速记和事件。
    适用于：通过主题标签定位相关内容。
    参数：
        tag_names: 标签名称列表
        user_id: 用户 ID
    """ 
    async with neo4j_conn.get_session() as session:
        result = await session.run("""
            MATCH (u:User {user_id: $uid})-[:OWNS]->(m)-[:HAS_TAG]->(t:Tag)
            WHERE t.name IN $tags
            WITH m, collect(t.name) AS matched_tags
            RETURN m.memo_id AS id, m.title AS title,
                   left(m.content, 200) AS content_preview,
                   labels(m)[0] AS type,
                   matched_tags
            ORDER BY size(matched_tags) DESC
            LIMIT 20
        """, tags=tag_names, uid=user_id)
        
        items = []
        async for record in result:
            items.append(dict(record))
        return json.dumps(items, ensure_ascii=False)


@tool  
async def search_by_time_range(start_date: str, end_date: str, user_id: int) -> str:
    """
    通过时间范围搜索速记和事件。
    适用于：找出某个时间段内的所有内容，用于时间线关联。
    参数：
        start_date: 开始日期（格式：YYYY-MM-DD）
        end_date: 结束日期
        user_id: 用户 ID
    """
    async with neo4j_conn.get_session() as session:
        result = await session.run("""
            MATCH (u:User {user_id: $uid})-[:OWNS]->(x)
            WHERE x.created_at >= date($start) AND x.created_at <= date($end)
            RETURN coalesce(x.memo_id, x.event_id) AS id,
                   coalesce(x.title, 'Event') AS title,
                   labels(x)[0] AS type,
                   coalesce(x.content, x.description) AS content,
                   x.created_at AS created_at
            ORDER BY created_at DESC
            LIMIT 30
        """, start=start_date, end=end_date, uid=user_id)
        
        items = []
        async for record in result:
            items.append(dict(record))
        return json.dumps(items, ensure_ascii=False)


# ============================================================
# 事件关联 Agent 的状态定义
# ============================================================

class EventRelationAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: int
    event_id: int
    event_data: dict
    event_analysis: EventAnalysis
    collected_candidates: list[dict]
    final_decisions: list[dict]


# ============================================================
# 事件关联 Agent 节点定义
# ============================================================

async def event_agent_call_model(state: EventRelationAgentState):
    """事件关联 Agent 的 LLM 调用节点"""
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        temperature=0.3
    )
    tools = [vector_search_memos, search_by_entity_graph, search_by_tags, search_by_time_range]
    bound_llm = llm.bind_tools(tools)
    
    system_msg = SystemMessage(content="""
你是一个智能内容关联专家。用户刚刚创建了一个新的事件，你的任务是：

1. 首先深度分析这个事件：
   - 识别事件类型（project/habit/impact/personality/milestone）
   - 提取核心关键词
   - 判断时间范围
   - 推测可能关联的主题方向

2. 然后主动搜索用户的所有速记和事件：
   - 使用 vector_search_memos 进行语义模糊匹配
   - 使用 search_by_entity_graph 找到与实体相关的内容
   - 使用 search_by_tags 通过主题查找
   - 使用 search_by_time_range 按时间范围查找

3. 最后判断哪些内容应该与该事件建立关联：
   - 评估每个候选内容的关联度
   - 决定关系类型（RELATED_TO / LINKED_TO / EXTENDS / CONTRADICTS）
   - 给出关联理由

重要原则：
- 宁可漏掉一些弱关联，不要建立无意义的强关联
- 优先考虑语义相关性，而不是字面匹配
- 对于事件类内容，要特别关注时间上的连续性
- 每次工具调用都要说明你的搜索意图
- 不要重复搜索相同的内容
- 搜索完成后，输出最终的关联决策列表

输出格式要求：
对于每个最终确认的关联，输出：
```json
{{
  "target_id": 123,
  "target_type": "memo",
  "relation_type": "RELATED_TO",
  "score": 0.85,
  "reason": "该速记记录了事件初期的重要决策",
  "should_link": true
}}
```
""")
    
    response = bound_llm.invoke([system_msg] + state["messages"])
    return {"messages": [response]}


async def event_agent_tool_node(state: EventRelationAgentState):
    """事件关联 Agent 的工具执行节点"""
    tools_by_name = {
        "vector_search_memos": vector_search_memos,
        "search_by_entity_graph": search_by_entity_graph,
        "search_by_tags": search_by_tags,
        "search_by_time_range": search_by_time_range,
    }
    
    outputs = []
    last_message = state["messages"][-1]
    
    for tool_call in getattr(last_message, "tool_calls", []):
        tool = tools_by_name[tool_call["name"]]
        tool_args = tool_call["args"]
        
        # 注入 user_id
        if "user_id" not in tool_args:
            tool_args["user_id"] = state["user_id"]
        
        result = await tool.ainvoke(tool_args)
        outputs.append(ToolMessage(
            content=str(result),
            name=tool_call["name"],
            tool_call_id=tool_call["id"],
        ))
    
    return {"messages": outputs}


def should_continue_event_agent(state: EventRelationAgentState):
    """判断是否继续调用工具"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "end"


# ============================================================
# 事件关联 Agent 的主入口
# ============================================================

async def find_relations_event_node(state: MemoProcessState) -> dict:
    """
    事件的关联查找主节点。
    创建一个临时的 ReAct Agent，让它自主搜索并决策关联关系。
    """
    # 先对事件做深度分析
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        temperature=0.1
    )
    structured_llm = llm.with_structured_output(EventAnalysis)
    
    analysis = await structured_llm.ainvoke(f"""
    分析以下事件，提取其特征：

    标题：{state['title']}
    内容：{state['content']}
    
    请分析事件的类型、关键词、时间范围、优先级和周期性。
    """)
    
    # 构建事件关联 Agent
    workflow = StateGraph(EventRelationAgentState)
    workflow.add_node("agent", event_agent_call_model)
    workflow.add_node("tools", event_agent_tool_node)
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent", should_continue_event_agent,
        {"continue": "tools", "end": END}
    )
    workflow.add_edge("tools", "agent")
    
    event_agent = workflow.compile()
    
    # 运行 Agent
    initial_state = EventRelationAgentState(
        messages=[
            HumanMessage(content=f"""
用户刚创建了一个新事件，请帮他找出所有关联的速记和事件。

事件详情：
- ID: {state['memo_id']}
- 标题：{state['title']}
- 描述：{state['content']}
- 创建时间：{state.get('created_at', 'N/A')}

你的任务：
1. 使用多个搜索工具，全面查找可能相关的内容
2. 对找到的内容进行关联度评估
3. 输出最终的关联决策列表
""")
        ],
        user_id=state["user_id"],
        event_id=state["memo_id"],
        event_data={
            "title": state["title"],
            "content": state["content"]
        },
        event_analysis=analysis,
        collected_candidates=[],
        final_decisions=[]
    )
    
    final_state = None
    async for event_state in event_agent.astream(initial_state):
        final_state = event_state
    
    # 解析 Agent 最终输出，提取关联决策
    final_message = final_state["messages"][-1]
    final_relations = []
    
    if hasattr(final_message, "content"):
        # 从 AI 响应中提取 JSON 列表
        content = final_message.content
        if "```json" in content and "```" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
            final_relations = json.loads(json_str)
        else:
            # 简化：解析行内 JSON
            import re
            json_pattern = r'\{[^{}]*\}'
            matches = re.findall(json_pattern, content)
            for match in matches:
                try:
                    final_relations.append(json.loads(match))
                except:
                    pass
    
    return {
        "relation_candidates": final_relations,
        "final_relations": final_relations,
    }


# ============================================================
# 统一的关联查找入口
# ============================================================

async def find_relations_node(state: MemoProcessState) -> dict:
    """
    统一的关联查找入口，根据 memo_type 路由到不同的查找策略。
    """
    if state["memo_type"] == "event":
        return await find_relations_event_node(state)
    else:
        return await find_relations_quicknote(state)
