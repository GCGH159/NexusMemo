"""
速记API测试
测试创建、获取、更新、删除速记的功能
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.models import Memo, MemoStatus, User
from app.db.config import get_db
from app.services.auth import AuthService


class TestMemoAPI:
    """速记API测试"""
    
    @pytest.mark.asyncio
    async def test_create_memo(self, db: AsyncSession):
        """测试创建速记"""
        # 创建测试用户
        import uuid
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        user = User(username=username, email=f"{username}@test.com", password_hash=AuthService.hash_password("testpass123"))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/memos/",
                json={
                    "title": "测试速记",
                    "content": "这是一条测试速记内容",
                    "type": "quick_note",
                    "user_id": user.id
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "memo_id" in data
            assert data["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_memo(self, db: AsyncSession):
        """测试获取单条速记"""
        # 创建测试用户和速记
        import uuid
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        user = User(username=username, email=f"{username}@test.com", password_hash=AuthService.hash_password("testpass123"))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        memo = Memo(
            user_id=user.id,
            title="测试速记",
            content="测试内容",
            type="quick_note",
            status=MemoStatus.ACTIVE
        )
        db.add(memo)
        await db.commit()
        await db.refresh(memo)
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/memos/{memo.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["memo_id"] == memo.id
            assert data["title"] == "测试速记"
    
    @pytest.mark.asyncio
    async def test_list_memos(self, db: AsyncSession):
        """测试获取速记列表"""
        # 创建测试用户和多条速记
        import uuid
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        user = User(username=username, email=f"{username}@test.com", password_hash=AuthService.hash_password("testpass123"))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        for i in range(3):
            memo = Memo(
                user_id=user.id,
                title=f"测试速记{i}",
                content=f"测试内容{i}",
                type="quick_note",
                status=MemoStatus.ACTIVE
            )
            db.add(memo)
        await db.commit()
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/memos/",
                params={"user_id": user.id, "limit": 10}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "memos" in data
            assert "total" in data
            assert len(data["memos"]) == 3
            assert data["total"] == 3
    
    @pytest.mark.asyncio
    async def test_update_memo(self, db: AsyncSession):
        """测试更新速记"""
        # 创建测试用户和速记
        import uuid
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        user = User(username=username, email=f"{username}@test.com", password_hash=AuthService.hash_password("testpass123"))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        memo = Memo(
            user_id=user.id,
            title="原始标题",
            content="原始内容",
            type="quick_note",
            status=MemoStatus.ACTIVE
        )
        db.add(memo)
        await db.commit()
        await db.refresh(memo)
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/memos/{memo.id}",
                json={
                    "title": "更新后的标题",
                    "content": "更新后的内容"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["memo_id"] == memo.id
            assert data["message"] == "更新成功"
            
            # 清除会话缓存并验证数据库中的更新
            await db.commit()
            await db.refresh(memo)
            assert memo.title == "更新后的标题"
            assert memo.content == "更新后的内容"
    
    @pytest.mark.asyncio
    async def test_delete_memo(self, db: AsyncSession):
        """测试删除速记（软删除）"""
        # 创建测试用户和速记
        import uuid
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        user = User(username=username, email=f"{username}@test.com", password_hash=AuthService.hash_password("testpass123"))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        memo = Memo(
            user_id=user.id,
            title="待删除的速记",
            content="待删除的内容",
            type="quick_note",
            status=MemoStatus.ACTIVE
        )
        db.add(memo)
        await db.commit()
        await db.refresh(memo)
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/v1/memos/{memo.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["memo_id"] == memo.id
            assert data["message"] == "删除成功"
            
            # 清除会话缓存并验证软删除（状态变为DELETED）
            await db.commit()
            await db.refresh(memo)
            assert memo.status == MemoStatus.DELETED
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_memo(self, db: AsyncSession):
        """测试获取不存在的速记"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/memos/99999")
            
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_memo(self, db: AsyncSession):
        """测试更新不存在的速记"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/v1/memos/99999",
                json={"title": "新标题"}
            )
            
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_memo(self, db: AsyncSession):
        """测试删除不存在的速记"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/v1/memos/99999")
            
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_memo_status(self, db: AsyncSession):
        """测试更新速记状态"""
        # 创建测试用户和速记
        import uuid
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        user = User(username=username, email=f"{username}@test.com", password_hash=AuthService.hash_password("testpass123"))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        memo = Memo(
            user_id=user.id,
            title="测试速记",
            content="测试内容",
            type="quick_note",
            status=MemoStatus.ACTIVE
        )
        db.add(memo)
        await db.commit()
        await db.refresh(memo)
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 归档速记
            response = await client.put(
                f"/api/v1/memos/{memo.id}",
                json={"status": "archived"}
            )
            
            assert response.status_code == 200
            
            # 清除会话缓存并验证状态更新
            await db.commit()
            await db.refresh(memo)
            assert memo.status == MemoStatus.ARCHIVED
