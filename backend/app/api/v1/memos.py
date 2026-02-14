"""
速记API路由
提供创建速记和事件的接口
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.config import get_db
from memo_agent.workflow import process_new_memo

router = APIRouter(prefix="/memos", tags=["memos"])


class CreateMemoRequest(BaseModel):
    """创建速记请求"""
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    type: str = Field(default="quick_note", description="类型（quick_note | event）")
    user_id: int = Field(..., description="用户ID")


class CreateMemoResponse(BaseModel):
    """创建速记响应"""
    memo_id: int = Field(..., description="速记ID")
    status: str = Field(..., description="处理状态（processing | completed）")
    classification: dict = Field(default=None, description="分类结果")
    extraction: dict = Field(default=None, description="提取结果")
    relations: list = Field(default_factory=list, description="关联关系")
    event_links: list = Field(default_factory=list, description="事件绑定")


@router.post("/", response_model=CreateMemoResponse)
async def create_memo(
    request: CreateMemoRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    创建一条新的速记或事件。
    
    对于速记（quick_note）：同步处理，等待 1-3 秒返回
    对于事件（event）：同步处理（简化实现，暂不使用Celery）
    """
    user_id = request.user_id
    
    try:
        # 调用速记Agent处理
        result = await process_new_memo(
            user_id=user_id,
            memo_type=request.type,
            title=request.title,
            content=request.content,
        )
        
        return {
            "memo_id": result["memo_id"],
            "status": "completed",
            "classification": result.get("classification"),
            "extraction": result.get("extraction"),
            "relations": result.get("relations", []),
            "event_links": result.get("event_links", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/audio")
async def create_memo_from_audio(
    audio_file: UploadFile = File(...),
    user_id: int = None,
    db: AsyncSession = Depends(get_db),
):
    """
    上传音频，自动转文字后创建速记。
    
    注意：此功能需要配置Whisper模型，当前为简化实现，暂不实现音频转文字功能。
    """
    # TODO: 实现音频转文字功能
    # 1. 保存音频文件
    # 2. 调用 Whisper 转文字
    # 3. 创建速记
    
    raise HTTPException(status_code=501, detail="音频转文字功能暂未实现")


class GetMemoResponse(BaseModel):
    """获取速记响应"""
    memo_id: int
    title: str
    content: str
    type: str
    status: str
    created_at: str
    processed: bool


@router.get("/{memo_id}", response_model=GetMemoResponse)
async def get_memo(
    memo_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定速记的详细信息
    """
    from app.models import Memo
    
    memo = await db.get(Memo, memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="速记不存在")
    
    return {
        "memo_id": memo.id,
        "title": memo.title,
        "content": memo.content,
        "type": memo.type,
        "status": memo.status,
        "created_at": memo.created_at.isoformat() if memo.created_at else None,
        "processed": memo.processed,
    }


class ListMemosResponse(BaseModel):
    """获取速记列表响应"""
    memos: list[GetMemoResponse]
    total: int


@router.get("/", response_model=ListMemosResponse)
async def list_memos(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户的速记列表
    """
    from app.models import Memo
    from sqlalchemy import select, func
    
    # 查询总数
    count_query = select(func.count()).select_from(Memo).where(Memo.user_id == user_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 查询列表
    query = select(Memo).where(Memo.user_id == user_id).offset(skip).limit(limit).order_by(Memo.created_at.desc())
    result = await db.execute(query)
    memos = result.scalars().all()
    
    return {
        "memos": [
            {
                "memo_id": memo.id,
                "title": memo.title,
                "content": memo.content,
                "type": memo.type,
                "status": memo.status,
                "created_at": memo.created_at.isoformat() if memo.created_at else None,
                "processed": memo.processed,
            }
            for memo in memos
        ],
        "total": total,
    }
