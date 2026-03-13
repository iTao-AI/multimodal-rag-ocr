"""
API 路由定义模块

定义所有 RAG 对话相关的 API 端点
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List

from .schema import ChatRequest, ChatResponse
from .service import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# 服务实例
chat_service = ChatService()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    RAG 对话接口
    
    Args:
        request: 对话请求
    
    Returns:
        ChatResponse: 对话响应
    
    Examples:
        >>> response = await chat(ChatRequest(query="你好", collection_name="documents", ...))
    """
    result = await chat_service.chat(request)
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return result


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    流式对话接口
    
    Args:
        request: 对话请求
    
    Returns:
        StreamingResponse: 流式响应
    """
    from fastapi.responses import StreamingResponse
    
    async def generate():
        async for chunk in chat_service.chat_stream(request):
            yield f"data: {chunk}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "chat"}
