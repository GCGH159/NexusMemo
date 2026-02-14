"""
分类节点
对速记内容进行分类，匹配到用户的分类体系中
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from memo_agent.state import MemoProcessState
from memo_agent.schemas import ClassificationResult
from app.db.config import settings


async def classify_node(state: MemoProcessState) -> dict:
    """
    对速记内容进行分类
    
    流程：
    1. 分析速记内容的主题和类型
    2. 从用户的现有分类中选择最合适的分类
    3. 如果没有合适的分类，建议创建新分类
    """
    title = state["title"]
    content = state["content"]
    user_categories = state["user_graph_context"]["categories"]
    
    # 构建分类列表字符串
    if user_categories:
        categories_str = "\n".join([
            f"- {cat['name']} (类型: {cat['type']}, 使用次数: {cat['memo_count']})"
            for cat in user_categories
        ])
    else:
        categories_str = "（用户暂无分类）"
    
    # 初始化LLM
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        temperature=0.1
    )
    
    # 输出解析器
    parser = PydanticOutputParser(pydantic_object=ClassificationResult)
    
    # 构建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能内容分类专家。你的任务是将用户的速记内容分类到合适的分类体系中。

分类原则：
1. 优先使用用户已有的分类体系
2. 如果没有合适的分类，可以建议创建新分类
3. 分类要准确反映内容的主题和性质
4. 主分类应该是内容的核心主题，次分类是更具体的细分

分类类型说明：
- work: 工作相关
- personal: 个人生活
- study: 学习笔记
- project: 项目相关
- idea: 创意想法
- meeting: 会议记录
- other: 其他

请严格按照以下 JSON 格式输出：
{format_instructions}"""),
        ("human", """速记内容：
标题：{title}
内容：{content}

用户现有的分类体系：
{categories}

请为这条速记选择最合适的分类。如果现有分类都不合适，可以建议创建新分类。""")
    ]).partial(format_instructions=parser.get_format_instructions())
    
    # 执行分类
    chain = prompt | llm | parser
    try:
        result = await chain.ainvoke({
            "title": title,
            "content": content,
            "categories": categories_str
        })
        return {
            "classification_result": result.model_dump()
        }
    except Exception as e:
        # 如果解析失败，返回默认分类
        return {
            "classification_result": {
                "primary_category": "other",
                "secondary_category": "general",
                "confidence": 0.5,
                "reason": f"分类失败: {str(e)}"
            }
        }
