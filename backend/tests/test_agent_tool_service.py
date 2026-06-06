from pathlib import Path

from fastapi.testclient import TestClient

from backend.agent_tools import tool_service as service


def _auth_headers():
    return {"X-API-Key": "test-tool-key"}


def test_tool_endpoints_require_configured_api_key(monkeypatch):
    monkeypatch.setenv("RAG_OCR_TOOL_API_KEY", "test-tool-key")

    response = TestClient(service.app).post("/tools/rag-ocr/healthcheck")

    assert response.status_code == 401


def test_tool_endpoints_fail_closed_without_configured_api_key(monkeypatch):
    monkeypatch.delenv("RAG_OCR_TOOL_API_KEY", raising=False)

    response = TestClient(service.app).post("/tools/rag-ocr/healthcheck")

    assert response.status_code == 503


def test_health_returns_service_status_and_default_config(monkeypatch):
    monkeypatch.setenv("RAG_OCR_AGENT_PDF_URL", "http://127.0.0.1:9106")

    response = TestClient(service.app).get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "rag-ocr-agent-tool-service"
    assert payload["tools"] == ["rag-ocr"]
    assert payload["default_config"]["pdf_extraction_url"] == "http://127.0.0.1:9106"
    assert "api_key" not in str(payload).lower()
    assert "token" not in str(payload).lower()


def test_rag_ocr_healthcheck_forwards_request_config(monkeypatch):
    captured = {}
    monkeypatch.setenv("RAG_OCR_TOOL_API_KEY", "test-tool-key")

    def fake_check_services(config):
        captured["config"] = config
        return {"status": "ok", "services": {"pdf_extraction": {"ok": True}}}

    monkeypatch.setattr(service.agent_tool, "check_services", fake_check_services)

    response = TestClient(service.app).post(
        "/tools/rag-ocr/healthcheck",
        json={"timeout_seconds": 2.5},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert captured["config"].timeout_seconds == 2.5


def test_healthcheck_rejects_request_level_url_overrides(monkeypatch):
    monkeypatch.setenv("RAG_OCR_TOOL_API_KEY", "test-tool-key")

    response = TestClient(service.app).post(
        "/tools/rag-ocr/healthcheck",
        json={"pdf_extraction_url": "http://169.254.169.254"},
        headers=_auth_headers(),
    )

    assert response.status_code == 422


def test_extract_policy_forwards_pdf_output_and_config(tmp_path, monkeypatch):
    pdf = tmp_path / "policy.pdf"
    pdf.write_bytes(b"%PDF-1.4 demo")
    captured = {}
    monkeypatch.setenv("RAG_OCR_TOOL_API_KEY", "test-tool-key")
    monkeypatch.setenv("RAG_OCR_TOOL_INPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("RAG_OCR_TOOL_OUTPUT_DIR", str(tmp_path / "out"))

    def fake_extract_policy(pdf_path, output_dir, config):
        captured["pdf_path"] = Path(pdf_path)
        captured["output_dir"] = Path(output_dir)
        captured["config"] = config
        return {
            "status": "ok",
            "source_pdf": str(pdf_path),
            "artifacts": {"markdown": str(Path(output_dir) / "policy.rag_ocr.md")},
        }

    monkeypatch.setattr(service.agent_tool, "extract_policy", fake_extract_policy)

    response = TestClient(service.app).post(
        "/tools/rag-ocr/extract-policy",
        json={
            "pdf_path": str(pdf),
            "output_dir": str(tmp_path / "out"),
            "timeout_seconds": 3,
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert captured["pdf_path"] == pdf
    assert captured["output_dir"] == tmp_path / "out"
    assert captured["config"].timeout_seconds == 3


def test_extract_policy_rejects_paths_outside_configured_roots(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_OCR_TOOL_API_KEY", "test-tool-key")
    monkeypatch.setenv("RAG_OCR_TOOL_INPUT_ROOT", str(tmp_path / "inputs"))
    monkeypatch.setenv("RAG_OCR_TOOL_OUTPUT_DIR", str(tmp_path / "outputs"))
    outside_pdf = tmp_path / "outside.pdf"
    outside_pdf.write_bytes(b"%PDF-1.4 demo")

    response = TestClient(service.app).post(
        "/tools/rag-ocr/extract-policy",
        json={"pdf_path": str(outside_pdf), "output_dir": str(tmp_path / "outside-output")},
        headers=_auth_headers(),
    )

    assert response.status_code == 400
    assert "outside configured root" in response.json()["error"]


def test_extract_policy_rejects_output_outside_configured_root(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_OCR_TOOL_API_KEY", "test-tool-key")
    monkeypatch.setenv("RAG_OCR_TOOL_INPUT_ROOT", str(tmp_path / "inputs"))
    monkeypatch.setenv("RAG_OCR_TOOL_OUTPUT_DIR", str(tmp_path / "outputs"))
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    pdf = input_dir / "policy.pdf"
    pdf.write_bytes(b"%PDF-1.4 demo")

    response = TestClient(service.app).post(
        "/tools/rag-ocr/extract-policy",
        json={"pdf_path": str(pdf), "output_dir": str(tmp_path / "outside-output")},
        headers=_auth_headers(),
    )

    assert response.status_code == 400
    assert "output directory is outside configured root" in response.json()["error"]


def test_extract_policy_returns_structured_error(monkeypatch):
    monkeypatch.setenv("RAG_OCR_TOOL_API_KEY", "test-tool-key")
    monkeypatch.setenv("RAG_OCR_TOOL_INPUT_ROOT", "/")

    def fake_extract_policy(pdf_path, output_dir, config):
        raise service.agent_tool.AgentToolError("PDF does not exist")

    monkeypatch.setattr(service.agent_tool, "extract_policy", fake_extract_policy)

    response = TestClient(service.app).post(
        "/tools/rag-ocr/extract-policy",
        json={"pdf_path": "/not/found.pdf"},
        headers=_auth_headers(),
    )

    assert response.status_code == 400
    assert response.json() == {"status": "failed", "error": "PDF does not exist"}
