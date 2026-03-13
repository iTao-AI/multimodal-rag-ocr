"""
缓存模块
- redis_cache: Redis 缓存（支持内存降级）
"""
from .redis_cache import (
    RedisCache,
    MemoryCache,
    cache,
    get_cached,
    set_cached,
    cached
)

__all__ = [
    'RedisCache',
    'MemoryCache',
    'cache',
    'get_cached',
    'set_cached',
    'cached'
]
