"""
测试基础设施：mock pymilvus 连接和外部 API 调用
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import requests

# 将 backend 目录添加到 Python 路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)


@pytest.fixture
def mock_milvus_connection():
    """mock Milvus 连接，避免需要真实 Milvus 服务器"""
    with patch("Database.milvus_server.milvus_api.connections") as mock_conn, \
         patch("Database.milvus_server.milvus_api.utility") as mock_utility:
        mock_conn.connect = MagicMock()
        mock_utility.has_collection = MagicMock(return_value=False)
        mock_utility.list_collections = MagicMock(return_value=[])
        yield mock_conn, mock_utility


@pytest.fixture
def mock_embedding_api_failure():
    """mock Embedding API 调用，模拟完全失败（网络错误）"""
    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("网络连接失败")
        yield mock_post


@pytest.fixture
def mock_embedding_api_timeout():
    """mock Embedding API 调用，模拟超时"""
    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout("请求超时")
        yield mock_post


@pytest.fixture
def mock_embedding_api_http_error():
    """mock Embedding API 调用，模拟 HTTP 401 错误"""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid API key"}
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_embedding_api_success():
    """mock Embedding API 调用，模拟成功返回"""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 1024}]
        }
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def service_with_mocks(mock_milvus_connection, mock_embedding_api_failure):
    """
    创建一个 MilvusRAGService 实例，其中：
    - Milvus 连接被 mock
    - Embedding API 调用被 mock 为失败
    """
    # 需要重新导入，因为 patch 是在模块级别
    from Database.milvus_server.milvus_api import MilvusRAGService

    with patch("Database.milvus_server.milvus_api.connections.connect"), \
         patch("Database.milvus_server.milvus_api.utility.has_collection", return_value=False), \
         patch("Database.milvus_server.milvus_api.utility.list_collections", return_value=[]):
        service = MilvusRAGService()
        yield service
