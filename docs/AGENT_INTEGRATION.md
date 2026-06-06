# Agent Integration

This project exposes a small Python wrapper for upper-layer agents and automation scripts that need a stable RAG-OCR document ingestion entrypoint.

The wrapper is intentionally narrow:

- check local service health;
- run fast PDF extraction for one document;
- run markdown chunking;
- write deterministic artifacts;
- return machine-readable JSON.

It does not start Docker, manage Milvus, read backend-service credentials, call GPU OCR services, or insert documents into a vector database.

## Location

```bash
backend/agent_tools/rag_ocr_agent_tool.py
backend/agent_tools/tool_service.py
```

## HTTP Tool Service

For agents that prefer HTTP over shell execution, run the tool service:

```bash
python backend/agent_tools/tool_service.py --host 127.0.0.1 --port 8765
```

The service is a thin adapter over `rag_ocr_agent_tool.py`; extraction and chunking logic stays in the existing wrapper.
Set `RAG_OCR_TOOL_API_KEY` before starting it. All `/tools/*` requests must send the same value in `X-API-Key`.

### Service Health

```bash
curl http://127.0.0.1:8765/health
```

Returns:

```json
{
  "status": "ok",
  "service": "rag-ocr-agent-tool-service",
  "tools": ["rag-ocr"]
}
```

### RAG-OCR Stack Health

```bash
curl -X POST http://127.0.0.1:8765/tools/rag-ocr/healthcheck \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $RAG_OCR_TOOL_API_KEY" \
  -d '{"timeout_seconds": 5}'
```

### Extract And Chunk One Local PDF

```bash
curl -X POST http://127.0.0.1:8765/tools/rag-ocr/extract-policy \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $RAG_OCR_TOOL_API_KEY" \
  -d '{
    "pdf_path": "/path/to/policy.pdf",
    "output_dir": "/path/to/output-dir",
    "timeout_seconds": 30
  }'
```

The HTTP service returns the same artifact summary as the CLI wrapper.

### Service Configuration

Set defaults with environment variables:

| Variable | Purpose |
|---|---|
| `RAG_OCR_AGENT_PDF_URL` | PDF extraction service base URL |
| `RAG_OCR_AGENT_CHUNK_URL` | Text chunking service base URL |
| `RAG_OCR_AGENT_MILVUS_URL` | Milvus API base URL |
| `RAG_OCR_AGENT_CHAT_URL` | Chat service base URL |
| `RAG_OCR_AGENT_TIMEOUT_SECONDS` | Default upstream timeout |
| `RAG_OCR_TOOL_OUTPUT_DIR` | Default extraction artifact directory |
| `RAG_OCR_TOOL_INPUT_ROOT` | Allowed root for input PDFs, default current directory |
| `RAG_OCR_TOOL_API_KEY` | Required API key for `/tools/*` requests |
| `RAG_OCR_TOOL_HOST` | Tool service bind host |
| `RAG_OCR_TOOL_PORT` | Tool service port |

Request JSON may override only `timeout_seconds`. Upstream service URLs are server-controlled environment configuration and cannot be changed per request.

## Required Services

Start the normal backend stack before running extraction:

```bash
cd backend/Database/milvus_server
docker compose -f docker-compose.yaml up -d

cd ../..
bash start_all_services.sh
```

The wrapper checks these local endpoints:

| Service | URL |
|---|---|
| PDF Extraction | `http://127.0.0.1:8006/health` |
| Text Chunking | `http://127.0.0.1:8001/health` |
| Milvus API | `http://127.0.0.1:8000/health` |
| Chat | `http://127.0.0.1:8501/health` |

## Healthcheck

```bash
python backend/agent_tools/rag_ocr_agent_tool.py healthcheck
```

Example output when services are stopped:

```json
{
  "status": "failed",
  "services": {
    "pdf_extraction": {
      "ok": false,
      "url": "http://127.0.0.1:8006/health",
      "error": "<urlopen error [Errno 61] Connection refused>"
    }
  }
}
```

The command exits with:

- `0` when all required services are healthy;
- `1` when one or more services fail.

## Extract And Chunk One PDF

```bash
python backend/agent_tools/rag_ocr_agent_tool.py extract-policy \
  --pdf /path/to/policy.pdf \
  --out /path/to/output-dir
```

Generated artifacts:

| Artifact | Description |
|---|---|
| `<stem>.rag_ocr.md` | Markdown returned by `/extract/fast` |
| `<stem>.extract_fast.json` | Raw PDF extraction response |
| `<stem>.chunk.json` | Raw text chunking response |
| `<stem>.metadata_summary.json` | Compact summary with markdown length, metadata, images count, chunk stats, and artifact paths |

The command exits with:

- `0` when extraction and chunking both succeed;
- `1` when input validation, extraction, chunking, or JSON parsing fails.

## CLI URL Overrides

Use these flags when services run on non-default ports:

```bash
python backend/agent_tools/rag_ocr_agent_tool.py \
  --pdf-url http://127.0.0.1:8006 \
  --chunk-url http://127.0.0.1:8001 \
  --milvus-url http://127.0.0.1:8000 \
  --chat-url http://127.0.0.1:8501 \
  --timeout 10 \
  healthcheck
```

## Error Behavior

The wrapper fails explicitly for:

- missing input PDF;
- connection refused or timeout;
- non-2xx service response;
- malformed JSON response;
- extraction response without `success: true`;
- extraction response without non-empty markdown;
- chunking response without `success: true`.

It never falls back to empty markdown, random vectors, or guessed outputs.

## Security Notes

- The wrapper does not read `.env`.
- It does not print API keys or tokens.
- It does not send API keys to the frontend.
- The HTTP service requires `X-API-Key` for every `/tools/*` request.
- The HTTP service reads PDFs only below `RAG_OCR_TOOL_INPUT_ROOT`.
- The HTTP service writes artifacts only below `RAG_OCR_TOOL_OUTPUT_DIR`.
- The HTTP service rejects request-level upstream URL overrides.
- All service credentials remain server-side in the existing backend services.
