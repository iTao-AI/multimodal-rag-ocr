# Phase 5: Docker 统一编排 + 健康检查

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建统一 Docker Compose 一键启动全部服务，并添加健康检查编排替代 `sleep 2` 粗暴等待。

**Architecture:** 为 4 个 FastAPI 服务创建 Dockerfile，用 `docker-compose.full.yml` 统一编排（Milvus 基础设施 + 4 服务 + 前端构建），用健康检查脚本替代固定 sleep。

**Tech Stack:** Docker Compose v3.8, FastAPI/Uvicorn, Python 3.11 (vlm_rag), Node.js (前端构建)

---

## 当前状态

4 个 FastAPI 服务通过 `start_all_services.sh` 启动（PID 文件管理），Milvus 通过独立 `docker-compose.yaml` 启动，前端通过 `npm run dev` 启动。启动脚本用 `sleep 2` 等待服务就绪，无健康检查。

## 服务清单

| 服务 | 端口 | 入口文件 | 目录 |
|------|------|----------|------|
| PDF 提取 | 8006 | unified_pdf_extraction_service.py | Information-Extraction/unified/ |
| 文本切分 | 8001 | markdown_chunker_api.py | Text_segmentation/ |
| Milvus API | 8000 | milvus_api.py | Database/milvus_server/ |
| Chat 对话 | 8501 | kb_chat.py | chat/ |

---

### Task 5A: 统一 Docker Compose (#30)

**Files:**
- Create: `backend/Information-Extraction/unified/Dockerfile`
- Create: `backend/Text_segmentation/Dockerfile`
- Create: `backend/Database/milvus_server/Dockerfile`
- Create: `backend/chat/Dockerfile`
- Create: `backend/docker-compose.full.yml`
- Create: `backend/.dockerignore`
- Modify: `backend/.env.example` — 添加 Docker 相关变量

#### Step 1: 创建 PDF 提取服务 Dockerfile

```dockerfile
# backend/Information-Extraction/unified/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖并安装
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端公共模块
COPY common/ /app/common/
COPY requirements.txt /app/requirements.txt

# 复制服务代码
COPY Information-Extraction/unified/ /app/Information-Extraction/unified/

WORKDIR /app/Information-Extraction/unified

EXPOSE 8006

CMD ["python", "unified_pdf_extraction_service.py"]
```

#### Step 2: 创建文本切分服务 Dockerfile

```dockerfile
# backend/Text_segmentation/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ /app/common/
COPY Text_segmentation/ /app/Text_segmentation/

WORKDIR /app/Text_segmentation

EXPOSE 8001

CMD ["python", "markdown_chunker_api.py"]
```

#### Step 3: 创建 Milvus API 服务 Dockerfile

```dockerfile
# backend/Database/milvus_server/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ /app/common/
COPY Database/milvus_server/ /app/Database/milvus_server/

WORKDIR /app/Database/milvus_server

EXPOSE 8000

CMD ["python", "milvus_api.py"]
```

#### Step 4: 创建 Chat 服务 Dockerfile

```dockerfile
# backend/chat/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY common/ /app/common/
COPY chat/ /app/chat/

WORKDIR /app/chat

EXPOSE 8501

CMD ["python", "kb_chat.py"]
```

#### Step 5: 创建 .dockerignore

```
# backend/.dockerignore
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.env
*.log
logs/
pids/
output/
mineru_visualizations/
data/
tests/
knowledge-management/
knowledge-base-api/
fastapi-document-retrieval/
```

#### Step 6: 创建 docker-compose.full.yml

```yaml
# backend/docker-compose.full.yml
version: '3.8'

services:
  # === Milvus 基础设施 ===
  etcd:
    container_name: rag-etcd
    image: swr.cn-north-4.myhuaweicloud.com/ddn-k8s/quay.io/coreos/etcd:v3.5.5
    restart: "no"
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    volumes:
      - etcd-data:/etcd
    networks:
      - rag-net
    healthcheck:
      test: ["CMD", "etcdctl", "endpoint", "health"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    container_name: rag-minio
    image: quay.io/minio/minio:RELEASE.2025-06-13T11-33-47Z
    restart: "no"
    environment:
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY:-ragminio}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY:-ragminio123}
    volumes:
      - minio-data:/minio_data
    command: minio server /minio_data
    networks:
      - rag-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

  milvus:
    container_name: rag-milvus
    image: swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/milvusdb/milvus:v2.5.6-gpu
    restart: "no"
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
      COMMON_STORAGETYPE: minio
    volumes:
      - milvus-data:/var/lib/milvus
    depends_on:
      etcd:
        condition: service_healthy
      minio:
        condition: service_healthy
    networks:
      - rag-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 10s
      start_period: 30s
      timeout: 5s
      retries: 10

  # === FastAPI 微服务 ===
  pdf-extraction:
    build:
      context: ..
      dockerfile: backend/Information-Extraction/unified/Dockerfile
    ports:
      - "8006:8006"
    env_file:
      - .env
    environment:
      - PYTHONPATH=/app
    depends_on:
      milvus:
        condition: service_healthy
    networks:
      - rag-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8006/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  text-chunking:
    build:
      context: ..
      dockerfile: backend/Text_segmentation/Dockerfile
    ports:
      - "8001:8001"
    env_file:
      - .env
    environment:
      - PYTHONPATH=/app
    networks:
      - rag-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  milvus-api:
    build:
      context: ..
      dockerfile: backend/Database/milvus_server/Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - PYTHONPATH=/app
      - MILVUS_HOST=rag-milvus
      - MILVUS_PORT=19530
    depends_on:
      milvus:
        condition: service_healthy
    networks:
      - rag-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  chat:
    build:
      context: ..
      dockerfile: backend/chat/Dockerfile
    ports:
      - "8501:8501"
    env_file:
      - .env
    environment:
      - PYTHONPATH=/app
      - MILVUS_API_URL=http://milvus-api:8000
      - CHUNKING_SERVICE_URL=http://text-chunking:8001
      - EXTRACTION_API_URL=http://pdf-extraction:8006
    depends_on:
      milvus-api:
        condition: service_healthy
    networks:
      - rag-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/health"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  etcd-data:
  minio-data:
  milvus-data:

networks:
  rag-net:
    driver: bridge
```

#### Step 7: 更新 .env.example

```bash
# 追加到 backend/.env.example

# === Docker Compose 配置 ===
# Milvus 服务地址（容器内网络）
MILVUS_HOST=rag-milvus
MILVUS_PORT=19530

# 服务间通信地址
MILVUS_API_URL=http://milvus-api:8000
CHUNKING_SERVICE_URL=http://text-chunking:8001
EXTRACTION_API_URL=http://pdf-extraction:8006

# MinIO 安全凭证（生产环境必须修改）
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=

# 前端地址（CORS）
FRONTEND_URL=http://localhost:5173
```

#### Step 8: 验证

```bash
cd backend
docker compose -f docker-compose.full.yml config
```
Expected: YAML 解析成功，无语法错误。

#### Step 9: Commit

```bash
git add backend/Information-Extraction/unified/Dockerfile \
  backend/Text_segmentation/Dockerfile \
  backend/Database/milvus_server/Dockerfile \
  backend/chat/Dockerfile \
  backend/docker-compose.full.yml \
  backend/.dockerignore \
  backend/.env.example
git commit -m "feat: unified Docker Compose for all services (#30)"
```

---

### Task 5B: 健康检查编排 (#31)

**Files:**
- Create: `backend/health_check.sh`
- Modify: `backend/start_all_services.sh` — 替换 sleep 为健康检查
- Modify: `backend/stop_all_services.sh` — 添加健康检查确认停止

#### Step 1: 创建健康检查脚本

```bash
#!/bin/bash
# backend/health_check.sh
# 健康检查脚本 — 等待所有服务就绪

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
MAX_RETRIES=${HEALTH_CHECK_RETRIES:-30}
RETRY_INTERVAL=${HEALTH_CHECK_INTERVAL:-2}

# 服务列表: 名称:端口:健康端点
SERVICES=(
    "pdf_extraction:8006:/health"
    "text_chunking:8001:/health"
    "milvus_api:8000:/health"
    "chat:8501:/health"
)

# 检查单个服务
check_service() {
    local name=$1
    local port=$2
    local endpoint=$3
    local attempt=1

    while [ $attempt -le $MAX_RETRIES ]; do
        if curl -sf "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $name 就绪 (${attempt}s)"
            return 0
        fi
        sleep $RETRY_INTERVAL
        attempt=$((attempt + 1))
    done

    echo -e "  ${RED}✗${NC} $name 启动超时 (${MAX_RETRIES} 次重试)"
    return 1
}

# 主流程
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  健康检查 — 等待所有服务就绪${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

FAILED=0
for service in "${SERVICES[@]}"; do
    IFS=':' read -r name port endpoint <<< "$service"
    echo -e "${YELLOW}检查 $name (port:$port)...${NC}"
    if ! check_service "$name" "$port" "$endpoint"; then
        FAILED=1
    fi
done

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  所有服务已就绪${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  部分服务启动失败${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
```

#### Step 2: 确保 4 个服务都有 /health 端点

当前 4 个服务可能没有 `/health` 端点。在每个服务的主文件中添加：

```python
# 添加到每个 FastAPI 服务的 app 初始化之后
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}
```

需要修改的文件：
- `backend/Information-Extraction/unified/unified_pdf_extraction_service.py`
- `backend/Text_segmentation/markdown_chunker_api.py`
- `backend/Database/milvus_server/milvus_api.py`
- `backend/chat/kb_chat.py`

#### Step 3: 更新 start_all_services.sh

将脚本末尾的 `sleep 2` 替换为：

```bash
# 替换:
# sleep 2

# 为:
echo ""
echo -e "${BLUE}等待服务就绪...${NC}"
./health_check.sh
```

#### Step 4: 更新 stop_all_services.sh

添加停止确认：

```bash
# 在 stop_all_services.sh 末尾添加
echo ""
echo -e "${BLUE}确认服务已停止...${NC}"
ALL_STOPPED=true
for port in 8006 8001 8000 8501; do
    if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
        echo -e "  ${RED}✗${NC} 端口 $port 仍在响应"
        ALL_STOPPED=false
    fi
done
if [ "$ALL_STOPPED" = true ]; then
    echo -e "  ${GREEN}✓${NC} 所有服务已停止"
fi
```

#### Step 5: 验证

```bash
cd backend
chmod +x health_check.sh
bash -n health_check.sh && echo "Syntax OK"
bash -n start_all_services.sh && echo "start_all OK"
bash -n stop_all_services.sh && echo "stop_all OK"
```

#### Step 6: Commit

```bash
git add backend/health_check.sh \
  backend/start_all_services.sh \
  backend/stop_all_services.sh \
  backend/Information-Extraction/unified/unified_pdf_extraction_service.py \
  backend/Text_segmentation/markdown_chunker_api.py \
  backend/Database/milvus_server/milvus_api.py \
  backend/chat/kb_chat.py
git commit -m "feat: add health check orchestration, replace sleep with curl (#31)"
```

---

## Self-Review

### 1. Spec coverage
- #30 统一 Docker Compose: Task 5A 覆盖全部 4 个 Dockerfile + docker-compose.full.yml + .dockerignore + .env.example
- #31 健康检查编排: Task 5B 覆盖 health_check.sh + 4 个 /health 端点 + 更新 start/stop 脚本

### 2. Placeholder scan
- ✅ 无 TBD/TODO
- ✅ 所有代码步骤有实际代码
- ✅ 所有步骤有具体命令

### 3. Type/Name consistency
- ✅ 服务名称一致: pdf-extraction/text-chunking/milvus-api/chat
- ✅ 端口号一致: 8006/8001/8000/8501
- ✅ 网络名: rag-net 统一

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-30-phase5-docker-health.md`.

**Execution strategy:**
- 2 tasks, 独立可并行
- 但 Task 5B 依赖 5A 的 Dockerfile 中 healthcheck 配置，建议串行: 5A → 5B

**Which execution approach?**
1. **Subagent-Driven** (recommended) — dispatch fresh subagent per task, review between tasks
2. **Inline Execution** — execute tasks in this session
