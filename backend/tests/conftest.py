"""
Pytest 配置文件
定义全局 fixtures 和测试配置
"""
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """创建测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
async def setup_database():
    """设置测试数据库"""
    from app.db.config import AsyncSessionLocal
    from app.models import User
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        # 创建测试用户
        result = await session.execute(select(User).where(User.id == 1))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                id=1,
                username='test_user',
                email='test@example.com',
                password_hash='test_hash'
            )
            session.add(user)
            await session.commit()
    
    yield
    
    # 清理测试数据（可选）
    # async with AsyncSessionLocal() as session:
    #     # 清理测试数据
    #     pass
