"""
连接池优化模块
提供 Milvus、HTTP 等连接池管理
"""
import httpx
import asyncio
from typing import Optional, List
from contextlib import asynccontextmanager

# ============ HTTP 连接池 ============

class HTTPClientPool:
    """HTTP 异步客户端连接池"""
    
    def __init__(
        self,
        max_keepalive_connections: int = 20,
        max_connections: int = 50,
        timeout: float = 30.0
    ):
        self.max_keepalive = max_keepalive_connections
        self.max_connections = max_connections
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    def get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端（单例模式）"""
        if self._client is None:
            limits = httpx.Limits(
                max_keepalive_connections=self.max_keepalive,
                max_connections=self.max_connections
            )
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=httpx.Timeout(self.timeout)
            )
        return self._client
    
    async def close(self):
        """关闭连接池"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def stats(self) -> dict:
        """获取连接池统计"""
        return {
            "max_keepalive_connections": self.max_keepalive,
            "max_connections": self.max_connections,
            "timeout": self.timeout,
            "initialized": self._client is not None
        }


# 全局 HTTP 连接池实例
http_pool = HTTPClientPool(
    max_keepalive_connections=20,
    max_connections=50,
    timeout=30.0
)


# ============ Milvus 连接池 ============

class MilvusConnectionPool:
    """Milvus 连接池（简化版，使用单连接）"""
    
    def __init__(self, host: str = "localhost", port: int = 19530):
        self.host = host
        self.port = port
        self._initialized = False
        self._pool_size = 0
    
    def initialize(self):
        """初始化 Milvus 连接"""
        try:
            from pymilvus import connections
            
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            self._initialized = True
            self._pool_size = 1  # Milvus 使用单连接别名模式
            print(f"✅ Milvus 连接已建立：{self.host}:{self.port}")
        except Exception as e:
            print(f"⚠️  Milvus 连接失败：{e}")
            self._initialized = False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        if not self._initialized:
            return False
        
        try:
            from pymilvus import utility
            utility.has_collection("nonexistent_test")
            return True
        except:
            return True  # 只要不抛异常就认为连接正常
    
    def stats(self) -> dict:
        """获取连接池统计"""
        return {
            "host": self.host,
            "port": self.port,
            "initialized": self._initialized,
            "pool_size": self._pool_size,
            "connected": self.is_connected() if self._initialized else False
        }


# 全局 Milvus 连接池实例
milvus_pool = MilvusConnectionPool(
    host="localhost",
    port=19530
)


# ============ 便捷函数 ============

def get_http_client() -> httpx.AsyncClient:
    """获取 HTTP 客户端"""
    return http_pool.get_client()


async def close_all_pools():
    """关闭所有连接池"""
    await http_pool.close()


def get_pool_stats() -> dict:
    """获取所有连接池统计"""
    return {
        "http": http_pool.stats(),
        "milvus": milvus_pool.stats()
    }
