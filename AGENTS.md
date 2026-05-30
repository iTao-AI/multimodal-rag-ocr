# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 项目 WHAT
多模态 RAG OCR 知识库系统——用户上传 PDF，自动解析/切分/建索引，支持自然语言问答与混合检索。

## 项目 WHY
从"能跑通的 demo"提升到"生产级可用"，修复 25 个已知代码缺陷，建立可持续迭代的工程实践。详见 @specs/prd.md。

## 工作流 HOW

```
① 启动 feature    → 在 specs/00X-<slug>/ 下跑 /speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks
② task 启动必读    → @.specify/memory/constitution.md + @specs/00X-*/spec.md + @specs/00X-*/plan.md
③ 测试纪律         → 用 Skill("superpowers:test-driven-development")，纯函数写单元，接口写集成（Mock 外部 API）
④ feature 完成     → 跑验证 gate（机械：测试/构建/ lint；语义：完整性/正确性/一致性），commit 后进入下一个
⑤ 节奏铁律         → PRD 的 Must-have 必须先过测试再 merge；Should/Could 可带 TODO merge
```

## 技术栈

| 层 | 技术 | 版本 |
|---|------|------|
| OCR | PyMuPDF4LLM + MinerU / PaddleOCR-VL / DeepSeek-OCR | 0.0.27 |
| 后端 | FastAPI + Uvicorn | 0.119.0 / 0.37.0 |
| 向量库 | Milvus + pymilvus | 2.6.2 |
| 嵌入 | text-embedding-v4 (DashScope) | — |
| 检索 | BM25 (rank-bm25 + jieba) + Redis 缓存 | — |
| LLM | Qwen3-VL-Plus (DashScope) | — |
| 前端 | React + Vite + TypeScript | ^18.3.1 / ^6.0.3 / ^5.6.3 |
| UI | Radix UI + TailwindCSS | — |

## 命令清单

| 用途 | 命令 |
|------|------|
| 启动后端全部 | `cd backend && ./start_all_services.sh` |
| 停止后端 | `cd backend && ./stop_all_services.sh` |
| 启动 Milvus | `cd backend/Database/milvus_server && docker compose -f docker-compose.yaml up -d` |
| 停止 Milvus | `docker compose -f docker-compose.yaml down` |
| 启动前端 | `cd frontend && npm run dev` |
| 前端构建 | `cd frontend && npm run build` |
| 前端 lint | `cd frontend && npm run lint` |

## 约束

1. Milvus 禁用 `restart: always`（etcd WAL 日志占满磁盘）
2. 本地 Mac 无 GPU，V2.0 OCR 需远程 GPU（AutoDL）
3. Python 3.11 conda 环境 `vlm_rag`
4. API Key 只存 `backend/.env`，不提交 Git

## 项目宪法

遵循 @.specify/memory/constitution.md 的 6 条核心原则（Test-First / No Silent Failures / Explicit Over Clever / Security-First / Graceful Degradation / Frontend Defaults）。

## Anti-Patterns（禁止）

- 插入随机向量作为 API 失败 fallback（永久污染知识库）
- `async def` 内用同步 `requests.post()`（阻塞 event loop）
- `except Exception` 后只 `print` 不记录/不降级
- `allow_origins=["*"]` 与 `allow_credentials=True` 同用
- `fetch().json()` 不检查 `response.ok`（500 非 JSON 时组件崩溃）
- 在 Git 历史中提交 API Key
- 删除与自己改动无关的 dead code
- 前端持有或传输 LLM API Key

## Behavioral Guidelines (Karpathy-Inspired)

以下 4 条原则适用于全项目所有 task 实现期，目的是减少 AI 编码的常见失误。

### 1. Think Before Coding
**Don't assume. Don't hide confusion. Surface tradeoffs.**
Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First
**Minimum code that solves the problem. Nothing speculative.**
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
If you write 200 lines and it could be 50, rewrite it.

### 3. Surgical Changes
**Touch only what you must. Clean up only your own mess.**
When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.
The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution
**Define success criteria. Loop until verified.**
Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

## 关键文件导航

| 文件 | 何时读 |
|------|--------|
| @specs/prd.md | 任何新功能/修复前，确认 WHAT/WHY/验收标准 |
| @.specify/memory/constitution.md | 每次 task 启动，确认遵循哪条原则 |
| @AGENTS.md | 本文件，每次工作前确认项目上下文 |
| @specs/00X-*/spec.md | 执行具体 feature 时 |
| @docs/PROJECT_OVERVIEW.md | 了解项目技术细节时 |
| @docs/ROADMAP.md | 了解项目改进路线和优先级时 |

## 远程仓库
`git@github.com:iTao-AI/multimodal-rag-ocr.git`
