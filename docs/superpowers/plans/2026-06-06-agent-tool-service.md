# Agent Tool Service Implementation Plan

**Goal:** Productize the existing RAG-OCR agent CLI wrapper into a configurable HTTP tool service.

**Architecture:** Keep `rag_ocr_agent_tool.py` as the source of extraction and healthcheck behavior. Add `tool_service.py` as a thin FastAPI adapter with environment defaults, request overrides, structured errors, and a small CLI for local startup.

## Task 1: RED Tests

- [x] Add `backend/tests/test_agent_tool_service.py`.
- [x] Test `GET /health` exposes service readiness and non-secret config.
- [x] Test `POST /tools/rag-ocr/healthcheck` forwards config overrides to `check_services`.
- [x] Test `POST /tools/rag-ocr/extract-policy` forwards PDF path, output directory, and config to `extract_policy`.
- [x] Test `AgentToolError` returns HTTP 400 with `status=failed`.
- [x] Run the focused test and confirm it fails because `tool_service.py` is missing.

## Task 2: GREEN Service

- [x] Create `backend/agent_tools/tool_service.py`.
- [x] Define Pydantic request models for config overrides and extraction.
- [x] Build `ToolConfig` from environment defaults plus request overrides.
- [x] Add `GET /health`.
- [x] Add `POST /tools/rag-ocr/healthcheck`.
- [x] Add `POST /tools/rag-ocr/extract-policy`.
- [x] Add CLI startup wrapper around `uvicorn.run`.

## Task 3: Documentation

- [x] Extend `docs/AGENT_INTEGRATION.md` with the HTTP tool service.
- [x] Keep docs neutral: no private workflow context, private paths, or key material.

## Task 4: Verification

- [x] Run `python -m pytest backend/tests/test_agent_tool_service.py backend/tests/test_agent_tool.py -q`.
- [x] Run `python backend/agent_tools/tool_service.py --help`.
- [x] Run a secret scan over changed files.
- [x] Check git diff.
- [x] Commit P17 changes after verification.
