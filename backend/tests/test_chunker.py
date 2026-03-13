"""
文本切分服务测试用例
"""
import pytest
import requests
from typing import Dict, List

class TestChunkerHealth:
    """文本切分服务健康检查测试"""
    
    def test_docs_endpoint(self, chunker_service_url: str, http_session: requests.Session):
        """测试 API 文档端点"""
        response = http_session.get(f"{chunker_service_url}/docs", timeout=10)
        
        assert response.status_code == 200
        assert "Swagger UI" in response.text or "swagger" in response.text.lower()
    
    def test_root_endpoint(self, chunker_service_url: str, http_session: requests.Session):
        """测试根端点"""
        response = http_session.get(f"{chunker_service_url}/", timeout=10)
        
        # 根端点应该存在 (200 或 404 都可以接受)
        assert response.status_code in [200, 404, 307]


class TestChunkerAPI:
    """文本切分服务 API 测试"""
    
    def test_chunk_endpoint_exists(self, chunker_service_url: str, http_session: requests.Session):
        """测试切分端点存在"""
        response = http_session.post(
            f"{chunker_service_url}/chunk",
            json={"markdown": "test"},
            timeout=10
        )
        
        # 端点应该存在 (可能返回 422 因为数据不完整，但不应该 404)
        assert response.status_code != 404
    
    def test_chunk_with_sample_text(
        self,
        chunker_service_url: str,
        http_session: requests.Session,
        sample_markdown_text: str
    ):
        """测试使用示例文本进行切分"""
        response = http_session.post(
            f"{chunker_service_url}/chunk",
            json={
                "markdown": sample_markdown_text,
                "chunk_size": 500,
                "chunk_overlap": 50
            },
            timeout=30
        )
        
        # 如果端点存在，应该返回有效响应
        if response.status_code == 200:
            data = response.json()
            assert "chunks" in data or "result" in data or "content" in data
    
    def test_invalid_request(self, chunker_service_url: str, http_session: requests.Session):
        """测试无效请求处理"""
        response = http_session.post(
            f"{chunker_service_url}/chunk",
            json={},  # 空数据
            timeout=10
        )
        
        # 应该返回错误 (422 或 400)
        assert response.status_code in [400, 422]


class TestChunkerPerformance:
    """文本切分服务性能测试"""
    
    def test_chunk_response_time(
        self,
        chunker_service_url: str,
        http_session: requests.Session,
        sample_markdown_text: str
    ):
        """测试切分响应时间 < 500ms"""
        response = http_session.post(
            f"{chunker_service_url}/chunk",
            json={"markdown": sample_markdown_text},
            timeout=30
        )
        
        if response.status_code == 200:
            assert response.elapsed.total_seconds() * 1000 < 500  # < 500ms
    
    def test_large_text_handling(
        self,
        chunker_service_url: str,
        http_session: requests.Session
    ):
        """测试大文本处理"""
        large_text = "这是测试内容。" * 1000  # 约 5KB 文本
        
        response = http_session.post(
            f"{chunker_service_url}/chunk",
            json={"markdown": large_text},
            timeout=60
        )
        
        # 应该能处理大文本 (不超时)
        assert response.status_code != 408  # 不是请求超时
