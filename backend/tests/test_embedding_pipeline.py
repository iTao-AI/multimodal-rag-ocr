"""
Embedding 管线测试 — 验证 API 失败时不会插入随机向量

核心验收标准（PRD #13）：
- Embedding API 失败时，应抛出 HTTPException(503)，而非返回 np.random.rand() 随机向量
- 自动重试 3 次（指数退避 1s→2s→4s）
- 仍失败返回 503 "向量生成服务不可用"
"""

import pytest
import time
import sys
import os
import numpy as np
from unittest.mock import patch, MagicMock
import requests
from fastapi import HTTPException


# 需要 mock 的模块路径
MILVUS_API_MODULE = "Database.milvus_server.milvus_api"


def _setup_test_environment():
    """设置测试环境变量"""
    os.environ["MILVUS_HOST"] = "localhost"
    os.environ["MILVUS_PORT"] = "19530"
    os.environ["EMBEDDING_URL"] = "http://test-api/embeddings"
    os.environ["EMBEDDING_MODEL_NAME"] = "text-embedding-v4"
    os.environ["EMBEDDING_API_KEY"] = "test-key"


def _mock_pymilvus():
    """
    在 import milvus_api 之前，将 pymilvus.connections 替换为 mock
    这样 MilvusRAGService.__init__ 中的 connections.connect 就不会真正执行
    """
    # 创建 mock connections 对象
    mock_connections = MagicMock()
    mock_connections.connect = MagicMock()

    # 创建 mock utility
    mock_utility = MagicMock()
    mock_utility.has_collection = MagicMock(return_value=False)
    mock_utility.list_collections = MagicMock(return_value=[])
    mock_utility.drop_collection = MagicMock()

    # 创建 mock Collection
    mock_collection_class = MagicMock()
    mock_collection = MagicMock()
    mock_collection.has_index = MagicMock(return_value=True)
    mock_collection_class.return_value = mock_collection

    # 创建 mock CollectionSchema
    mock_schema = MagicMock()

    # 创建 mock FieldSchema
    mock_field_schema = MagicMock()

    # 创建 mock DataType
    mock_data_type = MagicMock()

    # 注册到 sys.modules
    sys.modules["pymilvus"] = MagicMock()
    sys.modules["pymilvus"].connections = mock_connections
    sys.modules["pymilvus"].utility = mock_utility
    sys.modules["pymilvus"].Collection = mock_collection_class
    sys.modules["pymilvus"].CollectionSchema = mock_schema
    sys.modules["pymilvus"].FieldSchema = mock_field_schema
    sys.modules["pymilvus"].DataType = mock_data_type

    return mock_connections, mock_utility


def _make_test_service():
    """
    创建一个完全 mock 的 MilvusRAGService 实例
    """
    # 清除已缓存的模块
    modules_to_clear = [k for k in sys.modules.keys() if "milvus_api" in k]
    for mod in modules_to_clear:
        del sys.modules[mod]

    # 设置环境
    _setup_test_environment()

    # Mock pymilvus
    mock_conn, mock_utility = _mock_pymilvus()

    # 导入模块（此时 pymilvus 已被 mock）
    from Database.milvus_server.milvus_api import MilvusRAGService

    service = MilvusRAGService()
    service.embedding_url = "http://test-api/embeddings"
    service.embedding_model_name = "text-embedding-v4"
    service.embedding_api_key = "test-key"
    return service


class TestGenerateEmbeddingApiFailure:
    """generate_embedding() 在 API 失败时的行为测试"""

    def test_raises_503_on_connection_error(self):
        """
        当 Embedding API 网络连接失败时，应抛出 HTTPException(503)
        而不是返回 np.random.rand() 随机向量
        """
        service = _make_test_service()
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("网络连接失败")

            with pytest.raises(HTTPException) as exc_info:
                service.generate_embedding("测试文本")

            assert exc_info.value.status_code == 503
            assert "向量生成服务不可用" in exc_info.value.detail

    def test_raises_503_on_timeout(self):
        """当 Embedding API 超时时，应抛出 HTTPException(503)"""
        service = _make_test_service()
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("请求超时")

            with pytest.raises(HTTPException) as exc_info:
                service.generate_embedding("测试文本")

            assert exc_info.value.status_code == 503
            assert "向量生成服务不可用" in exc_info.value.detail

    def test_raises_503_on_http_401(self):
        """当 Embedding API 返回 401 时，应抛出 HTTPException(503)"""
        service = _make_test_service()
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_post.return_value = mock_response

            with pytest.raises(HTTPException) as exc_info:
                service.generate_embedding("测试文本")

            assert exc_info.value.status_code == 503
            assert "向量生成服务不可用" in exc_info.value.detail

    def test_returns_valid_embedding_on_success(self):
        """当 Embedding API 成功时，应返回有效向量"""
        service = _make_test_service()
        expected_embedding = [0.1] * 1024
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"embedding": expected_embedding}]
            }
            mock_post.return_value = mock_response

            result = service.generate_embedding("测试文本")

            assert result == expected_embedding
            assert len(result) == 1024
            # 确保不是随机向量
            assert result != np.random.rand(1024).tolist()

    def test_retries_3_times_on_failure(self):
        """
        API 失败时应重试 3 次（指数退避）
        验证 requests.post 被调用了 3 次
        """
        service = _make_test_service()
        call_times = []

        def slow_connection_error(*args, **kwargs):
            call_times.append(time.time())
            raise requests.exceptions.ConnectionError("网络连接失败")

        with patch("requests.post", side_effect=slow_connection_error):
            with pytest.raises(HTTPException):
                service.generate_embedding("测试文本")

        # 验证重试了 3 次
        assert len(call_times) == 3, f"预期 3 次重试，实际 {len(call_times)} 次"

    def test_exponential_backoff_timing(self):
        """
        重试间隔应符合指数退避：1s → 2s → 4s
        验证相邻两次调用之间的时间间隔
        """
        service = _make_test_service()
        call_times = []

        def track_time(*args, **kwargs):
            call_times.append(time.time())
            raise requests.exceptions.ConnectionError("失败")

        with patch("requests.post", side_effect=track_time):
            with pytest.raises(HTTPException):
                service.generate_embedding("测试文本")

        # 验证重试间隔
        assert len(call_times) == 3
        interval1 = call_times[1] - call_times[0]  # 第一次和第二次之间
        interval2 = call_times[2] - call_times[1]  # 第二次和第三次之间

        # 指数退避：1s, 2s (允许 0.3s 误差)
        assert interval1 >= 0.7, f"第一次重试间隔太短: {interval1:.2f}s (预期 ~1s)"
        assert interval2 >= 1.5, f"第二次重试间隔太短: {interval2:.2f}s (预期 ~2s)"
        # 第二次间隔应明显大于第一次（指数增长）
        assert interval2 > interval1, "退避间隔应指数增长"

    def test_succeeds_after_retry(self):
        """
        前两次失败，第三次成功 → 应返回有效向量
        """
        service = _make_test_service()
        call_count = [0]

        def fail_then_succeed(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise requests.exceptions.ConnectionError("失败")
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"embedding": [0.5] * 1024}]
            }
            return mock_response

        with patch("requests.post", side_effect=fail_then_succeed):
            result = service.generate_embedding("测试文本")

        assert call_count[0] == 3
        assert result == [0.5] * 1024
