# 面试准备指南

> 基于本项目实际实现编写。每个问题附带参考回答和对应的实际代码位置，让你在面试中既能说原理，也能说细节。

---

## 一、项目介绍类

### 1.1 请用 1 分钟介绍这个项目

**参考回答**:

Multimodal RAG OCR 是一个基于 RAG 架构的知识库问答系统。用户上传 PDF 文档后，系统通过 OCR 解析为 Markdown，然后按标题层级智能切分为语义 Chunk，生成向量后存入 Milvus 向量数据库。最终用户可以通过自然语言向知识库提问，系统会检索相关文档片段，再交给 LLM 生成有依据的回答。

系统采用 4 个独立的 FastAPI 微服务架构：PDF 提取、文本切分、向量数据库 API 和对话服务。前端使用 React + TypeScript 构建。支持 V1.0（快速模式）、V2.0（OCR 增强模式）和 V2.1（检索增强：BM25 + 查询改写 + Redis 缓存）三个版本。

**技术栈**: FastAPI、Milvus、React、TypeScript、TailwindCSS、pymupdf4llm、阿里云 DashScope

### 1.2 项目的亮点是什么？

**3 个可以展开的亮点**:

1. **Header-Recursive 切分算法** — 不是简单的固定长度分块，而是按 Markdown 标题层级递归切分，加上智能合并（语义连续性检测、表格保护、H1/H2 边界保护）和跨页桥接。代码在 `backend/Text_segmentation/header_recursive.py`。

2. **多 Reranker Provider 适配** — 对话服务支持 Jina、Qwen、BGE 和任意 OpenAI 兼容的 Reranker，通过模型名自动识别 provider，失败时自动降级到原始向量排序。代码在 `backend/chat/kb_chat.py:167-399`。

3. **运维事故响应** — Milvus 的 etcd 组件 WAL 日志无限增长，磁盘涨到 111GB。定位为 `restart: always` 导致的自动重启问题，改为手动启停 + 禁用自动重启策略。记录在 `OPERATIONS.md`。

---

## 二、RAG 原理类

### 2.1 RAG 的工作原理是什么？

**参考回答**:

RAG（Retrieval-Augmented Generation）检索增强生成，核心流程是 **检索 → 拼接 → 生成**：

```
用户提问
  │
  ▼
1. 计算问题的向量表示（Embedding）
  │
  ▼
2. 向量数据库中检索 Top-K 相关文档片段
  │
  ▼
3. 将检索结果拼接到 Prompt 中作为上下文
  │
  ▼
4. LLM 基于上下文生成回答
```

相比直接问 LLM，RAG 的优势：
- **减少幻觉**: 回答有知识库依据
- **私有知识**: 可以用企业内部文档
- **可追溯**: 能返回引用来源

**本项目实现**: 在 `kb_chat.py` 中，`retrieve_documents()` 调 Milvus API 检索，然后可选 BM25 混合重排或 `rerank_documents()` 做精排，最后 `generate_answer()` 调 LLM。V2.1 还加了 Query Rewrite（生成 3 个查询变体多路召回）和 Redis 缓存。

### 2.2 文本分块（Chunking）为什么重要？

**参考回答**:

Chunking 直接决定检索质量。块太大，检索到的内容噪声多；块太小，丢失上下文。

常见的 chunking 策略：

| 策略 | 优点 | 缺点 |
|------|------|------|
| 固定长度 | 简单 | 切割语义 |
| 按段落 | 语义完整 | 大小不均 |
| 滑动窗口 | 保留上下文 | 数据冗余 |
| **按标题递归**（本项目） | **兼顾语义和大小** | **实现复杂** |

本项目的 Header-Recursive 算法分 3 步：
1. 按 Markdown 页标逐页切分（最小单元）
2. 智能合并相邻块（尊重 H1/H2 边界，检测语义连续性）
3. 添加跨页桥接片段（防止跨页断裂导致检索遗漏）

### 2.3 什么是 Reranker？为什么需要它？

**参考回答**:

Reranker 是检索链路的第二级排序。第一级用向量相似度（如余弦）快速召回 Top-50，第二级用 Cross-Encoder 或 API 对这 50 个结果做精排。

**为什么需要**:
- 向量相似度是单向编码，只计算 query 和 doc 各自的向量，没有考虑两者的交互
- Reranker 是双向编码，同时看 query 和 doc，精度更高
- 类比：向量检索是"海选"，Reranker 是"面试"

**本项目**: V2.1 支持两级排序。第一级是 BM25 混合检索（向量相似度 + 关键词匹配加权融合），第二级是可选的 Reranker API（Jina/Qwen/BGE），通过模型名自动识别。失败时自动降级。

---

## 三、Milvus 向量数据库类

### 3.1 Milvus 是什么？为什么选择它？

**参考回答**:

Milvus 是开源向量数据库，专门用于存储和检索向量（Embedding）。

**向量数据库 vs 传统数据库**:

| 维度 | 传统数据库 | 向量数据库 |
|------|-----------|-----------|
| 查询方式 | 精确匹配（=, LIKE） | 相似度搜索（最近邻） |
| 索引 | B+ 树、Hash | HNSW、IVF、FLAT |
| 适用场景 | 结构化数据 | 语义搜索、推荐、图像检索 |

**选择 Milvus 的原因**:
- 支持亿级向量、毫秒级检索
- Python SDK 友好（pymilvus）
- 支持分布式部署
- 开源社区活跃

**对比其他方案**:
- Faiss: Facebook 出品，轻量但需自己封装
- Pinecone: 全托管但收费，国内访问慢
- Chroma: 轻量适合开发，生产环境不够成熟

### 3.2 Milvus Collection 如何设计？

**参考回答**:

Collection 是 Milvus 中存储的基本单位，类似关系数据库的表。设计要考虑：

**本项目的 Schema**:
```
id (INT64, PK)          — 主键
chunk_text (VARCHAR)     — 文本内容，用于返回时展示
file_name (VARCHAR)      — 文件名，用于按文件过滤
embedding (FLOAT_VECTOR) — 1024 维向量
metadata (JSON)          — 页码、标题等附加信息
```

**设计考虑**:
- `file_name` 字段支持按文件名过滤检索
- `metadata` 用 JSON 类型存储灵活元数据
- `chunk_text` 设得很大（65535），因为有些 chunk 可能很长

### 3.3 向量索引如何选择？

**参考回答**:

索引选择取决于数据规模、延迟要求和内存预算：

| 索引 | 适用规模 | 速度 | 内存 | 精度 |
|------|---------|------|------|------|
| FLAT | <10 万 | 慢 | 低 | 100% |
| IVF_FLAT | 10 万-100 万 | 中 | 中 | 高 |
| HNSW | >100 万 | 快 | 高 | 高 |

**关键参数**:
- IVF_FLAT 的 `nlist`: 聚类中心数，建议 = sqrt(N)，N 是向量总数
- HNSW 的 `M`: 每个节点的连接数（16-64），越大越准但越慢
- HNSW 的 `efConstruction`: 构建时的搜索范围（64-512）
- 检索时的 `nprobe`（IVF）或 `ef`（HNSW）: 越大越准但越慢

### 3.4 Milvus 部署有哪些坑？

**参考回答**:

本项目踩过的坑：

1. **etcd WAL 日志无限增长** — Milvus 依赖 etcd 做元数据管理，etcd 的 WAL 日志不会自动清理。如果用了 `restart: always`，Milvus 频繁重启会导致 etcd 不断写入 WAL，磁盘迅速占满（我们遇到过涨到 111GB 的情况）。

   **解决**: 禁止 `restart: always`，手动启停。用完就 `docker compose down`。

2. **MinIO 默认密码** — docker-compose 中 MinIO 默认 `minioadmin/minioadmin`，生产环境必须改。

3. **数据持久化** — Milvus 数据目录必须映射到宿主机，否则容器重建数据丢失。

---

## 四、Embedding 类

### 4.1 Embedding 模型如何选择？

**参考回答**:

考虑 4 个维度：

1. **语言支持**: 中文场景选 bge-large-zh、m3e-base 或阿里云 text-embedding-v4。纯英文可选 OpenAI ada-002 或 E5。

2. **维度**: 越高精度越高，但存储和计算成本也越高。384 维（MiniLM）到 1536 维（ada-002）。本项目用 1024 维（text-embedding-v4）。

3. **速度 vs 精度**: 本地模型速度取决于硬件。API 模型（如 DashScope）无需本地 GPU 但受网络延迟影响。

4. **成本**: 本地部署零 API 成本但需 GPU。API 按 token 计费。

| 模型 | 维度 | 中文 | 速度 | 成本 |
|------|------|------|------|------|
| text-embedding-v4 | 1024 | 好 | API | 按量计费 |
| bge-large-zh | 1024 | 优秀 | 本地需 GPU | 免费 |
| MiniLM-L12-v2 | 384 | 中 | 快 | 免费 |

### 4.2 如何评估 Embedding 质量？

**参考回答**:

1. **MTEB Benchmark**: 大规模文本嵌入基准测试，包含检索、聚类、分类等任务。参考 HuggingFace 的 MTEB Leaderboard。

2. **下游任务评估**: 在 RAG 场景直接测 Recall@K 和回答准确率。
   ```python
   # 构造测试集: (query, expected_chunks)
   # 计算检索到 expected_chunks 的比例
   ```

3. **相似度测试**:
   ```python
   pairs = [
       ("机器学习是什么？", "ML 的定义"),     # 应高相似
       ("机器学习", "今天天气"),             # 应低相似
   ]
   ```

---

## 五、架构设计类

### 5.1 为什么用微服务而不是单体？

**参考回答**:

本项目有 4 个独立 FastAPI 服务：

**优点**:
- **独立部署**: 可以单独更新某个服务
- **故障隔离**: 一个服务挂了不影响其他
- **独立扩展**: 对话服务可以多实例，提取服务单实例
- **资源隔离**: PDF 提取很耗 CPU，不影响对话服务的响应速度

**缺点**:
- 运维复杂：需要管理 4 个进程
- 服务间通过 HTTP 调用，有网络延迟
- 没有统一的服务发现和负载均衡

**如果重来**：会用 Docker Compose 统一编排，加健康检查和自动重启（但要避免 Milvus 那个坑）。

### 5.2 如果要支持 10 万 + 文档，如何优化？

**参考回答**:

**向量索引层**:
- 用 HNSW 替代 IVF_FLAT（大规模下性能更好）
- 按知识库分 Collection，不把所有数据塞一个集合

**缓存层**:
- Redis 缓存热门查询结果
- Embedding 结果缓存（相同文本不需重复计算）

**异步处理层**:
- PDF 上传改为异步任务队列（Celery/dramatiq）
- 用户拿到 task_id 后轮询结果
- 批量上传用 `asyncio.gather` 并发

**数据库层**:
- Embedding API 批量调用（一次请求多个文本，降低 API 调用次数）
- 连接池复用

### 5.3 如何保证数据一致性？

**参考回答**:

本项目存在一致性问题：
- Milvus 和文件系统之间无事务
- 上传中途失败可能留下孤儿文件

**正确做法**:
1. 先写文件系统（PDF 文件）
2. 再写 Milvus（向量）
3. 任何一步失败，回滚前面的操作
4. 定期扫描孤儿文件清理

或者引入消息队列做异步最终一致性。

---

## 六、故障排查类

### 6.1 搜索结果为空，如何排查？

**排查清单**:

1. **确认 Collection 有数据**
   ```bash
   curl http://localhost:8000/api/collections/kb_xxx/stats
   # 看 total_chunks 是否 > 0
   ```

2. **确认 Embedding API 正常**
   ```bash
   curl https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings \
     -H "Authorization: Bearer $KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"text-embedding-v4","input":["测试"]}'
   ```

3. **检查查询文本** — 是否为空？是否太短（1-2 个字很难匹配）？

4. **增大 top_k** — 也许默认 5 太少，试试 20。

5. **检查过滤表达式** — `filter_expr` 是否排除了所有结果？

### 6.2 对话服务返回错误，如何排查？

**排查清单**:

1. **检查 LLM API Key** — 是否过期、欠费
2. **检查 Milvus 是否运行** — 对话服务内部调 `:8000`
3. **查看日志** — `tail -f backend/logs/chat.log`
4. **测试非流式** — 流式调试更难，先用 `/chat` 端点确认基础链路

---

## 七、系统设计题

### 7.1 设计一个企业知识库问答系统

**参考架构**:

```
用户 → Nginx (HTTPS + 负载均衡) → API Gateway
  │
  ├─ Auth Service (JWT + RBAC)
  ├─ Document Service (上传/解析/切分)
  ├─ Search Service (向量检索 + Rerank)
  ├─ Chat Service (LLM 生成)
  └─ Admin Service (知识库管理/用户管理)
  │
  ├─ MySQL (用户/权限/文档元数据)
  ├─ Milvus Cluster (向量检索，3 节点)
  ├─ MinIO (文件存储)
  ├─ Redis (缓存 + 会话)
  └─ Elasticsearch (全文检索)
```

**与本项目相比的差距**:
- 鉴权（本项目无）
- 多租户隔离（本项目无）
- 审计日志（本项目无）
- 文档版本管理（本项目无）
- 监控告警（本项目无）

---

## 八、高频追问

### 8.1 "你说跨页桥接，能具体解释吗？"

**参考回答**:

PDF 按页解析后，一个自然段落可能被页标切割成两半。比如：

```
第 3 页: "...这是机器学习的基本概念，它包括..."
第 4 页: "...监督学习、无监督学习和强化学习三种范式。"
```

如果不做桥接，检索到"三种范式"时只能匹配到第 4 页的 chunk，但丢失了"机器学习"这个关键上下文。桥接 chunk 把两页边界处的文本拼接在一起，作为一个独立的检索单元：

```
Bridge: "...它包括...\n...监督学习..."
```

这样无论文本从哪边检索，都能命中桥接 chunk 获得完整语义。

### 8.2 "Reranker 和向量检索有什么区别？"

**参考回答**:

向量检索用的是**双编码器**（Bi-Encoder）：query 和 doc 各自编码成向量，然后用余弦相似度算距离。优点是 doc 的向量可以预先计算好存起来，检索时只算 query 的向量，非常快。

Reranker 用的是**交叉编码器**（Cross-Encoder）：query 和 doc 一起输入到模型里，让模型直接输出相关性分数。精度高但计算量大，因为每对 (query, doc) 都要重新跑一次模型。

所以标准做法是：双编码器先召回 Top-50（快），交叉编码器再精排（准）。本项目用的是 API 版的 Reranker（Jina/Qwen），原理一样，只是模型在远端。

### 8.3 "Milvus 和 MySQL 在这个系统里各自承担什么角色？"

**参考回答**:

本项目实际上只用到了 Milvus，没有 MySQL（Spec 文档里有 MySQL 但实际代码没用到）。

Milvus 既存储了向量，也存储了文本内容和元数据（JSON 字段）。这在小规模下是合理的，因为省去了双存储的一致性维护。

但如果要扩展到生产环境，应该引入关系数据库存文档元数据（文件名、上传时间、用户等），Milvus 只管向量检索。原因是：
- Milvus 的事务能力弱
- 复杂查询（JOIN, GROUP BY）不支持
- 权限管理不如 MySQL 成熟
