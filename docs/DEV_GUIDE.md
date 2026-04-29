# 开发指南

> 面向贡献者的开发入门文档。首次搭建环境、新增功能、调试排错，从这里开始。

---

## 一、环境搭建

### 1.1 前置条件

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.11 | 后端运行时 |
| Node.js | 18+ | 前端运行时 |
| Docker + Compose | 最新 | Milvus + Redis 部署 |
| Conda | 最新 | Python 虚拟环境管理 |

### 1.2 后端环境

```bash
# 创建并激活 conda 环境
conda create -n vlm_rag python=3.11
conda activate vlm_rag

# 安装依赖
cd backend
pip install -r requirements.txt
```

### 1.3 前端环境

```bash
cd frontend
npm install
```

### 1.4 Milvus 部署

```bash
cd backend/Database/milvus_server
docker compose -f docker-compose.yaml up -d
```

**重要**: Milvus 不使用 `restart: always`。关闭后需要手动重新启动。

### 1.5 环境变量

```bash
# 后端
cp backend/.env.example backend/.env  # 如果没有，手动创建
# 编辑 backend/.env，填入 API Key 和路径

# 前端
cp frontend/env.template frontend/.env
```

---

## 二、启动服务

### 2.1 一键启动后端

```bash
cd backend
./start_all_services.sh
```

启动后的服务列表：

| 服务 | 端口 | 健康检查 |
|------|------|---------|
| PDF 提取 | 8006 | `curl http://localhost:8006/health` |
| 文本切分 | 8001 | `curl http://localhost:8001/health` |
| Milvus API | 8000 | `curl http://localhost:8000/health` |
| 对话服务 | 8501 | `curl http://localhost:8501/health` |

### 2.2 启动前端

```bash
cd frontend
npm run dev
# → http://localhost:5173
```

### 2.3 停止服务

```bash
cd backend
./stop_all_services.sh

# 停止 Milvus
cd Database/milvus_server
docker compose -f docker-compose.yaml down
```

### 2.4 查看状态

```bash
cd backend
./status_services.sh
```

### 2.5 查看日志

```bash
# 所有日志
tail -f backend/logs/*.log

# 单个服务日志
tail -f backend/logs/chat.log
tail -f backend/logs/pdf_extraction.log
tail -f backend/logs/chunker.log
tail -f backend/logs/milvus_api.log
```

---

## 三、开发工作流

### 3.1 本地调试单个服务

不需要走 `start_all_services.sh`，可以直接启动单个服务：

```bash
# PDF 提取服务
cd backend/Information-Extraction/unified
python unified_pdf_extraction_service.py

# 文本切分服务
cd backend/Text_segmentation
python markdown_chunker_api.py

# Milvus API
cd backend/Database/milvus_server
python milvus_api.py

# 对话服务
cd backend/chat
python kb_chat.py
```

### 3.2 前端开发

```bash
cd frontend
npm run dev
```

Vite 配置了 `open: true`，会自动打开浏览器。修改代码后 HMR 自动刷新。

### 3.3 构建生产前端

```bash
cd frontend
npm run build
# 输出到 frontend/dist/
```

---

## 四、目录结构

### 4.1 后端

```
backend/
├── Information-Extraction/
│   └── unified/
│       ├── unified_pdf_extraction_service.py   # PDF 提取服务入口
│       ├── llm_extraction.py                   # VLM 提取逻辑
│       ├── ocr_v2_extractors.py                # V2.0 OCR 适配器
│       └── prompt.py                           # 提取 Prompt 模板
│
├── Text_segmentation/
│   ├── markdown_chunker_api.py                 # 切分服务入口
│   ├── header_recursive.py                     # 递归标题切分算法
│   └── MarkdownTextSplitter.py                 # LangChain 风格切分
│
├── Database/milvus_server/
│   ├── milvus_api.py                           # Milvus HTTP API
│   ├── milvus_kb_service.py                    # Milvus 操作封装
│   ├── localai_embeddings.py                   # 本地 Embedding 备选
│   ├── utils.py                                # 工具函数
│   ├── collection_name_mapping.json            # 集合映射
│   └── docker-compose.yaml                     # Milvus 部署
│
├── chat/
│   ├── kb_chat.py                              # 对话服务 (V2.1 增强)
│   ├── query_rewrite.py                        # 查询改写服务 (V2.1)
│   └── test_kb_chat_api.py                     # 测试脚本
│
├── common/
│   ├── __init__.py
│   └── cache_manager.py                        # Redis 缓存管理 (V2.1)
│
├── Database/milvus_server/
│   ├── milvus_api.py                           # Milvus HTTP API
│   ├── milvus_kb_service.py                    # Milvus 操作封装
│   ├── hybrid_search.py                        # BM25 混合检索 (V2.1)
│   ├── localai_embeddings.py                   # 本地 Embedding 备选
│   ├── utils.py                                # 工具函数
│   ├── collection_name_mapping.json            # 集合映射
│   └── docker-compose.yaml                     # Milvus 部署
│
├── .env                                        # 环境变量
├── requirements.txt                            # Python 依赖
├── start_all_services.sh                       # 启动脚本
├── stop_all_services.sh                        # 停止脚本
├── status_services.sh                          # 状态脚本
└── logs/                                       # 日志目录 (gitignore)
```

### 4.2 前端

```
frontend/
├── App.tsx                                     # 根组件
├── main.tsx                                    # 入口
├── index.html                                  # HTML 模板
├── components/
│   ├── Sidebar.tsx                             # 侧边导航
│   ├── Header.tsx                              # 顶部栏
│   ├── Dashboard.tsx                           # 仪表盘
│   ├── KnowledgeBase.tsx                       # 知识库列表
│   ├── KnowledgeBaseDetail.tsx                 # 知识库详情
│   ├── DocumentViewer.tsx                      # 文档查看
│   ├── Chat.tsx                                # 对话界面
│   ├── RetrievalTest.tsx                       # 检索测试
│   ├── Settings.tsx                            # 设置
│   ├── UploadDialog.tsx                        # 上传对话框
│   ├── ConfirmDialog.tsx                       # 确认对话框
│   └── ui/                                     # shadcn/ui 基础组件
├── styles/
│   ├── globals.css                             # 全局样式 (Tailwind)
│   └── index.css                               # 入口样式
├── vite.config.ts                              # Vite 配置
├── tailwind.config.ts                          # Tailwind 配置
├── postcss.config.js                           # PostCSS 配置
├── tsconfig.json                               # TypeScript 配置
├── env.template                                # 环境变量模板
└── package.json                                # 依赖
```

---

## 五、新增功能指南

### 5.1 新增 PDF 解析器

1. 在 `backend/Information-Extraction/unified/ocr_v2_extractors.py` 中添加解析函数：

```python
def parse_with_new_ocr(file_path: str) -> str:
    """使用新的 OCR 引擎解析 PDF"""
    response = requests.post(
        "http://new-ocr-api:port/parse",
        files={"file": open(file_path, "rb")}
    )
    return response.json()["markdown"]
```

2. 在 `unified_pdf_extraction_service.py` 的路由中注册新入口

3. 在 `backend/.env` 中添加新 OCR 的 API 地址

### 5.2 新增 Reranker Provider

在 `backend/chat/kb_chat.py` 的 `rerank_documents` 方法中：

```python
elif "new-provider" in base_url:
    # 新 provider
    response = requests.post(
        f"{base_url}/rerank",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "query": query, "documents": texts}
    )
    scores = [r["score"] for r in response.json()["results"]]
```

### 5.3 新增前端页面

1. 在 `frontend/components/` 创建新组件 `NewPage.tsx`
2. 在 `frontend/App.tsx` 中添加视图切换逻辑
3. 在侧边栏 `frontend/components/Sidebar.tsx` 中添加导航入口

### 5.4 新增 API 端点

以 Milvus API 为例，在 `milvus_api.py` 中：

```python
@app.post("/api/new_endpoint")
async def new_endpoint(request: NewRequestModel):
    """端点描述"""
    try:
        result = await do_something(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

记得在文件顶部添加对应的 Pydantic 模型。

---

## 六、调试技巧

### 6.1 服务启动失败

```bash
# 检查端口占用
lsof -i :8000

# 检查日志
cat backend/logs/pdf_extraction.log

# 检查 Python 依赖
pip list | grep fastapi

# 检查 Milvus 状态
cd backend/Database/milvus_server
docker compose ps
```

### 6.2 向量检索结果为空

排查步骤：
1. 确认 Collection 存在且有数据：`curl http://localhost:8000/api/collections/kb_xxx/stats`
2. 确认 Embedding API 正常：检查 `backend/logs/milvus_api.log`
3. 确认查询文本不为空
4. 尝试增大 `top_k`

### 6.3 对话服务报错

1. 检查 LLM API Key 是否有效
2. 检查 `kb_chat.py` 日志中的 traceback
3. 确认 Milvus API 可访问（对话服务内部调用 `:8000`）

### 6.4 前端白屏

1. 检查浏览器 DevTools Console 是否有 CORS 错误
2. 确认后端服务已启动（`./status_services.sh`）
3. 检查 `frontend/.env` 中的 API 地址是否正确

---

## 七、代码规范

### 7.1 Python

- 使用 FastAPI 标准模式：Pydantic models + async/await
- 错误统一使用 `HTTPException(status_code, detail)`
- 新代码使用 `logging` 模块，不用 `print()`

### 7.2 TypeScript/React

- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- 样式使用 TailwindCSS 类名
- 新组件放在 `components/` 目录下，shadcn/ui 组件放在 `components/ui/` 下

---

## 八、测试

### 8.1 现有测试脚本

```bash
# Milvus API 测试
cd backend/Database/milvus_server
python test_milvus_api.py

# 对话 API 测试
cd backend/chat
python test_kb_chat_api.py

# PDF 提取测试
cd backend/Information-Extraction/unified
python repose_test_extraction.py

# 文本切分测试
cd backend/Text_segmentation
python repose_test_segmentation.py
```

这些是手动运行的脚本，需要服务先启动。未来应迁移到 pytest。

---

## 九、发布流程

```bash
# 1. 确认所有服务正常
cd backend && ./status_services.sh

# 2. 前端构建
cd frontend && npm run build

# 3. 提交代码
git add -A
git commit -m "描述变更内容"

# 4. 推送到远端
git push
```
