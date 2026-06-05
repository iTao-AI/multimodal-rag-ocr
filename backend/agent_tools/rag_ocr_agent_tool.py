from __future__ import annotations

import argparse
import json
import mimetypes
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request


class AgentToolError(RuntimeError):
    """Raised when the agent tool cannot complete a requested operation."""


@dataclass(frozen=True)
class ToolConfig:
    pdf_extraction_url: str = "http://127.0.0.1:8006"
    text_chunking_url: str = "http://127.0.0.1:8001"
    milvus_api_url: str = "http://127.0.0.1:8000"
    chat_url: str = "http://127.0.0.1:8501"
    timeout_seconds: float = 10.0


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _read_json_response(response: Any) -> dict[str, Any]:
    raw = response.read()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise AgentToolError(f"invalid JSON response: {exc}") from exc
    if not isinstance(parsed, dict):
        raise AgentToolError("JSON response must be an object")
    return parsed


def _http_json(url: str, *, timeout: float) -> dict[str, Any]:
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            if status < 200 or status >= 300:
                raise AgentToolError(f"HTTP {status} from {url}")
            return _read_json_response(response)
    except AgentToolError:
        raise
    except (OSError, error.URLError, TimeoutError) as exc:
        raise AgentToolError(str(exc)) from exc


def _post_json(url: str, payload: dict[str, Any], *, timeout: float) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            if status < 200 or status >= 300:
                raise AgentToolError(f"HTTP {status} from {url}")
            return _read_json_response(response)
    except AgentToolError:
        raise
    except (OSError, error.URLError, TimeoutError) as exc:
        raise AgentToolError(str(exc)) from exc


def _post_multipart_file(url: str, pdf_path: Path, *, timeout: float) -> dict[str, Any]:
    boundary = f"----rag-ocr-agent-tool-{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(pdf_path.name)[0] or "application/pdf"
    file_bytes = pdf_path.read_bytes()
    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        (
            'Content-Disposition: form-data; name="file"; '
            f'filename="{pdf_path.name}"\r\n'
        ).encode("utf-8"),
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
        file_bytes,
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)
    req = request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            if status < 200 or status >= 300:
                raise AgentToolError(f"HTTP {status} from {url}")
            return _read_json_response(response)
    except AgentToolError:
        raise
    except (OSError, error.URLError, TimeoutError) as exc:
        raise AgentToolError(str(exc)) from exc


def check_services(config: ToolConfig) -> dict[str, Any]:
    services = {
        "pdf_extraction": _join_url(config.pdf_extraction_url, "/health"),
        "text_chunking": _join_url(config.text_chunking_url, "/health"),
        "milvus_api": _join_url(config.milvus_api_url, "/health"),
        "chat": _join_url(config.chat_url, "/health"),
    }

    results: dict[str, dict[str, Any]] = {}
    for name, url in services.items():
        started = time.perf_counter()
        try:
            payload = _http_json(url, timeout=config.timeout_seconds)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            results[name] = {
                "ok": True,
                "url": url,
                "latency_ms": elapsed_ms,
                "response": payload,
                "error": None,
            }
        except AgentToolError as exc:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            results[name] = {
                "ok": False,
                "url": url,
                "latency_ms": elapsed_ms,
                "response": None,
                "error": str(exc),
            }

    return {
        "status": "ok" if all(item["ok"] for item in results.values()) else "failed",
        "services": results,
    }


def extract_policy(pdf_path: Path | str, output_dir: Path | str, config: ToolConfig) -> dict[str, Any]:
    pdf = Path(pdf_path)
    if not pdf.exists():
        raise AgentToolError(f"PDF does not exist: {pdf}")
    if not pdf.is_file():
        raise AgentToolError(f"PDF path is not a file: {pdf}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = pdf.stem

    extraction_url = _join_url(config.pdf_extraction_url, "/extract/fast")
    extraction = _post_multipart_file(extraction_url, pdf, timeout=config.timeout_seconds)
    if extraction.get("success") is not True:
        raise AgentToolError(f"extraction failed: {extraction.get('message') or extraction.get('error')}")

    data = extraction.get("data")
    if not isinstance(data, dict):
        raise AgentToolError("extraction response missing data object")
    markdown = data.get("markdown")
    if not isinstance(markdown, str) or not markdown.strip():
        raise AgentToolError("extraction response missing markdown")

    chunk_url = _join_url(config.text_chunking_url, "/chunk")
    chunk_payload = {
        "markdown": markdown,
        "filename": f"{stem}.rag_ocr.md",
        "config": {
            "method": "header_recursive",
            "chunk_size": 1500,
            "chunk_overlap": 200,
            "merge_tolerance": 0.2,
            "max_page_span": 3,
            "bridge_span": 150,
            "add_bridges": True,
        },
        "metadata": {
            "source_filename": pdf.name,
            "pipeline": "rag_ocr_agent_tool",
        },
    }
    chunk_result = _post_json(chunk_url, chunk_payload, timeout=config.timeout_seconds)
    if chunk_result.get("success") is not True:
        raise AgentToolError(f"chunking failed: {chunk_result.get('message') or chunk_result.get('error')}")

    markdown_path = out_dir / f"{stem}.rag_ocr.md"
    extract_path = out_dir / f"{stem}.extract_fast.json"
    chunk_path = out_dir / f"{stem}.chunk.json"
    summary_path = out_dir / f"{stem}.metadata_summary.json"

    markdown_path.write_text(markdown, encoding="utf-8")
    extract_path.write_text(json.dumps(extraction, ensure_ascii=False, indent=2), encoding="utf-8")
    chunk_path.write_text(json.dumps(chunk_result, ensure_ascii=False, indent=2), encoding="utf-8")

    chunk_data = chunk_result.get("data") if isinstance(chunk_result.get("data"), dict) else {}
    chunk_stats = chunk_data.get("chunk_stats") if isinstance(chunk_data, dict) else None
    if not isinstance(chunk_stats, dict):
        chunk_stats = {}

    summary = {
        "source_pdf": str(pdf),
        "status": "ok",
        "markdown_chars": len(markdown),
        "metadata": data.get("metadata", {}),
        "images_count": len(data.get("images", []) if isinstance(data.get("images"), list) else []),
        "chunk_stats": chunk_stats,
        "artifacts": {
            "markdown": str(markdown_path),
            "extract_fast": str(extract_path),
            "chunk": str(chunk_path),
            "metadata_summary": str(summary_path),
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAG-OCR agent integration utility")
    parser.add_argument("--pdf-url", default=ToolConfig.pdf_extraction_url)
    parser.add_argument("--chunk-url", default=ToolConfig.text_chunking_url)
    parser.add_argument("--milvus-url", default=ToolConfig.milvus_api_url)
    parser.add_argument("--chat-url", default=ToolConfig.chat_url)
    parser.add_argument("--timeout", type=float, default=ToolConfig.timeout_seconds)

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("healthcheck", help="Check local RAG-OCR services")

    extract = subparsers.add_parser("extract-policy", help="Extract and chunk one PDF")
    extract.add_argument("--pdf", required=True, help="Input PDF path")
    extract.add_argument("--out", required=True, help="Output artifact directory")
    return parser


def _config_from_args(args: argparse.Namespace) -> ToolConfig:
    return ToolConfig(
        pdf_extraction_url=args.pdf_url,
        text_chunking_url=args.chunk_url,
        milvus_api_url=args.milvus_url,
        chat_url=args.chat_url,
        timeout_seconds=args.timeout,
    )


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    config = _config_from_args(args)

    try:
        if args.command == "healthcheck":
            result = check_services(config)
        elif args.command == "extract-policy":
            result = extract_policy(args.pdf, args.out, config)
        else:
            parser.error(f"unknown command: {args.command}")
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") == "ok" else 1
    except AgentToolError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
