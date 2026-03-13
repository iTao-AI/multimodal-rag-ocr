"""
Pytest 配置文件
包含测试夹具 (fixtures) 和全局配置
"""
import pytest
import requests
import time
import os
from typing import Dict, Generator

# ============ 测试配置 ============

@pytest.fixture(scope="session")
def services_config() -> Dict[str, Dict]:
    """服务配置"""
    return {
        "pdf_extraction": {
            "host": os.getenv("PDF_HOST", "http://localhost"),
            "port": int(os.getenv("PDF_PORT", "8006")),
        },
        "chunker": {
            "host": os.getenv("CHUNKER_HOST", "http://localhost"),
            "port": int(os.getenv("CHUNKER_PORT", "8001")),
        },
        "milvus_api": {
            "host": os.getenv("MILVUS_HOST", "http://localhost"),
            "port": int(os.getenv("MILVUS_PORT", "8000")),
        },
        "chat": {
            "host": os.getenv("CHAT_HOST", "http://localhost"),
            "port": int(os.getenv("CHAT_PORT", "8501")),
        },
    }

@pytest.fixture(scope="session")
def pdf_service_url(services_config: Dict) -> str:
    """PDF 提取服务 URL"""
    cfg = services_config["pdf_extraction"]
    return f"{cfg['host']}:{cfg['port']}"

@pytest.fixture(scope="session")
def chunker_service_url(services_config: Dict) -> str:
    """文本切分服务 URL"""
    cfg = services_config["chunker"]
    return f"{cfg['host']}:{cfg['port']}"

@pytest.fixture(scope="session")
def milvus_service_url(services_config: Dict) -> str:
    """Milvus API 服务 URL"""
    cfg = services_config["milvus_api"]
    return f"{cfg['host']}:{cfg['port']}"

@pytest.fixture(scope="session")
def chat_service_url(services_config: Dict) -> str:
    """对话检索服务 URL"""
    cfg = services_config["chat"]
    return f"{cfg['host']}:{cfg['port']}"

@pytest.fixture(scope="session")
def http_session() -> Generator[requests.Session, None, None]:
    """HTTP 会话"""
    session = requests.Session()
    yield session
    session.close()

@pytest.fixture
def sample_markdown_text() -> str:
    """示例 Markdown 文本"""
    return """# 测试文档标题

## 第一章：简介

这是一个测试文档，用于验证文本切分功能。

### 1.1 背景

Multimodal RAG 系统支持多模态数据的检索和生成。

### 1.2 目标

- 提高检索准确性
- 支持多模态数据
- 优化响应时间

## 第二章：技术架构

### 2.1 核心组件

1. PDF 提取服务
2. 文本切分服务
3. 向量数据库服务
4. 对话检索服务

### 2.2 数据流

用户提问 → 向量检索 → 重排序 → LLM 生成 → 返回答案

## 第三章：总结

本文档介绍了 Multimodal RAG 系统的基本架构和功能。
"""

@pytest.fixture
def sample_pdf_content() -> bytes:
    """示例 PDF 内容 (最小有效 PDF)"""
    # 这是一个最小的有效 PDF 文件用于测试
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n115\n%%EOF"

@pytest.fixture
def llm_config() -> Dict:
    """LLM 配置"""
    return {
        "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": os.getenv("DASHSCOPE_API_KEY", "test_key"),
        "model_name": "qwen3-vl-plus",
    }

@pytest.fixture
def chat_request_template() -> Dict:
    """对话请求模板"""
    return {
        "query": "什么是 RAG？",
        "collection_name": "test_collection",
        "top_k": 5,
        "score_threshold": 0.5,
        "stream": False,
        "return_source": True,
    }

# ============ 性能测试配置 ============

@pytest.fixture(scope="session")
def performance_config() -> Dict:
    """性能测试配置"""
    return {
        "concurrent_users": [1, 5, 10, 20],
        "requests_per_user": 10,
        "warmup_requests": 5,
        "timeout_seconds": 30,
    }

# ============ 测试辅助函数 ============

@pytest.fixture
def response_timer():
    """响应时间计时器"""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.time()
            return self
            
        def stop(self):
            self.end_time = time.time()
            return self
            
        def elapsed_ms(self) -> float:
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return 0.0
    
    return Timer()
