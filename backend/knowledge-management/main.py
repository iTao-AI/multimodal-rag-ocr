from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api.routes import router
from database.sql_db import init_db
from loguru import logger
import uvicorn
import sys
import uuid
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

# ============ 全局异常处理 ============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器 - 统一错误响应格式"""
    request_id = str(uuid.uuid4())
    
    # 记录详细错误日志
    logger.error(
        f"全局异常 [request_id={request_id}]: {exc}",
        exc_info=True
    )
    
    # 返回统一格式的错误响应
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "request_id": request_id,
                "details": None
            }
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理器"""
    request_id = str(uuid.uuid4())
    
    logger.warning(
        f"HTTP 异常 [request_id={request_id}]: {exc.detail}",
        status_code=exc.status_code
    )
    
    # 映射 HTTP 状态码到错误码
    error_code_map = {
        400: "INVALID_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
    }
    
    error_code = error_code_map.get(exc.status_code, "INTERNAL_ERROR")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code,
                "message": exc.detail,
                "request_id": request_id,
                "details": None
            }
        }
    )

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
