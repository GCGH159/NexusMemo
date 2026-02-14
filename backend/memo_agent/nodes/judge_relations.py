"""
判定关联关系节点
对候选的关联内容进行批量判定，决定是否建立真实的关联关系
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from memo_agent.state import MemoProcessState
from memo_agent.schemas import RelationBatchResult
from app.db.config import settings


async def judge_relations_node(state: MemoProcessState) -> dict:
    """
    对候选的关联内容进行批量判定，决定是否建立真实的关联关系。
    """
    if not state["relation_candidates"]:
        return {"final_relations": []}
    
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        temperature=0
    )
    structured_llm = llm.with_structured_output(RelationBatchResult)
    
    content = state["content"]
    candidates_json = json.dumps(state["relation_candidates"], ensure_ascii=False, indent=2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个内容关联专家。用户有一条新速记，系统找到了一些可能相关的内容。

你的任务：判断这些候选内容是否真的与新速记相关，如果相关则确定关系类型和强度。

关系类型说明：
- RELATED_TO: 一般性关联，语义上有相关性但没有强因果关系
- LINKED_TO: 直接链接，新内容是对候选内容的补充或延续
- EXTENDS: 扩展关系，新内容在候选内容的基础上展开了讨论
- CONTRADICTS: 矛盾关系，新内容与候选内容观点相左
- CAUSED_BY: 因果关系，新内容是由候选内容导致的

关联强度评分（0-1）：
- 0.9-1.0: 极强关联，必须关联
- 0.7-0.9: 强关联，应该关联
- 0.5-0.7: 中等关联，可选关联
- 0.3-0.5: 弱关联，不建议关联
- 0.0-0.3: 无关，不关联

规则：
1. 只建立评分 > 0.5 的关联
2. 关联理由要清晰具体
3. 如果有多个候选都相关，按评分排序保留前 5 个"""),
        ("human", """新速记内容：
{content}

候选相关内容：
{candidates}

请判断每个候选是否应该关联，并给出详细的关系类型、评分和理由。""")
    ])

    chain = prompt | structured_llm
    result = await chain.ainvoke({
        "content": content,
        "candidates": candidates_json,
    })
    
    # 过滤掉 should_link=False 的结果
    final_relations = [
        j.model_dump() for j in result.judgments if j.should_link
    ]
    
    return {
        "final_relations": final_relations,
    }
