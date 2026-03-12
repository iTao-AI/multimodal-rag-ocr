# Multimodal RAG - 部署流程

> 🚀 完整的部署流程图和步骤
> 
> **版本**: v1.0.0
> **最后更新**: 2026-03-12

---

## 📖 目录

- [部署架构总览](#-部署架构总览)
- [本地开发部署](#-本地开发部署)
- [生产环境部署](#-生产环境部署)
- [Docker 部署](#-docker-部署)
- [部署检查清单](#-部署检查清单)
- [回滚流程](#-回滚流程)

---

## 🏗️ 部署架构总览

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户访问层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Web 浏览器  │  │   移动设备   │  │  API 客户端   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS (443)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      负载均衡层 (Nginx)                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  • SSL 终止  • 请求路由  • 限流  • 静态文件服务           │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   前端服务       │ │   后端服务       │ │   后端服务       │
│   (Nginx)       │ │   (Instance 1)  │ │   (Instance 2)  │
│   Port: 80      │ │   Port: 8000-8501│ │  Port: 8000-8501│
└─────────────────┘ └─────────────────┘ └─────────────────┘
                                              │
                              ┌───────────────┼───────────────┐
                              │               │               │
                              ▼               ▼               ▼
                    ┌─────────────────┐ ┌─────────────────┐
                    │   Milvus DB     │ │     Redis       │
                    │   Port: 19530   │ │   Port: 6379    │
                    │   (Docker)      │ │   (Cache)       │
                    └─────────────────┘ └─────────────────┘
```

---

## 💻 本地开发部署

### 部署流程图

```
开始
  │
  ▼
┌─────────────┐
│ 1. 克隆项目  │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 2. 安装依赖  │
│ • Conda 环境  │
│ • Python 包   │
│ • Node.js 包  │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 3. 配置环境  │
│ • .env 文件   │
│ • API Key   │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 4. 启动     │
│ Milvus      │
│ (Docker)    │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 5. 启动     │
│ 后端服务    │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 6. 启动     │
│ 前端服务    │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 7. 验证     │
│ 部署        │
└─────────────┘
  │
  ▼
结束
```

### 详细步骤

#### 步骤 1: 克隆项目

```bash
git clone <repository-url>
cd Multimodal_RAG
```

#### 步骤 2: 安装依赖

```bash
# Python 环境
conda create -n vlm_rag python=3.11 -y
conda activate vlm_rag
cd backend
pip install -r requirements.txt

# Node.js 环境
cd ../frontend
npm install
```

#### 步骤 3: 配置环境

```bash
# 后端配置
cd backend
cp .env.example .env
# 编辑 .env，填入 API Key 等配置

# 前端配置
cd ../frontend
cp .env.example .env
```

#### 步骤 4: 启动 Milvus

```bash
cd backend/Database/milvus_server
docker-compose up -d

# 验证
docker-compose ps
```

#### 步骤 5: 启动后端服务

```bash
cd backend
./start_all_services.sh

# 验证
./status_services.sh
```

#### 步骤 6: 启动前端服务

```bash
cd frontend
npm run dev
```

#### 步骤 7: 验证部署

```bash
# 访问前端
http://localhost:5173

# 访问 API 文档
http://localhost:8000/docs
http://localhost:8501/docs
```

---

## 🏭 生产环境部署

### 部署流程图

```
开始
  │
  ▼
┌─────────────┐
│ 1. 服务器   │
│ 准备        │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 2. 系统     │
│ 优化        │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 3. 安装     │
│ 基础软件    │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 4. 部署     │
│ Milvus      │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 5. 部署     │
│ 应用服务    │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 6. 配置     │
│ Nginx       │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 7. 配置     │
│ HTTPS       │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 8. 配置     │
│ 监控告警    │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 9. 压力     │
│ 测试        │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 10. 上线    │
│ 验证        │
└─────────────┘
  │
  ▼
结束
```

### 关键步骤详解

#### 步骤 1: 服务器准备

**推荐配置**:
| 组件 | 配置 |
|-----|------|
| CPU | 8 核+ |
| 内存 | 16GB+ |
| 磁盘 | 200GB SSD |
| 网络 | 公网 IP |

#### 步骤 2: 系统优化

```bash
# 文件描述符
ulimit -n 65536

# 网络参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
sysctl -p
```

#### 步骤 3: 安装基础软件

```bash
# Python
sudo apt-get install python3.11 python3.11-venv

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install nodejs

# Docker
sudo apt-get install docker.io
```

#### 步骤 4: 部署 Milvus

```yaml
# docker-compose.prod.yaml
version: '3.5'
services:
  etcd:
    environment:
      - ETCD_AUTO_COMPACTION_MODE=periodic
      - ETCD_AUTO_COMPACTION_RETENTION=1h
  
  milvus-standalone:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

#### 步骤 5: 部署应用服务

```bash
# 创建 systemd 服务
sudo vim /etc/systemd/system/multimodal-rag.service

# 启用服务
sudo systemctl enable multimodal-rag
sudo systemctl start multimodal-rag
```

#### 步骤 6: 配置 Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    client_max_body_size 100M;
}
```

#### 步骤 7: 配置 HTTPS

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 步骤 8: 配置监控告警

```yaml
# Prometheus 告警规则
groups:
  - name: multimodal-rag
    rules:
      - alert: HighErrorRate
        expr: error_rate > 0.05
        for: 5m
        
      - alert: HighLatency
        expr: p99_latency > 2000ms
        for: 5m
```

#### 步骤 9: 压力测试

```bash
# 使用 wrk 测试
wrk -t12 -c400 -d30s http://your-domain.com/api/chat

# 预期结果
# QPS > 100
# P99 < 2s
```

#### 步骤 10: 上线验证

```bash
# 健康检查
curl http://your-domain.com/api/health

# 功能测试
# 1. 上传文档
# 2. 创建知识库
# 3. 对话测试
```

---

## 🐳 Docker 部署

### 部署流程

```
开始
  │
  ▼
┌─────────────┐
│ 1. 构建     │
│ Docker 镜像  │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 2. 编写     │
│ docker-     │
│ compose.yml │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 3. 启动     │
│ 容器        │
└─────────────┘
  │
  ▼
┌─────────────┐
│ 4. 验证     │
│ 服务        │
└─────────────┘
  │
  ▼
结束
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  milvus:
    image: milvusdb/milvus:v2.6.0
    ports:
      - "19530:19530"
    environment:
      - ETCD_AUTO_COMPACTION_MODE=periodic
    volumes:
      - ./volumes/milvus:/var/lib/milvus

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
      - "8001:8001"
      - "8006:8006"
      - "8501:8501"
    environment:
      - MILVUS_HOST=milvus
    depends_on:
      - milvus

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

### 启动命令

```bash
# 构建并启动
docker-compose up -d --build

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

---

## ✅ 部署检查清单

### 部署前检查

| 检查项 | 状态 | 备注 |
|-------|------|------|
| 服务器配置 | ⬜ | CPU/内存/磁盘 |
| 网络连通性 | ⬜ | 公网 IP/防火墙 |
| 域名解析 | ⬜ | DNS 配置 |
| SSL 证书 | ⬜ | Let's Encrypt |
| API Key | ⬜ | 阿里云百炼 |
| 备份策略 | ⬜ | 数据备份计划 |

### 部署中检查

| 检查项 | 状态 | 备注 |
|-------|------|------|
| Milvus 启动 | ⬜ | docker-compose ps |
| 后端服务 | ⬜ | 4 个服务正常 |
| 前端构建 | ⬜ | npm run build |
| Nginx 配置 | ⬜ | 反向代理 |
| HTTPS 配置 | ⬜ | SSL 证书 |

### 部署后检查

| 检查项 | 状态 | 备注 |
|-------|------|------|
| 健康检查 | ⬜ | /health 端点 |
| 功能测试 | ⬜ | 上传/对话 |
| 性能测试 | ⬜ | QPS/延迟 |
| 日志检查 | ⬜ | 无错误日志 |
| 监控配置 | ⬜ | 告警规则 |

---

## 🔄 回滚流程

### 回滚触发条件

- 严重 Bug 影响核心功能
- 性能严重下降
- 数据异常
- 安全漏洞

### 回滚步骤

```bash
# 1. 停止当前服务
sudo systemctl stop multimodal-rag

# 2. 备份当前数据
tar -czf backup-$(date +%Y%m%d).tar.gz /path/to/data

# 3. 恢复上一版本
git checkout <previous-tag>

# 4. 重启服务
sudo systemctl start multimodal-rag

# 5. 验证功能
curl http://localhost/health
```

### 回滚验证

| 验证项 | 方法 | 预期 |
|-------|------|------|
| 服务状态 | systemctl status | active |
| 健康检查 | /health | 200 OK |
| 功能测试 | 核心功能 | 正常 |
| 日志检查 | tail -f logs | 无错误 |

---

## 📊 部署时间估算

| 阶段 | 本地开发 | 生产环境 |
|-----|---------|---------|
| 环境准备 | 10 分钟 | 30 分钟 |
| 依赖安装 | 15 分钟 | 20 分钟 |
| Milvus 部署 | 5 分钟 | 10 分钟 |
| 应用部署 | 5 分钟 | 15 分钟 |
| 配置优化 | 5 分钟 | 30 分钟 |
| 验证测试 | 10 分钟 | 30 分钟 |
| **总计** | **50 分钟** | **2.5 小时** |

---

## 📞 故障联系

### 部署问题

| 问题 | 排查方向 | 文档 |
|-----|---------|------|
| Milvus 启动失败 | Docker 日志 | [故障排查](TROUBLESHOOTING.md) |
| 服务无法访问 | 防火墙/端口 | [运维手册](OPERATIONS.md) |
| 性能问题 | 资源配置 | [优化方案](OPTIMIZATION_PLAN.md) |

---

**文档版本**: v1.0.0
**最后更新**: 2026-03-12
**维护者**: knowledge Agent
