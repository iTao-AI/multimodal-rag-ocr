"""
PDF 提取服务测试用例
"""
import pytest
import requests
from typing import Dict

class TestPDFExtractionHealth:
    """PDF 提取服务健康检查测试"""
    
    def test_health_endpoint(self, pdf_service_url: str, http_session: requests.Session):
        """测试健康检查端点"""
        response = http_session.get(f"{pdf_service_url}/health", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "pdf-extraction"
    
    def test_docs_endpoint(self, pdf_service_url: str, http_session: requests.Session):
        """测试 API 文档端点"""
        response = http_session.get(f"{pdf_service_url}/docs", timeout=10)
        
        assert response.status_code == 200
        assert "Swagger UI" in response.text or "swagger" in response.text.lower()


class TestPDFExtractionAPI:
    """PDF 提取服务 API 测试"""
    
    def test_extract_fast_requires_file(self, pdf_service_url: str, http_session: requests.Session):
        """测试快速提取需要文件上传"""
        response = http_session.post(
            f"{pdf_service_url}/extract/fast",
            json={"mode": "fast"},
            timeout=10
        )
        
        # 应该返回 422 (缺少文件)
        assert response.status_code in [422, 400]
    
    def test_extract_accurate_requires_auth(self, pdf_service_url: str, http_session: requests.Session):
        """测试精确提取需要认证"""
        response = http_session.post(
            f"{pdf_service_url}/extract/accurate",
            json={
                "api_key": "invalid_key",
                "model_name": "qwen3-vl-plus",
                "model_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
            },
            timeout=10
        )
        
        # 应该返回 422 (缺少文件) 或 401 (认证失败)
        assert response.status_code in [422, 401, 400]
    
    def test_openapi_spec(self, pdf_service_url: str, http_session: requests.Session):
        """测试 OpenAPI 规范"""
        response = http_session.get(f"{pdf_service_url}/openapi.json", timeout=10)
        
        # 如果支持 OpenAPI 规范
        if response.status_code == 200:
            data = response.json()
            assert "openapi" in data or "swagger" in data
            assert "paths" in data or "paths" in str(data)


class TestPDFExtractionPerformance:
    """PDF 提取服务性能测试"""
    
    def test_health_response_time(self, pdf_service_url: str, http_session: requests.Session):
        """测试健康检查响应时间 < 100ms"""
        response = http_session.get(f"{pdf_service_url}/health", timeout=10)
        
        assert response.status_code == 200
        assert response.elapsed.total_seconds() * 1000 < 100  # < 100ms
    
    def test_docs_response_time(self, pdf_service_url: str, http_session: requests.Session):
        """测试文档页面响应时间 < 500ms"""
        response = http_session.get(f"{pdf_service_url}/docs", timeout=10)
        
        assert response.status_code == 200
        assert response.elapsed.total_seconds() * 1000 < 500  # < 500ms
