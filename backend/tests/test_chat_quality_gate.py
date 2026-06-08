import json

import pytest


def _llm_config():
    from chat.kb_chat import LLMConfig

    return LLMConfig(
        api_url="https://example.test/v1",
        api_key="***",
        model_name="test-model",
    )


def _request(**overrides):
    from chat.kb_chat import ChatRequest

    data = {
        "query": "What is the policy?",
        "collection_name": "kb",
        "llm_config": _llm_config(),
        "stream": False,
        "score_threshold": 0.2,
        "min_confidence_threshold": 0.6,
    }
    data.update(overrides)
    return ChatRequest(**data)


class FakeCache:
    def __init__(self, cached=None):
        self.cached = cached
        self.saved = None

    def get_query_result(self, collection_name, query):
        return self.cached

    def set_query_result(self, collection_name, query, payload):
        self.saved = payload


@pytest.fixture(autouse=True)
def stable_chat_config(monkeypatch):
    import chat.kb_chat as kb_chat

    cache = FakeCache()
    monkeypatch.setattr(kb_chat, "get_cache_manager", lambda: cache)
    monkeypatch.setattr(kb_chat, "QUERY_REWRITE_ENABLED", False)
    monkeypatch.setattr(kb_chat, "HYBRID_SEARCH_ENABLED", False)
    return cache


@pytest.mark.asyncio
async def test_non_stream_rejects_when_no_documents(monkeypatch):
    from chat.kb_chat import ChatService

    service = ChatService()

    async def no_documents(**kwargs):
        return []

    monkeypatch.setattr(service, "retrieve_documents", no_documents)

    async def fail_llm(*args, **kwargs):
        raise AssertionError("LLM should not be called for low-confidence answers")

    monkeypatch.setattr(service, "call_llm_non_stream", fail_llm)

    response = await service.chat_non_stream(_request())

    assert response.success is True
    assert "没有足够可靠依据" in response.answer
    assert response.sources is None
    assert response.quality_report.status == "rejected"
    assert response.quality_report.issues[0]["code"] == "no_retrieved_documents"
    assert response.metadata["llm_time"] == 0


@pytest.mark.asyncio
async def test_non_stream_rejects_low_confidence_cached_answer(monkeypatch, stable_chat_config):
    from chat.kb_chat import ChatService

    stable_chat_config.cached = {
        "answer": "Stale cached answer",
        "sources": [
            {
                "chunk_text": "Weak cached policy fragment",
                "filename": "policy.pdf",
                "score": 0.42,
                "metadata": {"page_start": 1},
            }
        ],
    }
    service = ChatService()

    async def fail_retrieve(**kwargs):
        raise AssertionError("Retrieval should not be called on cache hit")

    async def fail_llm(*args, **kwargs):
        raise AssertionError("LLM should not be called for low-confidence cached answers")

    monkeypatch.setattr(service, "retrieve_documents", fail_retrieve)
    monkeypatch.setattr(service, "call_llm_non_stream", fail_llm)

    response = await service.chat_non_stream(_request())

    assert response.answer != "Stale cached answer"
    assert "没有足够可靠依据" in response.answer
    assert response.quality_report.status == "rejected"
    assert response.quality_report.issues[0]["code"] == "low_max_score"
    assert response.metadata["cache_hit"] is True
    assert response.metadata["llm_time"] == 0


@pytest.mark.asyncio
async def test_non_stream_rejects_low_confidence_documents(monkeypatch):
    from chat.kb_chat import ChatService

    service = ChatService()

    async def low_confidence_documents(**kwargs):
        return [
            {
                "id": "doc-1",
                "chunk_text": "Weak policy fragment",
                "filename": "policy.pdf",
                "score": 0.42,
                "metadata": {"page_start": 1},
            }
        ]

    monkeypatch.setattr(service, "retrieve_documents", low_confidence_documents)

    async def fail_llm(*args, **kwargs):
        raise AssertionError("LLM should not be called for low-confidence answers")

    monkeypatch.setattr(service, "call_llm_non_stream", fail_llm)

    response = await service.chat_non_stream(_request())

    assert "没有足够可靠依据" in response.answer
    assert response.sources is not None
    assert response.quality_report.status == "rejected"
    assert response.quality_report.max_score == 0.42
    assert response.quality_report.min_confidence_threshold == 0.6
    assert response.quality_report.issues[0]["code"] == "low_max_score"


@pytest.mark.asyncio
async def test_non_stream_allows_high_confidence_documents(monkeypatch):
    from chat.kb_chat import ChatService

    service = ChatService()

    async def high_confidence_documents(**kwargs):
        return [
            {
                "id": "doc-1",
                "chunk_text": "Strong policy answer",
                "filename": "policy.pdf",
                "score": 0.88,
                "metadata": {"page_start": 1},
            }
        ]

    monkeypatch.setattr(service, "retrieve_documents", high_confidence_documents)

    called = {"llm": 0}

    async def fake_llm(*args, **kwargs):
        called["llm"] += 1
        return "Grounded answer"

    monkeypatch.setattr(service, "call_llm_non_stream", fake_llm)

    response = await service.chat_non_stream(_request())

    assert called["llm"] == 1
    assert response.answer == "Grounded answer"
    assert response.quality_report.status == "passed"
    assert response.quality_report.issues == []


@pytest.mark.asyncio
async def test_stream_rejects_low_confidence_documents(monkeypatch):
    from chat.kb_chat import ChatService

    service = ChatService()

    async def no_documents(**kwargs):
        return []

    monkeypatch.setattr(service, "retrieve_documents", no_documents)

    async def fail_stream(*args, **kwargs):
        raise AssertionError("LLM should not be streamed for low-confidence answers")
        yield ""

    monkeypatch.setattr(service, "call_llm_stream", fail_stream)

    events = []
    async for line in service.chat_stream(_request(stream=True)):
        events.append(json.loads(line))

    assert events[0]["type"] == "quality_report"
    assert events[0]["data"]["status"] == "rejected"
    assert any(event["type"] == "content" for event in events)
    metadata = [event for event in events if event["type"] == "metadata"][0]["data"]
    assert metadata["llm_time"] == 0
    assert metadata["documents_count"] == 0
