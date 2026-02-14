"""
搜索 API 路由
提供智能搜索接口
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.config import get_db
from search_agent.workflow import execute_search

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询")
    user_id: int = Field(..., description="用户ID")


class SearchResultItem(BaseModel):
    """搜索结果项"""
    type: str = Field(..., description="类型（memo | event）")
    id: int = Field(..., description="ID")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    score: float = Field(..., description="相关性分数")
    sources: list = Field(default_factory=list, description="搜索来源")


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str = Field(..., description="搜索查询")
    answer: str = Field(..., description="AI 生成的答案")
    results: list[SearchResultItem] = Field(..., description="搜索结果列表")
    sources: list = Field(..., description="来源信息")


@router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    执行智能搜索
    
    使用搜索 Agent 根据用户查询智能决策搜索策略，并返回相关结果。
    
    流程：
    1. Agent 决策搜索策略（全文搜索、图查询、多跳遍历）
    2. 执行相应的搜索
    3. 融合搜索结果
    4. LLM 排序并生成最终答案
    """
    try:
        result = await execute_search(
            user_id=request.user_id,
            query=request.query
        )
        
        return {
            "query": result["query"],
            "answer": result["answer"],
            "results": result["results"],
            "sources": result["sources"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
