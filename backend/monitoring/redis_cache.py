"""
Redis 缓存模块
用于向量检索结果缓存、查询结果缓存
"""
import json
import hashlib
import time
from typing import Optional, Any, Dict
from dataclasses import dataclass
import os

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

@dataclass
class CacheConfig:
    """缓存配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    default_ttl: int = 3600  # 1 小时
    max_memory: str = "256mb"

class RedisCache:
    """Redis 缓存客户端"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._redis: Optional[aioredis.Redis] = None
        self._connected = False
        
    async def connect(self) -> bool:
        """连接 Redis"""
        if not REDIS_AVAILABLE:
            print("⚠️  Redis 未安装，缓存功能禁用")
            return False
        
        try:
            self._redis = await aioredis.from_url(
                f"redis://{self.config.host}:{self.config.port}/{self.config.db}",
                password=self.config.password,
                decode_responses=True,
                socket_connect_timeout=5
            )
            await self._redis.ping()
            self._connected = True
            print(f"✓ Redis 连接成功：{self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            print(f"⚠️  Redis 连接失败：{e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self._redis:
            await self._redis.close()
            self._connected = False
    
    def _generate_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_data = json.dumps(args, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._connected:
            return None
        
        try:
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        if not self._connected:
            return False
        
        try:
            ttl = ttl or self.config.default_ttl
            await self._redis.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._connected:
            return False
        
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    # 便捷方法：向量检索缓存
    async def get_vector_search(self, query: str, collection: str, top_k: int) -> Optional[Dict]:
        """获取向量检索结果缓存"""
        key = self._generate_key("vector_search", query, collection, top_k)
        return await self.get(key)
    
    async def set_vector_search(self, query: str, collection: str, top_k: int, results: Dict, ttl: int = 1800):
        """设置向量检索结果缓存（30 分钟）"""
        key = self._generate_key("vector_search", query, collection, top_k)
        return await self.set(key, results, ttl)
    
    # 便捷方法：查询结果缓存
    async def get_query_result(self, query: str, context: Dict) -> Optional[str]:
        """获取查询结果缓存"""
        key = self._generate_key("query_result", query, context)
        return await self.get(key)
    
    async def set_query_result(self, query: str, context: Dict, answer: str, ttl: int = 3600):
        """设置查询结果缓存（1 小时）"""
        key = self._generate_key("query_result", query, context)
        return await self.set(key, {"answer": answer}, ttl)
    
    # 统计信息
    async def get_stats(self) -> Dict:
        """获取缓存统计"""
        if not self._connected:
            return {"connected": False}
        
        try:
            info = await self._redis.info("memory")
            keys_count = await self._redis.dbsize()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "keys_count": keys_count
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

# 全局缓存实例
_cache_instance: Optional[RedisCache] = None

def get_cache(config: Optional[CacheConfig] = None) -> RedisCache:
    """获取或创建缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache(config)
    return _cache_instance
