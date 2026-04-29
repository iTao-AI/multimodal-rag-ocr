# Multimodal RAG OCR — 项目全景文档

> 生成时间：2025-12-25
> 最近更新：2026-04-09 (V2.1: 检索增强)
> 目标：让任何人在读完后能完整理解整个项目的架构、数据流、API 契约和代码细节

---

## 一、项目定位

**Multimodal RAG OCR** 是一个基于 RAG（检索增强生成）架构的知识库系统。用户上传 PDF 文档后，系统自动完成 OCR 解析、文本切分、向量化存储，最终支持基于自然语言的智能问答。

### 三个版本


| 维度     | V1.0（基础版）         | V2.0（OCR 增强版）                        | V2.1（检索增强版）                     |
| ------ | ----------------- | ------------------------------------ | ------------------------------- |
| PDF 解析 | PyMuPDF4LLM + VLM | MinerU / PaddleOCR-VL / DeepSeek-OCR | 同 V2.0                          |
| 检索     | 纯向量相似度            | 同 V1.0                               | BM25 + 向量混合检索 + 查询改写 + Redis 缓存 |
| 适用场景   | 纯文本 PDF           | 扫描件、复杂排版                             | 同 V2.0，但问答质量更高                  |
| GPU 需求 | 不需要（纯 API 调用）     | 需要（GPU 服务器或 AutoDL）                  | 同 V2.0 + Docker Redis           |
| 前端入口   | 切换开关              | 切换开关                                 | 同 V2.0（后端透明升级）                  |


### 技术栈

- **后端**: Python 3.11 + FastAPI（4 个独立微服务）
- **向量数据库**: Milvus（Docker 部署，含 etcd + MinIO）
- **Embedding**: 阿里云 DashScope text-embedding-v4
- **LLM**: 阿里云 DashScope qwen3-vl-plus
- **检索增强** (V2.1): BM25 (rank-bm25), jieba 中文分词, Redis 缓存
- **前端**: React 18 + TypeScript + Vite + TailwindCSS + shadcn/ui
- **OCR V2**: MinerU（vLLM 后端）、PaddleOCR-VL、DeepSeek-OCR

---

## 二、整体架构

### 2.1 服务拓扑

```
                    ┌──────────────┐
                    │   前端 UI     │
                    │  Vite :5173   │
                    └──────┬───────┘
                           │ HTTP
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │ 知识库管理  │ │  对话问答   │ │  检索测试   │
     │ (Milvus API│ │  (kb_chat) │ │  (Milvus)  │
     │  :8000)    │ │  :8501)    │ │  :8000)    │
     └──────┬─────┘ └──────┬─────┘ └──────┬─────┘
            │              │              │
            ▼              ▼              ▼
     ┌──────────────────────────────────────────┐
     │          后端服务层                       │
     │                                          │
     │  ┌─────────────┐  ┌──────────────────┐  │
     │  │ PDF 提取     │  │ 文本切分          │  │
     │  │ :8006       │  │ :8001            │  │
     │  │ unified_pdf │  │ markdown_chunker │  │
     │  │ _extract    │  │ _api             │  │
     │  └──────┬──────┘  └────────┬─────────┘  │
     │         │                  │             │
     │         ▼                  ▼             │
     │  ┌──────────────────────────────────┐   │
     │  │     Milvus API (:8000)           │   │
     │  │  - 向量入库 (upload)              │   │
     │  │  - 向量检索 (search)              │   │
     │  │  - 集合管理 (collection CRUD)     │   │
     │  └──────────────┬───────────────────┘   │
     │                 │                        │
     │                 ▼                        │
     │  ┌──────────────────────────────────┐   │
     │  │     Chat Service (:8501)         │   │
     │  │  - 向量检索 + Rerank             │   │
     │  │  - LLM 生成 (流式/非流式)         │   │
     │  │  - 多轮对话                       │   │
     │  └──────────────────────────────────┘   │
     └──────────────────────────────────────────┘
                           │
                           ▼
     ┌──────────────────────────────────────────┐
     │          数据存储层                       │
     │                                          │
     │  ┌──────────┐  ┌──────────┐  ┌────────┐ │
     │  │  Milvus  │  │  MinIO   │  │ etcd   │ │
     │  │ (向量)   │  │ (对象存储)│  │ (元数据)│ │
     │  └──────────┘  └──────────┘  └────────┘ │
     │                                          │
     │  ┌──────────────────────────────────┐   │
     │  │  本地文件系统                      │   │
     │  │  backend/output/uploads/         │   │
     │  │  backend/output/extraction_results│   │
     │  └──────────────────────────────────┘   │
     └──────────────────────────────────────────┘
```

### 2.2 四个微服务


| 服务         | 端口   | 入口文件                                                                       | 职责                      |
| ---------- | ---- | -------------------------------------------------------------------------- | ----------------------- |
| PDF 提取     | 8006 | `backend/Information-Extraction/unified/unified_pdf_extraction_service.py` | 接收 PDF，输出 Markdown      |
| 文本切分       | 8001 | `backend/Text_segmentation/markdown_chunker_api.py`                        | 接收 Markdown，输出 Chunk 列表 |
| Milvus API | 8000 | `backend/Database/milvus_server/milvus_api.py`                             | 向量入库/检索/集合管理            |
| 对话服务       | 8501 | `backend/chat/kb_chat.py`                                                  | 检索增强 + LLM 问答           |


### 2.3 服务间调用方式

服务之间通过 **HTTP 调用** 通信，不是消息队列，不是 gRPC：

```
前端上传 PDF
  → POST :8006/extract        (PDF 提取服务)
  → POST :8001/chunk          (文本切分服务)
  → POST :8000/api/upload     (Milvus API 入库)
  → POST :8501/chat           (对话服务，内部调用 :8000 检索)
```

---

## 三、核心数据流

### 3.1 知识库上传全流程

```
用户上传 PDF
  │
  ▼
[1] 前端 → POST :8006/extract
     请求: multipart/form-data { file, collection_name }
     响应: { file_id, markdown, status }
     处理:
       V1.0: PyMuPDF4LLM 提取文本 → VLM 补充图表描述
       V2.0: MinerU API 调用 → 返回结构化 Markdown
     产物: backend/output/extraction_results/{file_id}/
           ├── output.md          (提取结果)
           └── images/            (提取的图片)
  │
  ▼
[2] 前端 → POST :8001/chunk
     请求: { "markdown_text": "...", "file_id": "..." }
     响应: { chunks: [...], count: N }
     处理:
       header_recursive.py: 递归按标题切分
       smart_merge_chunks_v2(): 智能合并过小的块
       add_cross_page_bridges_v2(): 跨页桥接
       table-aware: 表格完整性保护
  │
  ▼
[3] 前端 → POST :8000/api/upload
     请求: { collection_name, file_data: { chunks: [...] } }
     处理:
       a. 调用 Embedding API (DashScope) 获取向量
       b. 写入 Milvus Collection
       c. 更新 collection_name_mapping.json (文件 ID 映射)
     响应: { filename, file_id, status, chunks_count }
  │
  ▼
[4] 完成，前端刷新知识库列表
```

### 3.2 对话问答流程

```
用户输入问题
  │
  ▼
[1] 前端 → POST :8501/chat (或 /chat/stream)
     请求: {
       query: "什么是机器学习？",
       collection_name: "kb_xxx",
       llm_config: { api_key, model, base_url },
       rerank_config: { api_key, model, base_url },
       top_k: 5,
       history: [...]
     }
  │
  ▼
[2] kb_chat.py 内部检索 (V2.1 增强链路)
     a. Redis 缓存检查 → 命中则直接返回
     b. Query Rewrite → 生成 3 个查询变体（语义相同，用词不同）
     c. 多路召回 → 对每个变体调 :8000/api/search，合并去重
     d. BM25 混合检索 → 向量分 + BM25 关键词分融合重排
        （如果启用了 Reranker API，BM25 跳过，避免重复计算）
     e. Rerank（可选，支持 Jina/Qwen/BGE/通用 API，优先于 BM25）
     f. 将 Top-K chunks 拼接为 Context
     g. 写入 Redis 缓存
  │
  ▼
[3] 调用 LLM 生成回答
     非流式: 一次性返回
     流式: NDJSON 格式逐步返回
       {"type": "content", "content": "..."}
       {"type": "sources", "sources": [...]}
       {"type": "metadata", {
         "rewrite_time": 0.5,
         "retrieve_time": 1.2,
         "rerank_time": 0.0,
         "hybrid_time": 0.1,
         "llm_time": 2.3,
         "total_time": 4.1,
         "cache_hit": false
       }}
       {"type": "error", "message": "..."}  (出错时)
  │
  ▼
[4] 前端渲染回答 + 引用来源
```

**V2.1 降级策略**:

- Redis 不可用 → 跳过缓存，功能正常
- Query Rewrite 失败 → 使用原始查询
- BM25 异常 → 降级到原始向量排序
- 所有失败都是独立的，不会中断对话链路

### 3.3 检索测试流程

```
用户输入测试查询
  │
  ▼
[1] 前端 → POST :8000/api/search_by_filename (或 /api/search)
     请求: { collection_name, query_text, top_k }
  │
  ▼
[2] Milvus API
     a. 调用 Embedding API 获取查询向量
     b. Milvus 向量检索 (IP/COSINE 相似度)
     c. 返回 Top-K chunks + 相似度分数
  │
  ▼
[3] 前端展示检索结果列表
```

---

## 四、各服务详细实现

### 4.1 PDF 提取服务 (:8006)

**文件**: `backend/Information-Extraction/unified/unified_pdf_extraction_service.py`

**V1.0 模式**:

- 使用 `pymupdf4llm` 将 PDF 转为 Markdown
- 对图片页面调用 VLM（qwen3-vl-plus）进行描述
- 结果保存到 `backend/output/extraction_results/{file_id}/output.md`

**V2.0 模式**:

- 调用 MinerU API (`MINERU_API_URL`) 进行解析
- 可选 PaddleOCR-VL (`PADDLEOCR_VL_API_URL`)
- 可选 DeepSeek-OCR (`DEEPSEEK_OCR_API_URL`)
- 支持 `mineru_visualizations/` 可视化输出

**核心接口**:

```python
POST /extract              # 上传 PDF 文件
POST /extract/text         # 上传纯文本（跳过 OCR）
GET /health                # 健康检查
```

**关键依赖**: `pymupdf4llm`, `pdf2image`, `openai` (VLM 调用)

### 4.2 文本切分服务 (:8001)

**文件**: `backend/Text_segmentation/markdown_chunker_api.py`

**算法流程**:

1. `header_recursive.py`: 按 Markdown 标题层级递归切分
  - 优先按 H1/H2 切分，保证语义完整性
  - 过大的块继续按 H3/H4 细分
2. `smart_merge_chunks_v2()`: 智能合并
  - 设定最小/最大 chunk 大小
  - 合并相邻的小块，不超过最大阈值
  - 保持语义连贯（不切割句子中间）
3. `add_cross_page_bridges_v2()`: 跨页桥接
  - 检测跨页断裂的段落
  - 在相邻 chunk 间添加桥接文本，保留上下文
4. 表格感知: 不切割 Markdown 表格

**核心接口**:

```python
POST /chunk                # { "markdown_text": "...", "file_id": "..." }
GET /health                # 健康检查
```

### 4.3 Milvus API 服务 (:8000)

**文件**: `backend/Database/milvus_server/milvus_api.py`

**这是整个系统的核心数据枢纽**。所有向量操作都经过它。

**Collection Schema**:

```
Field            Type               说明
─────────────── ────────────────── ──────────────────
id               INT64 (PK)         主键
chunk_text       VARCHAR(65535)     文本内容
file_name        VARCHAR(65535)     文件名
embedding        FLOAT_VECTOR(1024) 向量 (text-embedding-v4 维度)
metadata         JSON               附加元数据
```

**Embedding 生成**:

- 调用 `EMBEDDING_URL` (DashScope text-embedding-v4)
- 并发线程池 `ThreadPoolExecutor` 批量编码
- **注意**: embedding API 失败时 fallback 到 `np.random.rand()` —— 这是个 bug，会插入垃圾向量

**核心接口**:

```python
POST /api/upload               # 上传 chunks（自动 embed + 入库）
POST /api/search               # 向量检索
POST /api/search_by_filename   # 按文件名过滤检索
POST /api/collections          # 创建集合
GET  /api/collections          # 列出所有集合
GET  /api/collections/{name}   # 获取集合详情
GET  /api/collections/{name}/stats  # 统计信息
GET  /api/collections/{name}/documents  # 列出文件
DELETE /api/collections/{name} # 删除集合
DELETE /api/documents          # 删除指定文件的所有 chunks
GET  /health                   # 健康检查
```

**辅助文件**:

- `milvus_kb_service.py`: Milvus 操作封装类
- `localai_embeddings.py`: 本地 Embedding 模型适配器（备用）
- `utils.py`: 工具函数
- `collection_name_mapping.json`: 集合名与文件 ID 的映射

### 4.4 对话服务 (:8501)

**文件**: `backend/chat/kb_chat.py`

**这是系统最复杂的单个服务**，负责完整的 RAG 问答链路。

**核心能力**:

1. **Redis 缓存** (V2.1): 相同查询直接返回缓存结果，避免重复检索和 API 调用
2. **Query Rewrite** (V2.1): 使用 LLM 生成 3 个语义相同的查询变体，提升召回率
3. **多路召回** (V2.1): 对每个改写变体检索，合并去重后取 Top-50 候选
4. **BM25 混合检索** (V2.1): 向量分 + BM25 关键词分加权融合，提高精确匹配
5. **向量检索**: 调用 `:8000/api/search` 获取候选 chunks
6. **Rerank**: 可选二次排序，支持 4 种 provider（优先于 BM25）
  - Jina: `jina.ai` rerank API
  - Qwen/DashScope: `dashscope` rerank
  - BGE: 本地 BGE 模型
  - 通用: 任意 OpenAI 兼容的 rerank API
7. **多轮对话**: 支持 `history` 参数，维护对话上下文
8. **流式输出**: NDJSON 协议 (`/chat/stream`)
9. **非流式输出**: 标准 JSON (`/chat`)
10. **过滤表达式**: 支持 Milvus `filter_expr` 按文件名等过滤

**V2.1 降级策略**: Redis、Query Rewrite、BM25 各自独立降级，不影响核心链路。

**核心接口**:

```python
POST /chat                     # 非流式问答
POST /chat/stream              # 流式问答 (NDJSON)
GET  /health                   # 健康检查
```

**流式响应格式 (NDJSON)**:

```json
{"type": "content", "content": "机器"}
{"type": "content", "content": "学习是"}
{"type": "content", "content": "AI 的..."}
{"type": "sources", "sources": [{"chunk_text": "...", "score": 0.95}]}
{"type": "metadata", {
  "rewrite_time": 0.5,
  "retrieve_time": 1.2,
  "rerank_time": 0.0,
  "hybrid_time": 0.1,
  "llm_time": 2.3,
  "total_time": 4.1,
  "documents_count": 5,
  "cache_hit": false
}}
{"type": "error", "message": "..."}  // 仅出错时
```

---

## 五、前端架构

### 5.1 技术栈

- React 18 + TypeScript
- Vite 6 (构建工具)
- TailwindCSS 3 + shadcn/ui 组件
- motion (动画)
- react-markdown (Markdown 渲染)
- lucide-react (图标)
- sonner (Toast 通知)
- zod (表单验证)

### 5.2 组件结构

```
frontend/
├── App.tsx                 # 根组件，路由/状态管理
├── components/
│   ├── Sidebar.tsx         # 左侧导航栏
│   ├── Header.tsx          # 顶部标题栏
│   ├── Dashboard.tsx       # 仪表盘首页
│   ├── KnowledgeBase.tsx   # 知识库列表
│   ├── KnowledgeBaseDetail.tsx  # 知识库详情（文件列表）
│   ├── DocumentViewer.tsx  # 文档查看器
│   ├── Chat.tsx            # 对话界面
│   ├── RetrievalTest.tsx   # 检索测试
│   ├── Settings.tsx        # 设置页
│   ├── UploadDialog.tsx    # 上传对话框
│   ├── ConfirmDialog.tsx   # 确认对话框
│   ├── Toast.tsx           # Toast 封装
│   └── ui/                 # shadcn/ui 基础组件
├── config-test.html         # 配置测试页
└── package.json
```

### 5.3 关键前端状态


| 状态                      | 存储方式         | 说明                                                 |
| ----------------------- | ------------ | -------------------------------------------------- |
| `activeView`            | React state  | 当前页面 (dashboard/knowledge/chat/retrieval/settings) |
| `selectedKnowledgeBase` | React state  | 选中的知识库 ID                                          |
| `selectedDocument`      | React state  | 选中的文档 ID                                           |
| `isV2`                  | localStorage | V1.0/V2.0 版本切换                                     |
| Chat messages           | 内存           | 当前对话历史                                             |


### 5.4 前端 API 调用

前端直接调用后端服务，不经过网关：

```typescript
// 知识库管理
const MILVUS_API_BASE = 'http://localhost:8000/api'

// 对话
const CHAT_API_BASE = 'http://localhost:8501'

// PDF 提取
const EXTRACTION_API_BASE = 'http://localhost:8006'
```

---

## 六、Milvus 数据库

### 6.1 部署方式

```yaml
# backend/Database/milvus_server/docker-compose.yaml
services:
  etcd:        # 元数据存储，官方镜像
  minio:       # 对象存储，默认账号 minioadmin/minioadmin
  standalone:  # Milvus 主服务
```

### 6.2 关键运维规则

1. **禁止 `restart: always`** — etcd WAL 日志会无限增长（曾经涨到 111GB）
2. **必须手动启停** — `docker compose up -d` / `docker compose down`
3. **数据持久化** — 映射到 `data/volumes/` 目录

---

## 七、配置管理

### 7.1 后端 .env（`backend/.env`）


| 配置组             | 关键变量                                                                                  | 说明                            |
| --------------- | ------------------------------------------------------------------------------------- | ----------------------------- |
| LLM             | `API_KEY`, `MODEL_NAME`, `MODEL_URL`                                                  | 生成模型（DashScope qwen3-vl-plus） |
| Embedding       | `EMBEDDING_URL`, `EMBEDDING_MODEL_NAME`, `EMBEDDING_API_KEY`                          | 向量模型（text-embedding-v4）       |
| 文件路径            | `UPLOAD_BASE_DIR`, `EXTRACTION_RESULTS_DIR`                                           | 本地存储路径                        |
| 服务端口            | `INFOR_EXTRAC_SERVICE_PORT=8006`, `CHUNK_SERVICE_PORT=8001`, `CHAT_SERVICE_PORT=8501` | 各服务端口                         |
| Milvus          | `MILVUS_HOST=localhost`, `MILVUS_PORT=19530`                                          | Milvus 连接                     |
| OCR V2          | `MINERU_API_URL`, `VLLM_SERVER_URL`, `DEEPSEEK_OCR_API_URL`, `PADDLEOCR_VL_API_URL`   | OCR 服务地址（需 GPU 服务器）           |
| **检索增强 (V2.1)** | `CACHE_ENABLED`, `REDIS_HOST`, `HYBRID_SEARCH_ENABLED`, `QUERY_REWRITE_ENABLED`       | 详见下方 7.3                      |


### 7.3 检索增强配置 (V2.1)


| 配置组       | 关键变量                       | 默认值         | 说明         |
| --------- | -------------------------- | ----------- | ---------- |
| Redis 缓存  | `CACHE_ENABLED`            | `true`      | 是否启用缓存     |
|           | `REDIS_HOST`               | `localhost` | Redis 地址   |
|           | `REDIS_PORT`               | `6379`      | Redis 端口   |
|           | `CACHE_TTL_SECONDS`        | `3600`      | 缓存过期时间     |
| BM25 混合检索 | `HYBRID_SEARCH_ENABLED`    | `true`      | 是否启用       |
|           | `BM25_WEIGHT`              | `0.3`       | BM25 关键词权重 |
|           | `VECTOR_WEIGHT`            | `0.7`       | 向量相似度权重    |
|           | `HYBRID_TOP_K`             | `50`        | 初筛候选数      |
|           | `HYBRID_FINAL_TOP_K`       | `10`        | 最终返回数      |
| 查询改写      | `QUERY_REWRITE_ENABLED`    | `true`      | 是否启用       |
|           | `QUERY_REWRITE_VARIATIONS` | `3`         | 改写变体数      |


### 7.2 前端环境变量

- `frontend/.env`（从 `env.template` 复制）
- 主要配置 API 基础地址

---

## 八、测试现状

### 8.1 已有测试脚本


| 文件                                                                 | 测试内容                     | 类型   |
| ------------------------------------------------------------------ | ------------------------ | ---- |
| `backend/Database/milvus_server/test_milvus_api.py`                | Milvus CRUD              | 手动脚本 |
| `backend/chat/test_kb_chat_api.py`                                 | 对话 API（非流式/流式/rerank/多轮） | 手动脚本 |
| `backend/Information-Extraction/unified/repose_test_extraction.py` | PDF 提取                   | 手动脚本 |
| `backend/Text_segmentation/repose_test_segmentation.py`            | 文本切分                     | 手动脚本 |


### 8.2 测试框架状态

- **没有 pytest / vitest 框架**
- 测试文件是手动运行的脚本，需要服务先启动
- 部分测试文件包含硬编码路径，换机器无法运行
- 测试文件内有硬编码 API key

---

## 九、安全现状


| 项目            | 状态  | 详情                                  |
| ------------- | --- | ----------------------------------- |
| CORS          | 宽松  | 所有服务 `allow_origins=["*"]`          |
| 鉴权            | 无   | 无 API key、JWT、Session               |
| API Key 泄露    | 有风险 | `backend/.env` 已提交到仓库；测试文件内有硬编码 key |
| Milvus 默认密码   | 有风险 | MinIO 默认 `minioadmin/minioadmin`    |
| 前端发送 LLM key  | 有风险 | Chat 组件从浏览器发送 `api_key` 到后端         |
| Rate Limiting | 无   | 无限流                                 |


---

## 十、与 Spec 文档的对比

Spec 文档（`~/Documents/specs/Multimodal_RAG/`）描述的是一个**参考架构**，与当前实现存在以下差异：


| 维度        | Spec 描述                    | 实际实现                              |
| --------- | -------------------------- | --------------------------------- |
| 数据库       | MySQL + Milvus             | 仅 Milvus（无 MySQL）                 |
| 架构        | 单体 FastAPI                 | 4 个独立微服务                          |
| PDF 解析    | PyMuPDF/PDFPlumber 等 5 种方案 | V1.0: PyMuPDF4LLM；V2.0: MinerU    |
| Embedding | 本地 sentence-transformers   | 远程 DashScope API                  |
| 前端        | 未详细设计                      | 完整 React + TypeScript + shadcn/ui |
| 部署        | Docker Compose 统一编排        | 脚本 + nohup 独立启动                   |




---

## 十一、项目文件索引

### 后端核心文件


| 路径                                                                         | 行数    | 职责                   |
| -------------------------------------------------------------------------- | ----- | -------------------- |
| `backend/Information-Extraction/unified/unified_pdf_extraction_service.py` | ~400  | PDF 提取服务入口           |
| `backend/Information-Extraction/unified/llm_extraction.py`                 | ~100  | VLM 提取逻辑             |
| `backend/Information-Extraction/unified/ocr_v2_extractors.py`              | ~200  | V2.0 OCR 适配器         |
| `backend/Text_segmentation/markdown_chunker_api.py`                        | ~200  | 文本切分服务               |
| `backend/Text_segmentation/header_recursive.py`                            | ~150  | 递归标题切分算法             |
| `backend/Text_segmentation/MarkdownTextSplitter.py`                        | ~100  | LangChain 风格切分       |
| `backend/Database/milvus_server/milvus_api.py`                             | ~1600 | Milvus HTTP API      |
| `backend/Database/milvus_server/milvus_kb_service.py`                      | ~200  | Milvus 操作封装          |
| `backend/Database/milvus_server/hybrid_search.py`                          | ~125  | BM25 混合检索 (V2.1 新增)  |
| `backend/chat/kb_chat.py`                                                  | ~980  | 对话检索服务（最复杂，V2.1 增强）  |
| `backend/chat/query_rewrite.py`                                            | ~175  | 查询改写服务 (V2.1 新增)     |
| `backend/common/cache_manager.py`                                          | ~170  | Redis 缓存管理 (V2.1 新增) |
| `backend/requirements.txt`                                                 | 22    | Python 依赖            |
| `backend/start_all_services.sh`                                            | ~227  | 服务启动脚本               |


### 前端核心文件


| 路径                                            | 行数   | 职责      |
| --------------------------------------------- | ---- | ------- |
| `frontend/App.tsx`                            | ~150 | 根组件     |
| `frontend/components/Chat.tsx`                | ~300 | 对话界面    |
| `frontend/components/KnowledgeBase.tsx`       | ~200 | 知识库管理   |
| `frontend/components/KnowledgeBaseDetail.tsx` | ~300 | 知识库详情   |
| `frontend/components/DocumentViewer.tsx`      | ~200 | 文档查看    |
| `frontend/components/RetrievalTest.tsx`       | ~200 | 检索测试    |
| `frontend/components/Settings.tsx`            | ~150 | 设置页     |
| `frontend/components/UploadDialog.tsx`        | ~100 | 上传对话框   |
| `frontend/vite.config.ts`                     | ~32  | Vite 配置 |
| `frontend/package.json`                       | ~80  | 依赖管理    |


---

## 十二、已知技术债

> 来自之前的评估，按优先级排列


| #   | 问题                                               | 修复工作量 | 影响    |
| --- | ------------------------------------------------ | ----- | ----- |
| 1   | Embedding 失败时插入随机向量 (`np.random.rand()`)         | 15min | 数据完整性 |
| 2   | `kb_chat.py` 中 `requests.post()` 阻塞异步 event loop | 2h    | 并发性能  |
| 3   | `print()` 代替 `logging`                           | 1d    | 可观测性  |
| 4   | API key 已提交到仓库                                   | 1h    | 安全    |
| 5   | 无鉴权中间件                                           | 2-3d  | 安全    |
| 6   | 无 rate limiting                                  | 1d    | 成本控制  |
| 7   | 无 pytest 框架                                      | 3-5d  | 代码质量  |
| 8   | 无统一 docker-compose                               | 1-2d  | 部署体验  |
| 9   | 无项目 README                                       | 0.5d  | 可维护性  |
| 10  | 流式/非流式代码大量重复                                     | 2h    | 代码质量  |


---

## 十二、V2.1 检索增强状态


| 组件            | 状态  | 部署方式                          | 说明                      |
| ------------- | --- | ----------------------------- | ----------------------- |
| Query Rewrite | 已完成 | 无额外部署，复用 LLM API              | 失败时降级到原始查询              |
| BM25 混合检索     | 已完成 | `pip install rank-bm25 jieba` | 失败时降级到原始向量排序            |
| Redis 缓存      | 已完成 | `docker run redis:alpine`     | 不可用时自动降级，不影响功能          |
| 配置            | 已完成 | `.env` 新增 11 项变量              | 全部有默认值                  |
| 依赖            | 已完成 | `requirements.txt` +3         | rank-bm25, jieba, redis |


