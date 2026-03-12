# Multimodal RAG - 开发规范

> 📝 代码规范、Git 工作流、代码审查指南
> 
> **版本**: v1.0.0
> **最后更新**: 2026-03-12

---

## 📖 目录

- [代码规范](#-代码规范)
- [Git 工作流](#-git-工作流)
- [代码审查清单](#-代码审查清单)
- [贡献指南](#-贡献指南)
- [命名规范](#-命名规范)
- [文档规范](#-文档规范)

---

## 💻 代码规范

### Python 代码规范

#### 基本原则

遵循 [PEP 8](https://pep8.org/) 规范：

```python
# ✅ 好的代码
def calculate_similarity(vector1: list, vector2: list) -> float:
    """计算两个向量的余弦相似度"""
    dot_product = sum(a * b for a, b in zip(vector1, vector2))
    norm1 = math.sqrt(sum(a * a for a in vector1))
    norm2 = math.sqrt(sum(b * b for b in vector2))
    return dot_product / (norm1 * norm2)

# ❌ 不好的代码
def calcSim(v1,v2):
    d=sum(a*b for a,b in zip(v1,v2))
    n1=math.sqrt(sum(a*a for a in v1))
    return d/n1
```

#### 代码格式

```python
# 缩进：4 个空格
def my_function():
    if condition:
        do_something()

# 空行：函数之间 2 行，类方法之间 1 行
def function1():
    pass


def function2():
    pass

# 行长度：<100 字符
long_string = "This is a very long string that should be broken into multiple lines " \
              "for better readability"

# 导入顺序：标准库 → 第三方库 → 本地模块
import os
import sys

import requests
from fastapi import FastAPI

from .utils import helper_function
```

#### 类型注解

```python
# ✅ 使用类型注解
from typing import List, Dict, Optional

def process_data(
    items: List[str],
    config: Optional[Dict[str, any]] = None
) -> Dict[str, any]:
    pass

# ❌ 避免无类型注解
def process_data(items, config=None):
    pass
```

#### 错误处理

```python
# ✅ 明确的错误处理
try:
    result = await llm_api.chat(prompt)
except APIError as e:
    logger.error(f"API 调用失败：{e}")
    raise
except TimeoutError:
    logger.warning("API 超时，使用默认响应")
    return DEFAULT_RESPONSE

# ❌ 模糊的错误处理
try:
    result = await llm_api.chat(prompt)
except:
    pass
```

#### 日志规范

```python
import logging

logger = logging.getLogger(__name__)

# 日志级别使用
logger.debug("调试信息：详细的技术细节")
logger.info("普通信息：正常的操作流程")
logger.warning("警告信息：可能有问题，但不影响运行")
logger.error("错误信息：操作失败，但程序继续")
logger.critical("严重错误：程序可能无法继续")

# ✅ 好的日志
logger.info(f"用户 {user_id} 登录成功")

# ❌ 不好的日志
print("用户登录")  # 不要用 print
logger.info("登录")  # 信息不完整
```

---

### TypeScript 代码规范

#### 基本原则

遵循 [TypeScript 官方风格指南](https://google.github.io/styleguide/tsguide.html)

```typescript
// ✅ 好的代码
interface User {
  id: string;
  name: string;
  email?: string;  // 可选字段
}

function greetUser(user: User): string {
  return `Hello, ${user.name}!`;
}

// ❌ 不好的代码
interface user {  // 接口应该 PascalCase
  id: any;  // 避免使用 any
  name;  // 缺少类型注解
}
```

#### 代码格式

```typescript
// 缩进：2 个空格
function myFunction() {
  if (condition) {
    doSomething();
  }
}

// 分号：必须使用
const value = 42;

// 引号：单引号
const message = 'Hello';

// 行长度：<100 字符
```

#### React 组件规范

```typescript
// ✅ 函数组件 (优先)
const MyComponent: React.FC<Props> = ({ title, children }) => {
  return (
    <div className="my-component">
      <h1>{title}</h1>
      {children}
    </div>
  );
};

// ❌ 避免类组件 (除非必要)
class MyComponent extends React.Component<Props> {
  render() {
    return <div>{this.props.title}</div>;
  }
}
```

---

## 🌿 Git 工作流

### 分支模型

```
main (生产)
  │
  ├── develop (开发)
  │     │
  │     ├── feature/user-auth
  │     ├── feature/pdf-upload
  │     └── bugfix/login-error
  │
  └── release/v1.0.0 (发布)
```

### 分支命名

| 类型 | 命名格式 | 示例 |
|-----|---------|------|
| 功能分支 | `feature/<description>` | `feature/user-auth` |
| 修复分支 | `bugfix/<description>` | `bugfix/login-error` |
| 发布分支 | `release/<version>` | `release/v1.0.0` |
| 热修复 | `hotfix/<description>` | `hotfix/security-patch` |

### 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

| 类型 | 说明 |
|-----|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式 (不影响功能) |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具配置 |
| `security` | 安全相关 |

#### 提交示例

```bash
# ✅ 好的提交信息
feat(api): 添加用户认证接口

- 实现登录接口
- 实现登出接口
- 添加 JWT token 生成

Closes #123

# ✅ Bug 修复
fix(chat): 修复流式输出中断问题

当响应超过 2000 token 时，流式输出会中断。
添加缓冲机制解决这个问题。

Fixes #456

# ❌ 不好的提交信息
update code  # 太模糊
fix bug  # 没有说明是什么 bug
WIP  # 不应该提交未完成的工作
```

### Git 操作流程

#### 功能开发流程

```bash
# 1. 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/user-auth

# 2. 开发并提交
git add .
git commit -m "feat(auth): 实现登录功能"

# 3. 推送到远程
git push origin feature/user-auth

# 4. 创建 Pull Request
# 在 GitHub/GitLab 上创建 PR

# 5. 代码审查通过后合并
```

#### 发布流程

```bash
# 1. 创建发布分支
git checkout develop
git checkout -b release/v1.0.0

# 2. 版本号和最终测试
# 更新版本号
# 运行完整测试

# 3. 合并到 main
git checkout main
git merge release/v1.0.0
git tag v1.0.0

# 4. 合并回 develop
git checkout develop
git merge release/v1.0.0

# 5. 删除发布分支
git branch -d release/v1.0.0
```

---

## ✅ 代码审查清单

### 通用检查项

#### 代码质量

- [ ] 代码是否遵循项目规范？
- [ ] 是否有重复代码需要提取？
- [ ] 函数是否足够小 (<50 行)？
- [ ] 变量命名是否清晰？
- [ ] 是否有不必要的注释？
- [ ] 是否有 TODO 需要处理？

#### 功能正确性

- [ ] 功能是否按需求实现？
- [ ] 边界条件是否处理？
- [ ] 错误处理是否完善？
- [ ] 是否有单元测试？
- [ ] 测试覆盖率是否足够？

#### 性能考虑

- [ ] 是否有明显的性能问题？
- [ ] 是否有不必要的循环？
- [ ] 数据库查询是否优化？
- [ ] 是否有缓存机制？
- [ ] 内存使用是否合理？

#### 安全性

- [ ] 是否有 SQL 注入风险？
- [ ] 是否有 XSS 风险？
- [ ] 敏感信息是否加密？
- [ ] API 认证是否完善？
- [ ] 权限检查是否到位？

#### 可维护性

- [ ] 代码是否易于理解？
- [ ] 是否有完整的文档？
- [ ] 日志是否完善？
- [ ] 配置是否外置？
- [ ] 是否易于测试？

---

### Python 专项检查

```python
# 检查清单

# 1. 类型注解
def process_data(items: List[str]) -> Dict[str, Any]:  # ✅
    pass

# 2. 错误处理
try:
    risky_operation()
except SpecificError as e:  # ✅ 捕获具体异常
    logger.error(f"操作失败：{e}")

# 3. 资源管理
with open('file.txt') as f:  # ✅ 使用上下文管理器
    content = f.read()

# 4. 导入顺序
import os  # 标准库
import requests  # 第三方
from . import utils  # 本地

# 5. 日志使用
logger.info("操作成功")  # ✅ 使用 logger
print("操作成功")  # ❌ 不要用 print
```

---

### TypeScript/React 专项检查

```typescript
// 检查清单

// 1. 类型安全
interface Props {
  title: string;
  count?: number;  // 可选字段
}

// 2. React Hooks
const [count, setCount] = useState<number>(0);  // ✅ 指定类型

// 3. 组件结构
const MyComponent: React.FC<Props> = ({ title }) => {  // ✅ 函数组件
  return <div>{title}</div>;
};

// 4. 事件处理
const handleClick = useCallback(() => {  // ✅ 使用 useCallback
  doSomething();
}, []);

// 5. 异步操作
const fetchData = async () => {
  try {
    const response = await api.get('/data');
  } catch (error) {
    // 错误处理
  }
};
```

---

### Pull Request 模板

```markdown
## 变更说明

<!-- 描述本次 PR 的变更内容 -->

## 相关 Issue

<!-- 关联的 Issue 编号 -->
Closes #123

## 测试计划

<!-- 如何测试这些变更 -->
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成

## 截图 (如适用)

<!-- 前端变更提供截图 -->

## 检查清单

- [ ] 代码遵循项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 提交信息清晰
- [ ] 无合并冲突
```

---

## 🤝 贡献指南

### 如何贡献

#### 1. Fork 项目

```bash
# 在 GitHub 上 Fork 项目
# 然后克隆到本地
git clone git@github.com:your-username/Multimodal_RAG.git
```

#### 2. 创建分支

```bash
cd Multimodal_RAG
git checkout -b feature/your-feature
```

#### 3. 开发并提交

```bash
# 编写代码
# 运行测试
git add .
git commit -m "feat: 添加新功能"
```

#### 4. 推送并创建 PR

```bash
git push origin feature/your-feature
# 在 GitHub 上创建 Pull Request
```

#### 5. 代码审查

- 等待维护者审查
- 根据反馈修改
- 审查通过后合并

---

### 贡献类型

| 类型 | 说明 | 难度 |
|-----|------|------|
| 🐛 Bug 修复 | 修复已知问题 | ⭐ |
| ✨ 新功能 | 添加新功能 | ⭐⭐⭐ |
| 📝 文档 | 改进文档 | ⭐ |
| 🎨 重构 | 代码优化 | ⭐⭐ |
| 🧪 测试 | 添加测试 | ⭐⭐ |
| 🔒 安全 | 安全修复 | ⭐⭐⭐ |

---

### 开发环境设置

```bash
# 1. 克隆项目
git clone git@github.com:your-username/Multimodal_RAG.git

# 2. 安装后端依赖
cd backend
conda create -n vlm_rag python=3.11 -y
conda activate vlm_rag
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 3. 安装前端依赖
cd ../frontend
npm install

# 4. 运行测试
# 后端
pytest

# 前端
npm test
```

---

## 📛 命名规范

### Python 命名

```python
# 变量和函数：snake_case
user_name = "Tao"
def calculate_score():
    pass

# 类：PascalCase
class UserService:
    pass

# 常量：UPPER_CASE
MAX_RETRY_COUNT = 3
API_KEY = "xxx"

# 私有：前缀下划线
_internal_var = 42
def _helper_function():
    pass
```

### TypeScript 命名

```typescript
// 变量和函数：camelCase
const userName = "Tao";
function calculateScore() {}

// 类和接口：PascalCase
interface User {
  name: string;
}
class UserService {}

// 常量：UPPER_CASE
const MAX_RETRY_COUNT = 3;

// 私有：前缀下划线
const _internalVar = 42;
```

### 文件命名

```bash
# Python: snake_case
user_service.py
chat_handler.py

# TypeScript: PascalCase (组件) / camelCase (工具)
UserProfile.tsx
utils.ts

# 文档：UPPER_CASE 或 snake_case
README.md
USER_GUIDE.md
```

---

## 📄 文档规范

### Markdown 格式

```markdown
# H1 标题
## H2 标题
### H3 标题

**粗体** 用于强调
*斜体* 用于引用

- 列表项 1
- 列表项 2

[链接文本](URL)

![图片描述](图片 URL)

```python
# 代码块
def hello():
    print("Hello")
```
```

### API 文档格式

```markdown
## 端点名称

**端点**: `POST /api/chat`

**描述**: RAG 对话接口

**请求**:
```json
{
  "query": "用户问题"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "answer": "AI 回答"
  }
}
```
```

---

## 📊 代码质量指标

### 目标指标

| 指标 | 目标值 | 当前值 |
|-----|-------|-------|
| 测试覆盖率 | >80% | 待测 |
| 代码重复率 | <5% | 待测 |
| 平均函数长度 | <30 行 | 待测 |
| 文档覆盖率 | >90% | 待测 |
| 技术债务 | <10 小时 | 待测 |

### 质量检查工具

```bash
# Python
flake8  # 代码风格
black  # 代码格式化
mypy  # 类型检查
pytest  # 测试

# TypeScript
eslint  # 代码风格
prettier  # 代码格式化
tsc  # 类型检查
jest  # 测试
```

---

**文档版本**: v1.0.0
**最后更新**: 2026-03-12
**维护者**: knowledge Agent
