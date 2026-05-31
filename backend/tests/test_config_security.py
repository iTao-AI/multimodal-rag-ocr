import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

import sys
import os

# Add parent directory to path so we can import chat.kb_chat
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from chat.kb_chat import app

client = TestClient(app)


class TestConfigSecurity:
    """
    Ensure the /config/default endpoint does not leak the LLM API key.
    Per Constitution Principle IV: "API keys MUST NEVER appear in Git history,
    frontend state, or API responses."
    """

    def test_default_config_hides_api_key(self):
        """API key must be empty or redacted even when API_KEY env var is set."""
        # Simulate production environment where API_KEY is configured
        with patch.dict(os.environ, {"API_KEY": "fake-api-key-for-test"}):
            response = client.get("/config/default")
        assert response.status_code == 200, (
            f"Expected status 200, got {response.status_code}: {response.text}"
        )
        data = response.json()
        api_key = data.get("config", {}).get("llm", {}).get("api_key", "")
        assert api_key == "" or api_key == "***", (
            f"API Key leaked in response: {api_key[:5]}..."
        )

    def test_default_config_returns_other_fields(self):
        """Other config fields should still be present and populated."""
        response = client.get("/config/default")
        assert response.status_code == 200
        data = response.json()
        config = data.get("config", {})
        llm = config.get("llm", {})
        retrieval = config.get("retrieval", {})

        # These fields should exist
        assert "api_url" in llm
        assert "model_name" in llm
        assert "temperature" in llm
        assert "max_tokens" in llm
        assert "top_k" in retrieval
        assert "score_threshold" in retrieval
        assert "available_models" in config
