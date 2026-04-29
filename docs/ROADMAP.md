# 改进路线图

> 基于项目评估得出的技术债清单。按优先级分阶段排列，每个阶段可独立完成。

---

## 阶段总览

| 阶段 | 主题 | 预计工作量 | 优先级 | 状态 |
|------|------|-----------|--------|------|
| P0 | 关键 Bug 修复 | 2 小时 | 紧急 | 进行中 |
| P1 | 安全加固 | 2-3 天 | 高 | 未开始 |
| P2 | 代码质量提升 | 3-5 天 | 高 | 未开始 |
| P3 | 运维体验 | 2-3 天 | 中 | 部分完成（docs/） |
| V2.1 | 检索增强 | 30 min | 高 | 基本完成，待 Redis 验证 |
| P4 | 功能增强 | 1-2 周 | 中 | 未开始 |
| P5 | 生产就绪 | 按需 | 低 | 未开始 |

---

## P0: 关键 Bug 修复（2 小时）

### P0-1: 修复随机向量 Fallback

**文件**: `backend/Database/milvus_server/milvus_api.py`

**问题**: Embedding API 失败时 `np.random.rand(1024)` 插入垃圾向量，用户完全不知道。

**修复**:
```python
# 替换:
except Exception:
    embedding = np.random.rand(1024).tolist()

# 为:
except Exception as e:
    logger.error(f"Embedding API 失败: {e}")
    # 返回失败状态，让调用方处理
    raise HTTPException(
        status_code=503,
        detail=f"向量生成服务不可用: {e}"
    )
```

同时修改 `upload_kb_data` 的处理逻辑，遇到 503 时中止本次上传，不插入脏数据。

### P0-2: 修复异步代码中的同步阻塞

**文件**: `backend/chat/kb_chat.py:134`

**问题**: `retrieve_documents()` 是 `async def` 但内部用了同步的 `requests.post()`，阻塞整个 event loop。

**修复**:
```python
# 替换:
import requests
response = requests.post(...)

# 为:
import httpx
async with httpx.AsyncClient() as client:
    response = await client.post(...)
```

### P0-3: 清理已提交的敏感信息

**文件**: `backend/.env`, `backend/chat/test_kb_chat_api.py`

**问题**: API Key 已提交到 Git 仓库，即使后续加入 `.gitignore` 也无法清除历史记录。

**修复步骤**:
1. 撤销 API Key（在 DashScope 控制台）
2. 生成新的 Key
3. 用 `git filter-branch` 或 BFG 清除历史中的 Key
4. 从测试文件中移除硬编码 Key

---

## P1: 安全加固（2-3 天）

### P1-1: API Key 鉴权中间件

**范围**: 所有 4 个 FastAPI 服务

**方案**: 添加 API Key 中间件，通过请求头 `X-API-Key` 验证。

```python
# backend/common/middleware/auth.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

VALID_API_KEYS = os.getenv("VALID_API_KEYS", "").split(",")

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key not in VALID_API_KEYS:
            raise HTTPException(status_code=401, detail="无效的 API Key")

        return await call_next(request)
```

前端需要在 API 请求中附带 API Key。

### P1-2: CORS 收紧

当前所有服务 `allow_origins=["*"]`。改为只允许前端域名：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 生产环境改为实际域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### P1-3: 前端不再发送 LLM API Key

当前 Chat 组件从浏览器发送 `api_key` 到后端。改为后端统一使用 `backend/.env` 中的 Key，前端不接触密钥。

```typescript
// 移除:
llm_config: { api_key: "...", ... }

// 改为:
// 后端使用 .env 中配置的默认 Key
// 前端可选择模型但不传 Key
```

### P1-4: Milvus 默认密码

修改 `docker-compose.yaml` 中的 MinIO 密码为环境变量注入：

```yaml
environment:
  MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY:-}
  MINIO_SECRET_KEY: ${MINIO_SECRET_KEY:-}
```

---

## P2: 代码质量提升（3-5 天）

### P2-1: 引入结构化日志

**范围**: 所有后端服务

**替换所有 `print()` 为 `logging`**:

```python
import logging

logger = logging.getLogger(__name__)

# 替换:
print("正在调用 Embedding API...")
print(f"错误: {e}")

# 为:
logger.info("正在调用 Embedding API...")
logger.error(f"Embedding API 调用失败", exc_info=True)
```

**日志格式** (JSON):
```python
import json_logging
json_logging.init_fastapi(enable_json=True)
```

**请求日志中间件**: 添加 Request ID、方法、路径、耗时、状态码。

### P2-2: 引入 pytest 测试框架

**目录结构**:
```
backend/
├── tests/
│   ├── conftest.py           # 测试配置 + fixtures
│   ├── test_chunker.py       # 切分算法测试
│   ├── test_milvus_api.py    # Milvus API 测试
│   ├── test_kb_chat.py       # 对话服务测试
│   └── test_pdf_extract.py   # PDF 提取测试
└── pytest.ini
```

**优先写的测试**:

1. `test_chunker.py` — 切分算法（纯函数，最容易测）
   ```python
   def test_respects_h1_boundary():
       """一级标题不应该被合并跨越"""
   def test_cross_page_bridge():
       """跨页边界应该生成 bridge chunk"""
   def test_table_not_split():
       """Markdown 表格不应该被切割"""
   def test_merge_small_chunks():
       """小块应该合并到目标大小"""
   ```

2. `test_milvus_api.py` — 向量操作
   ```python
   def test_upload_and_search():
       """上传后应该能检索到"""
   def test_search_by_filename():
       """按文件名过滤应该生效"""
   ```

3. Mock 外部 API 调用（Embedding、LLM），不依赖网络。

### P2-3: 消除流式/非流式代码重复

`kb_chat.py` 中 `chat_stream` 和 `chat_non_stream` 有大量重复。提取公共的 RAG Pipeline：

```python
class RAGPipeline:
    async def retrieve(self, query, collection, top_k, filter_expr):
        # 检索 + Rerank
        ...

    async def build_prompt(self, query, context, history):
        # 构建 Prompt
        ...

# 流式和非流式都复用:
async def chat_stream(...):
    docs = await pipeline.retrieve(...)
    prompt = await pipeline.build_prompt(...)
    yield from stream_llm(prompt)

async def chat_non_stream(...):
    docs = await pipeline.retrieve(...)
    prompt = await pipeline.build_prompt(...)
    return await generate_llm(prompt)
```

### P2-4: 类型注解补全

给关键函数添加类型注解（当前部分函数缺少返回类型和参数类型）。

---

## P3: 运维体验（2-3 天）

### P3-1: 统一 Docker Compose

创建 `docker-compose.full.yml`，一键启动全部服务：

```yaml
services:
  etcd:
    # ... (复用现有配置)
  minio:
    # ...
  standalone:  # Milvus
    # ...

  pdf-extraction:
    build: ./Information-Extraction/unified
    ports: ["8006:8006"]
    env_file: ../../.env
    depends_on: [standalone]

  text-chunking:
    build: ../../Text_segmentation
    ports: ["8001:8001"]
    env_file: ../../.env

  milvus-api:
    build: ./milvus_server
    ports: ["8000:8000"]
    env_file: ../../.env
    depends_on: [standalone]

  chat:
    build: ../chat
    ports: ["8501:8501"]
    env_file: ../.env
    depends_on: [milvus-api]

  frontend:
    build: ../../frontend
    ports: ["5173:5173"]
    depends_on: [pdf-extraction, text-chunking, milvus-api, chat]
```

### P3-2: 健康检查编排

当前 `start_all_services.sh` 只 sleep 2 秒就认为成功。改为 HTTP 健康检查：

```bash
wait_for_service() {
    local port=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "http://localhost:${port}/health" > /dev/null; then
            echo "  ✓ $name 就绪"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    echo "  ✗ $name 启动超时"
    return 1
}
```

### P3-3: 项目 README

当前根目录只有 `OPERATIONS.md` 和 `CLAUDE.md`。需要创建一个 `README.md`：

```markdown
# Multimodal RAG OCR

[架构图]
[快速开始]
[功能特性]
[技术栈]
[架构说明]
[常见问题]
```

---

## P4: 功能增强（1-2 周）

---

## V2.1 检索增强 — 状态

| # | 项目 | 状态 | 说明 |
|---|------|------|------|
| 1 | Query Rewrite 服务 | ✅ 已完成 | `backend/chat/query_rewrite.py`，复用 LLM API，失败降级 |
| 2 | BM25 混合检索 | ✅ 已完成 | `backend/Database/milvus_server/hybrid_search.py`，rank-bm25 + jieba |
| 3 | Redis 缓存 | ✅ 已完成 | `backend/common/cache_manager.py`，不可用时自动降级 |
| 4 | kb_chat.py 集成 | ✅ 已完成 | 流式/非流式都已接入缓存、改写、BM25 |
| 5 | .env 配置 | ✅ 已完成 | 11 项新变量，全部有默认值 |
| 6 | requirements.txt | ✅ 已完成 | +rank-bm25, jieba, redis |
| 7 | Redis 部署 | ⏳ 待验证 | Docker pull 中，代码已支持无 Redis 降级运行 |

### P4: 功能增强（1-2 周）

### P4-1: 多轮对话持久化

当前对话历史只在内存中。应该持久化到存储，支持：
- 历史对话列表
- 恢复之前的对话
- 对话搜索

### P4-2: 文档上传进度

大文件上传时前端没有进度反馈。添加：
- 上传进度条
- 处理状态轮询（解析 → 切分 → 入库）

### P4-3: 知识库权限管理

当前所有知识库完全开放。添加：
- 知识库级别的可见性（公开/私有）
- 简单的密码保护

### P4-4: 文档预览

上传 PDF 后无法在系统内预览原文。添加：
- PDF 查看器（如 react-pdf）
- 高亮显示检索到的原文段落位置

### P4-5: 支持更多文件格式

当前只支持 PDF。扩展：
- Word (.docx)
- Markdown (.md)
- 网页 URL 抓取

---

## P5: 生产就绪（按需）

### P5-1: 监控告警

- Prometheus + Grafana 监控服务指标
- 慢查询告警（检索 > 1s）
- LLM API 失败率告警
- Milvus 磁盘空间监控

### P5-2: CI/CD

- GitHub Actions 自动测试
- 合并后自动构建 Docker 镜像
- 自动部署

### P5-3: 限流与配额

- `slowapi` 添加 API 限流
- 按用户/知识库设置配额
- 防止 LLM API 费用失控

### P5-4: 备份与恢复

- Milvus 定期备份
- Embedding 失败重试队列
- 孤儿文件清理任务

---

## 快速参考：每个阶段的产出

| 阶段 | 完成后可以说的 |
|------|---------------|
| V2.1 | 恢复了 Hybrid Search、Query Rewrite、Redis 缓存三大检索增强组件 |
| P0 | 修复了 3 个会导致数据损坏或性能下降的关键 Bug |
| P1 | 添加了完整的鉴权和安全加固 |
| P2 | 引入了测试框架和结构化日志，代码可维护性大幅提升 |
| P3 | 实现了 Docker 一键部署，运维体验标准化 |
| P4 | 扩展了多轮对话、文档预览等用户功能 |
| P5 | 达到生产级标准（监控、CI/CD、限流、备份） |
