# Multimodal RAG 运维手册

**版本**: v1.0  
**日期**: 2026-03-11  
**维护者**: dev Agent

---

## 📋 目录

1. [服务架构](#服务架构)
2. [日常监控](#日常监控)
3. [部署流程](#部署流程)
4. [故障排查](#故障排查)
5. [应急预案](#应急预案)

---

## 服务架构

### 服务清单

| 服务名称 | 端口 | 职责 | 进程名 |
|----------|------|------|--------|
| PDF 提取服务 | 8006 | PDF 文档解析 | `unified_pdf_extraction_service.py` |
| 文本切分服务 | 8001 | Markdown 文本切分 | `markdown_chunker_api.py` |
| 向量数据库服务 | 8000 | Milvus 向量检索 | `milvus_api.py` |
| 对话检索服务 | 8501 | RAG 对话生成 | `kb_chat.py` |

### 架构图

```
┌─────────────┐
│   前端界面   │
│  (React)    │
└──────┬──────┘
       │ HTTP
       ↓
┌─────────────────────────────────────┐
│         API Gateway (8000)          │
└──────┬──────────┬──────────┬────────┘
       │          │          │
       ↓          ↓          ↓
┌──────────┐ ┌──────────┐ ┌──────────┐
│ PDF 提取  │ │ 文本切分  │ │ 对话检索  │
│  (8006)  │ │  (8001)  │ │  (8501)  │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │
     └────────────┴────────────┘
                  │
                  ↓
          ┌───────────────┐
          │   Milvus DB   │
          │   (19530)     │
          └───────────────┘
```

---

## 日常监控

### 1. 服务状态检查

```bash
# 检查所有服务进程
ps aux | grep -E "(pdf|chunk|milvus|chat)" | grep -v grep

# 检查端口监听
lsof -nP -iTCP -sTCP:LISTEN | grep -E "(8000|8001|8006|8501)"

# 健康检查
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8006/health
curl http://localhost:8501/health
```

### 2. 日志分析

```bash
# 查看最新日志
tail -f backend/logs/app.log

# 查看错误日志
grep "ERROR" backend/logs/app.log | tail -20

# 日志统计
cat backend/logs/app.log | grep -c "ERROR"
cat backend/logs/app.log | grep -c "WARNING"
```

### 3. 性能指标

```bash
# CPU 使用率
top -pid $(pgrep -f "uvicorn|python") 

# 内存使用
ps aux | grep python | awk '{print $2, $3, $4, $11}'

# 磁盘使用
df -h ~/projects/demo/Multimodal_RAG
```

### 4. 监控脚本

```bash
#!/bin/bash
# monitor.sh - 服务监控脚本

SERVICES=("8000" "8001" "8006" "8501")
LOG_FILE="logs/monitor.log"

for port in "${SERVICES[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "✅ Port $port is OK" >> $LOG_FILE
    else
        echo "❌ Port $port is DOWN" >> $LOG_FILE
        # 发送告警
        # curl -X POST https://alert.example.com/webhook
    fi
done
```

---

## 部署流程

### 1. 代码审查

```bash
# 拉取最新代码
git pull origin main

# 代码质量检查
ruff check backend/
black --check backend/

# 运行测试
pytest backend/tests/ -v
```

### 2. 环境准备

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements-optimized.txt

# 检查环境变量
cp .env.example .env
# 编辑 .env 配置
```

### 3. 服务启动

```bash
cd backend

# 方式 1: 手动启动
python knowledge-management/main.py &
python chat/kb_chat.py &
python Information-Extraction/unified/unified_pdf_extraction_service.py &
python Text_segmentation/markdown_chunker_api.py &

# 方式 2: 使用启动脚本
./start_all_services.sh

# 方式 3: Docker 部署
docker compose up -d
```

### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8006/health
curl http://localhost:8501/health

# API 测试
curl -X POST http://localhost:8501/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "测试问题"}'

# 前端访问
open http://localhost:3000
```

### 5. 灰度发布

```bash
# 1. 部署到测试环境
# 2. 运行自动化测试
# 3. 10% 流量验证
# 4. 50% 流量验证
# 5. 100% 流量切换
```

---

## 故障排查

### 常见问题清单

#### 1. 服务无法启动

**症状**: 进程启动后立即退出

**排查步骤**:
```bash
# 1. 查看日志
tail -100 logs/app.log

# 2. 检查端口占用
lsof -i :8000

# 3. 检查依赖
pip list | grep fastapi

# 4. 检查配置
cat .env | grep API_KEY
```

**解决方案**:
```bash
# 释放端口
kill -9 $(lsof -t -i:8000)

# 重新安装依赖
pip install -r requirements-optimized.txt --force-reinstall
```

#### 2. Milvus 连接失败

**症状**: `pymilvus.exceptions.ConnectionError`

**排查步骤**:
```bash
# 1. 检查 Milvus 状态
docker ps | grep milvus

# 2. 检查网络
telnet localhost 19530

# 3. 查看 Milvus 日志
docker logs milvus-standalone
```

**解决方案**:
```bash
# 重启 Milvus
docker compose restart milvus

# 或重新部署
docker compose up -d milvus
```

#### 3. API 响应慢

**症状**: 请求响应时间 > 5 秒

**排查步骤**:
```bash
# 1. 检查 CPU
top

# 2. 检查内存
free -h

# 3. 检查磁盘 I/O
iostat -x 1

# 4. 检查慢查询
grep "slow" logs/app.log
```

**解决方案**:
```bash
# 优化 Milvus 索引
# 添加 Redis 缓存
# 增加服务实例
```

#### 4. 内存泄漏

**症状**: 内存使用持续增长

**排查步骤**:
```bash
# 1. 监控内存
ps aux | grep python | awk '{print $4}'

# 2. 分析内存
pip install memory_profiler
python -m memory_profiler script.py
```

**解决方案**:
```bash
# 重启服务
kill -9 $(pgrep -f "uvicorn")
./start_all_services.sh

# 长期方案：修复代码中的内存泄漏
```

---

## 应急预案

### P0 级故障（服务完全不可用）

**响应时间**: 5 分钟内

**处理流程**:
```
1. 确认故障范围
   ↓
2. 启动备用服务
   ↓
3. 通知相关人员
   ↓
4. 故障修复
   ↓
5. 服务恢复
   ↓
6. 事故复盘
```

**联系人**:
- 技术负责人：[待填写]
- 运维负责人：[待填写]
- 业务负责人：[待填写]

### P1 级故障（部分功能不可用）

**响应时间**: 30 分钟内

**处理流程**:
```
1. 定位故障服务
   ↓
2. 重启故障服务
   ↓
3. 验证功能恢复
   ↓
4. 记录故障日志
```

### P2 级故障（性能下降）

**响应时间**: 2 小时内

**处理流程**:
```
1. 性能分析
   ↓
2. 优化配置
   ↓
3. 监控验证
   ↓
4. 文档更新
```

---

## 附录

### A. 常用命令速查

```bash
# 服务管理
./start_all_services.sh      # 启动所有服务
./stop_all_services.sh       # 停止所有服务
./restart_all_services.sh    # 重启所有服务
./status_services.sh         # 查看服务状态

# 日志管理
tail -f logs/app.log         # 实时查看日志
grep "ERROR" logs/app.log    # 查看错误日志
logrotate -f logs/logrotate.conf  # 日志轮转

# 性能监控
top                          # CPU 监控
htop                         # 增强版 top
nmon                         # 综合监控

# 网络诊断
ping localhost               # 网络连通性
telnet localhost 8000        # 端口测试
curl http://localhost:8000/health  # 健康检查
```

### B. 配置文件位置

```
~/projects/demo/Multimodal_RAG/
├── backend/
│   ├── .env                    # 环境变量
│   ├── requirements.txt        # Python 依赖
│   └── logs/                   # 日志目录
├── docs/
│   ├── OPERATIONS.md           # 运维手册 (本文档)
│   ├── API.md                  # API 文档
│   └── TROUBLESHOOTING.md      # 故障排查
└── docker-compose.yml          # Docker 配置
```

### C. 监控指标阈值

| 指标 | 警告阈值 | 严重阈值 | 检查频率 |
|------|----------|----------|----------|
| CPU 使用率 | > 70% | > 90% | 1 分钟 |
| 内存使用率 | > 80% | > 95% | 1 分钟 |
| 磁盘使用率 | > 80% | > 90% | 5 分钟 |
| API 响应时间 | > 1s | > 5s | 实时 |
| 错误率 | > 1% | > 5% | 实时 |

---

**文档结束**

最后更新：2026-03-11  
下次审查：2026-03-18
