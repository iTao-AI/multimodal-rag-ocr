# Multimodal RAG API 文档

**版本**: v1.0  
**日期**: 2026-03-11  
**基础 URL**: `http://localhost:8000/api/v1`

---

## 📋 目录

1. [认证](#认证)
2. [知识库管理](#知识库管理)
3. [文档管理](#文档管理)
4. [向量检索](#向量检索)
5. [对话接口](#对话接口)
6. [错误码](#错误码)

---

## 认证

### API Key 认证

所有请求需要在 Header 中包含 API Key：

```http
Authorization: Bearer YOUR_API_KEY
```

---

## 知识库管理

### 创建知识库

**POST** `/knowledge-bases`

**请求**:
```json
{
  "name": "产品文档库",
  "description": "产品相关文档和 FAQ",
  "embedding_model": "text-embedding-v4"
}
```

**响应**:
```json
{
  "id": "kb_123456",
  "name": "产品文档库",
  "status": "active",
  "created_at": "2026-03-11T10:00:00Z"
}
```

### 获取知识库列表

**GET** `/knowledge-bases`

**响应**:
```json
{
  "total": 3,
  "items": [
    {
      "id": "kb_123456",
      "name": "产品文档库",
      "document_count": 150
    }
  ]
}
```

### 删除知识库

**DELETE** `/knowledge-bases/{kb_id}`

---

## 文档管理

### 上传文档

**POST** `/documents`

**Content-Type**: `multipart/form-data`

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | PDF/Markdown 文件 |
| kb_id | String | 是 | 知识库 ID |
| chunk_size | Integer | 否 | 切分大小 (默认 500) |

**响应**:
```json
{
  "id": "doc_789012",
  "filename": "product_manual.pdf",
  "chunks_created": 25,
  "status": "processed"
}
```

### 获取文档列表

**GET** `/knowledge-bases/{kb_id}/documents`

**响应**:
```json
{
  "total": 150,
  "items": [
    {
      "id": "doc_789012",
      "filename": "product_manual.pdf",
      "uploaded_at": "2026-03-10T15:30:00Z"
    }
  ]
}
```

### 删除文档

**DELETE** `/documents/{doc_id}`

---

## 向量检索

### 相似度搜索

**POST** `/search`

**请求**:
```json
{
  "kb_id": "kb_123456",
  "query": "如何重置密码？",
  "top_k": 5,
  "score_threshold": 0.7
}
```

**响应**:
```json
{
  "query": "如何重置密码？",
  "results": [
    {
      "chunk_id": "chunk_001",
      "content": "重置密码步骤：1. 访问官网...",
      "score": 0.92,
      "metadata": {
        "source": "product_manual.pdf",
        "page": 15
      }
    }
  ],
  "took_ms": 45
}
```

### 混合检索（向量 + 关键词）

**POST** `/search/hybrid`

**请求**:
```json
{
  "kb_id": "kb_123456",
  "query": "密码重置",
  "vector_weight": 0.7,
  "keyword_weight": 0.3,
  "top_k": 10
}
```

---

## 对话接口

### 智能问答

**POST** `/chat`

**请求**:
```json
{
  "kb_id": "kb_123456",
  "query": "如何重置密码？",
  "history": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "您好！有什么可以帮助的？"}
  ],
  "stream": false
}
```

**响应**:
```json
{
  "answer": "重置密码的步骤如下：\n1. 访问官网登录页面\n2. 点击'忘记密码'\n3. 输入注册邮箱\n4. 查收验证邮件\n5. 设置新密码",
  "sources": [
    {
      "chunk_id": "chunk_001",
      "content": "重置密码步骤：1. 访问官网...",
      "score": 0.92
    }
  ],
  "model": "qwen3-vl-plus",
  "took_ms": 1250
}
```

### 流式对话

**POST** `/chat/stream`

**响应** (SSE):
```
data: {"chunk": "重"}
data: {"chunk": "置"}
data: {"chunk": "密"}
data: {"chunk": "码"}
data: {"chunk": "的"}
data: {"done": true}
```

---

## 错误码

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 业务错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| KB_NOT_FOUND | 知识库不存在 | 检查 kb_id 是否正确 |
| DOC_UPLOAD_FAILED | 文档上传失败 | 检查文件格式和大小 |
| EMBEDDING_FAILED | 向量化失败 | 检查 Embedding 服务 |
| MILVUS_CONNECTION_ERROR | Milvus 连接失败 | 检查 Milvus 服务状态 |
| RATE_LIMIT_EXCEEDED | 请求频率超限 | 降低请求频率 |

### 错误响应格式

```json
{
  "error": {
    "code": "KB_NOT_FOUND",
    "message": "知识库 kb_123456 不存在",
    "details": {
      "kb_id": "kb_123456"
    }
  }
}
```

---

## 限流说明

| 接口 | 限流策略 |
|------|----------|
| `/chat` | 10 次/分钟 |
| `/search` | 30 次/分钟 |
| `/documents` (上传) | 5 次/分钟 |
| 其他接口 | 60 次/分钟 |

**限流响应**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超限，请稍后重试",
    "retry_after": 60
  }
}
```

---

## SDK 示例

### Python

```python
from rag_client import RAGClient

client = RAGClient(
    base_url="http://localhost:8000",
    api_key="your_api_key"
)

# 上传文档
doc = client.upload_document(
    kb_id="kb_123456",
    file_path="manual.pdf"
)

# 智能问答
response = client.chat(
    kb_id="kb_123456",
    query="如何重置密码？"
)
print(response.answer)
```

### JavaScript

```javascript
const client = new RAGClient({
  baseURL: 'http://localhost:8000',
  apiKey: 'your_api_key'
});

// 智能问答
const response = await client.chat({
  kb_id: 'kb_123456',
  query: '如何重置密码？'
});
console.log(response.answer);
```

---

## 性能指标

| 接口 | P50 | P95 | P99 |
|------|-----|-----|-----|
| `/chat` | 800ms | 1.5s | 2.5s |
| `/search` | 50ms | 100ms | 200ms |
| `/documents` (上传) | 2s | 5s | 10s |

---

**文档结束**

最后更新：2026-03-11  
API 版本：v1.0
