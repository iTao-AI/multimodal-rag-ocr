# Multimodal RAG OCR

A knowledge base system with PDF document ingestion, OCR extraction, vector storage, and AI-powered Q&A. Supports both lightweight PDF extraction (V1.0) and enterprise-grade OCR pipelines (V2.0 with MinerU / PaddleOCR-VL / DeepSeek-OCR).

## Features

- **PDF Knowledge Extraction**: Parse PDFs into structured markdown with LLM/VLM
- **Multi-Mode OCR**: MinerU, PaddleOCR-VL, DeepSeek-OCR for complex document processing
- **Hybrid Search**: BM25 + vector fusion retrieval (RRF) with Redis caching
- **Query Rewrite**: Automatic query expansion for better recall
- **Real-Time Chat**: RAG-based Q&A over your document collection
- **Knowledge Base Management**: CRUD operations via Milvus vector database

## Architecture

```
Frontend (Vite, :5173)
  ├── KnowledgeBase management (CRUD via Milvus API)
  ├── Chat interface (via kb_chat service)
  └── Document viewer

Backend Services (4 independent FastAPI microservices):
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
       ├── kb_chat.py                  (main chat endpoint)
       └── query_rewrite.py            (query expansion service)
```

**Data flow**: Upload PDF → PDF Extraction → Text Chunking → Milvus (embed + store) → Chat (retrieve + answer)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| OCR Engine | MinerU / PaddleOCR-VL / DeepSeek-OCR |
| LLM | Qwen3-VL-Plus (DashScope) |
| Embedding | text-embedding-v4 (DashScope) |
| Vector DB | Milvus (with etcd + MinIO) |
| Cache | Redis (query result caching) |
| Hybrid Search | BM25 + Vector RRF fusion |
| Backend | FastAPI (4 microservices) |
| Frontend | Vue 3 + Vite |
| Deployment | Docker (Milvus), AutoDL GPU server (OCR) |

## Project Structure

```
multimodal-rag-ocr/
├── backend/
│   ├── chat/                 # RAG chat service (:8501)
│   │   ├── kb_chat.py        # Main chat endpoint
│   │   └── query_rewrite.py  # Query expansion
│   ├── common/               # Shared utilities (cache, etc.)
│   ├── Database/milvus_server/  # Milvus wrapper + hybrid search
│   │   ├── milvus_api.py     # FastAPI service (:8000)
│   │   ├── milvus_kb_service.py
│   │   └── utils.py          # BM25 + RRF fusion
│   ├── fastapi-document-retrieval/  # V1 document retrieval
│   ├── Information-Extraction/      # PDF extraction service (:8006)
│   │   └── unified/          # V1 + V2 unified extraction
│   ├── Text_segmentation/    # Text chunking service (:8001)
│   ├── knowledge-management/ # Knowledge base management UI
│   └── .env.example          # Backend configuration
├── frontend/                 # Vue 3 frontend
├── ragflow-deploy/           # RAGFlow deployment (optional)
└── docs/                     # Architecture and deployment docs
```

## Quick Start

### Prerequisites

- Python 3.11 (conda environment recommended)
- Node.js >= 18
- Docker (for Milvus)
- DashScope API key (for LLM + embedding)
- Tavily API key (optional, for web search)

### 1. Backend Setup

```bash
# Create conda environment
conda create -n vlm_rag python=3.11
conda activate vlm_rag

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and service URLs
```

### 2. Start Milvus

```bash
cd backend/Database/milvus_server

# Start Milvus (MUST be manual — never use restart: always)
docker compose -f docker-compose.yaml up -d

# Stop when done (prevents etcd WAL log bloat)
docker compose -f docker-compose.yaml down
```

### 3. Start Backend Services

```bash
cd backend
./start_all_services.sh

# Or start individual services:
python -m Information-Extraction.unified.unified_pdf_extraction_service  # :8006
python -m Text_segmentation.markdown_chunker_api                         # :8001
python -m Database.milvus_server.milvus_api                              # :8000
python -m chat.kb_chat                                                   # :8501
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## API Endpoints

| Service | Port | Key Endpoints |
|---------|------|---------------|
| PDF Extraction | 8006 | `POST /upload`, `POST /extract` |
| Text Chunking | 8001 | `POST /chunk` |
| Milvus API | 8000 | `POST /collections`, `POST /search` |
| Chat Service | 8501 | `POST /chat`, `POST /rewrite` |

## Configuration

All configuration is in `backend/.env`. Key settings:

- **LLM**: `MODEL_NAME`, `MODEL_URL`, `API_KEY`
- **Embedding**: `EMBEDDING_MODEL_NAME`, `EMBEDDING_URL`
- **Milvus**: `MILVUS_HOST`, `MILVUS_PORT`
- **OCR Services**: `DEEPSEEK_OCR_API_URL`, `MINERU_API_URL`, `PADDLEOCR_VL_API_URL`
- **Cache**: `CACHE_ENABLED`, `REDIS_HOST`
- **Hybrid Search**: `HYBRID_SEARCH_ENABLED`, `BM25_WEIGHT`, `VECTOR_WEIGHT`

## Critical Constraints

1. **Milvus must NEVER use `restart: always`** in docker-compose — etcd WAL logs will fill the disk. Always manual start/stop.
2. **No GPU on local Mac** — MinerU, PaddleOCR-VL, and DeepSeek-OCR require a remote GPU server (AutoDL). Local `.env` points to `localhost` as proxy.
3. **Python environment**: conda `vlm_rag` (Python 3.11), not system Python.

## License

MIT
