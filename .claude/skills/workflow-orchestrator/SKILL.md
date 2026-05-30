---
name: workflow-orchestrator
description: >
  Use when starting any Phase of multi-worktree development ("开始 Phase 3",
  "执行后端可靠性修复", "创建 worktree 跑 tasks"). Enforces the 6-step
  workflow with mandatory checkpoints. Each step declares which Skill to invoke —
  by me, by subagent, or by you manually. Use when worktree, subagent dispatch,
  git merge, PR creation, or multi-step development workflows are mentioned.
---

# Workflow Orchestrator

Enforces the multi-Phase worktree + subagent workflow with **mandatory checkpoints**.

**Violating the letter of the rules is violating the spirit of the rules.**

## Core Principle

**流程为主，自动为辅** — Every step declares which Skill to invoke. Subagent behavior must be explicitly specified in its prompt — never assume it will call a Skill on its own. If unsure whether a Skill triggered correctly, assume it didn't and run it yourself.

**Auto-continue rule:** After completing any step (including user manual steps), proceed to the next step WITHOUT waiting for confirmation. Only stop at MANDATORY CHECKPOINT markers where user action is required. After the user reports completion, immediately continue to the next step.

**Parallel subagent rule:** If tasks have NO dependencies between them, dispatch ALL subagents in parallel using `superpowers:subagent-driven-development`. Only serialize subagents when task B depends on task A's output.

**Step execution discipline (CRITICAL — Phase 4 failures):**
- **Never output "准备中"/"preparing"/"正在派发" 等预告废话。** Subagent dispatch 直接做，不要预告再做。
- **No confirmation before dispatch.** Auto-continue rule means: finish Step N, immediately do Step N+1.

**Subagent worktree commit discipline (CRITICAL — Phase 4 #2):**
- Subagent prompt must include: `**Before committing, run \`git branch --show-current\` and verify you are on the worktree branch. NEVER commit to main.**`
- After subagent reports DONE, I verify: `git log --oneline main -1` must NOT show the subagent's commit.
- If subagent accidentally committed to main: cherry-pick to worktree + `git reset --hard <prev>` on main.

**Large-change subagent quota management:**
- If a task involves > 100 lines of mechanical changes (e.g. 300+ print→logger replacements), either:
  - Split into 2+ subagents (e.g. one per service), OR
  - I (main agent) do it directly instead of dispatching
- Subagent prompts for large-change tasks must warn: "This task involves many mechanical changes. If you hit API quota limits, report BLOCKED so the main agent can take over."

**Bulk text replacement safety:**
- When replacing patterns like print() → logger, use precise matching. Avoid replacing strings that CONTAIN the target pattern as a substring (e.g. `logger.info("print("...")"`).
- After bulk replacement, always grep to verify no malformed output like `logger.info("print("...")"`.

**Git stash/pop in worktree sessions:**
- Avoid git stash/pop during subagent sessions. If needed to protect work, use explicit file backup instead.
- Stash pop has overwritten fixes in Phase 4. Do not use git stash unless absolutely necessary.

## Red Flags — STOP and Start Over

- Subagent 写完后自动 commit 了 → **退回，手动跑 Skill 后再 commit**
- 直接 merge 到 main 没创建 PR → **退回，用 /ship 创建 PR**
- Skill 运行结果不确定 → **当作未触发，手动再跑一次**
- "之前 Phase 已经跑过了，这次跳过吧" → **不跳，每 Phase 都跑完**
- "我手动测试过了，不用再跑 verification" → **手动测试 ≠ verification skill**

**All of these mean: Delete any uncommitted work. Return to the last checkpoint. Run the Skill manually.**

## Pre-Flight Check

Before starting any Phase:
1. `git branch --show-current` is on `main`
2. `git status` is clean (no uncommitted changes)
3. Plan file exists at `docs/superpowers/plans/*.md`
4. Old worktrees cleaned: `git worktree prune && git branch -D fix/* enhance/* 2>/dev/null`

If any check fails, stop and fix first.

## The Workflow

Each Phase follows this exact sequence. **No skipping, no reordering, no batching.**

### Step 1: 创建 Worktree（我调用 Skill）

**Skill:** `superpowers:using-git-worktrees`

I invoke this skill to create the isolated worktree. Do NOT run `git worktree add` directly — the skill handles `.worktreeinclude` copying (`.env`, `.credentials.yaml`) and initialization.

### Step 2: Subagent 写代码（我使用 Skill 派发）

**Skill:** `superpowers:subagent-driven-development`

I invoke this skill to dispatch the subagent(s). 

**If tasks are independent:** Dispatch ALL subagents in parallel (single message with multiple Agent tool calls).
**If tasks have dependencies:** Dispatch subagents serially — wait for each to complete before dispatching the next.

The subagent prompt must explicitly declare:

```
你是本项目的实现工程师，正在执行 [Phase 名称] 的开发任务。

工作目录：../worktrees/<worktree-name>/
分支：<branch-name>

必读文件（按顺序）：
1. specs/prd.md
2. .specify/memory/constitution.md
3. CLAUDE.md

## 硬性约束（违反任一即视为任务失败）

- **必须在当前 worktree 分支上 commit**，执行 `git branch --show-current` 确认分支名，严禁切换到 main 分支操作
- **只 add 该 Task 涉及的文件**，严禁 `git add -A`
- **批量替换后必须验证**：grep 确认无 malformed 输出（如 `logger.info("print("...")")`）
- **遇到 API 配额限制立即报告 BLOCKED**，不要反复重试

任务清单：
[从 Plan 文档中复制该 Phase 的全部 Task 内容]

## 每个 Task 必须按以下顺序执行：

1. **调用** `Skill("superpowers:test-driven-development")` — 写测试 → RED → 实现 → GREEN → REFACTOR
2. **调用** `Skill("superpowers:verification-before-completion")` — 验证实现
3. 验证通过后 commit（格式见下方）
4. 报告 Task 完成，等待下一个 Task

## Commit 格式
fix: 简短描述 (#缺陷号)

问题：痛点描述（1句）
方案：核心变更（1-2句）
价值：对用户的收益（1句）

技术细节：
- 文件路径: 变更说明

Test plan:
- 验证步骤
```

### Step 3: 手动 Code Review（你调用 Skill）← MANDATORY CHECKPOINT

> 📋 下一步：**请手动运行** `/review`
> 审查 subagent 写好的代码 diff

`/review` 覆盖以下 4 类缺陷：

| 类别 | 关注点 |
|------|--------|
| 韧性缺陷 | 缺重试/缺超时/缺熔断器 |
| 横切一致性 | 鉴权/限流/日志是否覆盖所有接口 |
| 防御性编码 | 未处理的 null/缺输入校验/缺幂等键 |
| 数据库迁移 | 是否有回滚脚本+是否分批操作 |

**DO NOT proceed until review has 0 unresolved defects.**

If defects found → instruct subagent to fix, then re-run this Step.

### Step 4: 手动 Verification（你调用 Skill）← MANDATORY CHECKPOINT

> 📋 下一步：**请手动运行** `superpowers:verification-before-completion`

注意：subagent 已自行验证过一次，你需要从外部独立再验证一次。

**DO NOT proceed until verification passes.**

If verification fails → instruct subagent to fix, then re-run from Step 3.

### Step 5: 手动 /ship（你调用 Skill）← MANDATORY CHECKPOINT

> 📋 下一步：**请手动运行** `/ship`
> 这将创建 PR 并推送到 GitHub，确保 GitHub 上有 PR 记录

**必须先 /ship，再清理 worktree。**

### Step 6: 清理 worktree（你调用 Skill）

> 📋 下一步：**请手动运行** `superpowers:finishing-a-development-branch`
> 清理 worktree 目录和分支

**必须在 /ship 合并之后执行，否则会导致 orphan worktree。**

## Conditional Phases

Not every Phase needs every Skill. Auto-detect based on diff scope:

| Phase 类型 | 额外 Skills（subagent prompt 中显式声明） |
|-----------|------------|
| 前端 UI 变更 | `/qa`（浏览器验证） |
| 安全变更（密钥/CORS/鉴权） | `/cso`（安全审计） |
| 涉及部署 | `/canary`（监控） |

## Skill Responsibility Matrix

| Step | Who invokes | Which Skill |
|------|-------------|-------------|
| 1 | Me | `superpowers:using-git-worktrees` |
| 2 | Me (dispatch) | `superpowers:subagent-driven-development` → subagent calls `test-driven-development` + `verification-before-completion` |
| 3 | You (manual) | `/review` |
| 4 | You (manual) | `superpowers:verification-before-completion` |
| 5 | You (manual) | `/ship` |
| 6 | You (manual) | `superpowers:finishing-a-development-branch` |

## Checklist Card

Display at each CHECKPOINT:

```
=== 当前进度 ===
Phase: [名称]
Worktree: [分支名]
当前步骤: Step N / 6

✅ Step 1: Worktree 创建（我已调用 using-git-worktrees）
✅ Step 2: Subagent 写代码（我已用 subagent-driven-development 派发）
⏳ Step 3: [等待你手动执行 Code Review]

📋 请运行: /review
   完成后告诉我审查结果
```
