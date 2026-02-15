"""
FastAPI主应用
启动后端服务的入口文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.config import settings, neo4j_conn, redis_conn
from app.api.v1 import memos, auth, preferences, search
from app.services.reminder import reminder_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("🚀 启动 NexusMemo 后端服务...")
    print(f"📝 数据库: {settings.MYSQL_DATABASE}")
    print(f"🔗 Neo4j: {settings.NEO4J_URI}")
    print(f"⚡ Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"🤖 LLM: {settings.LLM_MODEL}")
    
    yield
    
    # 关闭时
    print("🛑 关闭 NexusMemo 后端服务...")
    await neo4j_conn.close()
    await redis_conn.close()


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="NexusMemo - 智能速记系统",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(memos.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(preferences.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "database": "connected",
        "neo4j": "connected",
        "redis": "connected",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
