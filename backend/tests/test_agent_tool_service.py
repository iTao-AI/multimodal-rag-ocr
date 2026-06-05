from pathlib import Path

from fastapi.testclient import TestClient

from backend.agent_tools import tool_service as service


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

    def fake_check_services(config):
        captured["config"] = config
        return {"status": "ok", "services": {"pdf_extraction": {"ok": True}}}

    monkeypatch.setattr(service.agent_tool, "check_services", fake_check_services)

    response = TestClient(service.app).post(
        "/tools/rag-ocr/healthcheck",
        json={
            "pdf_extraction_url": "http://127.0.0.1:9106",
            "text_chunking_url": "http://127.0.0.1:9101",
            "timeout_seconds": 2.5,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert captured["config"].pdf_extraction_url == "http://127.0.0.1:9106"
    assert captured["config"].text_chunking_url == "http://127.0.0.1:9101"
    assert captured["config"].timeout_seconds == 2.5


def test_extract_policy_forwards_pdf_output_and_config(tmp_path, monkeypatch):
    pdf = tmp_path / "policy.pdf"
    pdf.write_bytes(b"%PDF-1.4 demo")
    captured = {}

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
            "text_chunking_url": "http://127.0.0.1:9101",
            "timeout_seconds": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert captured["pdf_path"] == pdf
    assert captured["output_dir"] == tmp_path / "out"
    assert captured["config"].text_chunking_url == "http://127.0.0.1:9101"
    assert captured["config"].timeout_seconds == 3


def test_extract_policy_returns_structured_error(monkeypatch):
    def fake_extract_policy(pdf_path, output_dir, config):
        raise service.agent_tool.AgentToolError("PDF does not exist")

    monkeypatch.setattr(service.agent_tool, "extract_policy", fake_extract_policy)

    response = TestClient(service.app).post(
        "/tools/rag-ocr/extract-policy",
        json={"pdf_path": "/not/found.pdf"},
    )

    assert response.status_code == 400
    assert response.json() == {"status": "failed", "error": "PDF does not exist"}
