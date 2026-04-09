# MinerU OCR 服务（V2.0）

本项目本地 Mac 无 NVIDIA GPU，OCR 功能需在 GPU 服务器上部署。

## AutoDL 接入步骤

1. 租用 AutoDL 实例（推荐 RTX 4090 / A100，24GB+ 显存）
2. 在 AutoDL 中克隆 MinerU 项目并构建 Docker 镜像
3. 启动 vllm-server + api + gradio 三个 profile
4. 修改本项目 `backend/.env` 中的远程地址指向 AutoDL 实例

```bash
# AutoDL 实例中执行
wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/docker/china/Dockerfile
docker build -t mineru-vllm:2.5.4 -f Dockerfile .
wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/docker/compose.yaml
docker compose -f compose.yaml --profile vllm-server --profile api --profile gradio up -d
```

详细部署文档见 `OPERATIONS.md`
