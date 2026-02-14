"""
分类生成服务
使用 LangChain 根据用户选择的一级分类生成二级分类
"""
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.db.config import settings


class SubCategories(BaseModel):
    """二级分类生成结果"""
    categories: List[str] = Field(description="二级分类列表")
    descriptions: Dict[str, str] = Field(description="每个分类的简短描述")


class CategoryService:
    """分类生成服务"""
    
    # 预定义的一级分类
    PRIMARY_CATEGORIES = [
        "学习资料",
        "刊物",
        "运动",
        "工作项目",
        "生活记录",
        "兴趣爱好",
        "财务记录",
        "健康医疗",
        "旅行计划",
        "社交活动"
    ]
    
    def __init__(self):
        """初始化分类服务"""
        # 输出解析器
        self.parser = PydanticOutputParser(pydantic_object=SubCategories)
        
        # LLM 配置 - 使用 openai_api_base 和 openai_api_key
        self.llm = ChatOpenAI(
            openai_api_base=settings.LLM_BASE_URL,
            openai_api_key=settings.LLM_API_KEY,
            model_name=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE
        )
        
        # 提示词模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个智能分类助手。根据用户选择的一级兴趣分类，"
                      "生成 8-12 个具体的二级分类。分类应该有实际意义且互不重叠。"
                      "每个分类应该简短明了，适合作为笔记的分类标签。\n\n"
                      "{format_instructions}"),
            ("human", "用户选择的一级分类是：{primary_categories}\n"
                      "请生成对应的二级分类。")
        ]).partial(format_instructions=self.parser.get_format_instructions())
        
        # 构建链
        self.chain = self.prompt | self.llm | self.parser
    
    async def generate_subcategories(
        self,
        primary_categories: List[str]
    ) -> SubCategories:
        """
        根据一级分类生成二级分类
        
        参数：
            primary_categories: 一级分类列表
        
        返回：
            SubCategories 对象，包含二级分类列表和描述
        """
        # 验证一级分类
        for category in primary_categories:
            if category not in self.PRIMARY_CATEGORIES:
                raise ValueError(f"无效的一级分类: {category}")
        
        # 调用 LLM 生成二级分类
        try:
            result = await self.chain.ainvoke({
                "primary_categories": ", ".join(primary_categories)
            })
            return result
        except Exception as e:
            # 如果解析失败，返回默认值
            print(f"LLM 解析失败: {str(e)}")
            default_categories = [
                "笔记", "资料", "教程", "练习", 
                "总结", "计划", "心得", "其他"
            ]
            return SubCategories(
                categories=default_categories,
                descriptions={cat: f"{cat}相关内容" for cat in default_categories}
            )
    
    @staticmethod
    def get_primary_categories() -> List[str]:
        """获取所有预定义的一级分类"""
        return CategoryService.PRIMARY_CATEGORIES.copy()
    
    @staticmethod
    def validate_primary_category(category: str) -> bool:
        """验证一级分类是否有效"""
        return category in CategoryService.PRIMARY_CATEGORIES
