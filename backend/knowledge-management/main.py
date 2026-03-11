from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api.routes import router
from database.sql_db import init_db
from loguru import logger
import uvicorn
import sys
from datetime import datetime

# 配置日志
logger.remove()
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="5 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)
logger.add(sys.stderr, level="DEBUG")

# 限流器配置
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="RAG 知识库管理系统",
    description="基于 FastAPI、SQL 和 Milvus 的知识库管理和向量检索服务",
    version="1.0.0"
)

# CORS 配置（生产环境白名单）
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# 添加限流处理
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 注册路由
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()
    logger.info("✅ 数据库初始化完成")

@app.get("/")
@limiter.limit("60/minute")
async def root(request: Request):
    logger.info("Root endpoint accessed")
    return {
        "message": "RAG 知识库管理系统",
        "status": "running",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
@limiter.limit("10/second")
async def health_check(request: Request):
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "knowledge-management",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True
    )
