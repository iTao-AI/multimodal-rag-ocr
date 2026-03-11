# Multimodal RAG - 多模态检索增强生成系统

> 🤖 基于 Milvus 向量数据库 + Qwen3-VL 大模型  
> 支持 PDF 文档解析、智能问答、知识库管理

---

## 📖 项目简介

本项目是一个完整的多模态 RAG（检索增强生成）系统，支持：
- 📄 PDF 文档智能解析
- 🔍 向量检索 + 重排序
- 💬 智能问答对话
- 📚 知识库管理

---

## 🏗️ 项目结构

```
Multimodal_RAG/
├── backend/              # 后端服务
│   ├── Database/        # Milvus 向量数据库
│   ├── Information-Extraction/  # PDF 解析服务
│   ├── Text_segmentation/       # 文本切分服务
│   ├── chat/            # 对话检索服务
│   └── knowledge-*      # 知识库管理
├── frontend/            # 前端界面
├── README.md           # 项目说明
└── 部署文档.md         # 部署指南
```

---

## 🚀 快速开始

### 后端服务

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动所有服务
./start_all_services.sh

# 查看状态
./status_services.sh
```

### 前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

---

## 📋 服务列表

| 服务 | 端口 | 功能 |
|------|------|------|
| PDF 提取 | 8006 | PDF 文档解析 |
| 文本切分 | 8001 | Markdown 文本切分 |
| 向量数据库 | 8000 | Milvus 存储与检索 |
| 对话检索 | 8501 | RAG 对话、LLM 生成 |

---

## ⚠️ Milvus 使用注意

**重要**：Milvus 的 etcd 组件 WAL 日志可能疯涨，建议：
- 定期清理磁盘
- 用完即停服务
- 监控磁盘占用

---

## 📖 文档

- [服务管理指南](backend/README_SERVICES.md)
- [部署文档](部署文档.md)

---

**最后更新**: 2026-03-11
