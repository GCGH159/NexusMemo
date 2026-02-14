"""
用户认证服务
处理密码哈希、Token 生成、会话管理
"""
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Session
from app.db.config import settings


class AuthService:
    """用户认证服务"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        # bcrypt 限制密码不能超过 72 字节，截取到 70 字节以确保安全
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 70:
            password_bytes = password_bytes[:70]
        # 生成盐值并哈希
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            # bcrypt 限制密码不能超过 72 字节，截取到 70 字节以确保安全
            password_bytes = plain_password.encode('utf-8')
            if len(password_bytes) > 70:
                password_bytes = password_bytes[:70]
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
    
    @staticmethod
    def generate_token() -> str:
        """生成随机 Token"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        username: str,
        password: str,
        email: Optional[str] = None,
        preferences: Optional[dict] = None
    ) -> User:
        """
        创建新用户
        
        参数：
            db: 数据库会话
            username: 用户名
            password: 密码（明文）
            email: 邮箱（可选）
            preferences: 用户偏好（可选）
        
        返回：
            创建的用户对象
        """
        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            raise ValueError(f"用户名 '{username}' 已存在")
        
        # 哈希密码
        password_hash = AuthService.hash_password(password)
        
        # 创建用户
        user = User(
            username=username,
            password_hash=password_hash,
            email=email,
            preferences=preferences or {}
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        验证用户凭据
        
        参数：
            db: 数据库会话
            username: 用户名
            password: 密码（明文）
        
        返回：
            验证成功返回用户对象，失败返回 None
        """
        # 查询用户
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # 验证密码
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: int,
        expire_minutes: Optional[int] = None
    ) -> Session:
        """
        创建用户会话
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            expire_minutes: 过期分钟数（默认使用配置）
        
        返回：
            创建的会话对象
        """
        if expire_minutes is None:
            expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
        # 生成 Token
        token = AuthService.generate_token()
        
        # 计算过期时间
        expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        # 创建会话
        session = Session(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return session
    
    @staticmethod
    async def verify_session(
        db: AsyncSession,
        token: str
    ) -> Optional[User]:
        """
        验证会话 Token
        
        参数：
            db: 数据库会话
            token: 会话 Token
        
        返回：
            验证成功返回用户对象，失败返回 None
        """
        # 查询会话（禁用缓存以确保获取最新数据）
        result = await db.execute(
            select(Session).where(Session.token == token).execution_options(no_cache=True)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        # 检查是否过期
        if session.expires_at < datetime.utcnow():
            return None
        
        # 获取用户（禁用缓存）
        result = await db.execute(
            select(User).where(User.id == session.user_id).execution_options(no_cache=True)
        )
        user = result.scalar_one_or_none()
        
        return user
    
    @staticmethod
    async def delete_session(
        db: AsyncSession,
        token: str
    ) -> bool:
        """
        删除会话（注销）
        
        参数：
            db: 数据库会话
            token: 会话 Token
        
        返回：
            删除成功返回 True，失败返回 False
        """
        result = await db.execute(
            select(Session).where(Session.token == token)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return False
        
        await db.delete(session)
        await db.commit()
        # 强制刷新会话缓存，确保删除操作立即生效
        db.expire_all()
        
        return True
    
    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """
        清理过期会话
        
        参数：
            db: 数据库会话
        
        返回：
            删除的会话数量
        """
        result = await db.execute(
            select(Session).where(Session.expires_at < datetime.utcnow())
        )
        expired_sessions = result.scalars().all()
        
        count = len(expired_sessions)
        for session in expired_sessions:
            await db.delete(session)
        
        await db.commit()
        
        return count
