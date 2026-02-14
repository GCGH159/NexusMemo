"""
用户偏好服务
管理用户的分类偏好设置
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models import UserCategoryPreference


class UserPreferenceService:
    """用户偏好服务"""
    
    @staticmethod
    async def get_user_preferences(
        db: AsyncSession,
        user_id: int,
        category_level: Optional[int] = None
    ) -> List[UserCategoryPreference]:
        """
        获取用户的分类偏好
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            category_level: 分类级别（1=一级分类，2=二级分类），None表示获取所有
        
        返回：
            用户偏好列表
        """
        query = select(UserCategoryPreference).where(UserCategoryPreference.user_id == user_id)
        
        if category_level is not None:
            query = query.where(UserCategoryPreference.category_level == category_level)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def add_user_preference(
        db: AsyncSession,
        user_id: int,
        category_level: int,
        category_name: str,
        selected: bool = True
    ) -> UserCategoryPreference:
        """
        添加用户分类偏好
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            category_level: 分类级别（1=一级分类，2=二级分类）
            category_name: 分类名称
            selected: 是否选中
        
        返回：
            创建的偏好对象
        """
        # 检查是否已存在
        existing = await db.execute(
            select(UserCategoryPreference).where(
                UserCategoryPreference.user_id == user_id,
                UserCategoryPreference.category_level == category_level,
                UserCategoryPreference.category_name == category_name
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"偏好已存在: {category_name}")
        
        # 创建偏好
        preference = UserCategoryPreference(
            user_id=user_id,
            category_level=category_level,
            category_name=category_name,
            selected=selected
        )
        
        db.add(preference)
        await db.commit()
        await db.refresh(preference)
        
        return preference
    
    @staticmethod
    async def update_user_preference(
        db: AsyncSession,
        user_id: int,
        category_level: int,
        category_name: str,
        selected: bool
    ) -> bool:
        """
        更新用户分类偏好
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            category_level: 分类级别（1=一级分类，2=二级分类）
            category_name: 分类名称
            selected: 是否选中
        
        返回：
            更新成功返回 True，失败返回 False
        """
        result = await db.execute(
            select(UserCategoryPreference).where(
                UserCategoryPreference.user_id == user_id,
                UserCategoryPreference.category_level == category_level,
                UserCategoryPreference.category_name == category_name
            )
        )
        preference = result.scalar_one_or_none()
        
        if not preference:
            return False
        
        preference.selected = selected
        await db.commit()
        
        return True
    
    @staticmethod
    async def delete_user_preference(
        db: AsyncSession,
        user_id: int,
        category_level: int,
        category_name: str
    ) -> bool:
        """
        删除用户分类偏好
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            category_level: 分类级别（1=一级分类，2=二级分类）
            category_name: 分类名称
        
        返回：
            删除成功返回 True，失败返回 False
        """
        result = await db.execute(
            delete(UserCategoryPreference).where(
                UserCategoryPreference.user_id == user_id,
                UserCategoryPreference.category_level == category_level,
                UserCategoryPreference.category_name == category_name
            )
        )
        
        await db.commit()
        
        return result.rowcount > 0
    
    @staticmethod
    async def batch_add_preferences(
        db: AsyncSession,
        user_id: int,
        primary_categories: List[str],
        sub_categories: List[str]
    ) -> None:
        """
        批量添加用户分类偏好
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            primary_categories: 一级分类列表
            sub_categories: 二级分类列表
        """
        # 添加一级分类偏好
        for category in primary_categories:
            try:
                await UserPreferenceService.add_user_preference(
                    db=db,
                    user_id=user_id,
                    category_level=1,
                    category_name=category,
                    selected=True
                )
            except ValueError:
                # 如果已存在，跳过
                pass
        
        # 添加二级分类偏好
        for category in sub_categories:
            try:
                await UserPreferenceService.add_user_preference(
                    db=db,
                    user_id=user_id,
                    category_level=2,
                    category_name=category,
                    selected=True
                )
            except ValueError:
                # 如果已存在，跳过
                pass
    
    @staticmethod
    async def get_selected_categories(
        db: AsyncSession,
        user_id: int,
        category_level: Optional[int] = None
    ) -> List[str]:
        """
        获取用户选中的分类名称列表
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            category_level: 分类级别（1=一级分类，2=二级分类），None表示获取所有
        
        返回：
            选中的分类名称列表
        """
        query = select(UserCategoryPreference.category_name).where(
            UserCategoryPreference.user_id == user_id,
            UserCategoryPreference.selected == True
        )
        
        if category_level is not None:
            query = query.where(UserCategoryPreference.category_level == category_level)
        
        result = await db.execute(query)
        return result.scalars().all()
