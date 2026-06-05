# Agent Integration

This project exposes a small Python wrapper for upper-layer agents and automation scripts that need a stable RAG-OCR document ingestion entrypoint.

The wrapper is intentionally narrow:

- check local service health;
- run fast PDF extraction for one document;
- run markdown chunking;
- write deterministic artifacts;
- return machine-readable JSON.

It does not start Docker, manage Milvus, read API keys, call GPU OCR services, or insert documents into a vector database.

## Location

```bash
backend/agent_tools/rag_ocr_agent_tool.py
```

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

## URL Overrides

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
- It writes artifacts only to the caller-provided output directory.
- All service credentials remain server-side in the existing backend services.
