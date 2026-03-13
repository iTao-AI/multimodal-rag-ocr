# Agent-RAG 项目技术方案设计

**版本**: v1.0  
**创建日期**: 2026-03-13  
**设计者**: dev Agent  
**状态**: 设计稿

---

## 📊 项目概述

### 项目目标

在现有 Multimodal RAG 项目基础上，集成 LangChain 1.0+ Agent 能力，打造具备多步推理和工具调用能力的智能 Agent 系统。

**目标岗位**: Agent 开发工程师 (首选) / RAG 开发工程师 (保底)

### 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **前端** | React + TypeScript + Vite | 18+ |
| **后端** | FastAPI + Python | 3.10+ |
| **Agent 框架** | LangChain | 1.0+ |
| **向量数据库** | Milvus | 2.6+ |
| **大模型** | 阿里云百炼 (Qwen3-VL) | Latest |
| **缓存** | Redis | 7.0+ |
| **部署** | Docker + Docker Compose | Latest |

---

## 🏗️ 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端界面 (React)                      │
│  - 对话界面                                              │
│  - Agent 状态可视化                                       │
│  - 工具调用展示                                          │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/WebSocket
                     ↓
┌─────────────────────────────────────────────────────────┐
│              API Gateway (FastAPI)                       │
│  - 请求路由                                              │
│  - 认证授权                                              │
│  - 限流熔断                                              │
└────────────┬─────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────┐
│              Agent 核心层 (LangChain 1.0+)               │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Agent Executor                                     │  │
│  │ - 任务规划 (Planner)                               │  │
│  │ - 工具调度 (Tool Dispatcher)                       │  │
│  │ - 执行监控 (Executor Monitor)                      │  │
│  └───────────────────────────────────────────────────┘  │
└────────────┬─────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────┐
│                  工具层 (Tools)                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────┐  │
│  │ 搜索工具   │ │ API 工具    │ │ 数据库工具         │  │
│  │ (Search)   │ │ (API Call) │ │ (SQL/NoSQL)        │  │
│  └────────────┘ └────────────┘ └────────────────────┘  │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────┐  │
│  │ RAG 工具    │ │ 计算工具   │ │ 自定义工具         │  │
│  │ (Retrieval)│ │ (Calculator)│ │ (Custom)           │  │
│  └────────────┘ └────────────┘ └────────────────────┘  │
└────────────┬─────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────┐
│                  数据层 (Data)                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────┐  │
│  │ Milvus     │ │ MySQL      │ │ Redis              │  │
│  │ (向量库)   │ │ (元数据)   │ │ (缓存)             │  │
│  └────────────┘ └────────────┘ └────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent 核心模块设计

### 1. Agent Executor

**职责**: 任务规划、工具调度、执行监控

```python
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Any

class AgentExecutor:
    """Agent 执行器"""
    
    def __init__(
        self,
        llm: ChatModel,
        tools: List[BaseTool],
        prompt: ChatPromptTemplate,
        max_iterations: int = 10,
        verbose: bool = True
    ):
        self.llm = llm
        self.tools = tools
        self.prompt = prompt
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # 创建 Agent
        self.agent = self._create_agent()
        
        # 创建执行器
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            max_iterations=max_iterations,
            verbose=verbose
        )
    
    def _create_agent(self):
        """创建 Agent"""
        from langchain.agents import create_openai_tools_agent
        
        return create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
    
    def invoke(self, input: str) -> Dict[str, Any]:
        """执行任务"""
        return self.executor.invoke({
            "input": input
        })
```

---

### 2. 任务规划器 (Planner)

**职责**: 多步任务分解、执行计划生成

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

class TaskPlan(BaseModel):
    """任务计划"""
    steps: List[str] = Field(description="任务步骤列表")
    expected_output: str = Field(description="预期输出")
    tools_needed: List[str] = Field(description="需要的工具")

class TaskPlanner:
    """任务规划器"""
    
    def __init__(self, llm: ChatModel):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=TaskPlan)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个任务规划专家，请将复杂任务分解为可执行的步骤"),
            ("human", "任务：{task}\n\n{format_instructions}"),
        ])
        
        self.chain = self.prompt | self.llm | self.parser
    
    def plan(self, task: str) -> TaskPlan:
        """生成任务计划"""
        return self.chain.invoke({
            "task": task,
            "format_instructions": self.parser.get_format_instructions()
        })
```

**使用示例**:
```python
planner = TaskPlanner(llm)

plan = planner.plan("分析上个月的销售数据，找出 Top 3 产品，并生成报告")

# 输出:
# TaskPlan(
#     steps=[
#         "1. 查询上个月的销售数据",
#         "2. 按产品分组并计算总销售额",
#         "3. 排序找出 Top 3 产品",
#         "4. 生成分析报告"
#     ],
#     expected_output="销售分析报告",
#     tools_needed=["database_query", "data_analysis", "report_generation"]
# )
```

---

### 3. 工具调度器 (Tool Dispatcher)

**职责**: 工具注册、工具选择、并行执行

```python
from typing import Dict, List, Callable
from concurrent.futures import ThreadPoolExecutor

class ToolDispatcher:
    """工具调度器"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def dispatch(self, tool_name: str, input: str) -> str:
        """调度工具执行"""
        if tool_name not in self.tools:
            raise ValueError(f"工具 {tool_name} 不存在")
        
        tool = self.tools[tool_name]
        return tool.invoke(input)
    
    def dispatch_parallel(self, tool_inputs: List[tuple]) -> List[str]:
        """并行执行多个工具"""
        futures = []
        
        for tool_name, input in tool_inputs:
            future = self.executor.submit(self.dispatch, tool_name, input)
            futures.append(future)
        
        results = []
        for future in futures:
            results.append(future.result())
        
        return results
```

---

### 4. 执行日志记录

**方案**: LangSmith + 自定义日志

```python
from langsmith import Client
from langsmith.run_helpers import traceable
import logging

# 配置 LangSmith
client = Client()
logging.basicConfig(level=logging.INFO)

class AgentLogger:
    """Agent 日志记录器"""
    
    @staticmethod
    @traceable(run_type="chain")
    def log_task_start(task: str):
        """记录任务开始"""
        logging.info(f"任务开始：{task}")
    
    @staticmethod
    @traceable(run_type="tool")
    def log_tool_call(tool_name: str, input: str, output: str):
        """记录工具调用"""
        logging.info(f"工具调用：{tool_name}")
        logging.info(f"输入：{input}")
        logging.info(f"输出：{output}")
    
    @staticmethod
    @traceable(run_type="chain")
    def log_task_complete(output: str):
        """记录任务完成"""
        logging.info(f"任务完成：{output}")
    
    @staticmethod
    @traceable(run_type="retriever")
    def log_retrieval(query: str, results: List[str]):
        """记录检索过程"""
        logging.info(f"检索查询：{query}")
        logging.info(f"检索结果：{len(results)} 条")
```

**LangSmith 仪表盘**:
- Agent 执行追踪
- 工具调用延迟
- 任务规划耗时
- 错误率统计

---

## 🛠️ 工具集成设计

### 工具分类

| 工具类型 | 工具名称 | 功能 | 调用方式 |
|----------|----------|------|----------|
| **搜索工具** | `search_web` | 网络搜索 | API 调用 |
| **RAG 工具** | `search_knowledge_base` | 知识库检索 | Milvus 检索 |
| **API 工具** | `call_api` | 通用 API 调用 | HTTP 请求 |
| **数据库工具** | `query_database` | SQL 查询 | SQLAlchemy |
| **计算工具** | `calculator` | 数学计算 | Python eval |
| **报告工具** | `generate_report` | 生成报告 | LLM 生成 |

### 工具定义示例

```python
from langchain.tools import tool
from langchain_core.callbacks import CallbackManagerForToolRun

@tool
def search_knowledge_base(query: str, top_k: int = 5) -> str:
    """从知识库搜索相关信息"""
    results = milvus_search(query, top_k=top_k)
    return format_results(results)

@tool
def query_database(sql: str) -> str:
    """执行 SQL 查询"""
    # 安全验证
    if not is_safe_sql(sql):
        return "错误：SQL 不安全"
    
    result = execute_sql(sql)
    return format_sql_result(result)

@tool
def generate_report(data: dict, template: str = "default") -> str:
    """生成分析报告"""
    prompt = f"基于以下数据生成{template}报告：\n{data}"
    return llm.invoke(prompt)
```

---

## 📅 工作分解 (7-10 天)

### Day 1-2: LangChain 1.0+ 升级

**任务**:
- [ ] 升级 LangChain 到 1.0+
- [ ] 迁移现有代码到 LCEL
- [ ] 添加类型注解
- [ ] 测试验证

**交付物**:
- LangChain 1.0+ 迁移报告
- 测试通过率 100%

**风险**:
- ⚠️ API 变更可能导致兼容性问题
- 📋 缓解：充分测试

---

### Day 3-4: Agent 核心模块实现

**任务**:
- [ ] 实现 Agent Executor
- [ ] 实现任务规划器
- [ ] 实现工具调度器
- [ ] 单元测试

**交付物**:
- Agent 核心代码
- 单元测试用例 (20+)

**风险**:
- ⚠️ 任务规划准确率可能不高
- 📋 缓解：使用 Few-Shot Prompting

---

### Day 5-6: 工具集成

**任务**:
- [ ] 实现 5-6 个基础工具
- [ ] 工具注册机制
- [ ] 并行执行支持
- [ ] 集成测试

**交付物**:
- 工具库 (5-6 个工具)
- 集成测试报告

**风险**:
- ⚠️ 工具调用失败率可能较高
- 📋 缓解：添加重试机制

---

### Day 7-8: 执行日志与监控

**任务**:
- [ ] LangSmith 集成
- [ ] 自定义日志记录
- [ ] 监控仪表盘
- [ ] 告警规则

**交付物**:
- 完整的日志系统
- Grafana 仪表盘

**风险**:
- ⚠️ LangSmith 可能有学习曲线
- 📋 缓解：参考官方文档

---

### Day 9-10: 性能优化与文档

**任务**:
- [ ] 性能基准测试
- [ ] 优化响应时间
- [ ] 编写技术文档
- [ ] 准备面试材料

**交付物**:
- 性能测试报告
- 技术文档 (完整)
- 面试准备材料

**风险**:
- ⚠️ 性能可能不达标
- 📋 缓解：提前进行性能测试

---

## 🎯 技术亮点提炼

### 与纯 RAG 的差异

| 维度 | 纯 RAG | Agent-RAG | 优势 |
|------|--------|-----------|------|
| **查询方式** | 单步检索 | 多步推理 | 处理复杂问题 |
| **能力范围** | 检索 + 生成 | 检索 + 生成 + 工具调用 | 更广泛 |
| **自主性** | 被动响应 | 主动规划 | 更智能 |
| **适用场景** | 简单问答 | 复杂任务 | 更实用 |

### 技术选型理由

**为什么选择 LangChain 1.0+?**
1. LCEL 表达式更简洁
2. 类型安全 (TypeScript 风格)
3. 更好的错误处理
4. 流式输出原生支持
5. 更好的可观测性 (LangSmith)

**为什么选择 Agent 架构?**
1. 多步推理能力
2. 工具调用能力
3. 自主任务规划
4. 适应复杂场景

### 解决的问题

1. **复杂问题处理能力不足**
   - 纯 RAG 只能处理单步检索
   - Agent-RAG 可以处理多步推理

2. **工具调用能力缺失**
   - 纯 RAG 无法调用外部工具
   - Agent-RAG 可以调用搜索/API/数据库

3. **自主性不足**
   - 纯 RAG 被动响应
   - Agent-RAG 主动规划任务

---

## 📊 预期成果

### 功能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 工具调用成功率 | > 99% | 工具执行成功率 |
| 任务规划准确率 | > 85% | 任务分解准确率 |
| 响应时间 (P95) | < 500ms | 简单查询 |
| 响应时间 (P95) | < 2s | 复杂多步查询 |
| 并发能力 | > 100 QPS | 系统吞吐量 |

### 面试价值

**可展示的技术亮点**:
1. LangChain 1.0+ 实践经验
2. Agent 架构设计能力
3. 工具调用框架设计
4. 多步推理实现经验
5. 完整的性能数据支撑

**面试可讲案例**:
1. Agent 任务规划实现
2. 工具调用优化实践
3. 性能瓶颈定位与优化
4. LangSmith 可观测性实践

---

## 📁 文档结构

```
docs/
├── architecture/
│   ├── AGENT_RAG_DESIGN.md       # 本设计文档
│   ├── agent_executor.md         # Agent 执行器设计
│   ├── task_planner.md           # 任务规划器设计
│   └── tool_dispatcher.md        # 工具调度器设计
├── implementation/
│   ├── langchain_upgrade.md      # LangChain 1.0+ 迁移指南
│   ├── tools/                    # 工具实现文档
│   └── logging.md                # 日志记录方案
├── testing/
│   ├── performance_benchmark.md  # 性能基准测试
│   └── integration_tests.md      # 集成测试用例
└── interview/
    ├── talking_points.md         # 面试要点
    └── qa_preparation.md         # 面试问答准备
```

---

**设计完成时间**: 2026-03-13  
**设计者**: dev Agent  
**下次更新**: 实施过程中持续更新

---

**Agent-RAG 技术方案设计完成！** 🦾
