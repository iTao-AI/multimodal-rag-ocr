# Milvus 健康检查日志

> 📊 自动监控记录 - 防止 etcd WAL 日志疯涨事故重演

---

## 📋 监控配置

| 配置项 | 值 |
|--------|-----|
| **检查频率** | 每 30 分钟 |
| **告警阈值** | 10GB |
| **自动清理阈值** | 5GB (etcd WAL) |
| **脚本位置** | `Database/milvus_server/health_check.sh` |
| **日志位置** | `Database/milvus_server/health_check.log` |

---

## 🚨 历史事故记录

### 2026-03-02 etcd WAL 日志疯涨事故

**影响**: 系统崩溃，磁盘占用 111GB

**根因**: 
- Milvus 的 etcd 组件 WAL 日志持续增长
- 未配置自动清理机制
- 未设置磁盘使用告警

**教训**:
1. ✅ 必须定期检查 etcd WAL 日志大小
2. ✅ 设置自动清理机制 (超过 5GB 自动清理)
3. ✅ 设置告警阈值 (超过 10GB 发送通知)
4. ✅ 定期 snapshot 和 defrag

---

## 📊 检查记录

### 2026-03-11 12:40:00

**状态**: ✅ 监控脚本已创建

**操作**:
- 创建健康检查脚本 `health_check.sh`
- 配置告警阈值 10GB
- 配置自动清理阈值 5GB
- 创建本日志文件

**下一步**:
- [x] 设置 cron 定时任务 (每 30 分钟) ✅
- [ ] 配置飞书群 webhook 告警 (可选)
- [x] 首次运行健康检查 ✅

---

## 🔧 使用说明

### 手动运行检查

```bash
cd ~/projects/demo/Multimodal_RAG/backend/Database/milvus_server
./health_check.sh
```

### 查看日志

```bash
tail -f health_check.log
```

### 配置飞书告警

```bash
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

### 设置 cron 任务

```bash
# 编辑 crontab
crontab -e

# 添加以下行 (每 30 分钟检查一次)
*/30 * * * * /Users/mac/projects/demo/Multimodal_RAG/backend/Database/milvus_server/health_check.sh >> /Users/mac/projects/demo/Multimodal_RAG/backend/Database/milvus_server/cron.log 2>&1
```

---

## 📁 相关文件

| 文件 | 说明 |
|------|------|
| `health_check.sh` | 健康检查脚本 |
| `health_check.log` | 检查日志 |
| `docker-compose.yaml` | Milvus Docker 配置 |
| `volumes/etcd/` | etcd 数据目录 |
| `volumes/minio/` | MinIO 数据目录 |
| `volumes/milvus/` | Milvus 数据目录 |

---

_最后更新：2026-03-11_

### 2026-03-11 12:40:20

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---


### 2026-03-11 13:00:00

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---


### 2026-03-11 13:30:00

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---


### 2026-03-11 14:00:01

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---


### 2026-03-11 14:30:00

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---


### 2026-03-11 15:00:00

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---


### 2026-03-11 15:30:01

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---


### 2026-03-11 16:00:00

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---


### 2026-03-11 16:30:00

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---


### 2026-03-11 17:00:00

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---


### 2026-03-11 17:30:01

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---


### 2026-03-11 18:00:00

**状态**: ✅ 正常

**存储使用情况**:
- etcd:   0B
- minio:   0B
- milvus:   0B

---

