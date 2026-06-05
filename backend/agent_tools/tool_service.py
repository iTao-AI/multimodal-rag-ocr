from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

try:
    from backend.agent_tools import rag_ocr_agent_tool as agent_tool
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.agent_tools import rag_ocr_agent_tool as agent_tool


SERVICE_NAME = "rag-ocr-agent-tool-service"


class RagOcrConfigRequest(BaseModel):
    pdf_extraction_url: str | None = None
    text_chunking_url: str | None = None
    milvus_api_url: str | None = None
    chat_url: str | None = None
    timeout_seconds: float | None = Field(default=None, gt=0)


class ExtractPolicyRequest(RagOcrConfigRequest):
    pdf_path: str
    output_dir: str | None = None


def _env_str(name: str, fallback: str) -> str:
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else fallback


def _env_float(name: str, fallback: float) -> float:
    value = os.environ.get(name)
    if not value or not value.strip():
        return fallback
    try:
        parsed = float(value)
    except ValueError:
        return fallback
    return parsed if parsed > 0 else fallback


def _value_or_default(value: str | None, default: str) -> str:
    return value.strip() if value and value.strip() else default


def build_tool_config(overrides: RagOcrConfigRequest | None = None) -> agent_tool.ToolConfig:
    base = agent_tool.ToolConfig(
        pdf_extraction_url=_env_str("RAG_OCR_AGENT_PDF_URL", agent_tool.ToolConfig.pdf_extraction_url),
        text_chunking_url=_env_str("RAG_OCR_AGENT_CHUNK_URL", agent_tool.ToolConfig.text_chunking_url),
        milvus_api_url=_env_str("RAG_OCR_AGENT_MILVUS_URL", agent_tool.ToolConfig.milvus_api_url),
        chat_url=_env_str("RAG_OCR_AGENT_CHAT_URL", agent_tool.ToolConfig.chat_url),
        timeout_seconds=_env_float("RAG_OCR_AGENT_TIMEOUT_SECONDS", agent_tool.ToolConfig.timeout_seconds),
    )
    if overrides is None:
        return base
    return agent_tool.ToolConfig(
        pdf_extraction_url=_value_or_default(overrides.pdf_extraction_url, base.pdf_extraction_url),
        text_chunking_url=_value_or_default(overrides.text_chunking_url, base.text_chunking_url),
        milvus_api_url=_value_or_default(overrides.milvus_api_url, base.milvus_api_url),
        chat_url=_value_or_default(overrides.chat_url, base.chat_url),
        timeout_seconds=overrides.timeout_seconds or base.timeout_seconds,
    )


def default_output_dir() -> Path:
    return Path(_env_str("RAG_OCR_TOOL_OUTPUT_DIR", "agent-tool-output")).expanduser()


def config_to_public_dict(config: agent_tool.ToolConfig) -> dict[str, Any]:
    return {
        "pdf_extraction_url": config.pdf_extraction_url,
        "text_chunking_url": config.text_chunking_url,
        "milvus_api_url": config.milvus_api_url,
        "chat_url": config.chat_url,
        "timeout_seconds": config.timeout_seconds,
        "output_dir": str(default_output_dir()),
    }


def create_app() -> FastAPI:
    app = FastAPI(title="RAG-OCR Agent Tool Service", version="0.1.0")

    @app.exception_handler(agent_tool.AgentToolError)
    async def agent_tool_error_handler(_request, exc: agent_tool.AgentToolError):
        return JSONResponse(status_code=400, content={"status": "failed", "error": str(exc)})

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": SERVICE_NAME,
            "tools": ["rag-ocr"],
            "default_config": config_to_public_dict(build_tool_config()),
        }

    @app.post("/tools/rag-ocr/healthcheck")
    def rag_ocr_healthcheck(payload: RagOcrConfigRequest | None = None) -> dict[str, Any]:
        return agent_tool.check_services(build_tool_config(payload))

    @app.post("/tools/rag-ocr/extract-policy")
    def extract_policy(payload: ExtractPolicyRequest) -> dict[str, Any]:
        output_dir = Path(payload.output_dir).expanduser() if payload.output_dir else default_output_dir()
        return agent_tool.extract_policy(
            pdf_path=payload.pdf_path,
            output_dir=output_dir,
            config=build_tool_config(payload),
        )

    return app


app = create_app()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the RAG-OCR agent tool HTTP service")
    parser.add_argument("--host", default=os.environ.get("RAG_OCR_TOOL_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("RAG_OCR_TOOL_PORT", "8765")))
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload for local development")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    uvicorn.run("backend.agent_tools.tool_service:app", host=args.host, port=args.port, reload=args.reload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
