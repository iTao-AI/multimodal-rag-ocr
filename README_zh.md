# Multimodal RAG OCR

一个支持 PDF 文档解析、OCR 提取、向量存储和 AI 问答的知识库系统。支持轻量级 PDF 提取（V1.0）和企业级 OCR 管道（V2.0，MinerU / PaddleOCR-VL / DeepSeek-OCR）。

## 架构

```
前端（Vite, :5173）
  ├── 知识库管理（Milvus CRUD）
  ├── 聊天界面（kb_chat 服务）
  └── 文档查看器

后端服务（4 个独立 FastAPI 微服务）：
  ┌─ PDF 提取（:8006）── 从上传的 PDF 中提取文本/内容
  │    ├── llm_extraction.py          （V1.0：PyMuPDF4LLM + VLM）
  │    └── ocr_v2_extractors.py        （V2.0：MinerU/PaddleOCR/DeepSeek-OCR）
  │
  ├─ 文本分块（:8001）── 将提取的 Markdown 分割为块
  │    └── markdown_chunker_api.py
  │
  ├─ 向量数据库（:8000）── Milvus API 封装，用于嵌入 + 存储
  │    ├── milvus_api.py               （pymilvus 的 FastAPI 封装）
  │    └── milvus_kb_service.py
  │    （Milvus 通过 docker-compose 运行，含 etcd + MinIO）
  │
  └─ 聊天服务（:8501）── 基于 RAG 的知识库问答
       ├── kb_chat.py                  （主聊天端点）
       └── query_rewrite.py            （查询扩展服务）
```

**数据流**：上传 PDF → PDF 提取 → 文本分块 → Milvus（嵌入 + 存储）→ 聊天（检索 + 回答）

## 核心功能

- **PDF 知识提取**：使用 LLM/VLM 将 PDF 解析为结构化 Markdown
- **多模态 OCR**：MinerU、PaddleOCR-VL、DeepSeek-OCR 处理复杂文档
- **混合检索**：BM25 + 向量融合检索（RRF），配合 Redis 缓存
- **查询改写**：自动查询扩展提升召回率
- **实时聊天**：基于 RAG 的文档集合问答
- **知识库管理**：通过 Milvus 向量数据库进行 CRUD 操作

## 技术栈

| 层级 | 技术 |
|------|------|
| OCR 引擎 | MinerU / PaddleOCR-VL / DeepSeek-OCR |
| 大模型 | Qwen3-VL-Plus（DashScope） |
| 嵌入模型 | text-embedding-v4（DashScope） |
| 向量数据库 | Milvus（含 etcd + MinIO） |
| 缓存 | Redis（查询结果缓存） |
| 混合检索 | BM25 + 向量 RRF 融合 |
| 后端 | FastAPI（4 个微服务） |
| 前端 | Vue 3 + Vite |
| 部署 | Docker（Milvus），AutoDL GPU 服务器（OCR） |

## 快速开始

### 前置要求

- Python 3.11（建议使用 conda 环境）
- Node.js >= 18
- Docker（Milvus）
- DashScope API 密钥

### 1. 后端配置

```bash
conda create -n vlm_rag python=3.11
conda activate vlm_rag
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 API 密钥和服务地址
```

### 2. 启动 Milvus

```bash
cd backend/Database/milvus_server
docker compose -f docker-compose.yaml up -d
```

### 3. 启动后端服务

```bash
cd backend
./start_all_services.sh
```

### 4. 启动前端

```bash
cd frontend
npm install && npm run dev
# → http://localhost:5173
```

## API 端点

| 服务 | 端口 | 关键端点 |
|------|------|---------|
| PDF 提取 | 8006 | `POST /upload`, `POST /extract` |
| 文本分块 | 8001 | `POST /chunk` |
| Milvus API | 8000 | `POST /collections`, `POST /search` |
| 聊天服务 | 8501 | `POST /chat`, `POST /rewrite` |

## 重要约束

1. **Milvus 绝对不能使用 `restart: always`** — etcd WAL 日志会占满磁盘。始终手动启停。
2. **本地 Mac 没有 GPU** — MinerU、PaddleOCR-VL、DeepSeek-OCR 需要远程 GPU 服务器（AutoDL）。本地 `.env` 指向 `localhost` 作为代理。
3. **Python 环境**：使用 conda `vlm_rag`（Python 3.11），而非系统 Python。

## License

MIT
