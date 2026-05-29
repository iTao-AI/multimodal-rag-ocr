# Subagent + Worktree 执行流程模板

> 本文档可复用于任何基于 implementation plan 的多 Phase 并行开发流程。

---

## 可用 Skills 清单

### 核心 Skills（每个 worktree 必用）

| Skill | 用途 | 触发时机 |
|-------|------|----------|
| `superpowers:test-driven-development` | TDD 流程 | 每个 Task 开始时 |
| `superpowers:using-git-worktrees` | 隔离 worktree | Phase 开始时 |
| `superpowers:verification-before-completion` | 完成前自动验证 | Task 全部完成后、报告前 |
| `superpowers:requesting-code-review` | 发起 code review | commit 前 |
| `superpowers:receiving-code-review` | 响应 review 反馈 | 收到 review 意见后 |
| `superpowers:finishing-a-development-branch` | 分支合并 + 清理 | worktree 任务全部完成后 |
| `superpowers:executing-plans` | inline 执行 plan（备选） | 单文件小改动不需要 worktree 时 |

### 阶段 Skills（主 agent 在 Phase 合并后调用）

| Skill | 用途 | 触发时机 |
|-------|------|----------|
| `/review` | diff 审查 | merge 前，审查 worktree 分支的 diff |
| `/ship` | 创建 PR + 合并到 main | 替代手动 `git merge` |
| `/land-and-deploy` | 合并后跑 CI + 部署验证 | ship 完成后 |
| `/health` | 代码质量打分（0-10） | Phase 开始前记录 baseline + 合并后记录趋势 |

### 按需 Skills（按需触发）

| Skill | 用途 | 何时使用 |
|-------|------|----------|
| `/qa` | 前端 QA 测试 + 自动修 bug | Phase 涉及前端 UI 变更时 |
| `/investigate` | 结构化 4 阶段根因调查 | agent 遇到无法定位的 bug 时 |
| `/document-release` | PR 合并后自动更新文档 | 全部 Phase 完成后 |
| `/retro` | 周回顾，总结进度 | 全部 Phase 完成后，或每周末（非每个 Phase 后） |
| `/cso` | 首席安全官模式，安全审计 | 涉及安全变更时（密钥、鉴权、CORS） |
| `/canary` | 部署后监控 | 实际部署到生产环境后 |

---

## 执行前准备

确保以下条件已满足：
- [ ] PRD 已完成：`specs/prd.md`
- [ ] Implementation Plan 已完成：`docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- [ ] 当前分支为 `main`，工作区干净（`git status` 无未提交变更）
- [ ] 核心 Skills 已确认可用（见上方清单）
- [ ] 调用 `/health` 记录 baseline 质量分数（用于对比 Phase 后的质量变化）

---

## 主 Agent 提示词模板

将以下内容直接粘贴给主 Agent，替换 `[计划文件路径]` 和 `[Phase N]` 即可复用。

```
我准备执行保存在 `[计划文件路径]` 的 Implementation Plan。

请按照以下流程执行：

## 第一步：创建 Worktree

使用 `superpowers:using-git-worktrees` 创建隔离 worktree。
每个 worktree 基于 main 分支，位于 `../worktrees/<feature-slug>/` 目录。

Phase 的 worktree 命名规则：
- 修复类：`fix-<bug-slug>`
- 增强类：`enhance-<feature-slug>`

可并行的 Phase 同时创建，有依赖关系的 Phase 必须等前序 Phase 合并后再创建。

## 第二步：派发 Subagent

为每个 worktree 派发一个独立 subagent，使用以下 prompt 模板：

---

### Subagent Prompt 模板

你是本项目的实现工程师，正在执行 [Phase 名称] 的开发任务。

## 工作环境

- 工作目录：`../worktrees/<worktree-name>/`
- 分支：`<branch-name>`（worktree 自动创建的分支）
- Python 环境：conda activate vlm_rag（Python 3.11）

## 必读文件

开始任务前，按顺序阅读：
1. `specs/prd.md` — 了解业务目标和验收标准
2. `.specify/memory/constitution.md` — 6 条核心开发原则
3. `CLAUDE.md` — 项目上下文、技术栈、Anti-Patterns

## 任务清单

执行以下任务（按顺序，每个 task 完成后标记完成并 commit）：

[从 Plan 文档中复制该 Phase 的全部 Task 内容]

## TDD 强制要求（CRITICAL）

每个 Task 执行时，必须按以下顺序操作：

1. **先调用** `Skill("superpowers:test-driven-development")`
2. 按 TDD 流程执行：写测试 → 跑失败 → 实现 → 跑通过 → commit
3. **严禁跳过测试直接写实现**
4. **严禁手动写 test 文件或手动更新 tasks.md**

如果 skill 无法调用（技能缺失或配置错误），必须向我报告并等待指令，不能自行绕过。

## 完成前验证（CRITICAL）

所有任务完成后、报告完成前，必须调用：
`Skill("superpowers:verification-before-completion")`

该 skill 会：
- 实际运行测试并检查 exit code
- 验证无遗留 TODO/TBD
- 确认 Anti-Pattern 清单

**严禁**：未通过此 skill 就报告任务完成。

## Code Review（CRITICAL）

在 commit 之前，调用：
`Skill("superpowers:requesting-code-review")`

让其他 agent 或主 agent 审查 diff。根据 review 意见修改后，再 commit。

如果涉及安全变更（密钥、鉴权、CORS），额外调用：
`Skill("cso")`

## 提交规则（CRITICAL）

- 每个 Task 完成后立即 commit
- **必须在当前 worktree 分支上 commit，严禁切换到 main 分支操作**
- commit 前执行 `git branch --show-current` 确认当前分支名，如果不是 worktree 分支则停止并报告
- 只 add 该 Task 涉及的文件，严禁 `git add -A`
- commit message 必须严格使用以下 PR Body 格式，不可省略任何段落：

格式：`<type>: <description> (#PRD缺陷编号)`

段落要求（全部必填，禁止留空）：
  问题：现有痛点或缺失（1 句）
  方案：核心变更（1-2 句）
  价值：对用户或项目的收益（1 句；内部变更可省略）
  技术细节：关键文件变更（每条 1 句）
  Test plan：验证步骤清单（每条 1 句）
  设计选型：仅当涉及技术决策时写，格式：方案 | 选择 | 理由
  Breaking Changes：仅当有破坏性变更时写，说明影响和迁移方式

- type 只能是：fix（修复）, feat（新功能）, chore（清理）, test（测试）

## Review Gate

所有任务完成后，运行以下自检命令并报告结果：

1. `cd backend && python -m pytest tests/ -v` — 所有测试通过
2. `cd frontend && npm run lint` — 无 lint 错误
3. 代码审查：无 Anti-Pattern（见 CLAUDE.md）
4. 无遗留 TODO/TBD/占位符

报告格式：
- 任务完成数：X/Y
- 测试通过率：X/Y
- lint 状态：通过/失败（列出失败项）
- 遗留问题：无 或 列出具体问题

---

## 第三步：Review Gate + 合并

所有 subagent 完成后，主 Agent 执行：

1. **检查每个 worktree 的 commit 是否在正确分支上**
   ```bash
   cd ../worktrees/<worktree-name> && git log --oneline && git branch --show-current
   ```
   ⚠️ 如果 commit 在 main 上而非 worktree 分支，需要 cherry-pick 到正确分支。

2. **运行 `/review` 审查 diff**
   ```
   /review
   ```
   审查 worktree 分支相对于 main 的 diff。根据 review 结果决定是否合并。

3. **运行测试验证**
   ```bash
   cd ../worktrees/<worktree-name>/backend && python -m pytest tests/ -v
   ```

4. **检查 diff 质量**
   ```bash
   cd ../worktrees/<worktree-name> && git diff main --stat
   ```

5. **合并到 main**

   两种合并方式，根据场景选择：

   **方式 A：Solo 开发（手动合并 + skill 清理）** — 适用于单人项目，快速迭代
   ```bash
   git checkout main
   git merge <worktree-branch> --no-ff -m "<PR Body 格式>"
   # 然后调用 superpowers:finishing-a-development-branch 清理 worktree 和分支
   ```

   **方式 B：团队协作（/ship）** — 适用于需要 PR 审查的多人项目
   ```
   /ship
   ```
   `/ship` 会自动创建 PR、跑 CI、等待审查后合并。比手动合并重，但流程完整。

   合并 commit 的 message 同样要使用 PR Body 格式。

6. **Phase 合并后质量检查**

   调用 `/health` 运行代码质量打分：
   ```
   /health
   ```
   对比执行前的 baseline 分数，记录质量趋势，追踪 Phase 进展。

   可选：调用 `/retro` 做阶段回顾（仅限全部 Phase 完成后或每周末，非每个 Phase 后都跑）：
   ```
   /retro
   ```

7. **如果某个 worktree 失败**：修复后重新 commit，不合并有问题的部分

## 第四步：进入下一 Phase

当前 Phase 合并到 main 后：
1. 确保 main 分支是最新的
2. 调用 `/health` 记录质量趋势（对比 baseline）
3. 创建下一 Phase 的 worktree（基于最新 main）
4. 重复第二步和第三步

---

## Phase 依赖执行顺序

```
Phase 1（N 个并行 worktree）  → review → ship 合并 → health
    ↓
Phase 2（N 个并行 worktree）  → review → ship 合并 → health
    ↓
Phase 3（N 个并行 worktree）  → review → ship 合并 → health
    ↓
...（后续 Phase 依此类推）
```

**禁止**：有依赖关系的 Phase 不能并行创建 worktree。
**允许**：同一 Phase 内无依赖的 worktree 可以并行创建和执行。

---

## 全部 Phase 完成后

调用以下 skills 做最终收尾：

1. `/health` — 记录最终质量分数，对比 baseline 输出趋势图
2. `/retro` — 周回顾，总结本轮开发的进度和教训
3. `/document-release` — 更新 README、CHANGELOG、架构文档
4. `/land-and-deploy` — 部署到生产环境（如果有部署配置）
5. `/canary` — 部署后监控生产环境

---

## 快速执行检查清单

执行前逐项确认：

### 核心 Skills
- [ ] `superpowers:test-driven-development` 可用
- [ ] `superpowers:using-git-worktrees` 可用
- [ ] `superpowers:verification-before-completion` 可用
- [ ] `superpowers:requesting-code-review` 可用
- [ ] `superpowers:receiving-code-review` 可用
- [ ] `superpowers:finishing-a-development-branch` 可用

### Phase Skills
- [ ] `/review` 可用
- [ ] `/ship` 可用
- [ ] `/health` 可用

### 按需 Skills（按需确认）
- [ ] `/qa` 可用（前端相关）
- [ ] `/investigate` 可用（debug 需要）
- [ ] `/cso` 可用（安全相关）

### 环境
- [ ] PRD 已完成且无 TBD
- [ ] Plan 已完成且每个 Task 有精确文件路径和代码
- [ ] 当前分支为 main，工作区干净
- [ ] baseline 质量分数已记录（`/health`）
- [ ] conda 环境 `vlm_rag` 可用（Python 3.11）
- [ ] 前端 `node_modules` 已安装
- [ ] Milvus Docker 可启动（集成测试需要）
- [ ] Subagent Prompt 模板已替换所有占位符

---

## 复用说明

将此模板保存为 `docs/EXECUTION_WORKFLOW.md`，每次新 Feature 开发时：
1. 复制此模板
2. 替换 `[计划文件路径]`、`[Phase 名称]`、Task 清单
3. 按需调整 worktree 命名和 Phase 数量
4. 粘贴给主 Agent 执行
