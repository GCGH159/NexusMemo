"""
用户偏好服务测试
测试用户分类偏好的管理功能
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_preference import UserPreferenceService
from app.services.auth import AuthService
from app.models import UserCategoryPreference


class TestUserPreferenceService:
    """测试用户偏好服务"""
    
    @pytest.mark.asyncio
    async def test_add_preference(self, db: AsyncSession):
        """测试添加偏好"""
        import uuid
        unique_username = f"pref_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 添加偏好
        preference = await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料",
            selected=True
        )
        
        assert preference.id is not None
        assert preference.user_id == user.id
        assert preference.category_level == 1
        assert preference.category_name == "学习资料"
        assert preference.selected is True
    
    @pytest.mark.asyncio
    async def test_add_duplicate_preference(self, db: AsyncSession):
        """测试添加重复偏好"""
        import uuid
        unique_username = f"pref_dup_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 添加第一个偏好
        await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料"
        )
        
        # 尝试添加重复偏好
        with pytest.raises(ValueError, match="偏好已存在"):
            await UserPreferenceService.add_user_preference(
                db=db,
                user_id=user.id,
                category_level=1,
                category_name="学习资料"
            )
    
    @pytest.mark.asyncio
    async def test_get_user_preferences(self, db: AsyncSession):
        """测试获取用户偏好"""
        import uuid
        unique_username = f"pref_get_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 添加偏好
        await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料"
        )
        await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="运动"
        )
        
        # 获取偏好
        preferences = await UserPreferenceService.get_user_preferences(
            db=db,
            user_id=user.id
        )
        
        assert len(preferences) == 2
        assert any(pref.category_name == "学习资料" for pref in preferences)
        assert any(pref.category_name == "运动" for pref in preferences)
    
    @pytest.mark.asyncio
    async def test_update_preference(self, db: AsyncSession):
        """测试更新偏好"""
        import uuid
        unique_username = f"pref_update_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 添加偏好
        await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料",
            selected=True
        )
        
        # 更新偏好
        success = await UserPreferenceService.update_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料",
            selected=False
        )
        
        assert success is True
        
        # 验证更新
        preferences = await UserPreferenceService.get_user_preferences(
            db=db,
            user_id=user.id
        )
        assert preferences[0].selected is False
    
    @pytest.mark.asyncio
    async def test_delete_preference(self, db: AsyncSession):
        """测试删除偏好"""
        import uuid
        unique_username = f"pref_del_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 添加偏好
        await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料"
        )
        
        # 删除偏好
        success = await UserPreferenceService.delete_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料"
        )
        
        assert success is True
        
        # 验证删除
        preferences = await UserPreferenceService.get_user_preferences(
            db=db,
            user_id=user.id
        )
        assert len(preferences) == 0
    
    @pytest.mark.asyncio
    async def test_batch_add_preferences(self, db: AsyncSession):
        """测试批量添加偏好"""
        import uuid
        unique_username = f"pref_batch_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 批量添加偏好
        await UserPreferenceService.batch_add_preferences(
            db=db,
            user_id=user.id,
            primary_categories=["学习资料", "运动"],
            sub_categories=["课程笔记", "参考资料", "练习题库"]
        )
        
        # 验证添加
        preferences = await UserPreferenceService.get_user_preferences(
            db=db,
            user_id=user.id
        )
        assert len(preferences) == 5
        
        # 验证一级分类
        primary_prefs = await UserPreferenceService.get_user_preferences(
            db=db,
            user_id=user.id,
            category_level=1
        )
        assert len(primary_prefs) == 2
        
        # 验证二级分类
        sub_prefs = await UserPreferenceService.get_user_preferences(
            db=db,
            user_id=user.id,
            category_level=2
        )
        assert len(sub_prefs) == 3
    
    @pytest.mark.asyncio
    async def test_get_selected_categories(self, db: AsyncSession):
        """测试获取选中的分类"""
        import uuid
        unique_username = f"pref_selected_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 添加偏好（部分选中，部分未选中）
        await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料",
            selected=True
        )
        await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="运动",
            selected=False
        )
        
        # 获取选中的分类
        categories = await UserPreferenceService.get_selected_categories(
            db=db,
            user_id=user.id
        )
        
        assert len(categories) == 1
        assert categories[0] == "学习资料"


class TestPreferenceAPI:
    """测试偏好 API"""
    
    @pytest.mark.asyncio
    async def test_add_preference_api(self, client: AsyncClient, db: AsyncSession):
        """测试添加偏好 API"""
        import uuid
        unique_username = f"pref_api_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 添加偏好
        response = await client.post(
            f"/api/v1/preferences/?user_id={user.id}",
            json={
                "category_level": 1,
                "category_name": "学习资料",
                "selected": True
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "preference_id" in data
        assert data["message"] == "添加成功"
    
    @pytest.mark.asyncio
    async def test_get_preferences_api(self, client: AsyncClient, db: AsyncSession):
        """测试获取偏好列表 API"""
        import uuid
        unique_username = f"pref_api_get_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 添加偏好
        await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料"
        )
        
        # 获取偏好列表
        response = await client.get(f"/api/v1/preferences/?user_id={user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "preferences" in data
        assert data["total"] == 1
        assert data["preferences"][0]["category_name"] == "学习资料"
    
    @pytest.mark.asyncio
    async def test_update_preference_api(self, client: AsyncClient, db: AsyncSession):
        """测试更新偏好 API"""
        import uuid
        unique_username = f"pref_api_update_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 添加偏好
        await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料",
            selected=True
        )
        
        # 更新偏好
        response = await client.put(
            f"/api/v1/preferences/1/学习资料?user_id={user.id}",
            json={"selected": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "更新成功"
    
    @pytest.mark.asyncio
    async def test_delete_preference_api(self, client: AsyncClient, db: AsyncSession):
        """测试删除偏好 API"""
        import uuid
        unique_username = f"pref_api_del_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 添加偏好
        await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料"
        )
        
        # 删除偏好
        response = await client.delete(
            f"/api/v1/preferences/1/学习资料?user_id={user.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "删除成功"
    
    @pytest.mark.asyncio
    async def test_get_selected_categories_api(self, client: AsyncClient, db: AsyncSession):
        """测试获取选中分类 API"""
        import uuid
        unique_username = f"pref_api_selected_user_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = await AuthService.create_user(
            db=db,
            username=unique_username,
            password="testpass"
        )
        
        # 添加偏好
        await UserPreferenceService.add_user_preference(
            db=db,
            user_id=user.id,
            category_level=1,
            category_name="学习资料",
            selected=True
        )
        
        # 获取选中的分类
        response = await client.get(f"/api/v1/preferences/selected?user_id={user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert data["total"] == 1
        assert data["categories"][0] == "学习资料"
