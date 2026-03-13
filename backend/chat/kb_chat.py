"""
RAG 对话模块 - 主入口

精简版主文件，仅包含应用启动和路由注册
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import router

# 服务配置
SERVICE_PORT = int(os.getenv("CHAT_SERVICE_PORT", "8501"))
SERVICE_HOST = os.getenv("CHAT_SERVICE_HOST", "0.0.0.0")

# 创建 FastAPI 应用
app = FastAPI(
    title="RAG Chat Service",
    description="RAG 对话服务 - 支持向量召回、重排序、流式问答",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "RAG Chat Service",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    print(f"✅ RAG Chat Service started on {SERVICE_HOST}:{SERVICE_PORT}")


if __name__ == "__main__":
    uvicorn.run(
        "kb_chat:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        reload=False
    )
