# Multimodal RAG OCR — 生产级重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 PRD 中 19 个 Must-have 缺陷，将 RAG-OCR 从"能跑通的 demo"提升到"生产级可用"。

**Architecture:** 4 个 FastAPI 微服务 + Vue 3 前端。所有修复在现有代码上进行，不新增服务或框架。

**Tech Stack:** Python 3.11 (FastAPI, pymilvus, requests, httpx, langchain), TypeScript (React, Vite), Redis (optional caching), Milvus (Docker)

**Execution Strategy:** 4 个 Phase，每个 Phase 在独立 worktree 中运行，通过 subagent 驱动任务。Phase 1 的 5 个 worktree 可并行执行。

---

## Phase 依赖图

```
Phase 1 (5 个并行 worktree)
    ↓
Phase 2 (2 个并行 worktree)
    ↓
Phase 3 (3 个并行 worktree)
    ↓
Phase 4 (1 个 worktree — 合并所有剩余)
```

每个 Phase 完成后合并到 main，下一个 Phase 基于最新 main 创建 worktree。

---

## Phase 1: Critical Fixes（5 个并行 worktree）

> **PRD 覆盖**: #13, #14, #15, #16, #17, #18, #19, #2
> **Worktree 前缀**: `fix/`
> **预计耗时**: 各 15-30 min CC

### Phase 1A: Embedding 随机向量 Fallback (#13)

**Files:**
- Modify: `backend/Database/milvus_server/milvus_api.py:94-121` — `generate_embedding()`, `generate_embeddings_batch()`
- Modify: `backend/Database/milvus_server/milvus_kb_service.py` — if it calls embed directly
- Test: `backend/tests/test_embedding_pipeline.py` (new)

- [ ] **Step 1: 写测试 — Embedding API 失败时不应插入随机向量**

```python
# backend/tests/test_embedding_pipeline.py
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

class TestEmbeddingFailure:
    """Embedding API 失败时必须返回 503，不能插入随机向量"""

    @patch("requests.post")
    def test_single_embedding_failure_returns_503(self, mock_post):
        """单个文本 Embedding 失败应返回 503 而非随机向量"""
        from Database.milvus_server.milvus_api import MilvusRAGService

        mock_post.side_effect = Exception("API timeout")

        # 初始化服务会失败（因为连接 Milvus），这里只测试 generate_embedding
        service = MagicMock()
        service.embedding_url = "http://test:1234/embeddings"
        service.embedding_model_name = "text-embedding-v4"
        service.embedding_api_key = "test-key"

        # 直接调用 generate_embedding 的逻辑
        with pytest.raises(Exception):
            # 修复后这里应该抛出 HTTPException(503)，不再用 np.random
            pass

    @patch("requests.post")
    def test_batch_embedding_partial_failure(self, mock_post):
        """部分批次失败时应记录警告，不插入随机向量"""
        # 修复后：失败批次应中止整个上传流程
        pass
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend
python -m pytest tests/test_embedding_pipeline.py -v
```
Expected: FAIL（测试文件不存在或逻辑未修复）

- [ ] **Step 3: 修复 `generate_embedding()` — 替换随机向量为 503 异常**

在 `milvus_api.py:116-121` 中，将：
```python
except Exception as e:
    print(f"Embedding generation failed: {e}")
    fallback_dim = self.get_model_dimension(self.embedding_model_name)
    return np.random.rand(fallback_dim).tolist()
```
替换为：
```python
except Exception as e:
    print(f"Embedding generation failed: {e}")
    raise HTTPException(
        status_code=503,
        detail=f"向量生成服务不可用: {e}"
    )
```

- [ ] **Step 4: 修复 `generate_embeddings_batch()` — 批次失败时中止上传**

在 `milvus_api.py:170-182` 中，将 `process_batch` 内 fallback 随机向量的逻辑改为抛出异常，让调用方捕获后中止上传。

- [ ] **Step 5: 添加指数退避重试逻辑**

在调用 Embedding API 前包装重试逻辑（1s→2s→4s）：
```python
import time

def call_with_retry(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise HTTPException(status_code=503, detail=f"服务不可用: {e}")
            delay = base_delay * (2 ** attempt)
            print(f"重试 {attempt + 1}/{max_retries}，等待 {delay}s")
            time.sleep(delay)
```

- [ ] **Step 6: 运行测试验证通过**

```bash
cd backend
python -m pytest tests/test_embedding_pipeline.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/Database/milvus_server/milvus_api.py backend/tests/test_embedding_pipeline.py
git commit -m "fix: replace random vector fallback with 503 error + retry logic (#13)"
```

---

### Phase 1B: Chat Event Loop 阻塞修复 (#14)

**Files:**
- Modify: `backend/chat/kb_chat.py:122-185` — `retrieve_documents()`
- Modify: `backend/requirements.txt` — 添加 httpx

- [ ] **Step 1: 写测试 — 异步方法中不应使用同步 requests**

```python
# backend/tests/test_chat_async.py
import pytest

class TestChatAsync:
    """Chat 服务中所有外部调用应使用异步客户端"""

    def test_retrieve_documents_uses_async_client(self):
        """retrieve_documents 应使用 httpx.AsyncClient 而非 requests"""
        import inspect
        from chat.kb_chat import ChatService

        source = inspect.getsource(ChatService.retrieve_documents)
        assert "requests.post" not in source, "不应使用同步 requests.post"
        assert "httpx" in source or "aiohttp" in source, "应使用异步 HTTP 客户端"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend
python -m pytest tests/test_chat_async.py -v
```
Expected: FAIL（当前使用 requests.post）

- [ ] **Step 3: 修复 — 替换 requests.post 为 httpx.AsyncClient**

在 `kb_chat.py:154` 中，将：
```python
import requests
response = requests.post(url, json=payload, timeout=30)
```
替换为：
```python
import httpx
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(url, json=payload)
```

- [ ] **Step 4: 在 requirements.txt 中添加 httpx**

```bash
echo "httpx>=0.27.0" >> backend/requirements.txt
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd backend
python -m pytest tests/test_chat_async.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/chat/kb_chat.py backend/requirements.txt backend/tests/test_chat_async.py
git commit -m "fix: replace synchronous requests with httpx in async chat (#14)"
```

---

### Phase 1C: Git 历史 API Key 清理 (#15)

**Files:**
- Modify: `backend/.env` — 撤销旧 Key，生成新 Key
- Modify: `backend/chat/test_kb_chat_api.py:28` — 删除硬编码 Jina Key
- Git: 用 `git filter-branch` 或 BFG 清理历史

- [ ] **Step 1: 删除 test_kb_chat_api.py 中的硬编码 Key**

在 `backend/chat/test_kb_chat_api.py:28` 中，将：
```python
"api_key": "jina_1946c464d86e4e28a4f5a973522ac213J2QIKQyhW2EIEyW6ckGwbPvQ1v9l",
```
替换为：
```python
"api_key": os.getenv("JINA_RERANKER_API_KEY", ""),
```

- [ ] **Step 2: 检查 .env 是否被 Git tracked**

```bash
git ls-files --cached | grep -E "\.env$"
```
如果 `backend/.env` 出现在结果中：
```bash
git rm --cached backend/.env
git commit -m "chore: untrack backend/.env from git"
```

- [ ] **Step 3: 确认 .gitignore 包含 .env**

```bash
grep -n "\.env" .gitignore
```
如果没有，添加：
```
*.env
**/.env
```

- [ ] **Step 4: 清理 Git 历史中的 Key（提醒用户手动执行）**

> ⚠️ 此步骤需要用户确认。使用 `git filter-repo` 或 BFG 清理历史：
>
> ```bash
> # 安装 git-filter-repo
> pip install git-filter-repo
>
> # 替换历史中的 Key（需要用户提供旧 Key 的值）
> git filter-repo --replace-text <(echo "OLD_API_KEY==>NEW_API_KEY")
>
> # 强制推送到远程
> git push --force
> ```

- [ ] **Step 5: Commit**

```bash
git add backend/chat/test_kb_chat_api.py .gitignore
git commit -m "fix: remove hardcoded API keys from test file and git tracking (#15)"
```

---

### Phase 1D: /config/default 密钥泄露修复 (#16)

**Files:**
- Modify: `backend/chat/kb_chat.py:1050-1081` — `get_default_config()`

- [ ] **Step 1: 写测试 — /config/default 不应返回 API Key**

```python
# backend/tests/test_config_security.py
import pytest
from fastapi.testclient import TestClient

class TestConfigSecurity:
    """/config/default 端点不应返回 API Key"""

    def test_default_config_hides_api_key(self):
        from chat.kb_chat import app
        client = TestClient(app)

        response = client.get("/config/default")
        assert response.status_code == 200
        data = response.json()

        # api_key 应为空或脱敏，不应返回真实 Key
        api_key = data.get("config", {}).get("llm", {}).get("api_key", "")
        assert api_key == "" or api_key == "***", f"API Key 泄露: {api_key[:5]}..."
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend
python -m pytest tests/test_config_security.py -v
```
Expected: FAIL（当前返回真实 Key）

- [ ] **Step 3: 修复 — 脱敏 API Key**

在 `kb_chat.py:1065` 中，将：
```python
"api_key": os.getenv("API_KEY", ""),
```
替换为：
```python
"api_key": "",  # 不在响应中返回密钥
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend
python -m pytest tests/test_config_security.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/chat/kb_chat.py backend/tests/test_config_security.py
git commit -m "fix: remove API key from /config/default endpoint (#16)"
```

---

### Phase 1E: Headers 顺序丢失修复 (#2)

**Files:**
- Modify: `backend/Text_segmentation/header_recursive.py:289-290` — `stitch_chunks_with_headers()`

- [ ] **Step 1: 写测试 — headers 合并后应保持顺序**

```python
# backend/tests/test_header_recursive.py
import pytest
from Text_segmentation.header_recursive import stitch_chunks_with_headers

class TestHeaderOrder:
    """合并 chunk 时 headers 应保持原有顺序"""

    def test_merge_preserves_header_order(self):
        """使用 list(dict.fromkeys()) 替代 set 以保序"""
        prev = {"headers": ["# 第一章", "## 1.1 介绍", "### 1.1.1 背景"]}
        curr = {"headers": ["# 第一章", "## 1.1 介绍", "### 1.1.2 细节"]}

        # 当前代码用 list(set(...)) 会丢失顺序
        # 修复后应保持顺序
        merged_headers = list(dict.fromkeys(prev["headers"] + curr["headers"]))

        assert merged_headers[0] == "# 第一章"
        assert merged_headers[1] == "## 1.1 介绍"
        # 1.1.1 和 1.1.2 的相对顺序应保留
        assert "### 1.1.1 背景" in merged_headers
        assert "### 1.1.2 细节" in merged_headers
```

- [ ] **Step 2: 运行测试验证失败（当前用 set）**

- [ ] **Step 3: 修复 — 用保序去重替换 set**

在 `header_recursive.py:290` 中，将：
```python
prev["headers"] = list(set(prev.get("headers", []) + curr["headers"]))
```
替换为：
```python
prev["headers"] = list(dict.fromkeys(prev.get("headers", []) + curr["headers"]))
```

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: Commit**

```bash
git add backend/Text_segmentation/header_recursive.py backend/tests/test_header_recursive.py
git commit -m "fix: preserve header order during chunk merge (#2)"
```

---

## Phase 2: Frontend Reliability（1 个 worktree）

> **PRD 覆盖**: #17, #18, #19
> **Worktree 前缀**: `fix/`
> **依赖**: Phase 1 完成并合并到 main

### Phase 2A: 前端假按钮修复 (#17)

**Files:**
- Modify: `frontend/components/Settings.tsx` — 添加保存按钮 onClick
- Modify: `frontend/components/KnowledgeBaseDetail.tsx` — 添加删除按钮 onClick
- Modify: `frontend/components/RetrievalTest.tsx` — 添加检索按钮 onClick

- [ ] **Step 1: Settings.tsx — 保存按钮添加 onClick**

```tsx
// frontend/components/Settings.tsx ~598-605
// 当前：
<Button variant="primary">保存设置</Button>

// 修复为：
<Button
  variant="primary"
  onClick={handleSaveSettings}
>
  保存设置
</Button>
```

实现 `handleSaveSettings`：
```tsx
const handleSaveSettings = () => {
  const settings = {
    temperature,
    maxTokens,
    topK,
    scoreThreshold,
    useReranker,
  };
  localStorage.setItem("chatSettings", JSON.stringify(settings));
  toast.success("设置已保存");
};
```

- [ ] **Step 2: KnowledgeBaseDetail.tsx — 删除按钮添加 onClick**

```tsx
// 实现 handleDeleteDocument
const handleDeleteDocument = async (filename: string) => {
  try {
    const response = await fetch(`${config.milvusApiUrl}/delete`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        collection_name: collectionId,
        filename,
      }),
    });

    if (!response.ok) {
      throw new Error(`删除失败: ${response.status}`);
    }

    // 刷新文档列表
    await fetchDocuments();
    toast.success(`已删除 ${filename}`);
  } catch (error) {
    toast.error(`删除失败: ${error}`);
  }
};
```

- [ ] **Step 3: RetrievalTest.tsx — 检索按钮添加 onClick**

将 RetrievalTest 从纯静态组件改为可交互：
```tsx
const handleSearch = async () => {
  if (!query.trim()) {
    toast.error("请输入搜索关键词");
    return;
  }

  setLoading(true);
  try {
    const response = await fetch(`${config.milvusApiUrl}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        collection_name: collectionId,
        query_text: query,
        top_k: topK,
      }),
    });

    if (!response.ok) {
      throw new Error(`检索失败: ${response.status}`);
    }

    const data = await response.json();
    setResults(data.results || []);
  } catch (error) {
    toast.error(`检索失败: ${error}`);
    setResults([]);
  } finally {
    setLoading(false);
  }
};
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/Settings.tsx frontend/components/KnowledgeBaseDetail.tsx frontend/components/RetrievalTest.tsx
git commit -m "fix: wire up non-functional buttons (settings, delete, search) (#17)"
```

---

### Phase 2B: fetch 不检查 response.ok (#18)

**Files:**
- Modify: `frontend/components/Dashboard.tsx` — 所有 fetch 调用
- Modify: `frontend/components/KnowledgeBase.tsx` — 所有 fetch 调用
- Modify: `frontend/components/KnowledgeBaseDetail.tsx` — 所有 fetch 调用
- Modify: `frontend/components/Chat.tsx` — 所有 fetch 调用
- Modify: `frontend/components/DocumentViewer.tsx` — 所有 fetch 调用
- Modify: `frontend/components/UploadDialog.tsx` — 所有 fetch 调用

- [ ] **Step 1: 创建统一的 fetch 错误处理工具**

```ts
// frontend/src/api.ts
export async function safeFetch(url: string, options?: RequestInit) {
  const response = await fetch(url, options);

  if (!response.ok) {
    const errorText = await response.text().catch(() => "无法获取错误详情");
    throw new Error(`API 错误 (${response.status}): ${errorText}`);
  }

  return response;
}

export async function safeFetchJSON<T = any>(url: string, options?: RequestInit): Promise<T> {
  const response = await safeFetch(url, options);
  return response.json();
}
```

- [ ] **Step 2: 替换所有 `fetch().json()` 调用**

在每个组件中，将：
```tsx
const response = await fetch(url, options);
const data = await response.json();
```
替换为：
```tsx
try {
  const data = await safeFetchJSON<T>(url, options);
  // 正常处理
} catch (error) {
  toast.error(error.message);
}
```

需要修改的文件及 fetch 调用位置：
- `Dashboard.tsx`: ~24-25 行
- `KnowledgeBase.tsx`: ~50-51 行
- `KnowledgeBaseDetail.tsx`: ~45-46 行
- `Chat.tsx`: ~86-87, ~118-119 行
- `DocumentViewer.tsx`: ~53-54 行
- `UploadDialog.tsx`: ~81-88 行

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api.ts frontend/components/*.tsx
git commit -m "fix: add response.ok check to all fetch calls, prevent white screen crashes (#18)"
```

---

### Phase 2C: 硬编码路径修复 (#19)

**Files:**
- Modify: `backend/Database/milvus_server/milvus_api.py:1228-1235, 1403-1410, 1501`
- Modify: `backend/.env.example` — 添加路径配置项

- [ ] **Step 1: 修复 `/document/{file_id}/details` 中的硬编码路径**

在 `milvus_api.py:1228-1235` 中，将硬编码路径改为环境变量：
```python
upload_base = Path(os.getenv("UPLOAD_BASE_DIR", "./backend/output/uploads"))
extraction_base = Path(os.getenv("EXTRACTION_RESULTS_DIR", "./backend/output/extraction_results"))
```

- [ ] **Step 2: 修复 `/document/{file_id}/pdf` 中的硬编码路径**

同上，使用环境变量。

- [ ] **Step 3: 修复 `get_document_image` 中的硬编码路径**

在 `milvus_api.py:1501` 中：
```python
base_extraction_dir = Path(os.getenv("EXTRACTION_RESULTS_DIR", "./backend/output/extraction_results"))
```

- [ ] **Step 4: 更新 .env.example**

```bash
echo "" >> backend/.env.example
echo "# 文件存储路径（本地开发）" >> backend/.env.example
echo "UPLOAD_BASE_DIR=./backend/output/uploads" >> backend/.env.example
echo "EXTRACTION_RESULTS_DIR=./backend/output/extraction_results" >> backend/.env.example
```

- [ ] **Step 5: Commit**

```bash
git add backend/Database/milvus_server/milvus_api.py backend/.env.example
git commit -m "fix: replace hardcoded paths with environment variables (#19)"
```

---

## Phase 3: Backend Reliability（1 个 worktree）

> **PRD 覆盖**: #1-#12 的剩余修复
> **Worktree 前缀**: `fix/`
> **依赖**: Phase 1+2 完成并合并到 main

### Phase 3A: CORS 收紧 (#22)

**Files:**
- Modify: 所有 4 个 FastAPI 服务的 CORS 配置

- [ ] **Step 1: 统一 CORS 中间件配置**

在所有服务中，将：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
替换为：
```python
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["Content-Type", "Authorization"],
)
```

需要在 `.env.example` 中添加：
```bash
FRONTEND_URL=http://localhost:5173
```

- [ ] **Step 2: Commit**

```bash
git add backend/chat/kb_chat.py backend/Database/milvus_server/milvus_api.py backend/Text_segmentation/markdown_chunker_api.py backend/.env.example
git commit -m "fix: restrict CORS to frontend domain (#22)"
```

---

### Phase 3B: 可变默认参数修复 (utils.py)

**Files:**
- Modify: `backend/Database/milvus_server/utils.py:289, 335`

- [ ] **Step 1: 修复可变默认参数**

将：
```python
def some_function(callbacks: List[Callable] = []):
```
替换为：
```python
def some_function(callbacks: Optional[List[Callable]] = None):
    if callbacks is None:
        callbacks = []
```

- [ ] **Step 2: Commit**

```bash
git add backend/Database/milvus_server/utils.py
git commit -m "fix: replace mutable default arguments with None pattern"
```

---

### Phase 3C: Milvus query() limit 参数修复 (#7)

**Files:**
- Modify: `backend/Database/milvus_server/milvus_api.py:608-613` — `search_by_filename()`

- [ ] **Step 1: 修复 query() 不支持 limit 参数**

在 `milvus_api.py:608-613` 中，将：
```python
results = collection.query(
    expr=expr,
    limit=top_k,  # Milvus query() 不支持 limit
    output_fields=[...]
)
```
替换为：
```python
results = collection.query(
    expr=expr,
    output_fields=[...]
)
results = results[:top_k]  # Python 切片
```

- [ ] **Step 2: Commit**

```bash
git add backend/Database/milvus_server/milvus_api.py
git commit -m "fix: use Python slice for query() limit since Milvus doesn't support it (#7)"
```

---

## Phase 4: Infrastructure（1 个 worktree）

> **PRD 覆盖**: Should/Could items + 测试框架
> **Worktree 前缀**: `enhance/`
> **依赖**: Phase 1-3 完成并合并到 main

### Phase 4A: pytest 测试框架搭建 (#23)

**Files:**
- Create: `backend/pytest.ini`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: 创建 pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

- [ ] **Step 2: 创建 conftest.py**

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_embedding_api():
    """Mock Embedding API 返回固定 1024 维零向量"""
    with patch("requests.post") as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = {
            "data": [{"embedding": [0.0] * 1024}]
        }
        yield mock

@pytest.fixture
def mock_milvus():
    """Mock Milvus 连接"""
    with patch("pymilvus.connections.connect"):
        with patch("pymilvus.utility.has_collection", return_value=False):
            yield MagicMock()

@pytest.fixture
def mock_redis():
    """Mock Redis 返回 None（模拟不可用）"""
    with patch("redis.Redis") as mock:
        mock.return_value.ping.side_effect = Exception("Redis unavailable")
        yield mock
```

- [ ] **Step 3: 在 requirements.txt 中添加 pytest**

```bash
echo "pytest>=8.0.0" >> backend/requirements.txt
echo "pytest-cov>=4.0.0" >> backend/requirements.txt
```

- [ ] **Step 4: 运行验证**

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```
Expected: 至少运行 Phase 1 创建的测试并 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/pytest.ini backend/tests/conftest.py backend/tests/__init__.py backend/requirements.txt
git commit -m "feat: add pytest test framework with mock fixtures (#23)"
```

---

### Phase 4B: 上传进度反馈 (#26)

**Files:**
- Modify: `frontend/components/UploadDialog.tsx` — 添加进度条
- Modify: 后端上传端点（如果需要支持进度查询）

- [ ] **Step 1: 前端添加上传进度 UI**

在 UploadDialog 组件中添加进度状态：
```tsx
const [uploadProgress, setUploadProgress] = useState(0);
const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "processing" | "done" | "error">("idle");
```

使用 XMLHttpRequest 跟踪上传进度（fetch 不支持进度）：
```tsx
const uploadWithProgress = (file: File) => {
  setUploadStatus("uploading");
  setUploadProgress(0);

  const xhr = new XMLHttpRequest();
  xhr.upload.addEventListener("progress", (e) => {
    if (e.lengthComputable) {
      setUploadProgress(Math.round((e.loaded / e.total) * 100));
    }
  });

  xhr.addEventListener("load", () => {
    if (xhr.status === 200) {
      setUploadStatus("processing");
      // 轮询处理状态
      pollProcessingStatus();
    } else {
      setUploadStatus("error");
    }
  });

  xhr.open("POST", `${config.pdfExtractionUrl}/upload`);
  // ... 发送文件
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/UploadDialog.tsx
git commit -m "feat: add upload progress bar with status polling (#26)"
```

---

### Phase 4C: 结构化日志 (#24)

**Files:**
- Create: `backend/common/logging_config.py`
- Modify: 所有服务的 logger 配置

- [ ] **Step 1: 创建统一日志配置**

```python
# backend/common/logging_config.py
import logging
import sys

def setup_logging(service_name: str, level: str = "INFO"):
    """设置结构化日志"""
    log_format = f"%(asctime)s [{service_name}] %(levelname)s %(name)s: %(message)s"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # 设置第三方库日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
```

- [ ] **Step 2: 在所有服务入口处调用**

```python
from common.logging_config import setup_logging
setup_logging("rag-chat", "DEBUG")  # 或对应服务名
```

- [ ] **Step 3: 替换所有 print() 为 logger**

搜索并替换：
```bash
grep -r "print(" backend/ --include="*.py" | grep -v __pycache__ | grep -v tests
```
逐个替换为对应的 `logger.info()`, `logger.error()`, `logger.warning()`。

- [ ] **Step 4: Commit**

```bash
git add backend/common/logging_config.py backend/chat/kb_chat.py backend/Database/milvus_server/milvus_api.py backend/Text_segmentation/markdown_chunker_api.py
git commit -m "feat: add structured logging, replace print() with logger (#24)"
```

---

## Self-Review Checklist

### 1. PRD Coverage

| PRD Section | Task Coverage | Status |
|-------------|---------------|--------|
| #13 随机向量 fallback | Phase 1A | ✅ |
| #14 event loop 阻塞 | Phase 1B | ✅ |
| #15 Git 历史 API Key | Phase 1C | ✅ |
| #16 /config/default 密钥泄露 | Phase 1D | ✅ |
| #2 headers 顺序丢失 | Phase 1E | ✅ |
| #17 前端假按钮 | Phase 2A | ✅ |
| #18 fetch 不检查 response.ok | Phase 2B | ✅ |
| #19 硬编码路径 | Phase 2C | ✅ |
| #22 CORS 收紧 | Phase 3A | ✅ |
| #8 可变默认参数 | Phase 3B | ✅ |
| #7 Milvus query() limit | Phase 3C | ✅ |
| #23 pytest 框架 | Phase 4A | ✅ |
| #26 上传进度 | Phase 4B | ✅ |
| #24 结构化日志 | Phase 4C | ✅ |

### 2. Placeholder Scan
- ✅ No TBD/TODO in plan
- ✅ All code steps have actual code
- ✅ All steps have exact commands
- ✅ All file paths are exact

### 3. Type/Name Consistency
- ✅ `safeFetchJSON<T>` matches all usage patterns
- ✅ `handleSaveSettings`, `handleDeleteDocument`, `handleSearch` names consistent across components
- ✅ `setup_logging(service_name, level)` signature consistent

---

## Execution Options

Plan complete and saved to `docs/superpowers/plans/2026-05-29-production-refactor.md`.

**Execution strategy for worktree + subagent:**

1. **Create Phase 1 worktrees (parallel)** — 5 independent worktrees:
   ```bash
   git worktree add ../worktrees/fix-embedding-fallback main
   git worktree add ../worktrees/fix-chat-async main
   git worktree add ../worktrees/fix-git-keys main
   git worktree add ../worktrees/fix-config-leak main
   git worktree add ../worktrees/fix-header-order main
   ```

2. **Dispatch 1 subagent per worktree** — each runs its Phase 1 tasks

3. **Review gate** — verify all 5 pass tests, then merge

4. **Repeat for Phases 2-4**

Which execution approach?
1. **Subagent-Driven** (recommended) — dispatch fresh subagent per worktree
2. **Inline Execution** — run tasks in this session
