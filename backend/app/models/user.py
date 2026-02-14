"""
SQLAlchemy models for MySQL database.
"""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Enum, TIMESTAMP, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from app.db.config import Base
import enum


class MemoType(str, enum.Enum):
    """Memo type enumeration."""
    QUICK_NOTE = "quick_note"
    EVENT = "event"


class MemoStatus(str, enum.Enum):
    """Memo status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    email = Column(String(128), nullable=True)
    preferences = Column(JSON, nullable=True)  # User preferences (categories selected during registration)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    memos = relationship("Memo", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    category_preferences = relationship("UserCategoryPreference", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """Session model for authentication."""
    __tablename__ = "sessions"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(512), nullable=False, unique=True, index=True)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class Memo(Base):
    """Memo model for quick notes and events."""
    __tablename__ = "memos"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(Enum(MemoType), nullable=False, index=True)
    title = Column(String(256), nullable=True)
    content = Column(Text, nullable=False)
    audio_url = Column(String(512), nullable=True)  # Associated audio file URL
    status = Column(Enum(MemoStatus), default=MemoStatus.ACTIVE, nullable=False, index=True)
    processed = Column(Boolean, default=False, nullable=False, index=True)  # 是否已被Agent处理
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="memos")


class UserCategoryPreference(Base):
    """User category preference model."""
    __tablename__ = "user_category_preferences"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    category_level = Column(Integer, nullable=False)  # 1=primary category, 2=secondary category
    category_name = Column(String(128), nullable=False)
    selected = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="category_preferences")
    
    # Unique constraint to prevent duplicate preferences
    __table_args__ = (
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )
