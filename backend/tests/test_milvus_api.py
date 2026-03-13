"""
Milvus API 服务测试用例
"""
import pytest
import requests
from typing import Dict

class TestMilvusHealth:
    """Milvus API 服务健康检查测试"""
    
    def test_health_endpoint(self, milvus_service_url: str, http_session: requests.Session):
        """测试健康检查端点"""
        response = http_session.get(f"{milvus_service_url}/health", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
    
    def test_docs_endpoint(self, milvus_service_url: str, http_session: requests.Session):
        """测试 API 文档端点"""
        response = http_session.get(f"{milvus_service_url}/docs", timeout=10)
        
        assert response.status_code == 200
        assert "Swagger UI" in response.text or "swagger" in response.text.lower()


class TestMilvusAPI:
    """Milvus API 服务 API 测试"""
    
    def test_search_requires_collection(self, milvus_service_url: str, http_session: requests.Session):
        """测试搜索需要有效的集合"""
        response = http_session.post(
            f"{milvus_service_url}/search",
            json={
                "collection_name": "nonexistent_collection",
                "query_text": "test query",
                "top_k": 5
            },
            timeout=30
        )
        
        # 应该返回错误 (集合不存在)
        assert response.status_code in [400, 404, 500]
        
        if response.status_code == 500:
            data = response.json()
            assert "detail" in data
            assert "不存在" in str(data["detail"]) or "not exist" in str(data["detail"]).lower()
    
    def test_search_with_valid_params(self, milvus_service_url: str, http_session: requests.Session):
        """测试使用有效参数搜索"""
        response = http_session.post(
            f"{milvus_service_url}/search",
            json={
                "collection_name": "test_collection",
                "query_text": "测试查询",
                "top_k": 5
            },
            timeout=30
        )
        
        # 如果集合存在，应该返回结果
        # 如果不存在，应该返回明确的错误
        if response.status_code == 200:
            data = response.json()
            assert "results" in data or "data" in data or "status" in data


class TestMilvusPerformance:
    """Milvus API 服务性能测试"""
    
    def test_health_response_time(self, milvus_service_url: str, http_session: requests.Session):
        """测试健康检查响应时间 < 100ms"""
        response = http_session.get(f"{milvus_service_url}/health", timeout=10)
        
        assert response.status_code == 200
        assert response.elapsed.total_seconds() * 1000 < 100  # < 100ms
    
    def test_search_timeout_handling(self, milvus_service_url: str, http_session: requests.Session):
        """测试搜索超时处理"""
        # 使用一个很大的 top_k 值可能触发超时
        response = http_session.post(
            f"{milvus_service_url}/search",
            json={
                "collection_name": "test_collection",
                "query_text": "test",
                "top_k": 10000
            },
            timeout=5  # 短超时
        )
        
        # 应该返回超时错误或正常响应
        assert response.status_code in [200, 408, 500]
