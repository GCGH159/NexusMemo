"""
搜索策略决策节点
根据用户查询智能决策使用哪些搜索策略
"""
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from search_agent.state import SearchState
from app.db.config import settings


async def decide_search_strategy_node(state: SearchState) -> Dict:
    """
    决策搜索策略
    
    根据用户查询的内容和意图，决定使用哪些搜索策略：
    - fulltext: 关键词匹配（适用于明确的实体、标签、分类搜索）
    - cypher: 图查询（适用于复杂的图关系查询）
    - traversal: 多跳遍历（适用于探索关系链）
    
    参数：
        state: 当前状态
    
    返回：
        更新后的状态，包含选择的搜索策略
    """
    query = state["query"]
    
    # 使用 LLM 决策搜索策略
    llm = ChatOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=0
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个搜索策略决策专家。根据用户的搜索查询，决定使用哪些搜索策略。

可用的搜索策略：
1. fulltext - 全文搜索：适用于关键词、实体名、标签、分类等明确匹配
2. cypher - 图查询：适用于复杂的图关系查询，如"查找所有与X相关的Y"
3. traversal - 多跳遍历：适用于探索关系链，如"X通过什么路径连接到Y"

请根据查询内容，返回应该使用的策略列表（用逗号分隔）。
如果查询包含明确的关键词或实体名，使用 fulltext。
如果查询涉及复杂的关系或条件，使用 cypher。
如果查询需要探索关系链或路径，使用 traversal。
可以同时使用多个策略。

示例：
- "关于Python的学习笔记" -> fulltext
- "查找所有与'项目A'相关的会议记录" -> cypher
- "从'项目A'到'客户B'的关系链" -> traversal
- "查找与'Python'相关的所有速记和事件" -> fulltext,cypher
"""),
        ("user", "用户查询：{query}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        strategy_str = await chain.ainvoke({"query": query})
        # 解析策略列表
        strategies = [s.strip().lower() for s in strategy_str.split(",")]
        valid_strategies = ["fulltext", "cypher", "traversal"]
        search_strategy = [s for s in strategies if s in valid_strategies]
        
        # 如果没有有效策略，默认使用全文搜索
        if not search_strategy:
            search_strategy = ["fulltext"]
    except Exception as e:
        print(f"搜索策略决策失败: {str(e)}")
        search_strategy = ["fulltext"]
    
    return {
        "search_strategy": search_strategy
    }
