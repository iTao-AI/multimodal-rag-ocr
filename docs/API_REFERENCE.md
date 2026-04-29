# API 参考文档

> 本文档基于实际代码编写，非 spec 参考架构。所有端点、请求体、响应体均与实际实现一致。

---

## 一、服务总览

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| PDF 提取 | 8006 | HTTP/REST | PDF 解析为 Markdown |
| 文本切分 | 8001 | HTTP/REST | Markdown 切分为语义 Chunk |
| Milvus API | 8000 | HTTP/REST | 向量入库/检索/集合管理 |
| 对话服务 | 8501 | HTTP/REST | RAG 问答（流式/非流式） |

所有服务均无鉴权，CORS 配置为 `allow_origins=["*"]`。

---

## 二、PDF 提取服务 (:8006)

### 2.1 POST /extract

上传 PDF 文件，提取为 Markdown。

**请求**: `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | 是 | PDF 文件 |
| `collection_name` | string | 否 | 知识库名称（用于结果归类） |
| `mode` | string | 否 | `v1` 或 `v2`，默认 `v1` |

**响应 (200)**:
```json
{
  "file_id": "abc123-uuid-...",
  "filename": "document.pdf",
  "markdown": "# 文档标题\n\n正文内容...",
  "page_count": 10,
  "status": "success"
}
```

**响应 (400)**:
```json
{
  "detail": "只支持 PDF 文件"
}
```

**响应 (500)**:
```json
{
  "detail": "PDF 解析失败: ..."
}
```

**V1.0 处理流程**:
1. 保存上传文件到 `UPLOAD_BASE_DIR`
2. 调用 `pymupdf4llm` 提取 Markdown
3. 对含图片的页面调用 VLM 生成图片描述
4. 结果保存到 `EXTRACTION_RESULTS_DIR/{file_id}/output.md`

**V2.0 处理流程**:
1. 调用 MinerU API (`MINERU_API_URL`)
2. 或调用 PaddleOCR-VL (`PADDLEOCR_VL_API_URL`)
3. 或调用 DeepSeek-OCR (`DEEPSEEK_OCR_API_URL`)
4. 返回结构化 Markdown

### 2.2 POST /extract/text

上传纯文本文件（跳过 OCR，直接处理）。

**请求**: `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | 是 | 文本文件（.txt/.md） |

**响应**: 同 `/extract`

### 2.3 GET /health

```json
{ "status": "ok", "service": "pdf_extraction" }
```

---

## 三、文本切分服务 (:8001)

### 3.1 POST /chunk

接收 Markdown 文本，切分为语义 Chunk。

**请求** (`application/json`):
```json
{
  "markdown_text": "# 标题\n\n正文内容...",
  "file_id": "abc123-uuid-..."
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `markdown_text` | string | 是 | 要切分的 Markdown |
| `file_id` | string | 否 | 关联的文件 ID |

**响应 (200)**:
```json
{
  "chunks": [
    {
      "chunk_id": "chunk_001",
      "content": "# 标题\n\n第一段...",
      "metadata": {
        "header_level": 1,
        "word_count": 350
      }
    },
    {
      "chunk_id": "chunk_002",
      "content": "## 子标题\n\n第二段...",
      "metadata": {
        "header_level": 2,
        "word_count": 280
      }
    }
  ],
  "total_chunks": 2
}
```

**切分规则**:
1. 按 Markdown 标题层级递归切分（H1 → H2 → H3 → H4）
2. `smart_merge_chunks_v2()` 合并过小的相邻块
3. `add_cross_page_bridges_v2()` 添加跨页桥接文本
4. 保持表格完整性（不切割 Markdown 表格）

### 3.2 GET /health

```json
{ "status": "ok", "service": "text_chunking" }
```

---

## 四、Milvus API 服务 (:8000)

### 4.1 POST /api/upload

上传 Chunk 数据，自动生成 Embedding 并入库。

**请求** (`application/json`):
```json
{
  "collection_name": "kb_my_knowledge_base",
  "file_data": {
    "filename": "document.pdf",
    "file_id": "abc123",
    "chunks": [
      {
        "chunk_text": "机器学习是...",
        "metadata": { "page": 1, "header_level": 1 }
      }
    ]
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `collection_name` | string | 是 | 集合名（知识库标识） |
| `file_data.filename` | string | 是 | 文件名 |
| `file_data.file_id` | string | 是 | 文件唯一 ID |
| `file_data.chunks` | array | 是 | Chunk 列表 |
| `file_data.chunks[].chunk_text` | string | 是 | 文本内容 |
| `file_data.chunks[].metadata` | object | 否 | 附加元数据 |

**响应 (200)**:
```json
{
  "filename": "document.pdf",
  "file_id": "abc123",
  "status": "success",
  "message": "上传成功，共处理 15 个文本块",
  "chunks_count": 15
}
```

**处理流程**:
1. 检查/创建 Collection
2. 调用 Embedding API 批量生成向量（`ThreadPoolExecutor` 并发）
3. 插入 Milvus（字段：`chunk_text`, `file_name`, `embedding`, `metadata`）
4. 更新 `collection_name_mapping.json`

### 4.2 POST /api/search

向量语义检索。

**请求** (`application/json`):
```json
{
  "collection_name": "kb_my_knowledge_base",
  "query_text": "什么是机器学习？",
  "top_k": 5,
  "filter_expr": "file_name == 'AI入门.pdf'"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `collection_name` | string | 是 | 集合名 |
| `query_text` | string | 是 | 查询文本 |
| `top_k` | int | 否 | 返回数量，默认 10 |
| `filter_expr` | string | 否 | Milvus 过滤表达式 |

**响应 (200)**:
```json
{
  "query": "什么是机器学习？",
  "results": [
    {
      "chunk_text": "机器学习是人工智能的一个分支...",
      "file_name": "AI入门.pdf",
      "score": 0.92,
      "metadata": { "page": 3, "header_level": 2 }
    }
  ],
  "total_results": 5
}
```

### 4.3 POST /api/search_by_filename

按文件名限定检索。

**请求** (`application/json`):
```json
{
  "collection_name": "kb_my_knowledge_base",
  "filename": "AI入门.pdf",
  "query_text": "监督学习",
  "top_k": 5
}
```

### 4.4 POST /api/collections

创建集合。

**请求** (`application/json`):
```json
{ "collection_name": "kb_new_kb" }
```

### 4.5 GET /api/collections

列出所有集合。

**响应 (200)**:
```json
{
  "collections": [
    {
      "name": "kb_my_knowledge_base",
      "document_count": 5,
      "chunk_count": 150
    }
  ]
}
```

### 4.6 GET /api/collections/{name}

获取集合详情。

**响应 (200)**:
```json
{
  "name": "kb_my_knowledge_base",
  "description": "...",
  "num_entities": 150
}
```

### 4.7 GET /api/collections/{name}/stats

集合统计信息。

**响应 (200)**:
```json
{
  "collection_name": "kb_my_knowledge_base",
  "total_chunks": 150,
  "total_files": 5,
  "files": {
    "AI入门.pdf": 30,
    "深度学习.pdf": 45,
    ...
  }
}
```

### 4.8 GET /api/collections/{name}/documents

列出集合中的文件。

**响应 (200)**:
```json
{
  "documents": [
    {
      "filename": "AI入门.pdf",
      "file_id": "abc123",
      "chunk_count": 30
    }
  ]
}
```

### 4.9 DELETE /api/collections/{name}

删除整个集合（所有文件和向量）。

### 4.10 DELETE /api/documents

删除指定文件的所有 chunks。

**请求** (`application/json`):
```json
{
  "collection_name": "kb_my_knowledge_base",
  "file_name": "AI入门.pdf"
}
```

### 4.11 GET /health

```json
{ "status": "ok", "service": "milvus_api" }
```

---

## 五、对话服务 (:8501)

### 5.1 POST /chat

非流式 RAG 问答。

**请求** (`application/json`):
```json
{
  "query": "什么是机器学习？",
  "collection_name": "kb_my_knowledge_base",
  "llm_config": {
    "api_key": "sk-xxx",
    "model": "qwen3-vl-plus",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
  },
  "rerank_config": {
    "api_key": "sk-xxx",
    "model": "jina-reranker-v2-base-multilingual",
    "base_url": "https://api.jina.ai/v1"
  },
  "top_k": 5,
  "file_name": "",
  "filter_expr": "",
  "history": [
    { "role": "user", "content": "什么是AI？" },
    { "role": "assistant", "content": "人工智能是..." }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 用户问题 |
| `collection_name` | string | 是 | 知识库名 |
| `llm_config` | object | 否 | LLM 配置（不传则用后端默认） |
| `rerank_config` | object | 否 | Rerank 配置（不传则跳过） |
| `top_k` | int | 否 | 检索数量，默认 5 |
| `file_name` | string | 否 | 限定文件名 |
| `filter_expr` | string | 否 | Milvus 过滤表达式 |
| `history` | array | 否 | 对话历史 |

**响应 (200)**:
```json
{
  "answer": "机器学习是人工智能的一个分支，它使用算法和统计模型...",
  "sources": [
    {
      "chunk_text": "机器学习是...",
      "file_name": "AI入门.pdf",
      "score": 0.92
    }
  ],
  "total_tokens": 1234,
  "latency_ms": 567,
  "cache_hit": false
}
```

### 5.2 POST /chat/stream

流式 RAG 问答（NDJSON 协议）。

**请求**: 同 `POST /chat`

**响应** (`text/event-stream`，每行一个 JSON):
```
{"type": "content", "content": "机器"}
{"type": "content", "content": "学习是"}
{"type": "content", "content": "人工智能的"}
{"type": "content", "content": "一个分支..."}
{"type": "sources", "sources": [{"chunk_text": "...", "file_name": "...", "score": 0.92}]}
{"type": "metadata", {"rewrite_time": 0.5, "retrieve_time": 1.2, "rerank_time": 0.0, "hybrid_time": 0.1, "llm_time": 2.3, "total_time": 4.1, "documents_count": 5, "cache_hit": false}}
```

出错时:
```
{"type": "error", "message": "LLM API 调用失败: ..."}
```

### 5.3 GET /health

```json
{ "status": "ok", "service": "kb_chat" }
```

---

## 六、Reranker 支持

对话服务支持 4 种 Reranker provider，通过 `rerank_config` 的 `base_url` 自动识别：

| Provider | 匹配规则 | 说明 |
|----------|---------|------|
| Jina | URL 含 `jina.ai` | Jina Reranker API |
| Qwen/DashScope | URL 含 `dashscope` | 阿里云 rerank |
| BGE | URL 含 `bge` 或本地路径 | BGE 模型 |
| 通用 | 其他任意 OpenAI 兼容 API | 自定义 rerank 服务 |

Reranker 失败时自动降级到原始向量相似度排序，不中断问答。

---

## 七、错误码

| 状态码 | 含义 | 常见原因 |
|--------|------|---------|
| 200 | 成功 | — |
| 400 | 请求参数错误 | 缺少必填字段、文件类型不支持 |
| 404 | 资源不存在 | 集合/文件/文档不存在 |
| 500 | 服务器内部错误 | LLM API 故障、Milvus 连接失败 |
| 503 | 服务不可用 | Embedding API 超时 |

---

## 八、调用示例

### 8.1 完整上传流程（curl）

```bash
# Step 1: 创建集合
curl -X POST http://localhost:8000/api/collections \
  -H "Content-Type: application/json" \
  -d '{"collection_name": "kb_test"}'

# Step 2: 提取 PDF（返回 markdown）
curl -X POST http://localhost:8006/extract \
  -F "file=@document.pdf"

# Step 3: 切分（返回 chunks）
curl -X POST http://localhost:8001/chunk \
  -H "Content-Type: application/json" \
  -d '{"markdown_text": "# 标题\n\n正文...", "file_id": "abc123"}'

# Step 4: 入库（自动 embed）
curl -X POST http://localhost:8000/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "kb_test",
    "file_data": {
      "filename": "document.pdf",
      "file_id": "abc123",
      "chunks": [
        {"chunk_text": "第一段内容...", "metadata": {"page": 1}}
      ]
    }
  }'
```

### 8.2 对话（curl）

```bash
curl -X POST http://localhost:8501/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是机器学习？",
    "collection_name": "kb_test",
    "top_k": 5
  }'
```

### 8.3 Python 客户端示例

```python
import requests

class RAGClient:
    def __init__(self, base="http://localhost"):
        self.milvus = f"{base}:8000/api"
        self.chat = f"{base}:8501"
        self.extract = f"{base}:8006"
        self.chunk = f"{base}:8001"

    def upload_pdf(self, pdf_path: str, collection: str):
        with open(pdf_path, "rb") as f:
            r = requests.post(f"{self.extract}/extract", files={"file": f})
        result = r.json()

        r = requests.post(f"{self.chunk}/chunk", json={
            "markdown_text": result["markdown"],
            "file_id": result["file_id"]
        })
        chunks = r.json()["chunks"]

        r = requests.post(f"{self.milvus}/upload", json={
            "collection_name": collection,
            "file_data": {
                "filename": pdf_path,
                "file_id": result["file_id"],
                "chunks": chunks
            }
        })
        return r.json()

    def ask(self, query: str, collection: str, top_k=5):
        r = requests.post(f"{self.chat}/chat", json={
            "query": query,
            "collection_name": collection,
            "top_k": top_k
        })
        return r.json()
```
