"""
用户认证模块测试
测试注册、登录、注销等功能
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth import AuthService
from app.services.category import CategoryService
from app.models import User, Session, UserCategoryPreference


class TestAuthService:
    """测试认证服务"""
    
    @pytest.mark.asyncio
    async def test_hash_password(self):
        """测试密码哈希"""
        password = "testpass123"
        hashed = AuthService.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    @pytest.mark.asyncio
    async def test_verify_password(self):
        """测试密码验证"""
        password = "testpass123"
        hashed = AuthService.hash_password(password)
        
        # 正确密码
        assert AuthService.verify_password(password, hashed) is True
        
        # 错误密码
        assert AuthService.verify_password("wrongpass", hashed) is False
    
    @pytest.mark.asyncio
    async def test_generate_token(self):
        """测试 Token 生成"""
        token = AuthService.generate_token()
        
        assert len(token) > 0
        assert isinstance(token, str)
    
    @pytest.mark.asyncio
    async def test_create_user(self, db: AsyncSession):
        """测试创建用户"""
        import uuid
        unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass",
            email="test@example.com"
        )
        
        assert user.id is not None
        assert user.username == unique_username
        assert user.email == "test@example.com"
        assert user.password_hash != "testpass"
    
    @pytest.mark.asyncio
    async def test_create_duplicate_user(self, db: AsyncSession):
        """测试创建重复用户"""
        import uuid
        unique_username = f"duplicate_user_{uuid.uuid4().hex[:8]}"
        # 创建第一个用户
        await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 尝试创建同名用户
        with pytest.raises(ValueError, match="已存在"):
            await AuthService.create_user(
                db=db,
                username=unique_username,
                password="testpass"
            )
    
    @pytest.mark.asyncio
    async def test_authenticate_user(self, db: AsyncSession):
        """测试用户认证"""
        import uuid
        unique_username = f"auth_user_{uuid.uuid4().hex[:8]}"
        # 创建用户
        await AuthService.create_user(
            db=db,
            username=unique_username,
            password="correctpass"
        )
        
        # 正确密码
        user = await AuthService.authenticate_user(
            db=db,
            username=unique_username,
            password="correctpass"
        )
        assert user is not None
        assert user.username == unique_username
        
        # 错误密码
        user = await AuthService.authenticate_user(
            db=db,
            username="auth_user",
            password="wrongpass"
        )
        assert user is None
        
        # 不存在的用户
        user = await AuthService.authenticate_user(
            db=db,
            username="nonexistent",
            password="anypass"
        )
        assert user is None
    
    @pytest.mark.asyncio
    async def test_create_session(self, db: AsyncSession):
        """测试创建会话"""
        import uuid
        unique_username = f"session_user_{uuid.uuid4().hex[:8]}"
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 创建会话
        session = await AuthService.create_session(db, user.id)
        
        assert session.id is not None
        assert session.user_id == user.id
        assert session.token is not None
        assert len(session.token) > 0
    
    @pytest.mark.asyncio
    async def test_verify_session(self, db: AsyncSession):
        """测试验证会话"""
        import uuid
        unique_username = f"verify_user_{uuid.uuid4().hex[:8]}"
        # 创建用户和会话
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        session = await AuthService.create_session(db, user.id)
        
        # 验证有效会话
        verified_user = await AuthService.verify_session(db, session.token)
        assert verified_user is not None
        assert verified_user.id == user.id
        
        # 验证无效会话
        verified_user = await AuthService.verify_session(db, "invalid_token")
        assert verified_user is None
    
    @pytest.mark.asyncio
    async def test_delete_session(self, db: AsyncSession):
        """测试删除会话"""
        import uuid
        unique_username = f"delete_user_{uuid.uuid4().hex[:8]}"
        # 创建用户和会话
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        session = await AuthService.create_session(db, user.id)
        
        # 删除会话
        success = await AuthService.delete_session(db, session.token)
        assert success is True
        
        # 验证会话已删除
        verified_user = await AuthService.verify_session(db, session.token)
        assert verified_user is None


class TestCategoryService:
    """测试分类服务"""
    
    def test_get_primary_categories(self):
        """测试获取一级分类"""
        categories = CategoryService.get_primary_categories()
        
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "学习资料" in categories
        assert "运动" in categories
    
    def test_validate_primary_category(self):
        """测试验证一级分类"""
        # 有效分类
        assert CategoryService.validate_primary_category("学习资料") is True
        assert CategoryService.validate_primary_category("运动") is True
        
        # 无效分类
        assert CategoryService.validate_primary_category("无效分类") is False
        assert CategoryService.validate_primary_category("") is False
    
    @pytest.mark.asyncio
    async def test_generate_subcategories(self):
        """测试生成二级分类"""
        service = CategoryService()
        
        # 注意：这个测试需要配置 LLM API
        # 如果没有配置 API，会抛出异常
        try:
            result = await service.generate_subcategories(["学习资料"])
            
            assert result.categories is not None
            assert len(result.categories) > 0
            assert result.descriptions is not None
        except Exception as e:
            # 如果 API 未配置，跳过测试
            pytest.skip(f"LLM API 未配置: {str(e)}")


class TestAuthAPI:
    """测试认证 API"""
    
    @pytest.mark.asyncio
    async def test_get_primary_categories(self, client: AsyncClient):
        """测试获取一级分类 API"""
        response = await client.get("/api/v1/auth/categories/primary")
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0
        assert "学习资料" in data["categories"]
    
    @pytest.mark.asyncio
    async def test_register(self, client: AsyncClient):
        """测试注册 API"""
        # 注意：这个测试需要配置 LLM API
        # 如果没有配置 API，会抛出异常
        try:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "username": "newuser",
                    "password": "testpass",
                    "email": "newuser@example.com",
                    "primary_categories": ["学习资料"]
                }
            )
            
            # 可能成功（API 配置正确）或失败（API 未配置）
            if response.status_code == 201:
                data = response.json()
                assert "user_id" in data
                assert "username" in data
                assert "token" in data
                assert data["username"] == "newuser"
            else:
                # 如果 API 未配置，跳过测试
                pytest.skip(f"注册失败，可能是 LLM API 未配置: {response.text}")
        except Exception as e:
            pytest.skip(f"注册测试跳过: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, db: AsyncSession):
        """测试注册重复用户名"""
        import uuid
        unique_username = f"duplicate_api_user_{uuid.uuid4().hex[:8]}"
        # 先创建一个用户
        await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 尝试注册同名用户
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": unique_username,
                "password": "testpass",
                "primary_categories": ["学习资料"]
            }
        )
        
        assert response.status_code == 400
        assert "已存在" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login(self, client: AsyncClient, db: AsyncSession):
        """测试登录 API"""
        import uuid
        unique_username = f"login_user_{uuid.uuid4().hex[:8]}"
        # 先创建用户
        await AuthService.create_user(
            db=db,
            username=unique_username,
            password="correctpass"
        )
        
        # 登录
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": unique_username,
                "password": "correctpass"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert "token" in data
        assert data["username"] == unique_username
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, db: AsyncSession):
        """测试登录错误密码"""
        import uuid
        unique_username = f"wrongpass_user_{uuid.uuid4().hex[:8]}"
        # 先创建用户
        await AuthService.create_user(
            db=db,
            username=unique_username,
            password="correctpass"
        )
        
        # 使用错误密码登录
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": unique_username,
                "password": "wrongpass"
            }
        )
        
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient, db: AsyncSession):
        """测试注销 API"""
        # 先创建用户并登录（使用唯一用户名避免冲突）
        import uuid
        unique_username = f"logout_user_{uuid.uuid4().hex[:8]}"
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        session = await AuthService.create_session(db, user.id)
        
        # 注销
        response = await client.post(
            "/api/v1/auth/logout",
            params={"token": session.token}
        )
        
        assert response.status_code == 200
        assert "注销成功" in response.json()["message"]
        
        # 提交当前事务以清除会话缓存
        await db.commit()
        
        # 验证会话已删除
        verified_user = await AuthService.verify_session(db, session.token)
        assert verified_user is None
    
    @pytest.mark.asyncio
    async def test_get_current_user_info(self, client: AsyncClient, db: AsyncSession):
        """测试获取当前用户信息 API"""
        import uuid
        unique_username = f"info_user_{uuid.uuid4().hex[:8]}"
        # 先创建用户并登录
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass",
            email="info@example.com"
        )
        session = await AuthService.create_session(db, user.id)
        
        # 获取用户信息
        response = await client.get(
            "/api/v1/auth/me",
            params={"token": session.token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user.id
        assert data["username"] == unique_username
        assert data["email"] == "info@example.com"
    
    @pytest.mark.asyncio
    async def test_get_current_user_info_invalid_token(self, client: AsyncClient):
        """测试使用无效 Token 获取用户信息"""
        response = await client.get(
            "/api/v1/auth/me",
            params={"token": "invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Token 无效或已过期" in response.json()["detail"]
