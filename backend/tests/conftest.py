"""
Pytest 配置文件
定义全局 fixtures 和测试配置
"""
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db():
    """创建数据库会话"""
    from app.db.config import AsyncSessionLocal
    
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@pytest_asyncio.fixture(scope="session")
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
