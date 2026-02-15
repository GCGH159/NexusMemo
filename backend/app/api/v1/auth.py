"""
用户认证 API 路由
提供用户注册、登录、注销等接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.config import get_db
from app.services.auth import AuthService
from app.services.category import CategoryService
from app.models import User, UserCategoryPreference

router = APIRouter(prefix="/auth", tags=["auth"])


# ==================== 请求/响应模型 ====================

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    primary_categories: List[str] = Field(..., min_items=1, description="一级分类列表")
    sub_categories: Optional[List[str]] = Field(None, description="二级分类列表（可选，不提供则自动生成）")


class RegisterResponse(BaseModel):
    """注册响应"""
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    token: str = Field(..., description="会话Token")
    preferences: dict = Field(..., description="用户偏好")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    token: str = Field(..., description="会话Token")


class LogoutResponse(BaseModel):
    """注销响应"""
    message: str = Field(..., description="响应消息")


class GetPrimaryCategoriesResponse(BaseModel):
    """获取一级分类响应"""
    code: int = Field(200, description="响应码")
    message: str = Field("获取一级分类成功", description="响应消息")
    categories: List[str] = Field(..., description="一级分类列表")


class GenerateSubCategoriesRequest(BaseModel):
    """生成二级分类请求"""
    primary_categories: List[str] = Field(..., min_items=1, description="一级分类列表")


class GenerateSubCategoriesResponse(BaseModel):
    """生成二级分类响应"""
    code: int = Field(200, description="响应码")
    message: str = Field("生成二级分类成功", description="响应消息")
    categories: List[str] = Field(..., description="二级分类列表")
    descriptions: dict = Field(..., description="每个分类的描述")


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    user_id: int
    username: str
    email: Optional[str]
    created_at: str
    preferences: Optional[dict] = None


class CheckUsernameResponse(BaseModel):
    """检查用户名响应"""
    exists: bool = Field(..., description="用户名是否已存在")
    message: str = Field(..., description="响应消息")


# ==================== 依赖注入 ====================

async def get_current_user(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前登录用户
    
    参数：
        token: 会话 Token
        db: 数据库会话
    
    返回：
        当前用户对象
    
    异常：
        401: Token 无效或过期
    """
    user = await AuthService.verify_session(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期"
        )
    return user


# ==================== API 接口 ====================

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册
    
    流程：
    1. 验证一级分类
    2. 如果未提供二级分类，使用 LangChain 生成
    3. 创建用户
    4. 保存用户分类偏好
    5. 创建会话
    6. 在 Neo4j 中创建用户节点和分类节点
    """
    # 验证一级分类
    category_service = CategoryService()
    for category in request.primary_categories:
        if not category_service.validate_primary_category(category):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的一级分类: {category}"
            )
    
    # 如果未提供二级分类，自动生成
    sub_categories = request.sub_categories
    if not sub_categories:
        try:
            result = await category_service.generate_subcategories(request.primary_categories)
            sub_categories = result.categories
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"生成二级分类失败: {str(e)}"
            )
    
    # 创建用户
    try:
        user = await AuthService.create_user(
            db=db,
            username=request.username,
            password=request.password,
            email=request.email,
            preferences={
                "primary_categories": request.primary_categories,
                "sub_categories": sub_categories
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # 保存用户分类偏好到 MySQL
    for category in request.primary_categories:
        pref = UserCategoryPreference(
            user_id=user.id,
            category_level=1,
            category_name=category,
            selected=True
        )
        db.add(pref)
    
    for category in sub_categories:
        pref = UserCategoryPreference(
            user_id=user.id,
            category_level=2,
            category_name=category,
            selected=True
        )
        db.add(pref)
    
    await db.commit()
    
    # 在 Neo4j 中创建用户节点和分类节点
    try:
        from app.db.config import get_neo4j_session
        neo4j_session = await get_neo4j_session().__anext__()
        
        # 创建用户节点
        await neo4j_session.run(
            "MERGE (u:User {user_id: $user_id}) "
            "SET u.name = $username, u.created_at = datetime()",
            user_id=user.id,
            username=user.username
        )
        
        # 创建一级分类节点并建立 PREFERS 关系
        for category in request.primary_categories:
            await neo4j_session.run(
                "MERGE (c:Category {name: $name, level: 1}) "
                "MERGE (u:User {user_id: $user_id}) "
                "MERGE (u)-[:PREFERS]->(c)",
                name=category,
                user_id=user.id
            )
        
        # 创建二级分类节点并建立层级关系
        for sub_category in sub_categories:
            # 假设二级分类属于第一个一级分类（简化处理）
            primary_category = request.primary_categories[0] if request.primary_categories else "其他"
            
            await neo4j_session.run(
                "MERGE (c:Category {name: $name, level: 2}) "
                "MERGE (p:Category {name: $parent_name, level: 1}) "
                "MERGE (c)-[:CHILD_OF]->(p) "
                "MERGE (u:User {user_id: $user_id}) "
                "MERGE (u)-[:PREFERS]->(c)",
                name=sub_category,
                parent_name=primary_category,
                user_id=user.id
            )
        
        await neo4j_session.close()
    except Exception as e:
        # Neo4j 创建失败不影响注册流程
        print(f"Neo4j 创建失败: {str(e)}")
    
    # 创建会话
    session = await AuthService.create_session(db, user.id)
    
    return {
        "user_id": user.id,
        "username": user.username,
        "token": session.token,
        "preferences": user.preferences
    }


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    验证用户名和密码，创建会话
    """
    # 验证用户凭据
    user = await AuthService.authenticate_user(
        db=db,
        username=request.username,
        password=request.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 创建会话
    session = await AuthService.create_session(db, user.id)
    
    return {
        "user_id": user.id,
        "username": user.username,
        "token": session.token
    }


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注销
    
    删除会话 Token
    """
    success = await AuthService.delete_session(db, token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    return {"message": "注销成功"}


@router.get("/check-username", response_model=CheckUsernameResponse)
async def check_username(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """
    检查用户名是否已存在
    
    参数：
        username: 用户名
        db: 数据库会话
    
    返回：
        用户名是否存在
    """
    from sqlalchemy import select
    from app.models import User
    
    result = await db.execute(
        select(User).where(User.username == username)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        return {
            "exists": True,
            "message": "用户名已被注册"
        }
    
    return {
        "exists": False,
        "message": "用户名可用"
    }


@router.get("/categories/primary", response_model=GetPrimaryCategoriesResponse)
async def get_primary_categories():
    """
    获取所有预定义的一级分类
    """
    category_service = CategoryService()
    return {
        "code": 200,
        "message": "获取一级分类成功",
        "categories": category_service.get_primary_categories()
    }


@router.post("/categories/generate-sub", response_model=GenerateSubCategoriesResponse)
async def generate_subcategories(
    request: GenerateSubCategoriesRequest
):
    """
    根据一级分类生成二级分类
    
    使用 LangChain 自动生成相关的二级分类
    """
    category_service = CategoryService()
    
    # 验证一级分类
    for category in request.primary_categories:
        if not category_service.validate_primary_category(category):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的一级分类: {category}"
            )
    
    # 生成二级分类
    try:
        result = await category_service.generate_subcategories(request.primary_categories)
        return {
            "code": 200,
            "message": "生成二级分类成功",
            "categories": result.categories,
            "descriptions": result.descriptions
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成二级分类失败: {str(e)}"
        )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户信息
    """
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "preferences": current_user.preferences
    }
