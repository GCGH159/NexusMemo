"""
提取节点
从速记内容中提取标签和实体
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from memo_agent.state import MemoProcessState
from memo_agent.schemas import ExtractionResult
from app.db.config import settings


async def extract_tags_entities_node(state: MemoProcessState) -> dict:
    """
    从速记内容中提取标签和实体
    
    流程：
    1. 识别内容中的关键词和主题，生成标签
    2. 识别内容中的实体（人名、组织名、技术名、概念、地点等）
    3. 优先复用用户已有的标签
    4. 生成内容摘要
    """
    title = state["title"]
    content = state["content"]
    user_tags = state["user_graph_context"]["tags"]
    
    # 构建标签列表字符串
    if user_tags:
        tags_str = "\n".join([
            f"- {tag['name']} (使用次数: {tag['memo_count']})"
            for tag in user_tags
        ])
    else:
        tags_str = "（用户暂无标签）"
    
    # 初始化LLM
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        temperature=0.2
    )
    
    # 输出解析器
    parser = PydanticOutputParser(pydantic_object=ExtractionResult)
    
    # 构建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能内容提取专家。你的任务是从速记内容中提取标签、实体和时间信息。

提取原则：
1. 标签：提取内容的核心主题和关键词，优先使用用户已有的标签
2. 实体：识别内容中提到的人名、组织名、技术名、概念、地点等
3. 时间信息：识别内容中的时间表达，判断是过去、现在还是将来
4. 摘要：生成简洁的内容摘要（不超过100字）

实体类型说明：
- person: 人名
- organization: 组织/公司名
- technology: 技术栈/工具名
- concept: 概念/术语
- location: 地点

时间类型说明：
- past: 过去的时间
- present: 现在
- future: 将来的时间

提醒类型说明：
- deadline: 截止日期
- appointment: 约会/会议
- task: 任务/待办事项

**重要：datetime_str字段必须填写！**
- 如果是相对时间（如"明天"、"后天"、"下周三"、"下周五"），直接使用该词
- 如果是具体时间（如"2026-02-20"、"下周三下午2点"），提取可解析的部分（如"下周三"）
- 如果没有时间信息，time_type设为"present"，datetime_str设为"今天"

请严格按照以下 JSON 格式输出：
{format_instructions}"""),
        ("human", """速记内容：
标题：{title}
内容：{content}

用户常用的标签：
{tags}

请提取标签、实体和时间信息，并生成摘要。""")
    ]).partial(format_instructions=parser.get_format_instructions())
    
    # 执行提取
    chain = prompt | llm | parser
    try:
        result = await chain.ainvoke({
            "title": title,
            "content": content,
            "tags": tags_str
        })
        return {
            "extraction_result": result.model_dump()
        }
    except Exception as e:
        # 如果解析失败，返回默认提取结果
        return {
            "extraction_result": {
                "tags": [],
                "entities": [],
                "summary": f"提取失败: {str(e)}"
            }
        }
