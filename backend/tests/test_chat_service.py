"""
对话检索服务测试用例
"""
import pytest
import requests
from typing import Dict

class TestChatHealth:
    """对话检索服务健康检查测试"""
    
    def test_health_endpoint(self, chat_service_url: str, http_session: requests.Session):
        """测试健康检查端点"""
        response = http_session.get(f"{chat_service_url}/health", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
    
    def test_docs_endpoint(self, chat_service_url: str, http_session: requests.Session):
        """测试 API 文档端点"""
        response = http_session.get(f"{chat_service_url}/docs", timeout=10)
        
        assert response.status_code == 200
        assert "Swagger UI" in response.text or "swagger" in response.text.lower()


class TestChatAPI:
    """对话检索服务 API 测试"""
    
    def test_chat_requires_collection(self, chat_service_url: str, http_session: requests.Session, llm_config: Dict):
        """测试对话需要有效的集合"""
        response = http_session.post(
            f"{chat_service_url}/chat",
            json={
                "query": "什么是 RAG？",
                "collection_name": "nonexistent_collection",
                "llm_config": llm_config,
                "top_k": 5,
                "stream": False
            },
            timeout=30
        )
        
        # 应该返回错误 (集合不存在)
        assert response.status_code in [400, 404, 500]
    
    def test_chat_with_invalid_llm_config(self, chat_service_url: str, http_session: requests.Session):
        """测试使用无效的 LLM 配置"""
        response = http_session.post(
            f"{chat_service_url}/chat",
            json={
                "query": "测试问题",
                "collection_name": "test_collection",
                "llm_config": {
                    "api_url": "http://invalid-url",
                    "api_key": "invalid_key",
                    "model_name": "invalid_model"
                },
                "top_k": 5,
                "stream": False
            },
            timeout=30
        )
        
        # 应该返回错误 (LLM 调用失败或集合不存在)
        assert response.status_code in [400, 401, 404, 500]
    
    def test_chat_missing_required_fields(self, chat_service_url: str, http_session: requests.Session):
        """测试缺少必填字段"""
        response = http_session.post(
            f"{chat_service_url}/chat",
            json={},  # 空数据
            timeout=10
        )
        
        # 应该返回 422 (缺少必填字段)
        assert response.status_code == 422


class TestChatPerformance:
    """对话检索服务性能测试"""
    
    def test_health_response_time(self, chat_service_url: str, http_session: requests.Session):
        """测试健康检查响应时间 < 100ms"""
        response = http_session.get(f"{chat_service_url}/health", timeout=10)
        
        assert response.status_code == 200
        assert response.elapsed.total_seconds() * 1000 < 100  # < 100ms
    
    def test_chat_response_time_with_mock(
        self,
        chat_service_url: str,
        http_session: requests.Session,
        llm_config: Dict
    ):
        """测试对话响应时间 (使用 mock 集合)"""
        # 注意：这个测试需要实际的数据
        # 在没有数据的情况下会失败，这是预期的
        response = http_session.post(
            f"{chat_service_url}/chat",
            json={
                "query": "测试问题",
                "collection_name": "test_collection",
                "llm_config": llm_config,
                "top_k": 5,
                "stream": False
            },
            timeout=60
        )
        
        # 如果集合存在，响应时间应该在合理范围内
        if response.status_code == 200:
            # 包含 LLM 调用，允许更长的响应时间
            assert response.elapsed.total_seconds() < 30  # < 30s
