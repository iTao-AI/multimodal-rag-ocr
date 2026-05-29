import pytest
import inspect


class TestChatAsync:
    """验证 ChatService 的异步方法不使用同步 requests 调用"""

    def test_retrieve_documents_uses_async_client(self):
        """retrieve_documents 是 async 方法，不应使用同步 requests.post"""
        # 将 backend/ 目录加入路径以导入 kb_chat
        import sys, os
        backend_dir = os.path.join(os.path.dirname(__file__), os.pardir)
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)

        from chat.kb_chat import ChatService
        source = inspect.getsource(ChatService.retrieve_documents)

        # 不应使用同步 requests.post
        assert "requests.post" not in source, (
            "retrieve_documents 不应使用同步 requests.post，会阻塞事件循环"
        )

        # 应使用异步 HTTP 客户端（httpx）
        assert "httpx" in source, (
            "retrieve_documents 应使用 httpx.AsyncClient 进行异步 HTTP 调用"
        )

    def test_retrieve_documents_handles_http_error(self):
        """retrieve_documents 应捕获 httpx.HTTPError 而非 requests.RequestException"""
        import sys, os
        backend_dir = os.path.join(os.path.dirname(__file__), os.pardir)
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)

        from chat.kb_chat import ChatService
        source = inspect.getsource(ChatService.retrieve_documents)

        # 不应捕获 requests 异常
        assert "requests.exceptions" not in source, (
            "不应捕获 requests.exceptions，应使用 httpx.HTTPError"
        )
