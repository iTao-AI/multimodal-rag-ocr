# Agent Tool Healthcheck Design

## Context

The project already exposes four local FastAPI services:

- PDF Extraction: `http://localhost:8006`
- Text Chunking: `http://localhost:8001`
- Milvus API: `http://localhost:8000`
- Chat: `http://localhost:8501`

The services can process PDFs and produce markdown/chunk outputs, but upper-layer agents currently need to know multiple service URLs and response shapes. This makes agent integration brittle and hard to demonstrate.

## Goal

Add a small, neutral CLI wrapper that lets an agent or automation script:

1. Check whether the RAG-OCR service stack is ready.
2. Run fast PDF extraction and chunking for a single document.
3. Save markdown, metadata, and chunk JSON artifacts in a deterministic output directory.
4. Return machine-readable JSON without reading or printing API keys.

## Non-Goals

- No new FastAPI microservice.
- No frontend changes in this phase.
- No product-specific private paths, job-prep wording, or private demo assumptions.
- No automatic Milvus startup or Docker management.
- No VLM/MinerU/PaddleOCR orchestration in this phase.
- No vector database insertion in this phase.

## Architecture

Create `backend/agent_tools/rag_ocr_agent_tool.py`.

It exposes pure functions and a CLI:

- `check_services(config) -> dict`
  - Sends `GET` requests to the four health endpoints.
  - Returns per-service status, URL, HTTP status, latency, and error.
  - Overall status is `ok` only if all required services are healthy.

- `extract_policy(pdf_path, output_dir, config) -> dict`
  - Validates the input PDF path.
  - Calls PDF Extraction `/extract/fast`.
  - Extracts markdown from `data.markdown`.
  - Calls Text Chunking `/chunk`.
  - Writes:
    - `<stem>.rag_ocr.md`
    - `<stem>.extract_fast.json`
    - `<stem>.chunk.json`
    - `<stem>.metadata_summary.json`
  - Returns artifact paths and chunk stats.

- CLI commands:
  - `healthcheck`
  - `extract-policy --pdf <path> --out <dir>`

## Error Handling

- Missing input PDF returns a non-zero CLI exit and a JSON error.
- Connection errors, timeouts, non-2xx status codes, and malformed JSON are explicit failures.
- Extraction responses with `success != true` fail with the service message.
- Missing markdown fails explicitly; no empty markdown artifact is silently accepted.
- Chunking responses with `success != true` fail with the service message.

## Security

- The wrapper does not read `.env`.
- It does not print API keys.
- It only calls local HTTP service URLs unless the caller overrides URLs explicitly.
- Output artifacts are written only to the caller-provided output directory.

## Testing

Add `backend/tests/test_agent_tool.py`.

Tests mock HTTP calls and verify:

- All services healthy returns overall `ok`.
- One failed service returns overall `failed`.
- `extract_policy` writes markdown, raw extraction JSON, chunk JSON, and metadata summary.
- Missing markdown fails explicitly.
- Missing PDF fails explicitly.

## Success Criteria

- `python -m pytest backend/tests/test_agent_tool.py -q` passes.
- Existing targeted backend tests continue to pass.
- `python backend/agent_tools/rag_ocr_agent_tool.py healthcheck` produces JSON.
- Documentation explains the wrapper as a neutral agent integration utility.
