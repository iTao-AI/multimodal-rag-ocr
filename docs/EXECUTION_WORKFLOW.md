# Subagent + Worktree 执行流程模板

> 本文档可复用于任何基于 implementation plan 的多 Phase 并行开发流程。
>
> **v4 核心原则**：Subagent 只管写代码，Skill 调用全部由用户手动执行。全流程可控、可验证。

---

## 架构：谁负责什么

| 步骤 | 谁执行 | 说明 |
|------|--------|------|
| ① 创建 worktree | 主 Agent | `git worktree add` |
| ② 派发 subagent 写代码 | Subagent | 只负责读文件、改代码、不 commit |
| ③ **TDD 写测试** | **用户手动执行** | `superpowers:test-driven-development` |
| ④ subagent 实现代码 | Subagent | 根据 TDD 指导写实现 |
| ⑤ **代码审查** | **用户手动执行** | `superpowers:requesting-code-review` |
| ⑥ **完成前验证** | **用户手动执行** | `superpowers:verification-before-completion` |
| ⑦ commit | 用户手动或让 subagent 执行 | 所有 Skill 通过后 |
| ⑧ /ship + 合并 | 主 Agent | `git worktree remove` + `git worktree prune` |

---

## 可用 Skills 清单

### 核心 Skills（由用户在 subagent 停顿时手动调用）

| Skill | 用途 | 触发时机 |
|-------|------|----------|
| `superpowers:test-driven-development` | TDD 流程 | 每个 Task 开始，subagent 停顿时 |
| `superpowers:verification-before-completion` | 完成前自动验证 | 全部 task 完成后 |
| `superpowers:requesting-code-review` | 发起 code review | commit 前 |
| `superpowers:receiving-code-review` | 响应 review 反馈 | 收到 review 意见后 |

### 阶段 Skills（主 agent 调用）

| Skill | 用途 | 触发时机 |
|-------|------|----------|
| `superpowers:using-git-worktrees` | 隔离 worktree | Phase 开始时 |
| `superpowers:finishing-a-development-branch` | 分支合并 + 清理 | worktree 任务全部完成后 |
| `/review` | diff 审查 | merge 前 |
| `/ship` | 创建 PR + 合并到 main | 代替手动 merge |
| `/health` | 代码质量打分 | Phase 开始前 + 合并后 |

### 按需 Skills

| Skill | 用途 | 何时使用 |
|-------|------|----------|
| `/qa` | 前端 QA | 涉及前端 UI 变更 |
| `/investigate` | 根因调查 | 无法定位的 bug |
| `/cso` | 安全审计 | 密钥、鉴权、CORS |

---

## 执行前准备

- [ ] PRD 已完成：`specs/prd.md`
- [ ] Implementation Plan 已完成
- [ ] 当前分支为 `main`，工作区干净
- [ ] 清理旧 worktree 和分支：
  ```bash
  git worktree prune
  git branch -D fix/* enhance/*
  rm -rf ../worktrees/*
  ```
- [ ] 调用 `/health` 记录 baseline

---

## Subagent Prompt 模板（v4 — 停顿模式）

```
你是本项目的实现工程师，正在执行 [Phase 名称] 的开发任务。

## 工作环境
- 工作目录：../worktrees/<worktree-name>/
- 分支：<branch-name>（worktree 自动创建）
- Python 环境：conda activate vlm_rag

## 必读文件
1. specs/prd.md
2. .specify/memory/constitution.md
3. CLAUDE.md

## 工作模式（CRITICAL — 与之前不同）

你负责写代码，Skill 调用由用户手动执行。流程如下：

### 每个 Task 的步骤

**Step 1 — 你写测试 stub**
- 创建测试文件（如 backend/tests/test_xxx.py）
- 写好测试用例的骨架，但暂时不运行
- **完成后停下来**，报告："Task X 测试 stub 已写好，请运行 TDD skill"

**Step 2 — 等待用户运行 TDD**
- 用户运行 `superpowers:test-driven-development`
- 用户告诉你测试结果（RED → GREEN → REFACTOR）
- 根据结果写实现代码或修复测试

**Step 3 — 你实现代码**
- 写最小实现让测试通过
- **完成后停下来**，报告："Task X 实现完成，请运行 review"

**Step 4 — 等待用户运行 Code Review**
- 用户运行 `superpowers:requesting-code-review`
- 用户告诉你审查意见
- 根据意见修复

**Step 5 — 等待用户运行 Verification**
- 用户运行 `superpowers:verification-before-completion`
- 用户告诉你验证结果

**Step 6 — 等待用户确认 commit**
- 所有 Skill 通过后，用户让你 commit
- 你执行 commit，使用以下格式：

### Commit Message 格式

```
fix: 简短描述 (#缺陷号)

问题：痛点描述（1句）
方案：核心变更（1-2句）
价值：对用户的收益（1句）

技术细节：
- 文件路径: 变更说明

Test plan:
- 验证步骤
```

- type 只能是：fix, feat, chore, test
- **必须执行 `git branch --show-current` 确认分支名**
- **只 add 该 Task 涉及的文件，严禁 `git add -A`**

## 任务清单

[从 Plan 文档中复制该 Phase 的全部 Task 内容]

## 任务标签执行规则

### [FE] 前端任务
- 写测试前先读设计文档（如果有）
- 优先复用现有组件
- 遵守 Frontend Defaults 原则

### [BE] 后端任务
- 按 plan 契约写测试 stub
- 外部 API 调用必须有超时和重试

### [INT] 集成任务
- 在对应 [FE] 和 [BE] 都通过后启动
- E2E 类在最后跑真实链路

## 最终报告格式

全部 task 完成后，报告：

```
=== [Phase 名称] 完成报告 ===
任务完成数：X/Y
[FE] 任务：M 个 | [BE] 任务：K 个 | [INT] 任务：L 个
代码审查：发现 X 个缺陷已全部修复
遗留问题：无
```

---

## 主 Agent 流程

### 第一步：创建 Worktree

```bash
git worktree add ../worktrees/<feature-slug> main -b <branch-name>
```

### 第二步：派发 Subagent

用上面的 **Subagent Prompt 模板** 派发 subagent。

### 第三步：用户手动执行 Skills

Subagent 写代码过程中，你会在以下时刻停顿：

1. **测试 stub 写好时** → 你运行 `superpowers:test-driven-development`
2. **实现完成时** → 你运行 `superpowers:requesting-code-review`
3. **全部完成时** → 你运行 `superpowers:verification-before-completion`

每个 Skill 运行后，把结果告诉 subagent，让它继续。

### 审查格式参考（用户手动执行时可参考）

运行 `superpowers:requesting-code-review` 时，审查必须覆盖 4 类缺陷：

| 类别 | 关注点 | 示例 |
|------|--------|------|
| 韧性缺陷 | 缺重试/缺超时/缺熔断器 | `chat.py:134 retrieve_documents() 缺超时设置` |
| 横切一致性 | 鉴权/限流/日志是否覆盖所有接口 | `4 个接口里 3 个有鉴权检查，第 4 个漏了` |
| 防御性编码 | 未处理的 null/缺输入校验/缺幂等键 | `api.py:42 未处理 API 返回空 choices` |
| 数据库迁移 | 是否有回滚脚本+是否分批操作 | `20240101_add_column.py 无回滚脚本` |

审查报告格式：

| 编号 | 类别 | 文件:行 | 描述 | 修复优先级 |
|------|------|---------|------|-----------|
| 1 | 韧性 | chat.py:134 | retrieve_documents() 缺超时设置 | P0 |
| 2 | 防御性 | api.py:42 | 未处理 API 返回空 choices | P1 |

0 个缺陷 → 进入 commit
有缺陷 → 回到对应 task 走 TDD 修复，重新走一次 review，直到 0 缺陷

如果涉及安全变更（密钥、鉴权、CORS），额外运行 `Skill("cso")`。

### 第四步：Review Gate + 合并

Subagent 全部 task 完成且 commit 后：

1. **检查 commit 分支**：
   ```bash
   cd ../worktrees/<worktree-name> && git log --oneline && git branch --show-current
   ```

2. **运行 `/review` 审查 diff**

3. **运行测试**：
   ```bash
   cd ../worktrees/<worktree-name>/backend && python -m pytest tests/ -v
   ```

4. **合并**：
   ```
   /ship
   ```

5. **清理**：
   ```bash
   git worktree remove ../worktrees/<worktree-name>
   git worktree prune
   ```

6. **质量检查**：
   ```
   /health
   ```

---

## Phase 依赖执行顺序

```
Phase 1 → review → ship → health
    ↓
Phase 2 → review → ship → health
    ↓
Phase 3 → review → ship → health
```

有依赖的 Phase 不能并行。同一 Phase 内无依赖的 worktree 可以并行。

---

## Lessons Learned（v4 更新）

| 问题 | 原因 | 修复 |
|------|------|------|
| subagent "模拟" TDD 而非真正调用 | Skill 在 subagent 中无法保证加载 | **v4 改为：subagent 停顿，用户手动执行** |
| subagent commit 打到 main | agent 意外 checkout | prompt 硬性约束 + 事后验证 |
| commit message 格式不统一 | 只给格式描述不给示例 | 给完整示例模板 |
| 审查清单未执行 | subagent 跳过审查步骤 | 审查由用户手动执行 |

---

## 复用说明

每次新 Feature 开发时：
1. 复制此模板
2. 替换 `[Phase 名称]`、Task 清单、worktree 名
3. 粘贴给主 Agent 执行
