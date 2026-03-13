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


@router.post("", response_model=ChatResponse, summary="RAG 对话", tags=["Chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """
    RAG 对话接口
    
    基于检索增强生成 (RAG) 的智能对话接口：
    
    1. **检索**: 从 Milvus 向量数据库检索相关文档
    2. **重排序**: 可选的重排序提升检索质量
    3. **生成**: 使用 LLM 生成回答
    4. **引用**: 返回答案来源文档
    
    ### 请求参数
    
    - **query**: 用户问题
    - **collection_name**: Milvus 集合名称
    - **top_k**: 召回文档数量 (默认 10)
    - **use_reranker**: 是否使用重排序 (默认 False)
    - **stream**: 是否流式输出 (默认 True)
    
    ### 响应
    
    - **answer**: AI 生成的回答
    - **sources**: 来源文档列表 (包含分数)
    - **metadata**: 元数据 (来源数量、上下文长度等)
    
    ### 示例
    
    ```python
    response = await chat(ChatRequest(
        query="如何重置密码？",
        collection_name="documents",
        top_k=5
    ))
    ```
    """
    result = await chat_service.chat(request)
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return result


@router.post("/stream", summary="流式对话", tags=["Chat"])
async def chat_stream(request: ChatRequest):
    """
    流式对话接口 (Server-Sent Events)
    
    实时流式输出对话内容，适用于需要即时反馈的场景。
    
    ### 响应格式
    
    ```
    data: {"chunk": "你", "is_last": false}
    data: {"chunk": "好", "is_last": false}
    data: {"chunk": "！", "is_last": true}
    ```
    
    ### 使用示例
    
    ```javascript
    const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: "你好", collection_name: "documents"})
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        console.log(chunk);
    }
    ```
    """
    from fastapi.responses import StreamingResponse
    
    async def generate():
        async for chunk in chat_service.chat_stream(request):
            yield f"data: {chunk}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/health", summary="健康检查", tags=["Health"])
async def health_check():
    """
    健康检查接口
    
    返回服务当前状态，用于监控和负载均衡。
    
    ### 响应
    
    - **status**: 服务状态 (healthy/unhealthy)
    - **service**: 服务名称
    - **timestamp**: 检查时间戳
    """
    from datetime import datetime
    
    return {
        "status": "healthy",
        "service": "chat",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
