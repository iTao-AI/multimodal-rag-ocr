# 更新日志 (CHANGELOG)

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

## [2.0.0] - 2026-04-09

### ✨ 重大更新

- **混合检索** - BM25 + 向量混合检索，检索精度显著提升
  - `hybrid_search_service.py` - 新增混合搜索服务
  - `search_enhanced.py` - 增强搜索端点
- **查询重写** - 基于 Qwen 模型的查询改写服务 (`query_rewrite_service.py`)
- **重排序** - Qwen3.5-Plus 重排序服务 (`rerank_service.py`)
- **流式输出** - kb_chat.py 支持流式/非流式输出 (81 行 → 924 行)
  - 异步处理、SSE 流式响应
  - 支持自定义 LLM/Reranker 配置
- **Redis 缓存** - 搜索结果缓存管理 (`cache_manager.py`)

### 🔧 配置变更

- 嵌入模型：`text-embedding-v4` → `text-embedding-v3`
- 新增阿里云百炼全套配置 (embedding/rerank/hybrid search)
- 新增混合检索权重配置 (BM25 0.3 + Vector 0.7)

### 📦 依赖新增

- `rank-bm25`、`jieba`（中文分词）、`scikit-learn`
- `redis`（缓存）、`python-dotenv`（配置管理）
- `fastapi` 锁定版本 0.119.0

### 📚 文档

- `IMPLEMENTATION_REPORT.md` - 实施报告
- `backend/IMPLEMENTATION_VECTOR_SEARCH.md` - 向量检索优化实施文档
- `backend/QUICKSTART.md` - 快速启动指南
- `backend/knowledge-base-api/test_vector_search.py` - 向量搜索测试

### 🗑️ 清理

- 移除冗余备份文件、日志文件
- 精简 `.gitignore`（去重）
- 移除未使用的 monitoring 配置
- 修复 CI 工作流配置

### 🔌 合并

- 合并 `iTao-AI/Multimodal_RAG` 仓库，整合向量检索优化功能

---

## [1.0.0] - 2026-03-11

### ✨ 新增功能
- **多模态 RAG 系统** - 完整的 PDF 文档解析、向量检索、智能问答
- **4 个后端服务**
  - PDF 提取服务 (端口 8006)
  - 文本切分服务 (端口 8001)
  - 向量数据库服务 (端口 8000)
  - 对话检索服务 (端口 8501)
- **前端界面** - React + TypeScript + shadcn/ui
- **知识库管理** - 文档上传、删除、检索
- **智能对话** - 支持多轮对话和历史记录

### 🔒 安全加固
- CORS 白名单配置（从 `*` 改为具体域名）
- .env 文件权限修复 (664 → 600)
- 请求限流集成 (slowapi)
  - 根路径：60 次/分钟
  - 健康检查：10 次/秒
  - 聊天接口：10 次/分钟
- API Key 集中管理

### ⚡ 性能优化
- Redis 缓存模块（可选）
- 日志轮转配置 (loguru, 10MB, 5 天)
- 配置集中管理 (config.py)
- 禁用 reload 模式（生产环境）

### 📚 文档
- README.md - 项目说明
- OPTIMIZATION_PLAN.md - 优化方案设计
- OPERATIONS.md - 运维手册
- API.md - 完整 API 文档
- CHANGELOG.md - 更新日志

### 🐛 Bug 修复
- 修复硬编码路径问题
- 修复 protobuf 版本冲突
- 修复 Milvus 连接配置

### 🔧 技术栈
- **后端**: FastAPI, SQLAlchemy, PyMilvus
- **前端**: React 18, TypeScript, Vite
- **数据库**: Milvus (向量), MySQL (元数据)
- **AI**: Qwen3-VL (多模态), text-embedding-v4
- **部署**: Docker, Docker Compose

---

## [0.1.0] - 2026-03-10

### ✨ 初始版本
- 项目初始化
- 基础架构搭建
- Git 仓库创建

---

## 版本说明

### 版本号格式
`主版本号。次版本号.修订号`

- **主版本号**: 不兼容的 API 变更
- **次版本号**: 向后兼容的功能新增
- **修订号**: 向后兼容的问题修正

### 发布类型
- **P0**: 紧急修复，立即发布
- **P1**: 重要功能，本周发布
- **P2**: 优化改进，迭代发布

---

## 未来计划

### v1.1.0 (计划中)
- [ ] Redis 缓存集成
- [ ] Prometheus 监控
- [ ] 性能测试报告
- [ ] Docker 镜像优化

### v1.2.0 (计划中)
- [ ] 多租户支持
- [ ] 权限管理
- [ ] 审计日志
- [ ] 高可用部署

### v2.0.0 (规划中)
- [ ] gRPC 服务间通信
- [ ] 分布式部署
- [ ] 自动扩缩容
- [ ] 混合检索优化

---

**维护者**: dev Agent  
**最后更新**: 2026-03-11
