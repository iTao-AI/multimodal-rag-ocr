# 核心算法详解

> 最近更新：2026-04-09 (V2.1: 新增 BM25 混合检索、Query Rewrite、Redis 缓存)
> 本文档深入分析系统中的核心算法。包含代码级细节和调参指南。

---

## 一、Header-Recursive 文本切分算法

**文件**: `backend/Text_segmentation/header_recursive.py`

这是系统中最有技术深度的算法。传统的文本切分要么按固定长度切割（破坏语义），要么按段落切割（大小不均），而这个算法**结合了 Markdown 标题层级、语义连续性检测和跨页桥接**。

### 1.1 算法流程（4 个阶段）

```
输入: Markdown 文本（含 {{第N页}} 页标）
  │
  ▼
┌─────────────────────────────────────────┐
│ Phase 1: 逐页切分                        │
│   - 按 {{第N页}} 分页                    │
│   - 每页内用 LangChain MarkdownTextSplitter │
│   - 每个 chunk 附带标题层级路径            │
│                                          │
│  产出: raw_chunks (最小不可分单元)        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Phase 2: 智能合并 (stitch_chunks)        │
│   - 合并相邻小块，不超过 chunk_size*1.2   │
│   - 尊重 H1/H2 标题边界                  │
│   - 语义连续性检测                        │
│   - 表格完整性保护                        │
│                                          │
│  产出: stitched (合并后的 chunks)         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Phase 3: 跨页桥接 (add_cross_bridges)    │
│   - 检测相邻页之间的 chunk                │
│   - 提取前 chunk 尾部 + 后 chunk 头部     │
│   - 作为独立的 bridge chunk 插入          │
│   - 继承前 chunk 的标题信息               │
│                                          │
│  产出: 最终 chunks 列表                  │
└─────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Phase 4: V2 增强 (smart_merge_v2)       │
│   - merge_tolerance 控制宽松度           │
│   - max_page_span 限制跨页数              │
│   - respect_headers 开关标题边界保护      │
└─────────────────────────────────────────┘
```

### 1.2 Phase 1: 逐页切分

```python
# split_pages() 函数
# 输入: "内容1{{第1页}}内容2{{第2页}}内容3"
# 输出:
#   full_text_clean = "内容1内容2内容3"
#   page_blocks = [(1, "内容1"), (2, "内容2"), (3, "内容3")]
```

然后每页内使用 LangChain 的 `MarkdownTextSplitter(chunk_size=600, chunk_overlap=80)` 进行基础切分。每个基础 chunk 记录：
- `page_start`, `page_end`, `pages` — 页码信息
- `headers` — 标题层级路径，如 `["# 第一章", "## 1.1 概述"]`
- `is_table_like` — 是否包含表格（以 `|` 开头或含 `\n|`）

### 1.3 Phase 2: 智能合并（核心逻辑）

这是算法最关键的部分。`stitch_chunks_with_headers()` 对每对相邻 chunk 做以下判断：

```
                是否有 H1/H2 标题边界？
                  │ 是 → 不合并，保留边界
                  │ 否
                  ▼
                是否跨页超过 max_page_span？
                  │ 是 → 不合并
                  │ 否
                  ▼
                同页还是相邻页？
                  │ 同页 → 合并后 <= max_allowed？→ 是则合并
                  │ 相邻页 → 合并后 <= chunk_size？
                  │             │ 是 → 语义连续性检查：
                  │             │       两边都是表格 → 合并
                  │             │       前块未完结 + 后块不是新段 → 合并
                  │             │       前块很短(<30%) + 后块不是新段 → 合并
                  │             │ 否 → 容忍范围内 + (表格 或 后块很短) → 合并
                  ▼
             执行合并 / 保留
```

**语义连续性检测** (`looks_like_block_start` / `ends_with_sentence_break`):

| 检测项 | 触发条件 | 意义 |
|--------|---------|------|
| 新标题 | 以 `#` / `##` 开头 | 新章节开始，不合并 |
| 分隔线 | 以 `---` / `***` 开头 | 内容分割，不合并 |
| 列表/代码 | 以 `*` / `-` / ``` 开头 | 新内容块开始 |
| 句子完结 | 以 `。！？.!？` 结尾 | 语义完整，可合并 |

**合并容忍度**:
- `chunk_size = 600` — 目标大小
- `merge_tolerance = 0.2` — 允许超出 20%，即最大 720 字符
- 短块（< chunk_size * 0.3 = 180 字符）优先合并

### 1.4 Phase 3: 跨页桥接

**问题**: PDF 被页标切割后，一个完整段落可能跨两页。检索时如果只命中段落的前半部分（在第 N 页），后半部分（在第 N+1 页）的 chunk 可能因为缺少上下文而语义不完整。

**解决方案**: 为每个跨页边界创建一个 bridge chunk：

```
Chunk A (Page 3):  "...这是机器学习的定义。"
Chunk B (Page 4):  "它在医疗、金融等领域有广泛应用。"

Bridge chunk: "这是机器学习的定义。\n它在医疗、金融等领域有广泛应用。"
  cross_page_bridge: true
  pages: [3, 4]
```

Bridge chunk 的 `bridge_span = 150` 字符，从前 chunk 尾部取 150 字符 + 后 chunk 头部取 150 字符。

### 1.5 调参指南

| 参数 | 默认值 | 说明 | 调大效果 | 调小效果 |
|------|--------|------|---------|---------|
| `chunk_size` | 600 | 目标 chunk 大小 | 大块，检索上下文多 | 小块，更精确 |
| `chunk_overlap` | 80 | 切分时重叠字符数 | 更多冗余但上下文更好 | 更少冗余 |
| `merge_tolerance` | 0.2 | 合并超出容忍比例 | 允许更大的块 | 更严格的块大小 |
| `max_page_span` | 3 | 最大跨页数 | 允许跨更多页合并 | 更严格的页限制 |
| `bridge_span` | 150 | 桥接片段长度 | 更多上下文 | 更短的桥 |
| `respect_headers` | true | 是否保护标题边界 | — | 忽略标题边界 |

### 1.6 每个 Chunk 的元数据

```json
{
  "page_start": 3,
  "page_end": 4,
  "pages": [3, 4],
  "text": "# 第一章\n## 1.1 概述\n\n正文内容...",
  "text_length": 450,
  "continued": true,
  "cross_page_bridge": false,
  "is_table_like": false,
  "headers": ["# 第一章", "## 1.1 概述"]
}
```

---

## 二、Reranker 算法

**文件**: `backend/chat/kb_chat.py` — `rerank_documents()` 方法（第 167-399 行）

Reranker 是检索链路的第二级排序。第一级是向量相似度（recall），第二级是 Reranker 精排（precision）。

### 2.1 流程

```
用户查询: "什么是机器学习？"
  │
  ▼
Milvus 向量检索 (recall_k=50)
  │
  ▼
[top 50 chunks by cosine similarity]
  │
  ▼
Reranker 精排
  │
  ├─ Jina reranker → POST /rerank
  ├─ Qwen/DashScope reranker → POST /compatible-mode/v1/rerank
  ├─ BGE reranker → 本地或 API
  └─ 通用 OpenAI 兼容 reranker
  │
  ▼
[top N chunks by relevance score]
  │
  ▼
拼接为 LLM Prompt Context
```

### 2.2 多 Provider 适配

Reranker 通过 `model_name` 自动识别 provider：

**Jina Reranker**:
```python
# 触发条件: model_name 包含 "jina"
# API: POST {base_url}/rerank
# Payload: { "model": "...", "query": "...", "documents": ["..."], "top_n": N }
# 响应: { "results": [{"index": 0, "relevance_score": 0.95}, ...] }
```

**Qwen/DashScope Reranker**:
```python
# 触发条件: model_name 包含 "gte-rerank" 或 URL 含 "dashscope"
# API: POST {base_url}/rerank
# Payload: { "model": "...", "input": { "query": "...", "documents": ["..."] } }
# 响应: { "output": { "results": [{"index": 0, "relevance_score": 0.95}, ...] } }
```

**BGE Reranker**:
```python
# 触发条件: model_name 包含 "bge"
# API: POST {base_url}/v1/rerank
# Payload: { "model": "...", "query": "...", "documents": ["..."] }
# 响应: { "results": [{"index": 0, "relevance_score": 0.95}, ...] }
```

**通用 (OpenAI 兼容)**:
```python
# 触发条件: 以上都不匹配
# API: POST {base_url}/rerank
# Payload: { "model": "...", "query": "...", "documents": ["..."] }
```

### 2.3 降级策略

Reranker 失败时不会中断问答，而是降级到原始向量排序：

```python
except Exception as e:
    print(f"重排序失败，降级到原始排序: {e}")
    for doc in documents:
        doc.setdefault("retrieval_score", doc["score"])
    return documents  # 返回原始检索结果
```

### 2.4 输出字段

Rerank 后的每个文档包含：
- `retrieval_score` — 原始向量相似度分数
- `rerank_score` — Reranker 分数
- `score` — 最终排序分数（= rerank_score）

---

## 三、向量检索与 Embedding

**文件**: `backend/Database/milvus_server/milvus_api.py`

### 3.1 Embedding 生成

- **模型**: 阿里云 DashScope `text-embedding-v4`
- **维度**: 1024
- **相似度度量**: IP（内积，因为 Embedding 已归一化，等价于余弦相似度）
- **并发方式**: `ThreadPoolExecutor` 批量编码

```python
# milvus_api.py 中的 embedding 调用
def generate_embedding(text: str) -> List[float]:
    response = requests.post(
        EMBEDDING_URL + "/embeddings",
        headers={"Authorization": f"Bearer {EMBEDDING_API_KEY}"},
        json={"model": EMBEDDING_MODEL_NAME, "input": text}
    )
    return response.json()["data"][0]["embedding"]
```

### 3.2 Milvus Collection Schema

```
Field            Type               约束
─────────────── ────────────────── ──────────────────────────
id               INT64              主键
chunk_text       VARCHAR(65535)     文本内容（非常大，允许长 chunk）
file_name        VARCHAR(65535)     文件名
embedding        FLOAT_VECTOR(1024) 向量
metadata         JSON               附加元数据（页码、标题等）
```

### 3.3 索引配置

系统使用 `IVF_FLAT` 或 `HNSW` 索引（取决于首次创建时的配置）。检索参数：

```python
search_params = {
    "metric_type": "IP",        # 内积（归一化向量等价于余弦）
    "params": {"nprobe": 16}    # 搜索的聚类中心数
}
```

### 3.4 已知 Bug: 随机向量 Fallback

```python
# milvus_api.py 第 115-116 行附近
except Exception:
    # Embedding API 失败，生成随机向量
    embedding = np.random.rand(1024).tolist()
```

这是一个严重 bug。随机向量会被插入 Milvus，导致：
1. 该 chunk 永远无法被正确检索到
2. 不会有任何错误提示
3. 如果 Embedding API 批量失败，整个知识库的数据都不可靠

**正确做法**: 应该返回 503 错误，让调用方重试或中止。

---

## 四、对话服务 RAG 流水线

**文件**: `backend/chat/kb_chat.py`（~700 行）

### 4.1 完整流水线

```
POST /chat
  │
  ▼
[1] retrieve_documents(query, collection_name, top_k, filter_expr)
     └─ 调用 :8000/api/search (同步 requests.post，在 async 中 — 这是 bug)
  │
  ▼
[2] rerank_documents(query, docs, rerank_config)  [可选]
     └─ 4 种 provider 自动识别，失败时降级
  │
  ▼
[3] build_prompt(query, context, history)
     └─ 拼接: 系统 Prompt + 历史对话 + 检索内容 + 用户问题
  │
  ▼
[4] generate_answer(prompt, llm_config)
     │
     ├─ 流式: AsyncOpenAI chat.completions.create(stream=True)
     │        → NDJSON 逐 token 输出
     │
     └─ 非流式: OpenAI chat.completions.create()
                → 一次性返回完整回答
  │
  ▼
[5] 返回 { answer, sources, total_tokens, latency_ms }
```

### 4.2 Prompt 模板

```python
prompt = f"""你是一个专业的知识库助手。请基于以下知识库信息回答问题。

知识库内容：
{context}

{history_prompt}

用户问题：{query}

请基于上述信息提供准确、详细的回答。"""
```

### 4.3 流式 NDJSON 协议

流式响应使用 NDJSON（Newline Delimited JSON），每行一个 JSON 对象：

```
{"type": "content", "content": "机"}
{"type": "content", "content": "器"}
{"type": "content", "content": "学习"}
{"type": "content", "content": "是"}
{"type": "sources", "sources": [...]}
{"type": "metadata", "total_tokens": 1234, "latency_ms": 567}
```

出错时：
```
{"type": "error", "message": "错误描述"}
```

前端通过 `fetch` + `TextDecoder` 逐行解析。

---

## 四-B. BM25 混合检索 (V2.1)

**文件**: `backend/Database/milvus_server/hybrid_search.py`

### 原理

纯向量检索的弱点是**同义词/缩写匹配差**。比如用户搜"监督学习"，但如果文档用的是"有监督学习"，向量相似度可能不够高。BM25 基于关键词匹配，恰好互补。

```
Milvus 向量召回 (Top-50)
  │
  ▼
候选文档: [{chunk_text, score, ...}, ...]
  │
  ▼
jieba 分词 → 查询分词 vs 每个 chunk 分词
  │
  ▼
BM25Okapi 打分
  │
  ▼
分数归一化 (min-max)
  │
  ▼
加权融合: score = 0.7 * vector_score_norm + 0.3 * bm25_score_norm
  │
  ▼
排序 → 返回 Top-10
```

### 关键参数

| 参数 | 默认值 | 说明 | 调大效果 | 调小效果 |
|------|--------|------|---------|---------|
| `vector_weight` | 0.7 | 向量相似度权重 | 更依赖语义匹配 | 更依赖关键词匹配 |
| `bm25_weight` | 0.3 | BM25 关键词权重 | 更依赖关键词匹配 | 更依赖语义匹配 |
| `final_top_k` | 10 | 最终返回数量 | 更多结果 | 更精确 |

### 降级策略

- `rank-bm25` 未安装 → 直接返回原始文档，不报错
- jieba 分词失败 → 返回原始文档
- 任何异常 → 返回原始文档，保留原始 score

---

## 四-C. Query Rewrite 查询改写 (V2.1)

**文件**: `backend/chat/query_rewrite.py`

### 原理

用户的问题可能表达不够精确。比如用户搜"那个学机器怎么搞"，通过 LLM 改写成"机器学习入门教程"、"如何开始学习 ML"、"机器学习基础知识"，然后用这 3 个变体分别检索，合并去重后作为候选。

```
用户查询: "那个学机器怎么搞"
  │
  ▼
LLM 改写 (temperature=0.7)
  │
  ▼
["那个学机器怎么搞", "机器学习入门教程", "如何开始学习 ML", "机器学习基础知识"]
  │
  ▼
对每个变体检索 Milvus
  │
  ▼
合并去重 (按 doc_id)
  │
  ▼
BM25 重排
```

### 3 种改写策略

| 方法 | 用途 | 成本 |
|------|------|------|
| `rewrite_query()` | 生成语义相同的查询变体 | 1 次 LLM API 调用 |
| `expand_query()` | 提取关键词 + 同义词扩展 | 1 次 LLM API 调用 |
| `generate_hypothetical_answer()` | HyDE 策略，生成假设性答案用于检索 | 1 次 LLM API 调用 |

当前默认使用 `rewrite_query()`，因为它最轻量且效果直接。

### 降级策略

- LLM API 不可用 → 返回 `[原始查询]`，不影响检索
- 响应解析失败 → 返回 `[原始查询]`
- 超时 (10s) → 返回 `[原始查询]`

---

## 四-D. Redis 缓存 (V2.1)

**文件**: `backend/common/cache_manager.py`

### 原理

相同查询的重复检索是最大浪费。缓存查询结果，命中则直接返回，跳过整个检索和 LLM 链路。

### 缓存键设计

```
key = f"query_result:{md5(collection_name + query)}"
```

### TTL

默认 3600 秒（1 小时）。知识库更新后缓存不会自动失效——这是已知的 tradeoff，未来可以通过 `clear_pattern(f"query_result:*")` 手动清除。

### 降级策略

- Redis 未安装 (`pip install redis`) → 自动禁用，不影响功能
- Redis 连接失败 → 自动禁用
- 所有缓存操作失败 → 静默跳过，不中断检索链路

---

## 五、算法对比

### 5.1 切分算法对比

| 策略 | 语义完整性 | 块大小均匀 | 跨页处理 | 实现复杂度 |
|------|-----------|-----------|---------|-----------|
| 固定长度 | 差 | 好 | 无 | 低 |
| LangChain 默认 | 中 | 中 | 无 | 低 |
| **本系统** | **好** | **好** | **桥接** | **高** |

### 5.2 排序算法对比

| 策略 | 精度 | 速度 | 成本 |
|------|------|------|------|
| 纯向量相似度 | 中 | 快 | 低（仅 Embedding） |
| **向量 + Reranker** | **高** | **中** | **中**（额外 API 调用） |
| 纯 Reranker | 最高 | 慢 | 高 |

### 5.3 Embedding 对比

| 模型 | 维度 | 中文支持 | 速度 | 本项目使用 |
|------|------|---------|------|-----------|
| text-embedding-v4 | 1024 | 好 | API | 是 |
| bge-large-zh | 1024 | 优秀 | 本地需 GPU | 否 |
| m3e-base | 768 | 优秀 | 本地需 GPU | 否 |
| text-embedding-ada-002 | 1536 | 中 | API | 否 |
