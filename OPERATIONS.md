# Milvus 部署运维记录

## 2026-03-02: Milvus etcd WAL 日志疯涨事故（P0 级）

**问题**: Milvus 的 etcd 组件 WAL 日志没有自动清理，磁盘占用暴涨至 111GB

**解决**:
1. 停止 Milvus 服务
2. 清理 WAL 日志（504MB → 0）
3. 清理 npm 缓存（1.1GB → 8.9MB）
4. 关闭自动启动
5. 总计释放 ~100GB

## 2026-04-09: 项目迁移部署

### 项目信息
- **远程仓库**: `git@github.com:iTao-AI/multimodal-rag-ocr.git`
- **本地路径**: `/Users/mac/Developer/Projects/Active/multimodal-rag-ocr`
- **版本**: V1.0 (PyMuPDF4LLM+VLM) / V2.0 (MinerU+PaddleOCR-VL+DeepSeek-OCR)

### 后端服务

| 服务 | 端口 | 路径 |
|------|------|------|
| PDF提取 | 8006 | `backend/Information-Extraction/unified/unified_pdf_extraction_service.py` |
| 文本切分 | 8001 | `backend/Text_segmentation/markdown_chunker_api.py` |
| Milvus API | 8000 | `backend/Database/milvus_server/milvus_api.py` |
| 对话服务 | 8501 | `backend/chat/kb_chat.py` |

### 启动后端服务

```bash
cd backend
chmod +x start_all_services.sh
./start_all_services.sh
```

### Milvus 手动启停

```bash
# 进入 Milvus 目录
cd backend/Database/milvus_server

# 启动 Milvus
docker compose -f docker-compose.yaml up -d

# 用完即停（防止 WAL 日志暴涨）
docker compose -f docker-compose.yaml down
```

### 前端服务

```bash
cd frontend
npm run dev
# 访问 http://localhost:5173
```

### 环境变量配置

- 后端配置: `backend/.env`
- 前端配置: `frontend/.env`（从 `env.template` 复制）
- 注意：`.env` 文件中的路径已适配本机项目目录

### OCR 服务（V2.0，需 GPU 服务器）

本项目支持三种 OCR 模式：MinerU、PaddleOCR-VL、DeepSeek-OCR。本地 Mac 无 NVIDIA GPU，需在 AutoDL/GPU 服务器上部署。

#### AutoDL 接入方案

1. **租用 AutoDL 实例**（推荐 RTX 4090 或 A100，24GB+ 显存）
2. **在 AutoDL 上部署 MinerU**：
   ```bash
   # 在 AutoDL 实例中执行
   wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/docker/china/Dockerfile
   # 修改 Dockerfile 基础镜像
   # FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/vllm/vllm-openai:v0.11.2
   docker build -t mineru-vllm:2.5.4 -f Dockerfile .

   # 下载 compose.yaml 并启动
   wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/docker/compose.yaml
   docker compose -f compose.yaml --profile vllm-server --profile api --profile gradio up -d
   ```
3. **修改本地 `.env` 中的远程地址**：
   ```bash
   # backend/.env 中的 MinerU API 地址改为 AutoDL 实例 IP
   MINERU_API_URL=http://<AutoDL实例IP>:8001/file_parse
   VLLM_SERVER_URL=http://<AutoDL实例IP>:30000
   ```
4. **本地前端会自动调用 V2.0 OCR 接口**，后端将请求转发到远程 GPU 服务器

#### MinerU 本地目录

- `minerU/` 保留为空目录结构，Dockerfile 可从项目仓库获取
- 构建后的镜像约 50GB，不建议在本地 Mac 构建

### 依赖安装

```bash
# 后端（使用 vlm_rag conda 环境）
conda activate vlm_rag
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 注意事项

1. **Milvus 必须手动启停**，禁止使用 `restart: always`，否则 etcd WAL 日志会无限增长
2. **minerU 目录**已加入 `.gitignore`，不提交到仓库；本地 Mac 无 GPU 无法运行 OCR，需通过 AutoDL 接入
3. **node_modules** 和数据库数据目录均已排除，避免推送大文件
4. **Python 虚拟环境**: 使用 conda `vlm_rag`（Python 3.11），非系统 Python
