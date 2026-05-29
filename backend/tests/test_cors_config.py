"""Tests for CORS configuration across all FastAPI services."""

import importlib
import os
import sys
from unittest.mock import patch

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _find_cors_middleware_kwargs(app):
    """Extract CORS middleware kwargs from a FastAPI app."""
    for mw in app.user_middleware:
        cls_name = getattr(mw.cls, "__name__", str(mw.cls))
        if "CORSMiddleware" in cls_name:
            return mw.kwargs
    return None


def _load_service_app(module_path):
    """Dynamically load a service module and return its 'app' attribute."""
    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)

    try:
        if module_path in sys.modules:
            del sys.modules[module_path]
        mod = importlib.import_module(module_path)
        return getattr(mod, "app", None)
    except Exception as e:
        pytest.skip(f"Cannot load {module_path}: {e}")


class TestCORSNotWildcard:
    """CORS must not use wildcard origins with credentials."""

    def test_kb_chat_no_wildcard_cors(self):
        """kb_chat.py must not use allow_origins=['*']"""
        with patch.dict(os.environ, {"FRONTEND_URL": "http://localhost:5173"}, clear=False):
            app = _load_service_app("backend.chat.kb_chat")
            assert app is not None, "kb_chat must expose 'app'"
            cors_kwargs = _find_cors_middleware_kwargs(app)
            assert cors_kwargs is not None, "kb_chat must have CORS middleware"
            origins = cors_kwargs.get("allow_origins", [])
            assert "*" not in origins, "kb_chat: allow_origins must not contain '*'"

    def test_milvus_api_no_wildcard_cors(self):
        """milvus_api.py must not use allow_origins=['*']"""
        with patch.dict(os.environ, {"FRONTEND_URL": "http://localhost:5173"}, clear=False):
            app = _load_service_app("backend.Database.milvus_server.milvus_api")
            assert app is not None, "milvus_api must expose 'app'"
            cors_kwargs = _find_cors_middleware_kwargs(app)
            assert cors_kwargs is not None, "milvus_api must have CORS middleware"
            origins = cors_kwargs.get("allow_origins", [])
            assert "*" not in origins, "milvus_api: allow_origins must not contain '*'"

    def test_markdown_chunker_no_wildcard_cors(self):
        """markdown_chunker_api.py must not use allow_origins=['*']"""
        with patch.dict(os.environ, {"FRONTEND_URL": "http://localhost:5173"}, clear=False):
            app = _load_service_app("backend.Text_segmentation.markdown_chunker_api")
            assert app is not None, "markdown_chunker_api must expose 'app'"
            cors_kwargs = _find_cors_middleware_kwargs(app)
            assert cors_kwargs is not None, "markdown_chunker_api must have CORS middleware"
            origins = cors_kwargs.get("allow_origins", [])
            assert "*" not in origins, "markdown_chunker_api: allow_origins must not contain '*'"

    def test_unified_extraction_no_wildcard_cors(self):
        """unified_pdf_extraction_service.py must not use allow_origins=['*']"""
        with patch.dict(os.environ, {"FRONTEND_URL": "http://localhost:5173"}, clear=False):
            app = _load_service_app("backend.Information_Extraction.unified.unified_pdf_extraction_service")
            assert app is not None, "unified_pdf_extraction_service must expose 'app'"
            cors_kwargs = _find_cors_middleware_kwargs(app)
            assert cors_kwargs is not None, "unified_pdf_extraction must have CORS middleware"
            origins = cors_kwargs.get("allow_origins", [])
            assert "*" not in origins, "unified_pdf_extraction: allow_origins must not contain '*'"


class TestCORSUsesFrontendURL:
    """CORS must read FRONTEND_URL from environment."""

    def test_kb_chat_uses_env_var(self):
        """kb_chat CORS must use FRONTEND_URL env var"""
        test_url = "http://test-frontend:3000"
        with patch.dict(os.environ, {"FRONTEND_URL": test_url}, clear=False):
            app = _load_service_app("backend.chat.kb_chat")
            cors_kwargs = _find_cors_middleware_kwargs(app)
            origins = cors_kwargs.get("allow_origins", [])
            assert test_url in origins, f"kb_chat: CORS must include {test_url} from FRONTEND_URL"

    def test_milvus_api_uses_env_var(self):
        """milvus_api CORS must use FRONTEND_URL env var"""
        test_url = "http://test-frontend:3000"
        with patch.dict(os.environ, {"FRONTEND_URL": test_url}, clear=False):
            app = _load_service_app("backend.Database.milvus_server.milvus_api")
            cors_kwargs = _find_cors_middleware_kwargs(app)
            origins = cors_kwargs.get("allow_origins", [])
            assert test_url in origins, f"milvus_api: CORS must include {test_url} from FRONTEND_URL"

    def test_markdown_chunker_uses_env_var(self):
        """markdown_chunker_api CORS must use FRONTEND_URL env var"""
        test_url = "http://test-frontend:3000"
        with patch.dict(os.environ, {"FRONTEND_URL": test_url}, clear=False):
            app = _load_service_app("backend.Text_segmentation.markdown_chunker_api")
            cors_kwargs = _find_cors_middleware_kwargs(app)
            origins = cors_kwargs.get("allow_origins", [])
            assert test_url in origins, f"markdown_chunker_api: CORS must include {test_url} from FRONTEND_URL"

    def test_unified_extraction_uses_env_var(self):
        """unified_pdf_extraction CORS must use FRONTEND_URL env var"""
        test_url = "http://test-frontend:3000"
        with patch.dict(os.environ, {"FRONTEND_URL": test_url}, clear=False):
            app = _load_service_app("backend.Information_Extraction.unified.unified_pdf_extraction_service")
            cors_kwargs = _find_cors_middleware_kwargs(app)
            origins = cors_kwargs.get("allow_origins", [])
            assert test_url in origins, f"unified_pdf_extraction: CORS must include {test_url} from FRONTEND_URL"


class TestCORSRestrictedMethods:
    """CORS must not allow all methods (*)."""

    def test_kb_chat_methods_restricted(self):
        """kb_chat must not allow all methods (*)"""
        with patch.dict(os.environ, {"FRONTEND_URL": "http://localhost:5173"}, clear=False):
            app = _load_service_app("backend.chat.kb_chat")
            cors_kwargs = _find_cors_middleware_kwargs(app)
            methods = cors_kwargs.get("allow_methods", [])
            assert "*" not in methods, "kb_chat: allow_methods must not be '*'"

    def test_milvus_api_methods_restricted(self):
        """milvus_api must not allow all methods (*)"""
        with patch.dict(os.environ, {"FRONTEND_URL": "http://localhost:5173"}, clear=False):
            app = _load_service_app("backend.Database.milvus_server.milvus_api")
            cors_kwargs = _find_cors_middleware_kwargs(app)
            methods = cors_kwargs.get("allow_methods", [])
            assert "*" not in methods, "milvus_api: allow_methods must not be '*'"

    def test_markdown_chunker_methods_restricted(self):
        """markdown_chunker_api must not allow all methods (*)"""
        with patch.dict(os.environ, {"FRONTEND_URL": "http://localhost:5173"}, clear=False):
            app = _load_service_app("backend.Text_segmentation.markdown_chunker_api")
            cors_kwargs = _find_cors_middleware_kwargs(app)
            methods = cors_kwargs.get("allow_methods", [])
            assert "*" not in methods, "markdown_chunker_api: allow_methods must not be '*'"

    def test_unified_extraction_methods_restricted(self):
        """unified_pdf_extraction must not allow all methods (*)"""
        with patch.dict(os.environ, {"FRONTEND_URL": "http://localhost:5173"}, clear=False):
            app = _load_service_app("backend.Information_Extraction.unified.unified_pdf_extraction_service")
            cors_kwargs = _find_cors_middleware_kwargs(app)
            methods = cors_kwargs.get("allow_methods", [])
            assert "*" not in methods, "unified_pdf_extraction: allow_methods must not be '*'"


class TestEnvExample:
    """backend/.env.example must include FRONTEND_URL."""

    def test_env_example_has_frontend_url(self):
        """backend/.env.example must define FRONTEND_URL"""
        env_example = os.path.join(BACKEND_DIR, ".env.example")
        assert os.path.exists(env_example), ".env.example must exist"
        with open(env_example, "r") as f:
            content = f.read()
        assert "FRONTEND_URL" in content, \
            ".env.example must include FRONTEND_URL configuration"
