"""
绑定事件节点
判断当前速记应该绑定到哪些事件上
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from memo_agent.state import MemoProcessState
from memo_agent.schemas import EventBindingBatchResult
from app.db.config import settings


async def bind_events_node(state: MemoProcessState) -> dict:
    """
    判断当前速记应该绑定到哪些事件上。
    事件绑定是速记与事件的特殊关联关系，用于"事件看板"视图。
    """
    ctx = state["user_graph_context"]
    active_events = ctx["active_events"]
    
    if not active_events:
        return {"event_links": []}
    
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        temperature=0
    )
    
    # 输出解析器
    parser = PydanticOutputParser(pydantic_object=EventBindingBatchResult)
    
    events_json = json.dumps(active_events, ensure_ascii=False, indent=2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个事件关联专家。用户有一条新速记，请判断它应该绑定到哪些活跃事件上。

事件绑定规则：
1. 如果速记的内容与某个事件的目标、进展、相关讨论直接相关，应该绑定
2. 如果速记是事件的执行过程记录，必须绑定
3. 如果速记只是偶尔提及事件但不涉及具体内容，不绑定

绑定强度评分（0-1）：
- > 0.7: 强绑定，应该绑定
- 0.5-0.7: 中等绑定，可选绑定  
- < 0.5: 弱绑定，不绑定

输出：
- decisions: 对每个活跃事件的绑定决策
- auto_detected_events: 如果内容中提及了用户尚未创建的事件，列出建议

请严格按照以下 JSON 格式输出：
{format_instructions}"""),
        ("human", """新速记内容：
{content}

用户当前活跃的事件列表：
{events}

请判断该速记应该绑定到哪些事件，以及是否检测到潜在的新事件。""")
    ]).partial(format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser
    try:
        result = await chain.ainvoke({
            "content": state["content"],
            "events": events_json,
        })
        
        # 只保留 should_bind=True 的绑定
        decisions = result.decisions or []
        final_links = [
            d.model_dump() for d in decisions if d.should_bind
        ]
        
        return {
            "event_links": final_links,
        }
    except Exception as e:
        # 如果解析失败，返回空事件链接列表
        return {
            "event_links": [],
        }
