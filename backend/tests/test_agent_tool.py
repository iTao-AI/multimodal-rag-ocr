import json
from pathlib import Path

import pytest

from backend.agent_tools import rag_ocr_agent_tool as tool


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def getcode(self):
        return self.status


def test_check_services_all_healthy(monkeypatch):
    def fake_urlopen(request, timeout):
        return FakeResponse({"status": "healthy"})

    monkeypatch.setattr(tool.request, "urlopen", fake_urlopen)

    result = tool.check_services(tool.ToolConfig(timeout_seconds=1))

    assert result["status"] == "ok"
    assert set(result["services"]) == {
        "pdf_extraction",
        "text_chunking",
        "milvus_api",
        "chat",
    }
    assert all(item["ok"] for item in result["services"].values())


def test_check_services_marks_failed_service(monkeypatch):
    def fake_urlopen(request, timeout):
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if ":8501" in url:
            raise OSError("connection refused")
        return FakeResponse({"status": "healthy"})

    monkeypatch.setattr(tool.request, "urlopen", fake_urlopen)

    result = tool.check_services(tool.ToolConfig(timeout_seconds=1))

    assert result["status"] == "failed"
    assert result["services"]["chat"]["ok"] is False
    assert "connection refused" in result["services"]["chat"]["error"]


def test_extract_policy_writes_artifacts(tmp_path, monkeypatch):
    pdf = tmp_path / "policy.pdf"
    pdf.write_bytes(b"%PDF-1.4 demo")

    def fake_urlopen(request, timeout):
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if url.endswith("/extract/fast"):
            return FakeResponse(
                {
                    "success": True,
                    "message": "fast extraction ok",
                    "filename": "policy.pdf",
                    "data": {
                        "markdown": "{{第1页}}\n# Policy\nA policy answer.",
                        "metadata": {"total_pages": 1, "total_images": 1},
                        "images": [{"name": "page_1_full.png"}],
                    },
                }
            )
        if url.endswith("/chunk"):
            return FakeResponse(
                {
                    "success": True,
                    "message": "chunk ok",
                    "filename": "policy.rag_ocr.md",
                    "data": {
                        "chunk_stats": {
                            "total_chunks": 1,
                            "bridge_chunks": 0,
                            "cross_page_chunks": 0,
                            "single_page_chunks": 1,
                            "table_chunks": 0,
                            "avg_chunk_length": 32.0,
                        },
                        "chunks": [{"text": "A policy answer."}],
                    },
                }
            )
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(tool.request, "urlopen", fake_urlopen)

    result = tool.extract_policy(
        pdf_path=pdf,
        output_dir=tmp_path / "out",
        config=tool.ToolConfig(timeout_seconds=1),
    )

    assert result["status"] == "ok"
    assert result["chunk_stats"]["total_chunks"] == 1
    for artifact_path in result["artifacts"].values():
        assert Path(artifact_path).exists()

    markdown = Path(result["artifacts"]["markdown"]).read_text(encoding="utf-8")
    assert "# Policy" in markdown

    summary = json.loads(Path(result["artifacts"]["metadata_summary"]).read_text())
    assert summary["markdown_chars"] == len(markdown)
    assert summary["metadata"]["total_pages"] == 1


def test_extract_policy_rejects_missing_pdf(tmp_path):
    with pytest.raises(tool.AgentToolError, match="PDF does not exist"):
        tool.extract_policy(
            pdf_path=tmp_path / "missing.pdf",
            output_dir=tmp_path / "out",
            config=tool.ToolConfig(),
        )


def test_extract_policy_rejects_missing_markdown(tmp_path, monkeypatch):
    pdf = tmp_path / "policy.pdf"
    pdf.write_bytes(b"%PDF-1.4 demo")

    def fake_urlopen(request, timeout):
        return FakeResponse(
            {
                "success": True,
                "message": "fast extraction ok",
                "filename": "policy.pdf",
                "data": {"metadata": {"total_pages": 1}},
            }
        )

    monkeypatch.setattr(tool.request, "urlopen", fake_urlopen)

    with pytest.raises(tool.AgentToolError, match="markdown"):
        tool.extract_policy(
            pdf_path=pdf,
            output_dir=tmp_path / "out",
            config=tool.ToolConfig(timeout_seconds=1),
        )
