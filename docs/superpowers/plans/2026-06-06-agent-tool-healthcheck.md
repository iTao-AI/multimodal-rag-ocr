# Agent Tool Healthcheck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a neutral CLI wrapper for RAG-OCR service health checks and PDF-to-markdown/chunk extraction.

**Architecture:** Implement a focused Python module under `backend/agent_tools/` with pure functions for service probing and extraction orchestration, plus a small argparse CLI. Tests mock HTTP calls and file writes so no live services or API keys are required.

**Tech Stack:** Python 3.11, stdlib `urllib.request`, `argparse`, `json`, `pytest`.

---

### Task 1: Agent Tool Tests

**Files:**
- Create: `backend/tests/test_agent_tool.py`

- [ ] **Step 1: Write healthcheck tests**

Create tests that mock `urllib.request.urlopen` and assert:

```python
def test_check_services_all_healthy(monkeypatch):
    ...
    result = tool.check_services(tool.ToolConfig(timeout_seconds=1))
    assert result["status"] == "ok"
    assert all(item["ok"] for item in result["services"].values())

def test_check_services_marks_failed_service(monkeypatch):
    ...
    result = tool.check_services(tool.ToolConfig(timeout_seconds=1))
    assert result["status"] == "failed"
    assert result["services"]["chat"]["ok"] is False
```

- [ ] **Step 2: Write extraction tests**

Create tests that mock the extraction and chunking HTTP calls and assert:

```python
def test_extract_policy_writes_artifacts(tmp_path, monkeypatch):
    pdf = tmp_path / "policy.pdf"
    pdf.write_bytes(b"%PDF-1.4 demo")
    result = tool.extract_policy(pdf, tmp_path / "out", tool.ToolConfig(timeout_seconds=1))
    assert result["status"] == "ok"
    assert Path(result["artifacts"]["markdown"]).exists()
    assert result["chunk_stats"]["total_chunks"] == 1
```

- [ ] **Step 3: Write failure tests**

Cover missing PDF and missing markdown:

```python
def test_extract_policy_rejects_missing_pdf(tmp_path):
    with pytest.raises(tool.AgentToolError):
        tool.extract_policy(tmp_path / "missing.pdf", tmp_path / "out", tool.ToolConfig())

def test_extract_policy_rejects_missing_markdown(tmp_path, monkeypatch):
    ...
    with pytest.raises(tool.AgentToolError, match="markdown"):
        tool.extract_policy(pdf, tmp_path / "out", tool.ToolConfig())
```

- [ ] **Step 4: Run tests and confirm RED**

Run:

```bash
cd /Users/mac/Developer/Projects/Active/multimodal-rag-ocr
python -m pytest backend/tests/test_agent_tool.py -q
```

Expected: fail because `backend.agent_tools.rag_ocr_agent_tool` does not exist.

### Task 2: Agent Tool Implementation

**Files:**
- Create: `backend/agent_tools/__init__.py`
- Create: `backend/agent_tools/rag_ocr_agent_tool.py`

- [ ] **Step 1: Implement data model and error type**

Define:

```python
class AgentToolError(RuntimeError):
    pass

@dataclass(frozen=True)
class ToolConfig:
    pdf_extraction_url: str = "http://127.0.0.1:8006"
    text_chunking_url: str = "http://127.0.0.1:8001"
    milvus_api_url: str = "http://127.0.0.1:8000"
    chat_url: str = "http://127.0.0.1:8501"
    timeout_seconds: float = 10.0
```

- [ ] **Step 2: Implement HTTP helpers**

Use `urllib.request` and return parsed JSON. Raise `AgentToolError` for connection errors, timeout, HTTP non-2xx, and invalid JSON.

- [ ] **Step 3: Implement `check_services`**

Probe:

```python
{
    "pdf_extraction": f"{config.pdf_extraction_url}/health",
    "text_chunking": f"{config.text_chunking_url}/health",
    "milvus_api": f"{config.milvus_api_url}/health",
    "chat": f"{config.chat_url}/health",
}
```

- [ ] **Step 4: Implement `extract_policy`**

Call:

```text
POST /extract/fast multipart file=<pdf>
POST /chunk JSON {markdown, filename, config, metadata}
```

Write four artifacts with deterministic names.

- [ ] **Step 5: Implement CLI**

Commands:

```bash
python backend/agent_tools/rag_ocr_agent_tool.py healthcheck
python backend/agent_tools/rag_ocr_agent_tool.py extract-policy --pdf path/to/doc.pdf --out output/dir
```

Return JSON to stdout. Exit `0` on ok and `1` on failure.

### Task 3: Documentation

**Files:**
- Create: `docs/AGENT_INTEGRATION.md`
- Modify: `docs/README.md`

- [ ] **Step 1: Add neutral integration guide**

Document:

- What the wrapper does.
- Required services.
- Commands.
- Output artifact names.
- Security notes.
- Error behavior.

- [ ] **Step 2: Link from docs README**

Add one link to `docs/AGENT_INTEGRATION.md`.

### Task 4: Verification and Commit

- [ ] **Step 1: Run targeted tests**

```bash
python -m pytest backend/tests/test_agent_tool.py -q
```

Expected: pass.

- [ ] **Step 2: Run backend tests**

```bash
python -m pytest backend/tests -q
```

Expected: pass, or record unrelated failures.

- [ ] **Step 3: Run CLI smoke without services**

```bash
python backend/agent_tools/rag_ocr_agent_tool.py healthcheck
```

Expected: JSON with `status: failed` when local services are stopped; no stack trace or key output.

- [ ] **Step 4: Secret scan**

```bash
rg -n 'sk-[A-Za-z0-9]|API_KEY=|Bearer [A-Za-z0-9._-]{16,}' backend/agent_tools docs/AGENT_INTEGRATION.md backend/tests/test_agent_tool.py
```

Expected: no real secrets.

- [ ] **Step 5: Commit**

```bash
git add backend/agent_tools backend/tests/test_agent_tool.py docs/AGENT_INTEGRATION.md docs/README.md docs/superpowers/specs/2026-06-06-agent-tool-healthcheck-design.md docs/superpowers/plans/2026-06-06-agent-tool-healthcheck.md
git commit -m "feat(agent-tools): add rag ocr healthcheck wrapper"
```
