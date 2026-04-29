# 文档索引

Multimodal RAG OCR 项目文档集。按阅读顺序排列。

> 最近更新：2026-04-09 (V2.1: 检索增强)

---

## 推荐阅读顺序

| # | 文档 | 目标读者 | 阅读时间 |
|---|------|---------|---------|
| 1 | [项目概览](./PROJECT_OVERVIEW.md) | 所有人 | 20 min |
| 2 | [API 参考](./API_REFERENCE.md) | 前后端开发者 | 10 min |
| 3 | [开发指南](./DEV_GUIDE.md) | 搭建环境/写代码的人 | 15 min |
| 4 | [算法详解](./ALGORITHM_DEEP_DIVE.md) | 想深入理解核心逻辑的人 | 30 min |
| 5 | [面试准备](./INTERVIEW_PREP.md) | 准备用此项目面试的人 | 30 min |
| 6 | [改进路线图](./ROADMAP.md) | 计划改进项目的人 | 10 min |

## V2.1 新增内容

| 组件 | 文件 | 说明 |
|------|------|------|
| Query Rewrite | `backend/chat/query_rewrite.py` | LLM 生成查询变体，提升召回率 |
| BM25 混合检索 | `backend/Database/milvus_server/hybrid_search.py` | 向量分 + 关键词分融合 |
| Redis 缓存 | `backend/common/cache_manager.py` | 查询结果缓存，TTL 1 小时 |
| 集成改动 | `backend/chat/kb_chat.py` | 流式/非流式都已接入 3 组件 |
| 配置 | `backend/.env` | +11 项 V2.1 环境变量 |
| 依赖 | `backend/requirements.txt` | +rank-bm25, jieba, redis |

---

## 快速查询

### 我想了解...

| 主题 | 跳转 |
|------|------|
| 系统整体架构 | [项目概览 → 第二节](./PROJECT_OVERVIEW.md#二整体架构) |
| 上传一个 PDF 的全流程 | [项目概览 → 第三节](./PROJECT_OVERVIEW.md#三核心数据流) |
| 某个 API 怎么调用 | [API 参考](./API_REFERENCE.md) |
| 怎么启动服务 | [开发指南 → 第二节](./DEV_GUIDE.md#二启动服务) |
| 文本切分算法细节 | [算法详解 → 第一节](./ALGORITHM_DEEP_DIVE.md#一header-recursive-文本切分算法) |
| Reranker 怎么工作 | [算法详解 → 第二节](./ALGORITHM_DEEP_DIVE.md#二reranker-算法) |
| 向量检索和 Embedding | [算法详解 → 第三节](./ALGORITHM_DEEP_DIVE.md#三向量检索与-embedding) |
| 面试怎么介绍项目 | [面试准备](./INTERVIEW_PREP.md) |
| 下一步改进计划 | [改进路线图](./ROADMAP.md) |

---

## 其他资源

| 资源 | 路径 | 说明 |
|------|------|------|
| 运维记录 | `OPERATIONS.md` | Milvus 事故、部署经验 |
| 后端环境变量 | `backend/.env` | 所有配置项（含注释） |
| 前端环境变量模板 | `frontend/env.template` | 前端配置模板 |
| Python 依赖 | `backend/requirements.txt` | 后端依赖清单 |
| Node 依赖 | `frontend/package.json` | 前端依赖清单 |
| 项目级配置 | `CLAUDE.md` | AI 辅助开发指南 |
| Git 忽略规则 | `.gitignore` | 不提交的文件列表 |

---

## 文档维护

- 文档与实际代码不一致时，以代码为准，更新文档
- 新增 API 端点时同步更新 [API 参考](./API_REFERENCE.md)
- 修复 Bug 后评估是否更新 [算法详解](./ALGORITHM_DEEP_DIVE.md)
- 完成改进阶段后更新 [改进路线图](./ROADMAP.md)
