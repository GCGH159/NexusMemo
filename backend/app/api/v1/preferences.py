"""
用户偏好 API 路由
提供用户分类偏好的管理接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.config import get_db
from app.services.user_preference import UserPreferenceService

router = APIRouter(prefix="/preferences", tags=["preferences"])


class AddPreferenceRequest(BaseModel):
    """添加偏好请求"""
    category_level: int = Field(..., description="分类级别（1=一级分类，2=二级分类）")
    category_name: str = Field(..., description="分类名称")
    selected: bool = Field(default=True, description="是否选中")


class AddPreferenceResponse(BaseModel):
    """添加偏好响应"""
    preference_id: int
    message: str


class UpdatePreferenceRequest(BaseModel):
    """更新偏好请求"""
    selected: bool = Field(..., description="是否选中")


class UpdatePreferenceResponse(BaseModel):
    """更新偏好响应"""
    message: str


class PreferenceResponse(BaseModel):
    """偏好响应"""
    preference_id: int
    user_id: int
    category_level: int
    category_name: str
    selected: bool
    created_at: str


class PreferencesListResponse(BaseModel):
    """偏好列表响应"""
    preferences: List[PreferenceResponse]
    total: int


@router.post("/", response_model=AddPreferenceResponse, status_code=status.HTTP_201_CREATED)
async def add_preference(
    user_id: int,
    request: AddPreferenceRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    添加用户分类偏好
    """
    try:
        preference = await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user_id,
            category_level=request.category_level,
            category_name=request.category_name,
            selected=request.selected
        )
        
        return {
            "preference_id": preference.id,
            "message": "添加成功",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=PreferencesListResponse)
async def get_preferences(
    user_id: int,
    category_level: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户的分类偏好列表
    """
    preferences = await UserPreferenceService.get_user_preferences(
        db=db,
        user_id=user_id,
        category_level=category_level
    )
    
    return {
        "preferences": [
            {
                "preference_id": pref.id,
                "user_id": pref.user_id,
                "category_level": pref.category_level,
                "category_name": pref.category_name,
                "selected": pref.selected,
                "created_at": pref.created_at.isoformat() if pref.created_at else None,
            }
            for pref in preferences
        ],
        "total": len(preferences),
    }


@router.put("/{category_level}/{category_name}", response_model=UpdatePreferenceResponse)
async def update_preference(
    user_id: int,
    category_level: int,
    category_name: str,
    request: UpdatePreferenceRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    更新用户分类偏好
    """
    success = await UserPreferenceService.update_user_preference(
        db=db,
        user_id=user_id,
        category_level=category_level,
        category_name=category_name,
        selected=request.selected
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="偏好不存在"
        )
    
    return {"message": "更新成功"}


@router.delete("/{category_level}/{category_name}")
async def delete_preference(
    user_id: int,
    category_level: int,
    category_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    删除用户分类偏好
    """
    success = await UserPreferenceService.delete_user_preference(
        db=db,
        user_id=user_id,
        category_level=category_level,
        category_name=category_name
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="偏好不存在"
        )
    
    return {"message": "删除成功"}


class SelectedCategoriesResponse(BaseModel):
    """选中分类响应"""
    categories: List[str]
    total: int


@router.get("/selected", response_model=SelectedCategoriesResponse)
async def get_selected_categories(
    user_id: int,
    category_level: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户选中的分类名称列表
    """
    categories = await UserPreferenceService.get_selected_categories(
        db=db,
        user_id=user_id,
        category_level=category_level
    )
    
    return {
        "categories": categories,
        "total": len(categories),
    }
