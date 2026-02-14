"""
清理测试数据库中的测试数据
"""
import asyncio
from sqlalchemy import select, delete
from app.db.config import AsyncSessionLocal
from app.models import User, Session, Memo, UserCategoryPreference


async def cleanup_test_data():
    """清理测试数据"""
    async with AsyncSessionLocal() as session:
        # 按照外键约束顺序删除数据
        # 1. 先删除 memos 表中的数据
        await session.execute(
            delete(Memo)
        )
        
        # 2. 删除 sessions 表中的数据
        await session.execute(
            delete(Session)
        )
        
        # 3. 删除 user_category_preferences 表中的数据
        await session.execute(
            delete(UserCategoryPreference)
        )
        
        # 4. 删除测试用户（用户名包含 test 的用户）
        await session.execute(
            delete(User).where(User.username.like('%test%'))
        )
        
        # 5. 删除测试用户（用户名包含 user 的用户）
        await session.execute(
            delete(User).where(User.username.like('%user%'))
        )
        
        await session.commit()
        print("✅ 测试数据清理完成")


if __name__ == "__main__":
    asyncio.run(cleanup_test_data())
