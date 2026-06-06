# Agent Tool Service Design

## Context

`backend/agent_tools/rag_ocr_agent_tool.py` already gives agents a stable CLI for service health checks and single-PDF extraction/chunking. A local workspace Skill currently shells out to that CLI. That works for local automation, but it leaves the integration coupled to a script path and makes later tool integrations harder to share across agents.

## Goal

Add a small configurable HTTP tool service that wraps the existing RAG-OCR agent tool without duplicating extraction or chunking logic.

The service should let an upper-layer agent:

- check whether the tool service itself is reachable;
- check the RAG-OCR backend service stack;
- run PDF extraction/chunking for a local PDF path;
- override timeout per request;
- set safe defaults through environment variables;
- receive machine-readable JSON errors without secrets.

## Non-Goals

- No Docker, Milvus, or backend service startup orchestration.
- No OpenClaw-specific private paths in public documentation.
- No token, cookie, or `.env` access.
- No vector database insertion.
- No broad plugin registry in this phase.
- No frontend changes.

## API

Create `backend/agent_tools/tool_service.py`.

Endpoints:

- `GET /health`
  - Returns service process health and default configuration metadata.

- `POST /tools/rag-ocr/healthcheck`
  - Requires `X-API-Key`.
  - Body may include a timeout override.
  - Calls `rag_ocr_agent_tool.check_services`.
  - Returns the existing wrapper result.

- `POST /tools/rag-ocr/extract-policy`
  - Requires `X-API-Key`.
  - Body fields:
    - `pdf_path`: required local PDF path.
    - `output_dir`: optional output directory; defaults to `RAG_OCR_TOOL_OUTPUT_DIR` or `agent-tool-output`.
    - timeout override.
  - Calls `rag_ocr_agent_tool.extract_policy`.
  - Returns the existing wrapper summary.

## Configuration

Environment variables:

- `RAG_OCR_AGENT_PDF_URL`
- `RAG_OCR_AGENT_CHUNK_URL`
- `RAG_OCR_AGENT_MILVUS_URL`
- `RAG_OCR_AGENT_CHAT_URL`
- `RAG_OCR_AGENT_TIMEOUT_SECONDS`
- `RAG_OCR_TOOL_API_KEY`
- `RAG_OCR_TOOL_INPUT_ROOT`
- `RAG_OCR_TOOL_OUTPUT_DIR`

Upstream URLs remain server-controlled. Request-level URL overrides are rejected. Input and output paths must remain inside their configured roots.

## Error Handling

- `AgentToolError` becomes HTTP `400` with `{"status":"failed","error":"..."}`.
- Unexpected server errors become HTTP `500` with a generic JSON failure shape.
- The service does not log or return secret values.

## Testing

Add `backend/tests/test_agent_tool_service.py` using FastAPI `TestClient`.

Tests cover:

- service health returns configured defaults;
- tool endpoints require API-key authentication;
- healthcheck endpoint passes timeout overrides into the wrapper and rejects URL overrides;
- extract endpoint passes PDF path, output directory, and config into the wrapper;
- paths outside configured roots and non-PDF input are rejected;
- missing PDF or wrapper errors return structured HTTP `400`.

## Success Criteria

- `python -m pytest backend/tests/test_agent_tool_service.py -q` passes.
- Existing `backend/tests/test_agent_tool.py` still passes.
- `python backend/agent_tools/tool_service.py --help` works.
- Public docs describe the service neutrally and without private workflow context.
