# Multimodal RAG - 故障排查手册

> 🔧 常见问题诊断与解决方案
> 
> **版本**: v1.0.0
> **最后更新**: 2026-03-12

---

## 📖 目录

- [故障排查流程](#-故障排查流程)
- [服务启动问题](#-服务启动问题)
- [Milvus 问题](#-milvus-问题)
- [API 问题](#-api-问题)
- [前端问题](#-前端问题)
- [性能问题](#-性能问题)
- [数据问题](#-数据问题)
- [网络问题](#-网络问题)

---

## 🔍 故障排查流程

### 标准排查流程

```
故障发生
    │
    ▼
┌─────────────┐
│ 1. 确认     │
│ 故障现象    │
└─────────────┘
    │
    ▼
┌─────────────┐
│ 2. 查看     │
│ 错误日志    │
└─────────────┘
    │
    ▼
┌─────────────┐
│ 3. 定位     │
│ 故障组件    │
└─────────────┘
    │
    ▼
┌─────────────┐
│ 4. 执行     │
│ 修复方案    │
└─────────────┘
    │
    ▼
┌─────────────┐
│ 5. 验证     │
│ 修复结果    │
└─────────────┘
    │
    ▼
┌─────────────┐
│ 6. 记录     │
│ 故障报告    │
└─────────────┘
    │
    ▼
结束
```

### 快速诊断命令

```bash
# 1. 检查服务状态
./status_services.sh

# 2. 查看端口占用
netstat -tuln | grep -E '8000|8001|8006|8501|19530'

# 3. 查看进程
ps aux | grep python

# 4. 查看日志
tail -f logs/*.log

# 5. 检查磁盘
df -h

# 6. 检查内存
free -h

# 7. 检查 Docker
docker-compose ps
```

---

## 🚀 服务启动问题

### 问题 1: 服务无法启动

**症状**:
```bash
./start_all_services.sh
# 无响应或立即退出
```

**可能原因**:
| 原因 | 概率 | 排查方法 |
|-----|------|---------|
| 端口被占用 | 40% | `lsof -i :8000` |
| 依赖未安装 | 30% | `pip list` |
| 配置文件错误 | 20% | `cat .env` |
| 权限问题 | 10% | `ls -la` |

**解决方案**:

```bash
# 1. 检查端口
lsof -i :8000
# 如果占用，杀死进程
kill -9 $(lsof -t -i:8000)

# 2. 检查依赖
pip install -r requirements.txt

# 3. 检查配置
cat backend/.env
# 确认 API Key 等配置正确

# 4. 检查权限
chmod +x start_all_services.sh
```

---

### 问题 2: 服务启动后立即退出

**症状**:
```bash
./start_all_services.sh
# 服务启动，但几秒后退出
```

**排查步骤**:

```bash
# 1. 查看日志
tail -f logs/chat.log

# 2. 查看系统日志
journalctl -u multimodal-rag

# 3. 手动启动测试
cd backend/chat
python kb_chat.py
```

**常见错误**:

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `Connection refused` | Milvus 未启动 | `docker-compose up -d` |
| `API Key invalid` | 配置错误 | 检查 .env 文件 |
| `Module not found` | 依赖缺失 | `pip install` |
| `Address in use` | 端口占用 | `kill` 占用进程 |

---

## 🗄️ Milvus 问题

### 问题 1: Milvus 无法启动

**症状**:
```bash
docker-compose ps
# milvus 状态为 Exit
```

**排查步骤**:

```bash
# 1. 查看 Milvus 日志
docker-compose logs milvus

# 2. 查看 etcd 日志
docker-compose logs etcd

# 3. 检查磁盘空间
df -h
docker system df
```

**常见解决方案**:

```bash
# 方案 1: 清理 etcd 日志
cd Database/milvus_server
docker-compose down
rm -rf volumes/_etcd/*
docker-compose up -d

# 方案 2: 重启 Milvus
docker-compose restart milvus

# 方案 3: 重新部署
docker-compose down
rm -rf volumes/*
docker-compose up -d
```

---

### 问题 2: Milvus 连接超时

**症状**:
```python
pymilvus.exceptions.MilvusException: <MilvusException: (code=2, message=connect timeout)>
```

**可能原因**:
| 原因 | 排查方法 | 解决方案 |
|-----|---------|---------|
| Milvus 未启动 | `docker-compose ps` | 启动 Milvus |
| 网络问题 | `telnet localhost 19530` | 检查防火墙 |
| 配置错误 | `cat .env` | 修正配置 |

**解决方案**:

```bash
# 1. 确认 Milvus 运行
docker-compose ps
# 应该看到 milvus-standalone running

# 2. 测试连接
telnet localhost 19530

# 3. 检查配置
cat backend/.env | grep MILVUS
# MILVUS_HOST=localhost
# MILVUS_PORT=19530

# 4. 重启 Milvus
docker-compose restart milvus
```

---

### 问题 3: Milvus 磁盘占用过高

**症状**:
```bash
df -h
# /var/lib/docker 占用>90%
```

**解决方案**:

```bash
# 1. 清理 etcd WAL 日志
cd Database/milvus_server/volumes
rm -rf _etcd/*

# 2. 清理 Docker 缓存
docker system prune -a

# 3. 配置自动压缩
# 编辑 docker-compose.yaml
etcd:
  environment:
    - ETCD_AUTO_COMPACTION_MODE=periodic
    - ETCD_AUTO_COMPACTION_RETENTION=1h

# 4. 设置监控告警
# 磁盘使用率>80% 时告警
```

---

## 📡 API 问题

### 问题 1: API 返回 500 错误

**症状**:
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error"
  }
}
```

**排查步骤**:

```bash
# 1. 查看错误日志
tail -f logs/chat.log | grep ERROR

# 2. 查看完整堆栈
cat logs/chat.log | grep -A 20 "Traceback"

# 3. 测试端点
curl http://localhost:8501/health
```

**常见原因**:

| 错误类型 | 原因 | 解决方案 |
|---------|------|---------|
| LLM API 错误 | API Key 无效/余额不足 | 检查阿里云账号 |
| Milvus 错误 | 连接断开/集合不存在 | 检查 Milvus 状态 |
| 代码错误 | Bug/异常 | 查看堆栈修复 |

---

### 问题 2: API 响应慢

**症状**:
```bash
# 正常响应时间<2s
# 实际响应时间>10s
```

**排查步骤**:

```bash
# 1. 测试各组件延迟
curl -w "@format.txt" http://localhost:8000/health
# format.txt: "Time: %{time_total}s\n"

# 2. 查看慢查询日志
cat logs/*.log | grep "took [5-9][0-9]s"

# 3. 检查系统资源
top
free -h
```

**优化方案**:

```bash
# 1. 优化 Milvus 索引
python optimize_index.py --index-type HNSW

# 2. 启用缓存
# 编辑 config.py，启用 Redis 缓存

# 3. 调整参数
# top_k: 50 → 20
# score_threshold: 0.3 → 0.5
```

---

### 问题 3: API 返回 429 (限流)

**症状**:
```json
{
  "error": "Too many requests"
}
```

**解决方案**:

```bash
# 1. 检查限流配置
cat backend/config.py | grep rate_limit

# 2. 调整限流参数
RATE_LIMIT_PER_MINUTE = 100  # 根据需求调整

# 3. 添加白名单
# 对于重要用户添加白名单

# 4. 水平扩展
# 部署多个实例，使用 Nginx 负载均衡
```

---

## 🖥️ 前端问题

### 问题 1: 前端无法访问

**症状**:
```
http://localhost:5173
# 浏览器显示无法连接
```

**排查步骤**:

```bash
# 1. 检查前端服务
cd frontend
npm run dev

# 2. 检查端口
lsof -i :5173

# 3. 查看构建错误
npm run build
```

**常见解决方案**:

```bash
# 方案 1: 重新安装依赖
rm -rf node_modules package-lock.json
npm install

# 方案 2: 清除缓存
npm cache clean --force
rm -rf .vite

# 方案 3: 更换端口
# vite.config.ts
server: {
  port: 5174  // 更换端口
}
```

---

### 问题 2: 前端页面空白

**症状**:
- 页面加载后空白
- 控制台有错误

**排查步骤**:

```javascript
// 1. 打开浏览器开发者工具
// 2. 查看 Console 错误
// 3. 查看 Network 请求
```

**常见原因**:

| 错误 | 原因 | 解决方案 |
|-----|------|---------|
| `Failed to fetch` | API 地址错误 | 检查 .env 配置 |
| `Module not found` | 依赖缺失 | `npm install` |
| `CORS error` | 跨域问题 | 配置后端 CORS |

---

## ⚡ 性能问题

### 问题 1: 检索速度慢

**症状**:
```
正常：<500ms
实际：>5s
```

**排查步骤**:

```bash
# 1. 检查 Milvus 索引
python check_index.py

# 2. 查看索引类型
# FLAT → 慢
# HNSW → 快

# 3. 测试检索延迟
python test_search.py --collection my_kb
```

**优化方案**:

```bash
# 方案 1: 重建索引
python rebuild_index.py --type HNSW --M 16 --efConstruction 200

# 方案 2: 启用缓存
# 编辑 config.py，启用 Redis 缓存

# 方案 3: 减少 top_k
# 50 → 20

# 方案 4: 增加资源
# CPU: 4 核 → 8 核
# 内存：8GB → 16GB
```

---

### 问题 2: 内存占用高

**症状**:
```bash
free -h
# 内存使用>90%
```

**排查步骤**:

```bash
# 1. 查看进程内存
ps aux --sort=-%mem | head

# 2. 查看 Python 进程
ps aux | grep python
```

**解决方案**:

```bash
# 方案 1: 限制进程内存
# systemd 配置
MemoryLimit=4G

# 方案 2: 优化代码
# 避免大对象常驻内存
# 使用生成器代替列表

# 方案 3: 增加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 💾 数据问题

### 问题 1: 文档上传失败

**症状**:
```json
{
  "success": false,
  "error": "Upload failed"
}
```

**可能原因**:
| 原因 | 排查 | 解决 |
|-----|------|------|
| 文件过大 | 检查文件大小 | 压缩或分片 |
| 格式错误 | 检查文件类型 | 使用 PDF/MD |
| 磁盘满 | `df -h` | 清理空间 |

**解决方案**:

```bash
# 1. 检查文件大小
ls -lh document.pdf
# >50MB 需要压缩

# 2. 检查磁盘空间
df -h

# 3. 检查上传目录权限
ls -la backend/uploads
chmod 755 backend/uploads
```

---

### 问题 2: 向量数据丢失

**症状**:
```
知识库存在，但检索不到文档
```

**排查步骤**:

```bash
# 1. 检查集合
python check_collection.py --name my_kb

# 2. 检查向量数量
# 应该有 N 条记录

# 3. 查看插入日志
cat logs/milvus_api.log | grep insert
```

**解决方案**:

```bash
# 方案 1: 重新插入
python reinsert_vectors.py --collection my_kb

# 方案 2: 从备份恢复
python restore_from_backup.py --backup backup.json

# 方案 3: 重新上传文档
# 通过前端重新上传
```

---

## 🌐 网络问题

### 问题 1: 跨域请求失败

**症状**:
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**解决方案**:

```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 问题 2: 外部访问失败

**症状**:
```
从外部机器无法访问服务
```

**排查步骤**:

```bash
# 1. 检查防火墙
sudo ufw status

# 2. 检查安全组
# 云服务器检查安全组规则

# 3. 测试端口
telnet your-ip 8000
```

**解决方案**:

```bash
# 方案 1: 开放防火墙
sudo ufw allow 8000
sudo ufw allow 8501
sudo ufw allow 5173

# 方案 2: 配置 Nginx
# 反向代理到后端服务

# 方案 3: 检查云安全组
# 添加入站规则
```

---

## 📊 故障排查检查清单

### 快速检查

| 检查项 | 命令 | 正常状态 |
|-------|------|---------|
| 服务状态 | `./status_services.sh` | 全部 running |
| 端口占用 | `netstat -tuln` | 端口监听 |
| 磁盘空间 | `df -h` | 使用<80% |
| 内存使用 | `free -h` | 使用<90% |
| Milvus 状态 | `docker-compose ps` | running |
| 日志错误 | `tail logs/*.log` | 无 ERROR |

### 深度检查

| 检查项 | 命令 | 正常状态 |
|-------|------|---------|
| API 响应 | `curl /health` | 200 OK |
| 检索延迟 | `python test_search.py` | <500ms |
| 连接数 | `netstat -an | grep ESTABLISHED` | <100 |
| 进程数 | `ps aux | grep python` | 4 个服务 |

---

## 📞 获取帮助

### 内部资源

| 资源 | 位置 |
|-----|------|
| 运维手册 | [OPERATIONS.md](OPERATIONS.md) |
| 优化方案 | [OPTIMIZATION_PLAN.md](OPTIMIZATION_PLAN.md) |
| API 文档 | [API.md](API.md) |

### 外部资源

| 资源 | 链接 |
|-----|------|
| Milvus 文档 | https://milvus.io/docs |
| FastAPI 文档 | https://fastapi.tiangolo.com |
| 阿里云百炼 | https://help.aliyun.com/product/42154.html |

---

**文档版本**: v1.0.0
**最后更新**: 2026-03-12
**维护者**: knowledge Agent
