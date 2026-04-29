# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Multimodal RAG OCR** — A knowledge base system with PDF document ingestion, OCR extraction, vector storage, and AI-powered Q&A. Two versions:
- **V1.0**: PyMuPDF4LLM + VLM extraction
- **V2.0**: MinerU + PaddleOCR-VL + DeepSeek-OCR (requires GPU server)

## Architecture

The system has 4 independent backend FastAPI microservices + 1 frontend (React + Vite):

```
Frontend (Vite, :5173)
  ├── KnowledgeBase management (CRUD via Milvus API)
  ├── Chat interface (via kb_chat service)
  └── Document viewer

Backend Services:
  ┌─ PDF Extraction (:8006) ── Extracts text/content from uploaded PDFs
  │    ├── llm_extraction.py          (V1.0: PyMuPDF4LLM + VLM)
  │    └── ocr_v2_extractors.py        (V2.0: MinerU/PaddleOCR/DeepSeek-OCR)
  │
  ├─ Text Chunking (:8001) ── Splits extracted markdown into chunks
  │    └── markdown_chunker_api.py
  │
  ├─ Vector Database (:8000) ── Milvus API wrapper for embedding + storage
  │    ├── milvus_api.py               (FastAPI wrapper around pymilvus)
  │    └── milvus_kb_service.py
  │    (Milvus runs via docker-compose with etcd + MinIO)
  │
  └─ Chat Service (:8501) ── RAG-based knowledge base Q&A
       └── kb_chat.py
```

**Data flow**: Upload PDF → PDF Extraction (text/markdown) → Text Chunking → Milvus (embed + store) → Chat (retrieve + answer)

## Key Commands

### Backend
```bash
# Activate conda environment (Python 3.11)
conda activate vlm_rag

# Install dependencies
cd backend
pip install -r requirements.txt

# Start all backend services
./start_all_services.sh

# Check status / Stop all
./status_services.sh
./stop_all_services.sh

# View logs
tail -f logs/<service_name>.log
```

### Milvus (Docker)
```bash
cd backend/Database/milvus_server

# Start Milvus (MUST be manual, never auto-restart)
docker compose -f docker-compose.yaml up -d

# Stop Milvus (prevents WAL log bloat)
docker compose -f docker-compose.yaml down
```

### Frontend
```bash
cd frontend
npm install       # first time
npm run dev       # → http://localhost:5173
npm run build     # production build
npm run lint      # ESLint
```

## Configuration

- **Backend**: `backend/.env` — LLM model, embedding, Milvus, OCR service URLs
- **Frontend**: `frontend/.env` (copy from `frontend/env.template`)
- Uses Alibaba DashScope API (qwen3-vl-plus model, text-embedding-v4)

## Critical Constraints

1. **Milvus must NEVER use `restart: always`** in docker-compose — etcd WAL logs will fill the disk. Always manual start/stop.
2. **No GPU on local Mac** — MinerU, PaddleOCR-VL, and DeepSeek-OCR require a remote GPU server (AutoDL). Local `.env` points to `localhost` as proxy; real IPs go in the GPU server's config.
3. **Python environment**: conda `vlm_rag` (Python 3.11), not system Python.
4. **Large directories excluded**: `minerU/MinerU_2_5_4/`, `node_modules/`, `backend/output/`, `backend/Database/milvus_server/data/volumes/` are in `.gitignore`.

## Remote Repository

`git@github.com:iTao-AI/multimodal-rag-ocr.git`
