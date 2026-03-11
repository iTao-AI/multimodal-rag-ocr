# Multimodal RAG - 多模态检索增强生成系统

> 🤖 基于 Milvus 向量数据库 + Qwen3-VL 大模型  
> 🔍 支持 PDF 文档解析、智能问答、知识库管理  
> 📚 完整的企业级 RAG 解决方案

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 16+](https://img.shields.io/badge/node-16+-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📖 目录

- [项目简介](#-项目简介)
- [核心功能](#-核心功能)
- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [API 文档](#-api-文档)
- [前端功能](#-前端功能)
- [配置说明](#-配置说明)
- [服务管理](#-服务管理)
- [常见问题](#-常见问题)
- [待办事项](#-待办事项)

---

## 🎯 项目简介

Multimodal RAG 是一个完整的多模态检索增强生成（Retrieval-Augmented Generation）系统，结合了向量数据库的精确检索能力和大语言模型的强大生成能力。

### 技术栈

| 层级 | 技术 |
|-----|------|
| **大模型** | Qwen3-VL-Plus / GPT-4o |
| **向量数据库** | Milvus 2.6+ |
| **嵌入模型** | text-embedding-v4 |
| **后端框架** | FastAPI + Uvicorn |
| **前端框架** | React 18 + TypeScript + Vite |
| **UI 组件** | Radix UI + Tailwind CSS |

### 应用场景

- 📚 **企业知识库问答** - 内部文档、政策、流程查询
- 📄 **文档智能分析** - PDF、Markdown 文档内容提取和问答
- 💬 **智能客服** - 基于知识库的自动问答
- 🔍 **信息检索** - 多模态文档检索和重排序

---

## ✨ 核心功能

### 后端功能

| 功能 | 描述 | 状态 |
|-----|------|------|
| **PDF 智能解析** | 支持多模态 PDF 解析，提取文本和图片 | ✅ |
| **文本切分** | Markdown 文本智能切分，保持语义完整性 | ✅ |
| **向量嵌入** | 调用阿里云 text-embedding-v4 | ✅ |
| **向量存储** | Milvus 向量数据库存储和检索 | ✅ |
| **智能召回** | 相似度检索 + 阈值过滤 | ✅ |
| **文档重排序** | 可选的重排序模块提升精度 | ✅ |
| **RAG 对话** | 流式/非流式问答，支持历史对话 | ✅ |
| **知识库管理** | 集合创建、文档管理、状态查询 | ✅ |

### 前端功能

| 功能 | 描述 | 状态 |
|-----|------|------|
| **仪表盘** | 系统概览、统计数据 | ✅ |
| **知识库管理** | 创建、查看、删除知识库 | ✅ |
| **文档上传** | PDF 上传、解析进度跟踪 | ✅ |
| **文档查看** | 文档列表、内容预览 | ✅ |
| **智能对话** | RAG 问答、流式输出、来源展示 | ✅ |
| **检索测试** | 测试召回效果、分数展示 | ✅ |
| **系统设置** | API 配置、模型选择 | ✅ |

---

## 🏗️ 系统架构

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端界面 (React)                         │
│                    http://localhost:5173                         │
│  ┌──────────┬──────────┬──────────┬──────────┬─────────────┐   │
│  │ 仪表盘    │ 知识库    │ 文档查看  │  对话    │   设置      │   │
│  └──────────┴──────────┴──────────┴──────────┴─────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      后端微服务集群 (FastAPI)                     │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │ PDF 提取服务 │  │ 文本切分服务 │  │ 向量数据库  │  │对话检索 ││
│  │  Port 8006  │  │  Port 8001  │  │  Port 8000  │  │Port 8501││
│  │             │  │             │  │             │  │         ││
│  │ • PDF 解析   │  │ • Markdown  │  │ • 向量嵌入  │  │ • RAG   ││
│  │ • 图片提取  │  │ • 智能切分  │  │ • Milvus    │  │ • 重排序││
│  │ • 结果返回  │  │ • 块管理    │  │ • 相似度检索│  │ • 流式  ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ gRPC/HTTP
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    外部服务 & 数据存储                            │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Milvus DB  │  │ 阿里云百炼  │  │    本地文件系统          │  │
│  │  Port 19530 │  │  LLM API    │  │  • 上传文件             │  │
│  │             │  │             │  │  • 解析结果             │  │
│  │ • 向量存储  │  │ • Qwen3-VL  │  │  • 日志文件             │  │
│  │ • 相似度检索│  │ • Embedding │  │  • 配置文件             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 数据流

```
用户提问
    │
    ▼
┌─────────────────┐
│  1. 问题输入     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. 向量召回     │  Milvus 相似度检索 (top_k=10)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. 文档重排序   │  (可选) Reranker 精排 (top_n=5)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. 构建 Prompt  │  模板 + 检索结果 + 历史对话
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. LLM 生成     │  Qwen3-VL / GPT-4o
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  6. 返回答案     │  流式输出 + 来源文档
└─────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- **操作系统**: Linux / macOS / Windows (推荐 Linux)
- **Python**: 3.8 - 3.11
- **Node.js**: 16.0+
- **Docker**: 用于 Milvus 向量数据库
- **Conda**: Anaconda 或 Miniconda

### 1. 克隆项目

```bash
git clone <repository-url>
cd Multimodal_RAG
```

### 2. 后端部署

```bash
# 创建 Conda 虚拟环境
conda create -n vlm_rag python=3.11 -y
conda activate vlm_rag

# 进入后端目录
cd backend

# 安装 Python 依赖
pip install -r requirements.txt
# 或使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API Key 等配置

# 启动 Milvus (如未部署)
cd Database/milvus_server
./start_milvus.sh

# 返回后端目录，启动所有服务
cd ../..
./start_all_services.sh

# 验证服务状态
./status_services.sh
```

### 3. 前端部署

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
# 或使用国内镜像
npm install --registry=https://registry.npmmirror.com

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 API 地址

# 启动开发服务器
npm run dev
```

### 4. 访问系统

打开浏览器访问：**http://localhost:5173**

---

## 📡 API 文档

### 服务端口

| 服务 | 端口 | API 文档 |
|-----|------|---------|
| PDF 提取 | 8006 | http://localhost:8006/docs |
| 文本切分 | 8001 | http://localhost:8001/docs |
| 向量数据库 | 8000 | http://localhost:8000/docs |
| 对话检索 | 8501 | http://localhost:8501/docs |

### 核心 API

#### 1. PDF 提取服务 (8006)

```bash
# 上传并解析 PDF
POST /extract
Content-Type: multipart/form-data

文件：PDF 文件

响应:
{
  "success": true,
  "markdown_path": "/path/to/output.md",
  "images_dir": "/path/to/images/"
}
```

#### 2. 文本切分服务 (8001)

```bash
# 切分 Markdown 文本
POST /chunk
Content-Type: application/json

{
  "markdown_text": "# 标题\n内容...",
  "chunk_size": 500,
  "chunk_overlap": 50
}

响应:
{
  "chunks": [
    {"chunk_id": 1, "content": "..."},
    {"chunk_id": 2, "content": "..."}
  ]
}
```

#### 3. 向量数据库服务 (8000)

```bash
# 创建集合
POST /collection/create
{
  "collection_name": "my_kb",
  "dimension": 1024
}

# 插入向量
POST /collection/insert
{
  "collection_name": "my_kb",
  "vectors": [...],
  "metadata": [...]
}

# 相似度检索
POST /collection/search
{
  "collection_name": "my_kb",
  "query_vector": [...],
  "top_k": 10,
  "score_threshold": 0.5
}
```

#### 4. 对话检索服务 (8501)

```bash
# RAG 对话
POST /chat
Content-Type: application/json

{
  "query": "如何使用这个系统？",
  "collection_name": "my_kb",
  "llm_config": {
    "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key": "your_api_key",
    "model_name": "qwen3-vl-plus"
  },
  "top_k": 10,
  "use_reranker": false,
  "stream": true,
  "history": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的？"}
  ]
}

响应 (流式):
data: {"chunk": "你"}
data: {"chunk": "好"}
data: {"chunk": "！"}
...

响应 (非流式):
{
  "success": true,
  "answer": "你好！...",
  "sources": [
    {
      "chunk_text": "...",
      "filename": "doc.pdf",
      "score": 0.85
    }
  ]
}
```

完整 API 文档请访问各服务的 `/docs` 端点。

---

## 🖥️ 前端功能

### 页面结构

```
frontend/
├── components/
│   ├── Dashboard.tsx          # 仪表盘
│   ├── KnowledgeBase.tsx      # 知识库列表
│   ├── KnowledgeBaseDetail.tsx # 知识库详情
│   ├── DocumentViewer.tsx     # 文档查看器
│   ├── Chat.tsx               # 对话界面
│   ├── RetrievalTest.tsx      # 检索测试
│   ├── Settings.tsx           # 系统设置
│   ├── UploadDialog.tsx       # 上传对话框
│   └── ui/                    # UI 组件库
```

### 主要功能

#### 仪表盘
- 系统状态概览
- 知识库统计
- 最近活动

#### 知识库管理
- 创建/删除知识库
- 文档上传和管理
- 解析进度跟踪

#### 智能对话
- 流式输出
- 来源文档展示
- 历史对话记录

#### 检索测试
- 手动测试召回效果
- 相似度分数展示
- 文档内容预览

---

## ⚙️ 配置说明

### 后端配置 (.env)

```bash
# ============ 大模型服务配置 ============
API_KEY=sk-xxxxxxxxxxxxxxxx
MODEL_NAME=qwen3-vl-plus
MODEL_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ============ 向量嵌入服务配置 ============
EMBEDDING_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL_NAME=text-embedding-v4
EMBEDDING_API_KEY=sk-xxxxxxxxxxxxxxxx

# ============ 文件存储配置 ============
UPLOAD_BASE_DIR=/path/to/backend/output/uploads
EXTRACTION_RESULTS_DIR=/path/to/backend/output/extraction_results
MAX_FILE_SIZE_MB=50

# ============ Milvus 配置 ============
MILVUS_HOST=localhost
MILVUS_PORT=19530

# ============ 服务端口配置 ============
INFOR_EXTRAC_SERVICE_PORT=8006
CHUNK_SERVICE_PORT=8001
MILVUS_API_PORT=8000
CHAT_SERVICE_PORT=8501
```

### 前端配置 (.env)

```bash
# API 服务地址
VITE_MILVUS_API_URL=http://localhost:8000
VITE_CHAT_API_URL=http://localhost:8501
VITE_EXTRACTION_API_URL=http://localhost:8006
VITE_CHUNK_API_URL=http://localhost:8001
```

---

## 🔧 服务管理

### 启动脚本

```bash
cd backend

# 启动所有服务
./start_all_services.sh

# 停止所有服务
./stop_all_services.sh

# 重启所有服务
./restart_all_services.sh

# 查看服务状态
./status_services.sh

# 测试服务
./test_services.sh
```

### 日志管理

```bash
# 查看所有日志
tail -f backend/logs/*.log

# 查看单个服务日志
tail -f backend/logs/chat.log

# 清空日志
rm -rf backend/logs/*.log
```

### PID 管理

```bash
# 查看服务 PID
cat backend/pids/*.pid

# 停止特定服务
kill $(cat backend/pids/chat.pid)
```

---

## ❓ 常见问题

### 1. Milvus 启动失败

**问题**: Milvus 容器无法启动

**解决**:
```bash
# 检查 Docker 是否运行
docker ps

# 查看 Milvus 日志
cd Database/milvus_server
docker-compose logs

# 清理并重启
docker-compose down
docker-compose up -d
```

### 2. 端口被占用

**问题**: 服务启动时提示端口已被占用

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8006

# 杀死进程
kill -9 <PID>

# 或修改服务端口
# 编辑对应服务的 Python 文件，修改 port 参数
```

### 3. API Key 无效

**问题**: 调用 LLM 或 Embedding API 时返回认证错误

**解决**:
- 检查 `.env` 文件中的 `API_KEY` 和 `EMBEDDING_API_KEY`
- 确认阿里云百炼账号状态正常
- 检查 API 地址是否正确

### 4. 磁盘空间不足

**问题**: Milvus 的 etcd WAL 日志占用大量磁盘

**解决**:
```bash
# 定期清理 Milvus 数据
cd Database/milvus_server/volumes
rm -rf _etcd/*

# 或重新部署 Milvus
docker-compose down
rm -rf volumes/*
docker-compose up -d
```

### 5. 前端无法连接后端

**问题**: 前端请求后端 API 失败

**解决**:
- 检查后端服务是否正常运行 (`./status_services.sh`)
- 确认前端 `.env` 中的 API 地址正确
- 检查 CORS 配置 (后端已默认允许跨域)

---

## 📋 待办事项

### 功能增强

| 功能 | 优先级 | 状态 |
|-----|-------|------|
| 多知识库联合检索 | P1 | ⬜ 待开发 |
| 混合检索 (关键词 + 向量) | P1 | ⬜ 待开发 |
| 文档版本管理 | P2 | ⬜ 待开发 |
| 用户权限管理 | P2 | ⬜ 待开发 |
| 对话历史持久化 | P2 | ⬜ 待开发 |
| 批量文档上传 | P2 | ⬜ 待开发 |
| 文档自动分类 | P3 | ⬜ 待开发 |

### 性能优化

| 优化项 | 优先级 | 状态 |
|-------|-------|------|
| 向量检索缓存 | P1 | ⬜ 待开发 |
| 异步任务队列 | P1 | ⬜ 待开发 |
| 文档解析并行化 | P2 | ⬜ 待开发 |
| 前端懒加载 | P2 | ⬜ 待开发 |

### 文档完善

| 文档 | 优先级 | 状态 |
|-----|-------|------|
| API 详细文档 | P1 | ✅ 已完成 |
| 部署最佳实践 | P2 | ⬜ 待补充 |
| 故障排查指南 | P2 | ⬜ 待补充 |
| 性能调优指南 | P3 | ⬜ 待补充 |

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📞 联系方式

如有问题，请查看：
- [部署文档](部署文档.md)
- [服务管理指南](backend/README_SERVICES.md)
- 各服务的 `/docs` API 文档

---

**最后更新**: 2026-03-11
