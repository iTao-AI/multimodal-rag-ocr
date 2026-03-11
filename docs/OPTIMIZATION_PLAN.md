# Multimodal RAG 项目优化方案

**版本**: v1.0  
**日期**: 2026-03-11  
**状态**: 执行中

---

## 📊 当前状态评估

### 已完成✅
- ✅ Git 仓库初始化
- ✅ 后端 4 个服务运行 (3/4 正常)
- ✅ 前端界面部署
- ✅ Python 依赖安装
- ✅ 路径配置修复

### 待优化⚠️
- ⚠️ .env 文件权限 (当前 664 → 目标 600)
- ⚠️ API Key 明文存储
- ⚠️ CORS 配置过于宽松
- ⚠️ 缺少请求限流
- ⚠️ 缺少健康检查
- ⚠️ 缺少日志轮转
- ⚠️ Milvus 数据库未运行

---

## 🎯 优化方案

### 1. 代码质量审查

#### 1.1 发现的问题

| 问题 | 位置 | 严重性 | 建议 |
|------|------|--------|------|
| CORS 允许所有来源 | `main.py` | 🔴 高 | 配置白名单 |
| API Key 明文存储 | `.env` | 🔴 高 | 加密存储 |
| .env 权限 664 | `.env` | 🟡 中 | 改为 600 |
| 缺少请求限流 | 所有服务 | 🟡 中 | 添加 slowapi |
| 缺少健康检查 | 部分服务 | 🟢 低 | 添加/health 端点 |
| 缺少日志轮转 | 所有服务 | 🟢 低 | 配置 logging.handlers |

#### 1.2 代码结构问题

```
当前结构：
backend/
├── knowledge-management/      # 单体架构
├── fastapi-document-retrieval/ # 微服务架构
├── chat/                       # 独立服务
└── Information-Extraction/     # 工具集合

问题：
- 架构不统一（单体 + 微服务混合）
- 重复代码（配置加载、日志初始化）
- 缺少共享库
```

**建议**: 创建 `backend/shared/` 模块，提取公共组件

---

### 2. 性能优化

#### 2.1 向量检索性能

**当前配置**:
```python
# Milvus 配置
MILVUS_HOST = localhost
MILVUS_PORT = 19530
# 缺少连接池配置
```

**优化建议**:
```python
# 连接池配置
connections.connect(
    alias="default",
    host=MILVUS_HOST,
    port=MILVUS_PORT,
    user="",
    password="",
)

# 索引优化
index_params = {
    "metric_type": "IP",  # 内积相似度
    "index_type": "HNSW",  # 高性能索引
    "params": {"M": 8, "efConstruction": 200}
}
```

#### 2.2 缓存机制

**推荐方案**: Redis 缓存

```python
# 缓存配置
REDIS_HOST = localhost
REDIS_PORT = 6379
CACHE_TTL = 3600  # 1 小时

# 缓存内容:
# - 常见问题答案
# - 向量检索结果
# - 用户会话状态
```

#### 2.3 并发处理

**当前**: 同步处理  
**优化**: 异步处理 + 任务队列

```python
# 使用 Celery + Redis
@app.post("/search")
async def search(query: str):
    task = search_task.delay(query)
    return {"task_id": task.id}

# 前端轮询结果
```

---

### 3. 架构优化

#### 3.1 服务间通信

**当前**: HTTP REST API  
**优化**: gRPC (高性能场景)

| 通信方式 | 延迟 | 吞吐量 | 适用场景 |
|----------|------|--------|----------|
| HTTP/1.1 | 中 | 中 | 外部 API |
| gRPC | 低 | 高 | 内部服务 |
| Redis Pub/Sub | 极低 | 极高 | 实时通知 |

#### 3.2 Docker 资源配置

```yaml
# docker-compose.yml 优化
services:
  milvus:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
  
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
```

#### 3.3 健康检查

```python
# 健康检查端点
@app.get("/health")
async def health():
    checks = {
        "database": check_db(),
        "milvus": check_milvus(),
        "redis": check_redis()
    }
    status = "healthy" if all(checks.values()) else "unhealthy"
    return {"status": status, "checks": checks}
```

#### 3.4 日志轮转

```python
# logging.conf
[loggers]
keys=root,app

[handlers]
keys=consoleHandler,rotatingFileHandler

[handler_rotatingFileHandler]
class=handlers.RotatingFileHandler
args=('logs/app.log', 'a', 10485760, 5)  # 10MB, 保留 5 个文件
```

---

### 4. 安全加固

#### 4.1 .env 文件权限

```bash
# 立即执行
chmod 600 backend/.env
chmod 600 backend/**/.env
```

#### 4.2 API Key 加密存储

**方案 1**: 使用 dotenv + 加密
```python
from cryptography.fernet import Fernet

# 加密存储
cipher = Fernet(key)
encrypted_key = cipher.encrypt(api_key.encode())

# 解密使用
api_key = cipher.decrypt(encrypted_key).decode()
```

**方案 2**: 使用密钥管理服务
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault

#### 4.3 CORS 白名单

```python
# 修改前
allow_origins=["*"]

# 修改后
allow_origins=[
    "http://localhost:3000",
    "http://localhost:5173",
    "https://yourdomain.com"
]
```

#### 4.4 请求限流

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/search")
@limiter.limit("10/minute")  # 每分钟 10 次
async def search(request: Request, query: str):
    ...
```

---

### 5. 文档完善

#### 5.1 文档结构

```
docs/
├── README.md              # 项目说明 (已存在)
├── OPTIMIZATION_PLAN.md   # 优化方案 (本文档)
├── DEPLOYMENT.md          # 部署指南
├── OPERATIONS.md          # 运维手册
├── API.md                 # API 文档
├── DEVELOPMENT.md         # 开发规范
└── TROUBLESHOOTING.md     # 故障排查
```

#### 5.2 运维手册内容

```markdown
# 运维手册

## 日常监控
- 服务状态检查
- 日志分析
- 性能指标

## 部署流程
1. 代码审查
2. 测试验证
3. 灰度发布
4. 全量发布

## 故障排查
- 常见问题清单
- 诊断流程
- 应急预案
```

---

## 📋 执行计划

### 阶段 1: 安全加固 (立即执行)
- [ ] .env 权限修改 (600)
- [ ] CORS 白名单配置
- [ ] 请求限流添加

### 阶段 2: 性能优化 (本周内)
- [ ] Redis 缓存集成
- [ ] Milvus 索引优化
- [ ] 连接池配置

### 阶段 3: 架构优化 (下周内)
- [ ] 共享库提取
- [ ] 健康检查统一
- [ ] 日志轮转配置

### 阶段 4: 文档完善 (本周末)
- [ ] 运维手册
- [ ] API 文档
- [ ] 开发规范

---

## 🎯 预期效果

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| API 响应时间 | 500ms | 200ms | 60% ↓ |
| 并发处理能力 | 100 QPS | 500 QPS | 5x ↑ |
| 安全性评分 | C | A | 显著提升 |
| 代码复用率 | 30% | 70% | 40% ↑ |

---

**最后更新**: 2026-03-11  
**维护者**: dev Agent
