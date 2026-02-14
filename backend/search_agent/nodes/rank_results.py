"""
LLM 排序节点
使用 LLM 对搜索结果进行排序和生成最终答案
"""
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from search_agent.state import SearchState
from app.db.config import settings


async def rank_results_node(state: SearchState) -> Dict:
    """
    对搜索结果进行排序并生成最终答案
    
    使用 LLM 根据用户查询对搜索结果进行相关性排序，并生成总结性答案
    
    参数：
        state: 当前状态
    
    返回：
        更新后的状态，包含排序后的结果和最终答案
    """
    query = state["query"]
    merged_results = state.get("merged_results", [])
    
    if not merged_results:
        return {
            "ranked_results": [],
            "final_answer": "没有找到相关内容。",
            "sources": []
        }
    
    # 按分数排序
    sorted_results = sorted(merged_results, key=lambda x: x.get("score", 0), reverse=True)
    
    # 取前 20 个结果
    top_results = sorted_results[:20]
    
    # 使用 LLM 生成最终答案
    llm = ChatOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=0
    )
    
    # 构建结果摘要
    results_summary = "\n".join([
        f"{i+1}. [{r['type']}] {r['title']}\n   内容: {r['content'][:200]}...\n   来源: {', '.join(r.get('sources', []))}"
        for i, r in enumerate(top_results[:10])
    ])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能搜索助手。根据用户的查询和搜索结果，生成一个简洁、有用的答案。

要求：
1. 总结搜索结果中最相关的信息
2. 按照相关性排序结果
3. 如果有多个相关结果，分别说明它们的相关性
4. 答案要简洁明了，不超过 300 字
5. 使用中文回答

搜索结果：
{results_summary}
"""),
        ("user", "用户查询：{query}")
    ])
    
    try:
        chain = prompt | llm | StrOutputParser()
        final_answer = await chain.ainvoke({
            "query": query,
            "results_summary": results_summary
        })
    except Exception as e:
        print(f"LLM 排序失败: {str(e)}")
        final_answer = f"找到 {len(top_results)} 条相关内容。"
    
    # 提取来源信息
    sources = []
    for result in top_results:
        sources.append({
            "type": result["type"],
            "id": result["id"],
            "title": result["title"],
            "score": result.get("score", 0),
            "sources": result.get("sources", [])
        })
    
    return {
        "ranked_results": top_results,
        "final_answer": final_answer,
        "sources": sources
    }
