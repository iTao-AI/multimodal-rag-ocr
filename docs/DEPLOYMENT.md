# Multimodal RAG - 部署文档

> 🚀 完整的生产环境部署指南
> 
> **版本**: v1.0.0
> **最后更新**: 2026-03-11

---

## 📖 目录

- [环境要求](#-环境要求)
- [本地开发部署](#-本地开发部署)
- [生产环境部署](#-生产环境部署)
- [Docker 部署](#-docker-部署)
- [配置说明](#-配置说明)
- [服务管理](#-服务管理)
- [监控和日志](#-监控和日志)
- [故障排查](#-故障排查)

---

## 🖥️ 环境要求

### 硬件要求

| 环境 | CPU | 内存 | 磁盘 | GPU |
|-----|-----|------|------|-----|
| **开发** | 4 核 | 8GB | 50GB | 可选 |
| **生产** | 8 核+ | 16GB+ | 200GB+ | 推荐 |

### 软件要求

| 软件 | 版本 | 必需 |
|-----|------|------|
| Python | 3.8-3.11 | ✅ |
| Node.js | 16.0+ | ✅ |
| Docker | 20.0+ | ✅ (Milvus) |
| Conda | 最新 | 推荐 |
| Git | 最新 | ✅ |

### 外部依赖

| 服务 | 用途 | 必需 |
|-----|------|------|
| 阿里云百炼 | LLM + Embedding | ✅ |
| Milvus | 向量数据库 | ✅ |
| Redis | 缓存 (可选) | ⬜ |

---

## 💻 本地开发部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd Multimodal_RAG
```

### 2. 后端部署

```bash
# 创建 Conda 虚拟环境
conda create -n vlm_rag python=3.11 -y
conda activate vlm_rag

# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt
# 或使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入配置
```

### 3. 部署 Milvus

```bash
# 使用 Docker Compose
cd Database/milvus_server

# 启动 Milvus
docker-compose up -d

# 验证状态
docker-compose ps
```

### 4. 启动后端服务

```bash
# 返回后端目录
cd ../..

# 启动所有服务
./start_all_services.sh

# 验证状态
./status_services.sh
```

### 5. 前端部署

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
# 或使用国内镜像
npm install --registry=https://registry.npmmirror.com

# 配置环境变量
cp .env.example .env

# 启动开发服务器
npm run dev
```

### 6. 访问系统

**前端**: http://localhost:5173

**API 文档**:
- PDF 提取：http://localhost:8006/docs
- 文本切分：http://localhost:8001/docs
- 向量数据库：http://localhost:8000/docs
- 对话检索：http://localhost:8501/docs

---

## 🏭 生产环境部署

### 1. 服务器准备

**推荐配置**:
- CPU: 8 核+
- 内存：16GB+
- 磁盘：200GB SSD
- 网络：公网 IP

**系统优化**:
```bash
# 增加文件描述符限制
ulimit -n 65536

# 优化网络参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
sysctl -p
```

### 2. 安装依赖

```bash
# 安装系统依赖
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv nodejs npm docker.io

# 安装 Conda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### 3. 部署 Milvus (生产配置)

```yaml
# docker-compose.prod.yaml
version: '3.5'
services:
  etcd:
    environment:
      - ETCD_AUTO_COMPACTION_MODE=periodic
      - ETCD_AUTO_COMPACTION_RETENTION=1h
      - QUOTA_BACKEND_BYTES=8589934592
  
  milvus-standalone:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

### 4. 配置 Nginx

```nginx
# /etc/nginx/sites-available/multimodal-rag
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端 API 反向代理
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /chat/ {
        proxy_pass http://localhost:8501/;
        proxy_set_header Host $host;
    }
    
    # 文件上传大小限制
    client_max_body_size 100M;
}
```

### 5. 配置 systemd 服务

```ini
# /etc/systemd/system/multimodal-rag-backend.service
[Unit]
Description=Multimodal RAG Backend
After=network.target docker.service

[Service]
Type=forking
User=www-data
WorkingDirectory=/path/to/backend
ExecStart=/path/to/backend/start_all_services.sh
ExecStop=/path/to/backend/stop_all_services.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl enable multimodal-rag-backend
sudo systemctl start multimodal-rag-backend
sudo systemctl status multimodal-rag-backend
```

### 6. 配置 HTTPS

```bash
# 使用 Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🐳 Docker 部署

### 1. 构建镜像

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
EXPOSE 8000 8001 8006 8501

CMD ["./start_all_services.sh"]
```

```dockerfile
# Dockerfile.frontend
FROM node:18-alpine as build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 2. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  milvus:
    image: milvusdb/milvus:v2.6.0
    ports:
      - "19530:19530"
      - "9091:9091"
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
      - MILVUS_PORT=19530
    depends_on:
      - milvus
    volumes:
      - ./backend:/app
      - ./data:/app/data

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

### 3. 启动容器

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

## ⚙️ 配置说明

### 后端配置 (.env)

```bash
# ============ 大模型配置 ============
API_KEY=sk-your-api-key
MODEL_NAME=qwen3-vl-plus
MODEL_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ============ 嵌入模型配置 ============
EMBEDDING_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL_NAME=text-embedding-v4
EMBEDDING_API_KEY=sk-your-api-key

# ============ Milvus 配置 ============
MILVUS_HOST=localhost
MILVUS_PORT=19530

# ============ 文件存储配置 ============
UPLOAD_BASE_DIR=/path/to/uploads
EXTRACTION_RESULTS_DIR=/path/to/results
MAX_FILE_SIZE_MB=50

# ============ 服务端口 ============
INFOR_EXTRAC_SERVICE_PORT=8006
CHUNK_SERVICE_PORT=8001
MILVUS_API_PORT=8000
CHAT_SERVICE_PORT=8501
```

### 前端配置 (.env)

```bash
# API 地址
VITE_MILVUS_API_URL=http://localhost:8000
VITE_CHAT_API_URL=http://localhost:8501
VITE_EXTRACTION_API_URL=http://localhost:8006
VITE_CHUNK_API_URL=http://localhost:8001
```

### 生产环境配置

```bash
# .env.prod
# 使用域名而非 localhost
VITE_MILVUS_API_URL=https://api.your-domain.com
VITE_CHAT_API_URL=https://api.your-domain.com/chat
...

# 启用 HTTPS
VITE_USE_HTTPS=true
```

---

## 🔧 服务管理

### 启动脚本

```bash
# 启动所有服务
./start_all_services.sh

# 停止所有服务
./stop_all_services.sh

# 重启所有服务
./restart_all_services.sh

# 查看状态
./status_services.sh

# 测试服务
./test_services.sh
```

### 手动管理

```bash
# 启动单个服务
cd backend/Database/milvus_server
python milvus_api.py

# 查看 PID
cat pids/chat.pid

# 停止单个服务
kill $(cat pids/chat.pid)
```

### 自动重启

```bash
# 使用 systemd (推荐)
sudo systemctl enable multimodal-rag-backend

# 使用 supervisor
[program:multimodal-rag]
command=/path/to/start_all_services.sh
autostart=true
autorestart=true
```

---

## 📊 监控和日志

### 日志管理

```bash
# 查看所有日志
tail -f backend/logs/*.log

# 查看单个服务日志
tail -f backend/logs/chat.log

# 日志轮转
logrotate /etc/logrotate.d/multimodal-rag
```

### 监控指标

**关键指标**:
- API 响应时间
- 错误率
- QPS
- Milvus 连接数
- 磁盘使用率

**监控工具**:
- Prometheus + Grafana
- ELK Stack (日志)
- 阿里云监控

### 告警配置

```yaml
# 告警规则
alerts:
  - name: HighErrorRate
    condition: error_rate > 0.05
    duration: 5m
    
  - name: HighLatency
    condition: p99_latency > 2000ms
    duration: 5m
    
  - name: DiskUsage
    condition: disk_usage > 0.8
    duration: 10m
```

---

## 🔧 故障排查

### 常见问题

#### 1. Milvus 启动失败

**症状**: `connection refused`

**排查**:
```bash
# 检查 Docker 容器
docker-compose ps

# 查看 Milvus 日志
docker-compose logs milvus

# 检查端口
netstat -tuln | grep 19530
```

**解决**:
```bash
# 清理并重启
docker-compose down
rm -rf volumes/milvus/*
docker-compose up -d
```

---

#### 2. 服务端口占用

**症状**: `Address already in use`

**排查**:
```bash
lsof -i :8006
```

**解决**:
```bash
# 杀死占用进程
kill -9 $(lsof -t -i:8006)

# 或修改服务端口
# 编辑对应 Python 文件，修改 port 参数
```

---

#### 3. API Key 无效

**症状**: `401 Unauthorized`

**排查**:
```bash
# 检查 .env 配置
cat backend/.env | grep API_KEY

# 测试 API
curl -H "Authorization: Bearer sk-xxx" \
  https://dashscope.aliyuncs.com/compatible-mode/v1/models
```

**解决**:
- 确认 API Key 正确
- 检查账号余额
- 联系阿里云支持

---

#### 4. 磁盘空间不足

**症状**: `No space left on device`

**排查**:
```bash
df -h
du -sh /path/to/milvus/volumes/*
```

**解决**:
```bash
# 清理 etcd 日志
cd Database/milvus_server/volumes
rm -rf _etcd/*

# 清理旧日志
rm -rf backend/logs/*.log.*.gz

# 扩容磁盘
```

---

### 性能优化

#### 检索慢

```bash
# 检查 Milvus 索引
python check_index.py

# 优化索引
python optimize_index.py --index-type HNSW
```

#### 内存占用高

```bash
# 查看内存使用
ps aux | grep python

# 限制进程内存
systemctl edit multimodal-rag-backend
# 添加 MemoryLimit=4G
```

---

## 📝 部署检查清单

### 部署前

- [ ] 服务器配置检查
- [ ] 依赖安装完成
- [ ] Milvus 正常运行
- [ ] API Key 配置正确
- [ ] 防火墙规则配置
- [ ] 域名解析完成

### 部署后

- [ ] 所有服务启动
- [ ] 前端可访问
- [ ] API 测试通过
- [ ] 日志正常
- [ ] 监控告警配置
- [ ] 备份策略配置

### 安全加固

- [ ] HTTPS 配置
- [ ] API 认证启用
- [ ] CORS 配置
- [ ] 文件上传限制
- [ ] 速率限制配置
- [ ] 敏感信息加密

---

**文档版本**: v1.0.0
**最后更新**: 2026-03-11
