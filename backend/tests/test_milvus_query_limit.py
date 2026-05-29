"""
测试 Milvus query() 不支持 limit 参数的修复（#7）

Milvus 的 collection.query() 不支持 limit 参数，必须使用 Python 切片。
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
import json

# 将 backend 目录添加到 Python 路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# 设置必要的环境变量
os.environ.setdefault("MILVUS_HOST", "localhost")
os.environ.setdefault("MILVUS_PORT", "19530")
os.environ.setdefault("EMBEDDING_URL", "http://localhost:8001/embed")
os.environ.setdefault("EMBEDDING_MODEL_NAME", "text-embedding-v4")
os.environ.setdefault("EMBEDDING_API_KEY", "test-key")

# 在模块加载前 mock pymilvus.connections.connect，防止模块级初始化失败
_mock_pymilvus = MagicMock()
sys.modules.setdefault("pymilvus", _mock_pymilvus)
sys.modules.setdefault("pymilvus.connections", _mock_pymilvus.connections)
sys.modules.setdefault("pymilvus.Collection", _mock_pymilvus.Collection)
sys.modules.setdefault("pymilvus.CollectionSchema", _mock_pymilvus.CollectionSchema)
sys.modules.setdefault("pymilvus.FieldSchema", _mock_pymilvus.FieldSchema)
sys.modules.setdefault("pymilvus.DataType", _mock_pymilvus.DataType)
sys.modules.setdefault("pymilvus.utility", _mock_pymilvus.utility)

# 让模块级 MilvusRAGService() 初始化不报错
_mock_pymilvus.connections.connect = MagicMock()
_mock_pymilvus.utility.has_collection = MagicMock(return_value=False)
_mock_pymilvus.utility.list_collections = MagicMock(return_value=[])


# 现在可以安全导入
from Database.milvus_server.milvus_api import MilvusRAGService


@pytest.fixture
def mock_service_for_query():
    """
    创建 mock 的 MilvusRAGService，用于测试 query 相关方法。
    mock collection.query() 返回假数据，验证不带 limit 参数。
    """
    from Database.milvus_server.milvus_api import MilvusRAGService as _Service

    # Mock 假数据 — 超过 top_k 的查询结果
    def make_fake_results(n=20):
        return [
            {
                "id": i,
                "chunk_text": f"测试文本 {i}",
                "filename": "test.pdf",
                "file_id": f"file_{i}",
                "metadata": json.dumps({"page_start": i}),
                "created_at": f"2026-01-{i:02d}T00:00:00"
            }
            for i in range(n)
        ]

    fake_results = make_fake_results(20)

    with patch.object(_Service, "connect_to_milvus"):

        service = _Service()

        # mock collection
        mock_collection = MagicMock()
        mock_collection.query = MagicMock(return_value=fake_results)
        mock_collection.num_entities = 100

        with patch("Database.milvus_server.milvus_api.Collection", return_value=mock_collection), \
             patch("Database.milvus_server.milvus_api.utility.has_collection", return_value=True):
            yield service, mock_collection, fake_results


class TestQueryNoLimitParameter:
    """验证 query() 不使用 limit 参数，改用 Python 切片"""

    def test_search_by_filename_does_not_pass_limit(self, mock_service_for_query):
        """search_by_filename 调用 query() 时不传 limit 参数"""
        service, mock_collection, _ = mock_service_for_query

        results = service.search_by_filename(
            collection_name="test_kb",
            filename="test.pdf",
            top_k=5
        )

        # 验证 query() 没有被传入 limit 参数
        query_call_kwargs = mock_collection.query.call_args.kwargs
        assert "limit" not in query_call_kwargs, (
            f"query() 不应该传 limit 参数，实际传了: {query_call_kwargs}"
        )

        # 验证返回结果被切片为 top_k
        assert len(results) == 5, f"应该返回 {5} 条，实际返回 {len(results)}"

    def test_search_by_filename_returns_all_when_less_than_top_k(self, mock_service_for_query):
        """结果数少于 top_k 时，返回全部结果"""
        service, mock_collection, fake_results = mock_service_for_query

        # 让 query 只返回 3 条
        mock_collection.query.return_value = fake_results[:3]

        results = service.search_by_filename(
            collection_name="test_kb",
            filename="test.pdf",
            top_k=10
        )

        assert len(results) == 3, f"应该返回 3 条，实际返回 {len(results)}"

    def test_get_collection_stats_does_not_pass_limit(self, mock_service_for_query):
        """get_collection_stats 调用 query() 时不传 limit 参数"""
        service, mock_collection, _ = mock_service_for_query

        stats = service.get_collection_stats("test_kb")

        # 验证 query() 没有被传入 limit 参数
        query_call_kwargs = mock_collection.query.call_args.kwargs
        assert "limit" not in query_call_kwargs, (
            f"query() 不应该传 limit 参数，实际传了: {query_call_kwargs}"
        )

        # 验证 stats 结构
        assert "total_documents" in stats
        assert "total_chunks" in stats

    def test_get_collection_documents_does_not_pass_limit(self, mock_service_for_query):
        """get_collection_documents 调用 query() 时不传 limit 参数"""
        service, mock_collection, _ = mock_service_for_query

        docs = service.get_collection_documents("test_kb")

        # 验证 query() 没有被传入 limit 参数
        query_call_kwargs = mock_collection.query.call_args.kwargs
        assert "limit" not in query_call_kwargs, (
            f"query() 不应该传 limit 参数，实际传了: {query_call_kwargs}"
        )
