# PRD: Multimodal RAG OCR — 生产级重构与增强

**日期**: 2026-05-28
**状态**: APPROVED
**版本**: 1.1
**分支**: main

---

## 1. 业务目标与产品目标

### 业务目标
1. 将 RAG-OCR 从"能跑通的 demo"提升到"生产级可用"
2. 修复 25 个已知代码缺陷（4 个致命、12 个高优先级）
3. 建立可持续迭代的工程实践（测试、日志、Docker 编排）

### 产品目标
1. 知识管理者能够上传 PDF 文档，系统自动解析、切分、建索引，支持自然语言问答
2. 检索准确率达到 Recall@5 ≥ 80%，混合检索比纯向量检索提升 ≥ 10%
3. 系统在外部 API 失败时优雅降级，不插入脏数据

### Non-Goals（明确不做什么）
- 不构建多租户系统
- 不支持 10 万+ 文档规模
- 不处理并发 100+ 请求
- 不提供 Word/Markdown/网页导入（当前仅 PDF）
- 不实现 RBAC 权限系统（只做 API Key 鉴权）
- 不做 CI/CD 自动化部署
- 不实现监控告警（Prometheus/Grafana）

---

## 2. 用户画像

### 主画像：知识管理者
- 企业或研究机构的工作人员
- 日常处理大量 PDF 文档（行业报告、产品手册、学术论文）
- 需要快速从文档中找到特定信息，而不是从头阅读
- 技术背景有限，需要简单易用的界面
- 典型场景：上传 20 份行业报告 → 创建知识库 → 提问"这份报告里关于 AI 提效的具体数据是什么？" → 获得有引用来源的回答

### 反画像：大规模企业级场景
- 需要多租户隔离、10 万+ 文档、高并发、SLA 99.9%
- 需要完善的 RBAC 权限、审计日志、数据备份恢复
- 需要零 GPU 本地环境下的完整 OCR 能力
- 这些需求超出本系统当前的设计范围，明确排除

---

## 3. 核心用户故事（INVEST 格式）

### Story 1: 文档入库
**作为** 知识管理者，**我希望** 上传 PDF 文档后系统自动解析为 Markdown 并建立向量索引，**以便** 后续可以检索。
- 独立：可单独测试
- 可协商：PDF 大小限制、支持格式可调整
- 有价值：知识库的入口
- 可估算：中等工作量
- 小型：一个功能点

### Story 2: 自然语言问答
**作为** 研究者，**我希望** 用自然语言向知识库提问，**以便** 获得有引用来源的回答。

### Story 3: 知识库管理
**作为** 管理员，**我希望** 创建、查看、删除知识库及其中的文档，**以便** 维护知识的生命周期。

### Story 4: 检索质量
**作为** 用户，**我希望** 系统能准确理解我的问题并返回相关文档，**以便** 快速定位相关段落。

### Story 5: 系统可靠性
**作为** 运维人员，**我希望** 系统在外部 API 失败时不会插入脏数据，**以便** 保持知识库的完整性。

---

## 4. 系统架构

### 4.1 组件依赖图

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vite :5173)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │Dashboard │  │Knowledge │  │  Chat    │  │ Settings│ │
│  │          │  │Base      │  │Interface │  │ (local) │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────────┘ │
└───────┼─────────────┼─────────────┼─────────────────────┘
        │             │             │
        │ HTTP        │ HTTP        │ HTTP (SSE/NDJSON)
        ▼             ▼             ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐
│ PDF Extraction│ │ Text Chunking │ │   Chat Service        │
│ (:8006)       │ │ (:8001)       │ │   (:8501)             │
│ PyMuPDF4LLM   │ │ Header-Rec.   │ │ ├─ Query Rewrite      │
│ MinerU/Paddle │ │ Markdown      │ │ ├─ BM25 Hybrid        │
│ DeepSeek-OCR  │ │ Splitter      │ │ ├─ Reranker           │
└───────┬───────┘ └───────┬───────┘ │ └─ Redis Cache        │
        │                 │         └───────────┬───────────┘
        │                 │                     │
        │                 ▼                     │ HTTP search
        │         ┌───────────────┐             ▼
        │         │  Milvus API   │◄────────────────────┐
        │         │  (:8000)      │                     │
        │         │               │                     │
        │         └───────┬───────┘                     │
        │                 │ pymilvus                    │
        ▼                 ▼                             │
┌───────────────────────────────────────────────────────────┤
│  Milvus DB (Docker)  │  Redis (optional)                 │
│  etcd + MinIO        │  :6379                            │
└───────────────────────────────────────────────────────────┘
```

### 4.2 数据流图：文档上传链路

```
用户上传 PDF
  │
  ▼ Happy: 解析成功 → Markdown → Header-Recursive 切分 → Embedding → Milvus insert
  │  Nil:   PDF 文件为空        → 400 "文件无内容"
  │  Empty: PDF 无法解析        → 400 "无法解析此 PDF"
  │  Error: Embedding API 失败  → 重试 3 次 → 仍失败 → 503 "向量生成服务不可用"
  │                                    (不插入随机向量)
  ▼
前端显示结果
  │
  ▼ Happy: 显示上传成功 + chunk 数量
  │  Nil:   显示错误提示 + 重试按钮
  │  Empty: 不适用
  │  Error: 显示 503 错误，不白屏
```

### 4.3 数据流图：对话问答链路

```
用户输入问题
  │
  ▼ Happy: Redis 缓存命中 → 流式返回缓存答案
  │  Nil:   查询为空       → 400 "问题不能为空"
  │  Empty: 无匹配文档      → 直接 LLM 回答（无引用）
  │  Error: Milvus 不可用  → 503 "检索服务不可用"
  │
  ▼ (未命中缓存)
Query Rewrite (生成 3 个变体)
  │
  ▼ Happy: 3 个查询 → 多路召回 → 去重合并
  │  Nil:   改写失败 → 使用原始查询
  │  Empty: 改写返回空 → 使用原始查询
  │  Error: 改写 API 失败 → 降级使用原始查询
  │
  ▼ 多路召回
Milvus 搜索 (每个查询 top_k)
  │
  ▼ Happy: 向量 + BM25 RRF 融合 → Top-10
  │  Nil:   无结果 → 直接 LLM 回答
  │  Empty: 结果不足 → 用现有结果
  │  Error: BM25 失败 → 降级纯向量排序
  │
  ▼ Reranker (可选)
Reranker API (Jina/Qwen/BGE)
  │
  ▼ Happy: 精排 → Top-5
  │  Nil:   无配置 → 跳过
  │  Empty: 所有分数低于阈值 → 跳过
  │  Error: Reranker API 失败 → 降级原始向量排序
  │
  ▼ Prompt 构建
LLM 生成 (流式)
  │
  ▼ Happy: 流式输出 → 来源文档 → 元数据
  │  Nil:   LLM 返回空 → 显示"未生成回答"
  │  Empty: 不适用
  │  Error: LLM API 失败 → 显示错误，不白屏
```

---

## 5. 功能清单（MoSCoW 优先级）

| # | 功能 | 优先级 | 状态 | 关联缺陷 |
|---|------|--------|------|----------|
| 1 | PDF 解析为 Markdown (V1) | Must | 已有需修复 | — |
| 2 | Header-Recursive 智能切分 | Must | 已有需修复 | headers 顺序丢失 |
| 3 | 向量 Embedding + Milvus | Must | 已有需修复 | 随机向量 fallback |
| 4 | 向量检索（相似度） | Must | 已有 | — |
| 5 | BM25 混合检索 + RRF | Must | 已有 | — |
| 6 | Query Rewrite | Must | 已有需修复 | JSON 注入风险 |
| 7 | Redis 缓存 | Must | 已有 | — |
| 8 | Reranker 多 provider | Must | 已有 | — |
| 9 | 流式/非流式对话 | Must | 已有需修复 | 代码重复、event loop 阻塞 |
| 10 | 知识库 CRUD | Must | 已有需修复 | query() limit 参数 |
| 11 | 文件上传 & 删除 | Must | 已有 | — |
| 12 | 文档预览（PDF） | Must | 已有需修复 | 硬编码路径 |
| 13 | 修复随机向量 fallback | Must | 待修复 | #1 |
| 14 | 修复 event loop 阻塞 | Must | 待修复 | #2 |
| 15 | 清除 Git 历史 API Key | Must | 待修复 | #3 |
| 16 | 修复 /config/default 密钥泄露 | Must | 待修复 | #8 |
| 17 | 修复前端假按钮 | Must | 待修复 | 前端审查 #1,#2,#3 |
| 18 | 修复 fetch 不检查 response.ok | Must | 待修复 | 前端审查 #5 |
| 19 | 修复硬编码路径 | Must | 待修复 | #5, #6 |
| 20 | 消除 chat 代码重复 | Should | 待修复 | #3 |
| 21 | API Key 鉴权中间件 | Should | 新增 | — |
| 22 | CORS 收紧 | Should | 待修复 | #4 |
| 23 | pytest 测试框架 | Should | 新增 | — |
| 24 | 结构化日志 | Should | 待修复 | #11 |
| 25 | 修复可变默认参数等 | Should | 待修复 | #8, #9 |
| 26 | 上传进度反馈 | Should | 新增 | — |
| 27 | 修复 Milvus query() limit | Should | 待修复 | #7 |
| 28 | 修复 headers 顺序 | Could | 待修复 | #9 |
| 29 | 修复 Jina Key 泄露 | Could | 待修复 | #2 |
| 30 | 统一 Docker Compose | Could | 新增 | — |
| 31 | 健康检查编排 | Could | 新增 | — |

### Won't-have（本轮不做）
- 多租户 / 权限管理
- 多格式支持（Word/网页）
- 多轮对话持久化
- 监控告警 / CI/CD

---

## 6. 关键边界条件

### 数据缺失
- Embedding API 失败：自动重试 3 次（指数退避 1s→2s→4s），仍失败返回 503，**不插入随机向量**
- Reranker API 失败：降级使用原始向量排序
- Redis 不可用：禁用缓存，直接查询
- Milvus 不可用：返回 503，明确错误信息

### 并发
- 单次上传 1 个 PDF，不支持批量并发
- 对话服务支持单用户流式输出
- Embedding 批量处理 4 线程池，batch_size=32

### 失败处理
- 外部服务 5xx：返回明确错误，不泄露堆栈
- PDF 解析失败：400 + 错误原因
- 切分算法异常：400 + 错误原因
- 前端 fetch 失败：显示用户友好提示，不白屏

---

## 7. Error & Rescue Map

| 方法/组件 | 可能失败 | 异常类型 | 捕获? | 恢复动作 | 用户看到 |
|-----------|----------|----------|-------|----------|----------|
| `generate_embedding()` | API 超时 | `requests.Timeout` | Y | 指数退避重试 3 次 | "向量生成服务不可用，请重试" |
| `generate_embedding()` | API 401/403 | `HTTPError` | Y | 不重试，记录日志 | "API 密钥无效，请检查配置" |
| `generate_embedding()` | 网络不可达 | `ConnectionError` | Y | 指数退避重试 3 次 | "网络连接失败，请检查网络" |
| `generate_embeddings_batch()` | 部分批次失败 | `HTTPError` | Y | 该批次降级为随机向量 + 记录警告 | 上传继续，日志记录异常批次 |
| `retrieve_documents()` | Milvus 不可用 | `HTTPError` | Y | 返回空列表 + 503 | "检索服务暂时不可用" |
| `retrieve_documents()` | Milvus 超时 | `Timeout` | Y | 返回空列表 + 503 | "检索超时，请重试" |
| `rerank_documents()` | Reranker API 失败 | `Exception` | Y | 降级原始向量排序 | 无感知（内部降级） |
| `rewrite_query()` | LLM 返回非 JSON | `JSONDecodeError` | Y | 降级原始查询 | 无感知（内部降级） |
| `rewrite_query()` | API 返回空 choices | `IndexError` | Y | 降级原始查询 | 无感知（内部降级） |
| `call_llm_stream()` | LLM API 失败 | `APIError` | Y | 流式输出错误事件 | "回答生成失败" |
| `cache_manager.get()` | Redis 连接断开 | `ConnectionError` | Y | 禁用缓存 | 无感知（内部降级） |
| `fetch()` 前端 | 后端 500 非 JSON | `SyntaxError` | N ← **GAP** | — | **前端崩溃（白屏）** |
| Milvus `query()` | limit 参数无效 | `MilvusException` | Y | Python 切片 `[:top_k]` | 无感知（内部修复） |

**GAP 修复**：前端所有 `fetch().json()` 调用前必须检查 `response.ok`，失败时显示错误提示而非崩溃。

---

## 8. 技术决策

### TD1: Embedding 失败重试策略
**决策**：自动重试 3 次（指数退避 1s→2s→4s）。仍失败返回 503。

### TD2: 前端设置页的功能范围
**决策**：设置保存到 localStorage。后端不管理用户偏好。

### TD3: 测试覆盖深度
**决策**：两层覆盖：
- 单元测试：`header_recursive.py` 切分算法（纯函数）
- 集成测试：Milvus 上传 + 检索端到端（Mock Embedding API）
不需要 E2E 测试。

### TD4: Milvus query() limit 参数修复
**决策**：使用 `query()[:top_k]` Python 切片。改动小，立即修复。

---

## 9. 非功能需求

| 指标 | 目标值 | 测量方式 |
|------|--------|----------|
| 单次检索响应时间 P95 | ≤ 1s | 向量检索 + BM25 融合 |
| 对话首字延迟 P95 | ≤ 3s | 包含检索 + LLM 生成 |
| PDF 上传到可检索 P95 | ≤ 30s | 100 页以内文档 |
| 检索准确率 Recall@5 | ≥ 80% | 20 个标准 query benchmark |
| 混合检索提升 | ≥ 10% | BM25+RRF vs 纯向量对比 |
| 测试覆盖率 | chunker ≥ 80% | pytest --cov |

---

## 10. 验收标准（Given/When/Then）

### Story 1: 文档入库
- **Given** 用户已创建知识库
- **When** 用户上传一个有效的 PDF 文件
- **Then** 系统解析为 Markdown，按 Header-Recursive 算法切分，生成向量，存入 Milvus
- **And** 前端显示上传成功及处理的 chunk 数量
- **And** 如果 Embedding API 失败 3 次重试后仍不可用，上传中止，前端显示明确错误

### Story 2: 自然语言问答
- **Given** 知识库中有文档
- **When** 用户输入一个与自然语言相关的问题
- **Then** 系统返回包含引用来源的回答
- **And** 每个来源包含文件名和相关度分数
- **And** 流式输出首字延迟 ≤ 3s

### Story 3: 知识库管理
- **Given** 用户已访问系统
- **When** 用户创建知识库
- **Then** 系统创建 Milvus Collection 并返回成功状态
- **When** 用户删除知识库中的文档
- **Then** 后续检索结果不再包含该文档

### Story 4: 检索质量
- **Given** 知识库中有足够的文档
- **When** 运行包含 20 个标准 query 的 benchmark 脚本
- **Then** Recall@5 ≥ 80%
- **And** 混合检索（BM25+RRF）比纯向量检索 Recall@5 提升 ≥ 10%

### Story 5: 系统可靠性
- **Given** 某个外部服务（Embedding/Reranker/Redis）不可用
- **When** 用户发起请求
- **Then** 系统优雅降级或返回 503 错误
- **And** 不崩溃、不泄露堆栈信息、不插入脏数据
- **And** 前端显示用户友好的错误提示

---

## 11. 北极星指标 + 关停线

### 北极星指标
**检索准确率（Recall@5 ≥ 80%）**

理由：RAG 系统的核心体验，直接决定用户信任度。所有技术决策（切分、混合检索、Reranker）都服务于这个指标。

### 关停线
1. **效果关停**：20 个标准 query 的 benchmark 中，混合检索 Recall@5 无提升或下降 → BM25+RRF 无价值，回退
2. **时间关停**：M 级修复在 2 周内未完成 → 暂停 S/C 级，确保核心代码干净

---

## 12. 依赖与约束

### 外部依赖
| 依赖 | 用途 | 风险 |
|------|------|------|
| DashScope API（阿里云） | LLM + Embedding + Reranker | 按量计费，可能欠费 |
| Milvus（Docker） | 向量数据库 | etcd WAL 日志占满磁盘 |
| Redis（可选） | 缓存 | 不可用时自动降级 |
| MinerU / PaddleOCR-VL / DeepSeek-OCR | V2.0 OCR | 需远程 GPU（AutoDL） |

### 约束
- 本地 Mac 无 GPU，V2.0 OCR 需远程 GPU
- Python 3.11 conda 环境（vlm_rag）
- 不破坏现有 V1/V2 数据格式兼容性
- Milvus 禁用 `restart: always`

### 合规
- 当前无用户数据合规要求
- API Key 管理是内部安全问题
