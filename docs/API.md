# Multimodal RAG - API 文档

> 📡 完整的 API 接口文档
> 
> **版本**: v1.0.0
> **最后更新**: 2026-03-11

---

## 📖 目录

- [API 总览](#-api-总览)
- [PDF 提取服务](#-pdf-提取服务 -port-8006)
- [文本切分服务](#-文本切分服务 -port-8001)
- [向量数据库服务](#-向量数据库服务 -port-8000)
- [对话检索服务](#-对话检索服务 -port-8501)
- [错误码说明](#-错误码说明)
- [认证说明](#-认证说明)

---

## 📡 API 总览

### 服务端口

| 服务 | 端口 | 基础 URL | Swagger |
|-----|------|---------|---------|
| PDF 提取 | 8006 | http://localhost:8006 | http://localhost:8006/docs |
| 文本切分 | 8001 | http://localhost:8001 | http://localhost:8001/docs |
| 向量数据库 | 8000 | http://localhost:8000 | http://localhost:8000/docs |
| 对话检索 | 8501 | http://localhost:8501 | http://localhost:8501/docs |

### 通用响应格式

**成功响应**:
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功",
  "timestamp": "2026-03-11T12:00:00Z"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {...}
  },
  "timestamp": "2026-03-11T12:00:00Z"
}
```

---

## 📄 PDF 提取服务 (Port 8006)

### 基础信息

- **服务名称**: PDF Extraction Service
- **端口**: 8006
- **文件**: `Information-Extraction/unified/unified_pdf_extraction_service.py`
- **Swagger**: http://localhost:8006/docs

---

### API 接口

#### 1. 上传并解析 PDF

**端点**: `POST /extract`

**描述**: 上传 PDF 文件并进行多模态解析，提取文本和图片。

**请求**:
```
Content-Type: multipart/form-data

参数:
- file: PDF 文件 (required)
- extract_images: boolean (optional, default: true)
- output_format: string (optional, default: "markdown")
```

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "status": "completed",
    "markdown_path": "/path/to/output.md",
    "images_dir": "/path/to/images/",
    "page_count": 10,
    "file_size": 1024000,
    "processing_time": 2.5
  },
  "message": "PDF 解析成功"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PDF",
    "message": "无效的 PDF 文件"
  }
}
```

**示例** (curl):
```bash
curl -X POST http://localhost:8006/extract \
  -F "file=@document.pdf" \
  -F "extract_images=true"
```

---

#### 2. 批量解析 PDF

**端点**: `POST /extract/batch`

**描述**: 批量上传并解析多个 PDF 文件。

**请求**:
```
Content-Type: multipart/form-data

参数:
- files: PDF 文件数组 (required, max: 10)
- extract_images: boolean (optional)
```

**响应**:
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_789",
    "total": 5,
    "success": 4,
    "failed": 1,
    "results": [
      {
        "filename": "doc1.pdf",
        "status": "success",
        "markdown_path": "/path/to/doc1.md"
      },
      {
        "filename": "doc2.pdf",
        "status": "failed",
        "error": "文件损坏"
      }
    ]
  }
}
```

---

#### 3. 获取解析进度

**端点**: `GET /extract/{task_id}/status`

**描述**: 获取 PDF 解析任务的进度。

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "status": "processing",
    "progress": 65,
    "current_page": 6,
    "total_pages": 10,
    "estimated_time": 5
  }
}
```

**状态枚举**:
- `pending` - 等待处理
- `processing` - 处理中
- `completed` - 完成
- `failed` - 失败

---

#### 4. 健康检查

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy",
  "service": "pdf_extraction",
  "version": "1.0.0",
  "timestamp": "2026-03-11T12:00:00Z"
}
```

---

## ✂️ 文本切分服务 (Port 8001)

### 基础信息

- **服务名称**: Text Chunking Service
- **端口**: 8001
- **文件**: `Text_segmentation/markdown_chunker_api.py`
- **Swagger**: http://localhost:8001/docs

---

### API 接口

#### 1. 切分 Markdown 文本

**端点**: `POST /chunk`

**描述**: 对 Markdown 文本进行智能切分，保持语义完整性。

**请求**:
```json
{
  "markdown_text": "# 标题\n\n这是内容...",
  "chunk_size": 500,
  "chunk_overlap": 50,
  "min_chunk_size": 100,
  "preserve_headers": true
}
```

**参数说明**:
| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| markdown_text | string | - | 要切分的 Markdown 文本 |
| chunk_size | integer | 500 | 每个 chunk 的目标大小 |
| chunk_overlap | integer | 50 | chunk 之间的重叠字符数 |
| min_chunk_size | integer | 100 | 最小 chunk 大小 |
| preserve_headers | boolean | true | 是否保留标题层级 |

**响应**:
```json
{
  "success": true,
  "data": {
    "total_chunks": 10,
    "chunks": [
      {
        "chunk_id": 1,
        "content": "# 标题\n\n这是第一段内容...",
        "start_index": 0,
        "end_index": 500,
        "header_level": 1,
        "header_text": "标题"
      },
      {
        "chunk_id": 2,
        "content": "这是第二段内容...",
        "start_index": 450,
        "end_index": 950,
        "header_level": 2,
        "header_text": "子标题"
      }
    ],
    "statistics": {
      "input_length": 5000,
      "avg_chunk_size": 480,
      "processing_time": 0.15
    }
  }
}
```

**示例** (curl):
```bash
curl -X POST http://localhost:8001/chunk \
  -H "Content-Type: application/json" \
  -d '{
    "markdown_text": "# 标题\n\n内容...",
    "chunk_size": 500,
    "chunk_overlap": 50
  }'
```

---

#### 2. 从文件切分

**端点**: `POST /chunk/file`

**描述**: 从 Markdown 文件读取并切分。

**请求**:
```
Content-Type: multipart/form-data

参数:
- file: Markdown 文件 (required)
- chunk_size: integer (optional)
- chunk_overlap: integer (optional)
```

**响应**: 同 `/chunk` 接口

---

#### 3. 切分策略

**端点**: `GET /chunk/strategies`

**描述**: 获取可用的切分策略。

**响应**:
```json
{
  "success": true,
  "data": {
    "strategies": [
      {
        "name": "fixed_size",
        "description": "固定大小切分",
        "params": ["chunk_size", "chunk_overlap"]
      },
      {
        "name": "semantic",
        "description": "语义切分（按段落）",
        "params": ["min_chunk_size", "max_chunk_size"]
      },
      {
        "name": "hierarchical",
        "description": "层级切分（按标题）",
        "params": ["max_depth"]
      }
    ]
  }
}
```

---

#### 4. 健康检查

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy",
  "service": "text_chunking",
  "version": "1.0.0"
}
```

---

## 🗄️ 向量数据库服务 (Port 8000)

### 基础信息

- **服务名称**: Vector Database Service
- **端口**: 8000
- **文件**: `Database/milvus_server/milvus_api.py`
- **Swagger**: http://localhost:8000/docs

---

### API 接口

#### 1. 创建集合

**端点**: `POST /collection/create`

**描述**: 创建新的 Milvus 集合用于存储向量。

**请求**:
```json
{
  "collection_name": "my_knowledge_base",
  "dimension": 1024,
  "metric_type": "COSINE",
  "index_type": "HNSW",
  "description": "我的知识库"
}
```

**参数说明**:
| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| collection_name | string | - | 集合名称 |
| dimension | integer | 1024 | 向量维度 |
| metric_type | string | COSINE | 相似度度量 (COSINE/L2/IP) |
| index_type | string | HNSW | 索引类型 |
| description | string | - | 集合描述 |

**响应**:
```json
{
  "success": true,
  "data": {
    "collection_name": "my_knowledge_base",
    "collection_id": "col_123456",
    "created_at": "2026-03-11T12:00:00Z",
    "dimension": 1024,
    "metric_type": "COSINE"
  },
  "message": "集合创建成功"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "COLLECTION_EXISTS",
    "message": "集合已存在"
  }
}
```

---

#### 2. 删除集合

**端点**: `DELETE /collection/drop`

**请求**:
```json
{
  "collection_name": "my_knowledge_base"
}
```

**响应**:
```json
{
  "success": true,
  "message": "集合已删除"
}
```

---

#### 3. 集合列表

**端点**: `GET /collection/list`

**响应**:
```json
{
  "success": true,
  "data": {
    "collections": [
      {
        "name": "my_knowledge_base",
        "count": 1000,
        "dimension": 1024,
        "created_at": "2026-03-11T12:00:00Z"
      },
      {
        "name": "another_kb",
        "count": 500,
        "dimension": 1024,
        "created_at": "2026-03-10T10:00:00Z"
      }
    ],
    "total": 2
  }
}
```

---

#### 4. 插入向量

**端点**: `POST /collection/insert`

**描述**: 向集合中插入向量数据。

**请求**:
```json
{
  "collection_name": "my_knowledge_base",
  "vectors": [
    [0.1, 0.2, 0.3, ...],
    [0.4, 0.5, 0.6, ...]
  ],
  "metadata": [
    {
      "chunk_id": "chunk_001",
      "filename": "document.pdf",
      "page": 1,
      "text": "原始文本内容..."
    },
    {
      "chunk_id": "chunk_002",
      "filename": "document.pdf",
      "page": 2,
      "text": "更多文本..."
    }
  ],
  "ids": ["id_001", "id_002"]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "inserted_count": 2,
    "ids": ["id_001", "id_002"]
  },
  "message": "插入成功"
}
```

---

#### 5. 相似度检索

**端点**: `POST /collection/search`

**描述**: 在集合中进行相似度检索。

**请求**:
```json
{
  "collection_name": "my_knowledge_base",
  "query_vector": [0.1, 0.2, 0.3, ...],
  "top_k": 10,
  "score_threshold": 0.5,
  "filter": "filename == 'document.pdf'",
  "output_fields": ["chunk_id", "filename", "text"]
}
```

**参数说明**:
| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| collection_name | string | - | 集合名称 |
| query_vector | array | - | 查询向量 |
| top_k | integer | 10 | 返回结果数量 |
| score_threshold | float | 0.5 | 相似度阈值 |
| filter | string | - | 过滤表达式 |
| output_fields | array | - | 返回字段 |

**响应**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "id_001",
        "score": 0.92,
        "entity": {
          "chunk_id": "chunk_001",
          "filename": "document.pdf",
          "text": "相关文本内容..."
        }
      },
      {
        "id": "id_002",
        "score": 0.85,
        "entity": {
          "chunk_id": "chunk_002",
          "filename": "document.pdf",
          "text": "更多相关文本..."
        }
      }
    ],
    "total_hits": 2,
    "search_time": 0.05
  }
}
```

---

#### 6. 生成嵌入向量

**端点**: `POST /embedding/generate`

**描述**: 调用阿里云 API 生成文本的嵌入向量。

**请求**:
```json
{
  "text": "要嵌入的文本内容",
  "model": "text-embedding-v4"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "vector": [0.1, 0.2, 0.3, ...],
    "dimension": 1024,
    "model": "text-embedding-v4",
    "usage": {
      "tokens": 50
    }
  }
}
```

---

#### 7. 健康检查

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy",
  "service": "vector_database",
  "milvus_status": "connected",
  "collection_count": 5
}
```

---

## 💬 对话检索服务 (Port 8501)

### 基础信息

- **服务名称**: Chat Retrieval Service
- **端口**: 8501
- **文件**: `chat/kb_chat.py`
- **Swagger**: http://localhost:8501/docs

---

### API 接口

#### 1. RAG 对话

**端点**: `POST /chat`

**描述**: 基于知识库的 RAG 对话。

**请求**:
```json
{
  "query": "如何使用这个系统？",
  "collection_name": "my_knowledge_base",
  "llm_config": {
    "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key": "sk-xxx",
    "model_name": "qwen3-vl-plus",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "top_k": 10,
  "score_threshold": 0.5,
  "use_reranker": false,
  "reranker_config": null,
  "history": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的？"}
  ],
  "stream": true,
  "return_source": true
}
```

**参数说明**:
| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| query | string | - | 用户问题 |
| collection_name | string | - | 知识库名称 |
| llm_config | object | - | LLM 配置 |
| top_k | integer | 10 | 召回文档数量 |
| score_threshold | float | 0.5 | 相似度阈值 |
| use_reranker | boolean | false | 是否使用重排序 |
| history | array | [] | 历史对话 |
| stream | boolean | true | 是否流式输出 |
| return_source | boolean | true | 是否返回来源 |

**响应** (非流式):
```json
{
  "success": true,
  "data": {
    "answer": "使用这个系统需要以下步骤：\n1. 安装依赖...\n2. 配置环境...\n3. 启动服务...",
    "sources": [
      {
        "chunk_text": "安装依赖：pip install -r requirements.txt",
        "filename": "README.md",
        "score": 0.92,
        "metadata": {
          "chunk_id": "chunk_001",
          "page": 1
        }
      }
    ],
    "usage": {
      "prompt_tokens": 500,
      "completion_tokens": 200,
      "total_tokens": 700
    },
    "latency": {
      "retrieval": 0.05,
      "generation": 1.2,
      "total": 1.25
    }
  }
}
```

**响应** (流式):
```
data: {"chunk": "使"}
data: {"chunk": "用"}
data: {"chunk": "这"}
data: {"chunk": "个"}
...
data: {"done": true}
```

---

#### 2. 流式对话

**端点**: `POST /chat/stream`

**描述**: 流式 RAG 对话（SSE）。

**请求**: 同 `/chat`

**响应** (SSE):
```
Content-Type: text/event-stream

data: {"type": "start", "message": "开始生成"}
data: {"type": "chunk", "content": "使"}
data: {"type": "chunk", "content": "用"}
...
data: {"type": "sources", "sources": [...]}
data: {"type": "end", "usage": {...}}
```

---

#### 3. 对话历史

**端点**: `GET /chat/{session_id}/history`

**描述**: 获取对话历史。

**响应**:
```json
{
  "success": true,
  "data": {
    "session_id": "session_123",
    "messages": [
      {"role": "user", "content": "你好", "timestamp": "2026-03-11T12:00:00Z"},
      {"role": "assistant", "content": "你好！", "timestamp": "2026-03-11T12:00:01Z"}
    ],
    "total": 2
  }
}
```

---

#### 4. 清空对话

**端点**: `DELETE /chat/{session_id}`

**响应**:
```json
{
  "success": true,
  "message": "对话已清空"
}
```

---

#### 5. 健康检查

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy",
  "service": "chat_retrieval",
  "llm_status": "connected",
  "active_sessions": 5
}
```

---

## ❌ 错误码说明

### 通用错误码

| 错误码 | HTTP 状态 | 说明 | 解决方案 |
|-------|---------|------|---------|
| `SUCCESS` | 200 | 操作成功 | - |
| `INVALID_REQUEST` | 400 | 请求参数无效 | 检查请求参数 |
| `UNAUTHORIZED` | 401 | 未授权 | 提供 API Key |
| `FORBIDDEN` | 403 | 禁止访问 | 检查权限 |
| `NOT_FOUND` | 404 | 资源不存在 | 检查资源 ID |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 | 联系管理员 |

### PDF 提取服务错误

| 错误码 | 说明 | 解决方案 |
|-------|------|---------|
| `INVALID_PDF` | 无效的 PDF 文件 | 检查文件完整性 |
| `FILE_TOO_LARGE` | 文件过大 | 压缩文件或分批处理 |
| `EXTRACTION_FAILED` | 解析失败 | 检查 PDF 格式 |
| `TASK_NOT_FOUND` | 任务不存在 | 检查 task_id |

### 向量数据库服务错误

| 错误码 | 说明 | 解决方案 |
|-------|------|---------|
| `COLLECTION_EXISTS` | 集合已存在 | 使用其他名称 |
| `COLLECTION_NOT_FOUND` | 集合不存在 | 检查集合名称 |
| `DIMENSION_MISMATCH` | 维度不匹配 | 使用正确的维度 |
| `SEARCH_FAILED` | 检索失败 | 检查 Milvus 状态 |

### 对话服务错误

| 错误码 | 说明 | 解决方案 |
|-------|------|---------|
| `LLM_API_ERROR` | LLM API 调用失败 | 检查 API Key 和网络 |
| `NO_RELEVANT_DOCS` | 未找到相关文档 | 调整阈值或补充知识库 |
| `STREAM_ERROR` | 流式输出错误 | 检查连接 |

---

## 🔐 认证说明

### API Key 认证

当前版本暂不需要认证，生产环境建议添加：

**请求头**:
```
Authorization: Bearer YOUR_API_KEY
```

### CORS 配置

后端服务已默认允许跨域：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📝 使用示例

### Python 示例

```python
import requests

# 1. 创建集合
response = requests.post('http://localhost:8000/collection/create', json={
    'collection_name': 'my_kb',
    'dimension': 1024
})

# 2. 上传 PDF
with open('document.pdf', 'rb') as f:
    response = requests.post('http://localhost:8006/extract', files={'file': f})

# 3. RAG 对话
response = requests.post('http://localhost:8501/chat', json={
    'query': '如何使用这个系统？',
    'collection_name': 'my_kb',
    'llm_config': {
        'api_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'api_key': 'sk-xxx',
        'model_name': 'qwen3-vl-plus'
    }
})
print(response.json()['data']['answer'])
```

### cURL 示例

```bash
# 健康检查
curl http://localhost:8000/health

# RAG 对话
curl -X POST http://localhost:8501/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "如何使用？",
    "collection_name": "my_kb",
    "llm_config": {
      "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "api_key": "sk-xxx",
      "model_name": "qwen3-vl-plus"
    }
  }'
```

---

**文档版本**: v1.0.0
**最后更新**: 2026-03-11
