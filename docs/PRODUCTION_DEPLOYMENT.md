# 生产环境部署指南

**版本**: v1.0  
**最后更新**: 2026-03-13  
**维护者**: dev Agent

---

## 📋 目录

1. [环境要求](#环境要求)
2. [部署步骤](#部署步骤)
3. [配置优化](#配置优化)
4. [监控告警](#监控告警)
5. [故障排查](#故障排查)

---

## 环境要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 | 说明 |
|------|----------|----------|------|
| **CPU** | 4 核 | 8 核+ | Milvus 需要较多 CPU |
| **内存** | 8GB | 16GB+ | Milvus 占用较大 |
| **磁盘** | 50GB | 100GB+ | SSD 推荐 |
| **网络** | 100Mbps | 1Gbps+ | 高并发需要 |

### 软件要求

| 软件 | 版本 | 说明 |
|------|------|------|
| **Docker** | 20.10+ | 容器运行时 |
| **Docker Compose** | 2.0+ | 编排工具 |
| **Python** | 3.10+ | 后端运行环境 |
| **Node.js** | 16+ | 前端构建 (可选) |

---

## 部署步骤

### 1. 环境准备

```bash
# 1. 克隆项目
git clone https://github.com/iTao-AI/Multimodal_RAG.git
cd Multimodal_RAG

# 2. 检查 Docker
docker --version
docker compose --version

# 3. 创建数据目录
mkdir -p data/milvus data/mysql data/redis
```

### 2. 配置环境变量

```bash
# 复制环境配置示例
cp .env.example .env

# 编辑环境变量
vim .env
```

**.env 配置说明**:
```bash
# LLM 配置
DASHSCOPE_API_KEY=sk-xxx
DASHSCOPE_MODEL_NAME=qwen3-vl-plus

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# MySQL 配置
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=rag
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=rag_db

# Redis 配置 (可选)
REDIS_HOST=redis
REDIS_PORT=6379

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 3. Docker 部署

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

**服务列表**:
- `api` - FastAPI 后端服务 (端口 8000)
- `milvus` - Milvus 向量数据库 (端口 19530)
- `mysql` - MySQL 数据库 (端口 3306)
- `redis` - Redis 缓存 (端口 6379)
- `frontend` - React 前端 (端口 3000, 可选)

### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 预期响应
{
  "status": "healthy",
  "service": "knowledge-management",
  "timestamp": "2026-03-13T16:00:00"
}

# 测试搜索
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "测试", "top_k": 5}'

# 测试对话
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "你好", "collection_name": "documents"}'
```

### 5. 前端部署 (可选)

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 使用 Nginx 部署
docker compose -f docker-compose.frontend.yml up -d
```

---

## 配置优化

### API 服务优化

**docker-compose.yml**:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    environment:
      - WORKERS=4  # Gunicorn worker 数量
      - THREADS=2  # 每个 worker 线程数
```

### Milvus 优化

**milvus.yaml**:
```yaml
queryNode:
  loadMemoryUsageFactor: 0.9  # 内存使用因子
  maxConcurrentQueryNum: 16   # 最大并发查询数

dataNode:
  flush:
    bufferSize: 16MB          # 缓冲区大小
```

### MySQL 优化

**my.cnf**:
```ini
[mysqld]
max_connections = 500
innodb_buffer_pool_size = 2G
innodb_log_file_size = 512M
query_cache_size = 128M
```

---

## 监控告警

### Prometheus 配置

**prometheus.yml**:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'rag-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'milvus'
    static_configs:
      - targets: ['milvus:9091']
```

### Grafana 仪表盘

**导入仪表盘**:
1. 访问 http://localhost:3000
2. 登录 (admin/admin)
3. 导入 Dashboard ID: 10280 (Milvus 监控)
4. 导入 Dashboard ID: 10970 (FastAPI 监控)

**关键监控指标**:
- API 响应时间 (P50/P95/P99)
- 错误率
- Milvus 连接数
- Milvus 检索延迟
- MySQL 连接数
- Redis 命中率
- CPU/内存使用率
- 磁盘使用率

### 告警规则

**alerting_rules.yml**:
```yaml
groups:
  - name: rag_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "错误率过高"
          description: "API 错误率超过 10%"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        annotations:
          summary: "响应时间过长"
          description: "P95 响应时间超过 1 秒"

      - alert: MilvusDown
        expr: up{job="milvus"} == 0
        for: 1m
        annotations:
          summary: "Milvus 服务不可用"
```

---

## 故障排查

### 常见问题

#### 1. 服务无法启动

**症状**: Docker 容器启动失败

**排查步骤**:
```bash
# 查看容器日志
docker compose logs api

# 检查端口占用
lsof -i :8000

# 检查资源使用
docker stats
```

**解决方案**:
```bash
# 重启服务
docker compose restart

# 重新构建
docker compose build --no-cache

# 清理并重新部署
docker compose down -v
docker compose up -d
```

#### 2. Milvus 连接失败

**症状**: `pymilvus.exceptions.ConnectionError`

**排查步骤**:
```bash
# 检查 Milvus 状态
docker compose ps milvus

# 查看 Milvus 日志
docker compose logs milvus

# 测试连接
docker compose exec milvus bash
milvus-cli connect
```

**解决方案**:
```bash
# 重启 Milvus
docker compose restart milvus

# 检查配置
cat docker-compose.yml | grep -A 10 milvus
```

#### 3. 性能下降

**症状**: 响应时间变长，并发能力下降

**排查步骤**:
```bash
# 检查资源使用
docker stats

# 检查慢查询
docker compose exec mysql mysql -u root -p -e "SHOW PROCESSLIST;"

# 检查 Milvus 性能
curl http://localhost:9091/metrics
```

**解决方案**:
```bash
# 增加资源限制
vim docker-compose.yml
# 修改 CPU/内存限制

# 优化 Milvus 配置
vim milvus.yaml
# 调整 queryNode 配置

# 清理缓存
docker compose exec redis redis-cli FLUSHALL
```

#### 4. 磁盘空间不足

**症状**: 磁盘使用率 > 90%

**排查步骤**:
```bash
# 检查磁盘使用
df -h

# 查找大文件
du -sh data/* | sort -hr | head -10

# 检查 Docker 磁盘使用
docker system df
```

**解决方案**:
```bash
# 清理 Docker 缓存
docker system prune -a

# 清理 Milvus 日志
docker compose exec milvus bash
rm -rf /var/lib/milvus/logs/*

# 扩容磁盘
# (根据云平台操作)
```

### 紧急恢复流程

```
1. 发现问题
   ↓
2. 确认影响范围
   ↓
3. 启动应急预案
   ↓
4. 恢复服务 (重启/回滚)
   ↓
5. 问题定位
   ↓
6. 修复验证
   ↓
7. 事后复盘
```

**紧急联系人**:
- 技术负责人：[待填写]
- 运维负责人：[待填写]
- 备份负责人：[待填写]

---

## 备份恢复

### 数据备份

```bash
# MySQL 备份
docker compose exec mysql mysqldump -u root -p rag_db > backup_$(date +%Y%m%d).sql

# Milvus 备份
docker compose exec milvus backup_collection -c documents -o /backup/documents_backup

# 配置文件备份
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml
```

### 数据恢复

```bash
# MySQL 恢复
docker compose exec -T mysql mysql -u root -p rag_db < backup_20260313.sql

# Milvus 恢复
docker compose exec milvus restore_collection -c documents -i /backup/documents_backup
```

---

## 性能基准

### 预期性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| API 响应 (P50) | < 150ms | 简单查询 |
| API 响应 (P95) | < 500ms | 复杂查询 |
| API 响应 (P99) | < 1000ms | 极端情况 |
| 并发能力 | > 100 QPS | 成功率>99% |
| Milvus 检索 | < 200ms | P95 延迟 |
| 可用性 | > 99.9% | 月度可用性 |

---

**部署指南完成时间**: 2026-03-13  
**下次更新**: 2026-04-13

---

**生产环境部署指南完成！** 🦾
