"""
RAG 对话服务模块

实现核心业务逻辑：检索、重排序、LLM 生成
"""

import os
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI

from .schema import (
    Message,
    LLMConfig,
    RerankerConfig,
    SourceDocument,
    ChatRequest,
    ChatResponse,
)
from cache.redis_cache import cache


class ChatService:
    """RAG 对话服务"""
    
    def __init__(self):
        self.default_prompt_template = """你是一个专业的 AI 助手。请根据以下检索到的相关信息回答用户的问题。

相关信息：
{context}

用户问题：{query}

请基于以上信息给出准确、详细的回答。如果信息不足以回答问题，请如实说明。"""
    
    async def chat(
        self,
        request: ChatRequest
    ) -> ChatResponse:
        """
        处理对话请求
        
        Args:
            request: 对话请求
        
        Returns:
            ChatResponse: 对话响应
        """
        try:
            # 1. 从缓存查找
            cache_key = f"rag:chat:{request.collection_name}:{request.query}"
            cached_result = await cache.get("chat", request.collection_name, request.query)
            
            if cached_result:
                return ChatResponse(**cached_result)
            
            # 2. 检索相关文档
            sources = await self._retrieve_documents(request)
            
            # 3. 重排序（可选）
            if request.use_reranker and request.reranker_config:
                sources = await self._rerank_documents(
                    sources, 
                    request.query, 
                    request.reranker_config
                )
            
            # 4. 构建上下文
            context = self._build_context(sources)
            
            # 5. 调用 LLM 生成回答
            answer = await self._generate_answer(
                query=request.query,
                context=context,
                history=request.history,
                llm_config=request.llm_config,
                prompt_template=request.prompt_template
            )
            
            # 6. 构建响应
            response = ChatResponse(
                success=True,
                message="success",
                answer=answer,
                sources=sources if request.return_source else None,
                metadata={
                    "sources_count": len(sources),
                    "context_length": len(context),
                    "use_reranker": request.use_reranker
                }
            )
            
            # 7. 写入缓存
            await cache.set(
                "chat",
                response.dict(),
                request.collection_name,
                request.query,
                ttl=3600
            )
            
            return response
            
        except Exception as e:
            return ChatResponse(
                success=False,
                message=f"error: {str(e)}",
                answer="",
                metadata={"error": str(e)}
            )
    
    async def _retrieve_documents(self, request: ChatRequest) -> List[SourceDocument]:
        """检索相关文档"""
        # 调用 Milvus API 检索
        # TODO: 实现实际的检索逻辑
        return []
    
    async def _rerank_documents(
        self,
        sources: List[SourceDocument],
        query: str,
        config: RerankerConfig
    ) -> List[SourceDocument]:
        """重排序文档"""
        # TODO: 实现重排序逻辑
        return sources
    
    def _build_context(self, sources: List[SourceDocument]) -> str:
        """构建上下文"""
        if not sources:
            return ""
        
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(f"[{i}] {source.chunk_text}")
        
        return "\n\n".join(context_parts)
    
    async def _generate_answer(
        self,
        query: str,
        context: str,
        history: List[Message],
        llm_config: LLMConfig,
        prompt_template: Optional[str] = None
    ) -> str:
        """生成回答"""
        # 使用默认模板或自定义模板
        template = prompt_template or self.default_prompt_template
        prompt = template.format(context=context, query=query)
        
        # 调用 LLM API
        client = AsyncOpenAI(
            api_key=llm_config.api_key,
            base_url=llm_config.api_url
        )
        
        # 构建消息列表
        messages = []
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": prompt})
        
        # 调用 API
        response = await client.chat.completions.create(
            model=llm_config.model_name,
            messages=messages,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens
        )
        
        return response.choices[0].message.content
    
    async def chat_stream(
        self,
        request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        # TODO: 实现流式输出
        yield ""
