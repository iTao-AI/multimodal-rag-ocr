"""
各服务全局异常处理集成示例
复制此代码到各服务的 main.py 文件中
"""

# ============================================
# PDF 提取服务 (8006) - 异常处理集成
# ============================================
"""
在 unified_pdf_extraction_service.py 中添加:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.exceptions import (
    setup_global_exception_handlers,
    RequestIDMiddleware,
    PerformanceLoggingMiddleware,
    ExternalServiceException,
    ValidationException
)

app = FastAPI(title="PDF 提取服务")

# 添加 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加中间件
app.add_middleware(RequestIDMiddleware)
app.add_middleware(PerformanceLoggingMiddleware)

# 设置全局异常处理器
setup_global_exception_handlers(app, service_name="pdf-extraction")

# 使用示例
@app.post("/extract/fast")
async def extract_pdf_fast(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.pdf'):
            raise ValidationException(
                message="仅支持 PDF 文件",
                details={"filename": file.filename}
            )
        
        result = await process_pdf(file)
        return {"success": True, "data": result}
        
    except ExternalServiceException as e:
        # 外部服务错误会自动被全局处理器捕获
        raise
    except Exception as e:
        # 其他异常也会被全局处理器捕获
        logger.error(f"PDF 提取失败：{e}")
        raise
```
"""

# ============================================
# 文本切分服务 (8001) - 异常处理集成
# ============================================
"""
在 markdown_chunker_api.py 中添加:

```python
from fastapi import FastAPI
from utils.exceptions import (
    setup_global_exception_handlers,
    RequestIDMiddleware,
    PerformanceLoggingMiddleware,
    ValidationException
)

app = FastAPI(title="Markdown 文本切分 API")

# 添加中间件
app.add_middleware(RequestIDMiddleware)
app.add_middleware(PerformanceLoggingMiddleware)

# 设置全局异常处理器
setup_global_exception_handlers(app, service_name="text-chunker")

# 使用示例
@app.post("/chunk")
async def chunk_text(request: ChunkRequest):
    if not request.markdown or len(request.markdown) == 0:
        raise ValidationException(
            message="Markdown 内容不能为空",
            details={"field": "markdown"}
        )
    
    if len(request.markdown) > 1000000:  # 1MB
        raise ValidationException(
            message="Markdown 内容过大",
            details={"max_size": "1MB", "actual_size": len(request.markdown)}
        )
    
    chunks = chunk_markdown(request.markdown)
    return {"chunks": chunks, "count": len(chunks)}
```
"""

# ============================================
# Milvus API 服务 (8000) - 异常处理集成
# ============================================
"""
在 milvus_api.py 中添加:

```python
from fastapi import FastAPI
from utils.exceptions import (
    setup_global_exception_handlers,
    RequestIDMiddleware,
    PerformanceLoggingMiddleware,
    NotFoundException,
    ExternalServiceException,
    ServiceUnavailableException
)

app = FastAPI(title="Milvus RAG Service")

# 添加中间件
app.add_middleware(RequestIDMiddleware)
app.add_middleware(PerformanceLoggingMiddleware)

# 设置全局异常处理器
setup_global_exception_handlers(app, service_name="milvus-rag")

# 使用示例
@app.post("/search")
async def search_vectors(request: SearchRequest):
    try:
        # 检查集合是否存在
        if not utility.has_collection(request.collection_name):
            raise NotFoundException(
                resource="知识库",
                details={"collection_name": request.collection_name}
            )
        
        # 执行搜索
        results = await milvus_search(
            collection_name=request.collection_name,
            query_text=request.query_text,
            top_k=request.top_k
        )
        
        return {"success": True, "results": results}
        
    except MilvusException as e:
        raise ExternalServiceException(
            service="Milvus",
            message=str(e),
            details={"error_code": e.code}
        )
    except ConnectionError as e:
        raise ServiceUnavailableException(
            message="Milvus 服务连接失败",
            details={"retry_after": 30}
        )
```
"""

# ============================================
# 对话检索服务 (8501) - 异常处理集成
# ============================================
"""
在 kb_chat.py 中添加:

```python
from fastapi import FastAPI
from utils.exceptions import (
    setup_global_exception_handlers,
    RequestIDMiddleware,
    PerformanceLoggingMiddleware,
    NotFoundException,
    ExternalServiceException,
    ValidationException
)

app = FastAPI(title="RAG 对话服务 API")

# 添加中间件
app.add_middleware(RequestIDMiddleware)
app.add_middleware(PerformanceLoggingMiddleware)

# 设置全局异常处理器
setup_global_exception_handlers(app, service_name="rag-chat")

# 使用示例
@app.post("/chat")
async def chat(request: ChatRequest):
    # 验证请求
    if not request.query or len(request.query.strip()) == 0:
        raise ValidationException(
            message="问题不能为空",
            details={"field": "query"}
        )
    
    try:
        # 检索文档
        documents = await retrieve_documents(
            query=request.query,
            collection_name=request.collection_name,
            top_k=request.top_k
        )
        
        if not documents or len(documents) == 0:
            raise NotFoundException(
                resource="相关文档",
                details={"query": request.query}
            )
        
        # 生成回答
        answer = await generate_answer(
            query=request.query,
            context=documents
        )
        
        return {
            "success": True,
            "answer": answer,
            "sources": documents
        }
        
    except OpenAIError as e:
        raise ExternalServiceException(
            service="LLM",
            message=f"AI 生成失败：{str(e)}",
            details={"model": request.llm_config.model_name}
        )
```
"""

# ============================================
# 统一错误响应示例
# ============================================
"""
所有服务返回的错误格式统一为:

404 错误示例:
{
  "error": {
    "code": "NOT_FOUND",
    "message": "知识库不存在",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status_code": 404,
    "details": {
      "collection_name": "test_kb"
    },
    "timestamp": "2026-03-12T15:30:00.000000",
    "path": "/api/search"
  }
}

500 错误示例:
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "服务器内部错误，请稍后重试",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status_code": 500,
    "details": {
      "type": "ValueError",
      "logged_at": "2026-03-12T15:30:00.000000"
    },
    "timestamp": "2026-03-12T15:30:00.000000",
    "path": "/api/chat"
  }
}

422 验证错误示例:
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status_code": 422,
    "details": {
      "errors": [
        {
          "field": "query",
          "message": "field required",
          "type": "missing"
        }
      ]
    },
    "timestamp": "2026-03-12T15:30:00.000000",
    "path": "/api/chat"
  }
}
"""

# ============================================
# 快速集成模板
# ============================================
"""
在每个服务的 FastAPI 应用创建处添加:

```python
from utils.exceptions import create_app_with_exception_handling

# 方式 1: 使用快捷函数
app = create_app_with_exception_handling(service_name="your-service-name")

# 方式 2: 手动配置
from fastapi import FastAPI
from utils.exceptions import (
    setup_global_exception_handlers,
    RequestIDMiddleware,
    PerformanceLoggingMiddleware
)

app = FastAPI(title="Your Service")

# 添加中间件
app.add_middleware(RequestIDMiddleware)
app.add_middleware(PerformanceLoggingMiddleware)

# 设置异常处理器
setup_global_exception_handlers(app, service_name="your-service-name")
```

然后在每个 API 端点中使用自定义异常:

```python
from utils.exceptions import ValidationException, NotFoundException

@app.post("/endpoint")
async def my_endpoint(data: MyData):
    # 验证
    if not data.is_valid():
        raise ValidationException(
            message="数据无效",
            details=data.get_errors()
        )
    
    # 业务逻辑
    result = await do_something(data)
    
    if not result:
        raise NotFoundException(resource="结果")
    
    return {"success": True, "data": result}
```
"""
