"""
数据模型定义模块

定义所有用于 RAG 对话的数据模型
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """对话消息"""
    role: str = Field(..., description="角色：user/assistant/system")
    content: str = Field(..., description="消息内容")


class LLMConfig(BaseModel):
    """大模型配置"""
    api_url: str = Field(..., description="LLM API 地址")
    api_key: str = Field(..., description="LLM API 密钥")
    model_name: str = Field(..., description="模型名称")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="采样温度")
    max_tokens: int = Field(2000, ge=1, description="最大生成 token 数")


class RerankerConfig(BaseModel):
    """重排序配置"""
    api_url: str = Field(..., description="Reranker API 地址")
    api_key: str = Field(..., description="Reranker API 密钥")
    model_name: str = Field(..., description="Reranker 模型名称")
    top_n: int = Field(5, ge=1, description="重排序后保留的文档数量")


class SourceDocument(BaseModel):
    """来源文档"""
    chunk_text: str
    filename: str
    score: float  # 主分数
    retrieval_score: Optional[float] = None  # 原始召回分数
    rerank_score: Optional[float] = None  # 重排序分数
    metadata: Dict[str, Any] = {}


class ChatRequest(BaseModel):
    """对话请求"""
    query: str = Field(..., description="用户问题")
    collection_name: str = Field(..., description="Milvus 集合名称")
    llm_config: LLMConfig = Field(..., description="大模型配置")
    
    # 召回配置
    top_k: int = Field(10, ge=1, le=50, description="召回文档数量")
    score_threshold: float = Field(0.5, ge=0.0, le=1.0, description="相似度阈值")
    
    # 重排序配置
    use_reranker: bool = Field(False, description="是否使用重排序")
    reranker_config: Optional[RerankerConfig] = Field(None, description="重排序配置")
    
    # 对话配置
    history: List[Message] = Field(default=[], description="历史对话")
    stream: bool = Field(True, description="是否流式输出")
    prompt_template: Optional[str] = Field(None, description="自定义 prompt 模板")
    return_source: bool = Field(True, description="是否返回来源文档")
    
    # Milvus 服务地址
    milvus_api_url: str = Field("http://localhost:8000", description="Milvus API 地址")


class ChatResponse(BaseModel):
    """对话响应（非流式）"""
    success: bool
    message: str
    answer: str
    sources: Optional[List[SourceDocument]] = None
    metadata: Dict[str, Any] = {}


class StreamChunk(BaseModel):
    """流式输出块"""
    chunk: str
    is_last: bool = False
