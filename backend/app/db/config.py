"""
Database configuration module.
Handles connections to MySQL, Neo4j, and Redis.
"""
from typing import AsyncGenerator, List, Union
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from neo4j import AsyncGraphDatabase
from redis import asyncio as aioredis
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore=["CORS_ORIGINS"]  # 忽略环境变量中的 CORS_ORIGINS
    )
    
    # MySQL
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "nexus_memo"
    
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # LLM
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0
    
    # Application
    APP_NAME: str = "NexusMemo"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["*"],  # 允许所有来源
        json_schema_extra={"env": None}  # 禁止从环境变量读取
    )
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Audio
    WHISPER_MODEL_SIZE: str = "base"
    AUDIO_UPLOAD_DIR: str = "./uploads/audio"
    
    @property
    def mysql_url(self) -> str:
        """Get MySQL connection URL."""
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()


# MySQL Database Setup
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


async_engine = create_async_engine(
    settings.mysql_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Neo4j Database Setup
class Neo4jConnection:
    """Neo4j connection manager."""
    
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.auth = (settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        self.driver = None
    
    async def connect(self):
        """Establish connection to Neo4j."""
        if self.driver is None:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=self.auth)
        return self.driver
    
    async def close(self):
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            self.driver = None
    
    async def get_session(self):
        """Get a Neo4j session."""
        driver = await self.connect()
        return driver.session()


neo4j_conn = Neo4jConnection()


async def get_neo4j_session():
    """Dependency for getting Neo4j sessions."""
    session = await neo4j_conn.get_session()
    try:
        yield session
    finally:
        await session.close()


# Redis Setup
class RedisConnection:
    """Redis connection manager."""
    
    def __init__(self):
        self.url = settings.redis_url
        self.client = None
    
    async def connect(self):
        """Establish connection to Redis."""
        if self.client is None:
            self.client = await aioredis.from_url(self.url, decode_responses=True)
        return self.client
    
    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            self.client = None
    
    async def get_client(self):
        """Get Redis client."""
        if self.client is None:
            await self.connect()
        return self.client


redis_conn = RedisConnection()


async def get_redis():
    """Dependency for getting Redis client."""
    client = await redis_conn.get_client()
    return client
