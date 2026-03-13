"""
Redis 缓存模块
支持 Redis 和内存缓存降级模式
"""
import json
import hashlib
import time
from typing import Any, Optional, Dict
from datetime import timedelta
import threading

# 尝试导入 Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class MemoryCache:
    """内存缓存（降级模式）"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            data = self._cache.get(key)
            if data:
                if data['expires'] > time.time():
                    return data['value']
                else:
                    del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: int = 1800):
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires': time.time() + ttl
            }
    
    def delete(self, key: str):
        with self._lock:
            self._cache.pop(key, None)
    
    def clear_pattern(self, pattern: str):
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
    
    def stats(self) -> Dict:
        with self._lock:
            return {
                "mode": "memory",
                "keys_count": len(self._cache),
                "message": "内存缓存模式（Redis 不可用）"
            }


class RedisCache:
    """Redis 缓存客户端"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self._redis = None
        self._mode = "redis"
        
        if REDIS_AVAILABLE:
            try:
                self._redis = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                self._redis.ping()
                print(f"✅ Redis 连接成功：{host}:{port}")
            except Exception as e:
                print(f"⚠️  Redis 连接失败：{e}，使用内存缓存降级")
                self._mode = "memory"
                self._redis = None
        else:
            print("⚠️  Redis 未安装，使用内存缓存降级")
            self._mode = "memory"
        
        # 降级到内存缓存
        if self._mode == "memory":
            self._memory_cache = MemoryCache()
    
    def _generate_key(self, *args) -> str:
        """生成缓存键"""
        key_data = ":".join(str(arg) for arg in args)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return key_hash
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if self._mode == "redis" and self._redis:
            try:
                data = self._redis.get(key)
                return json.loads(data) if data else None
            except Exception as e:
                print(f"Redis get error: {e}")
                return None
        else:
            return self._memory_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 1800):
        """设置缓存（默认 30 分钟）"""
        if self._mode == "redis" and self._redis:
            try:
                self._redis.setex(key, timedelta(seconds=ttl), json.dumps(value, ensure_ascii=False))
            except Exception as e:
                print(f"Redis set error: {e}")
        else:
            self._memory_cache.set(key, value, ttl)
    
    def delete(self, key: str):
        """删除缓存"""
        if self._mode == "redis" and self._redis:
            try:
                self._redis.delete(key)
            except Exception as e:
                print(f"Redis delete error: {e}")
        else:
            self._memory_cache.delete(key)
    
    def clear_pattern(self, pattern: str):
        """清除匹配模式的缓存"""
        if self._mode == "redis" and self._redis:
            try:
                keys = self._redis.keys(pattern)
                if keys:
                    self._redis.delete(*keys)
            except Exception as e:
                print(f"Redis clear error: {e}")
        else:
            self._memory_cache.clear_pattern(pattern)
    
    def stats(self) -> Dict:
        """获取缓存统计"""
        if self._mode == "redis" and self._redis:
            try:
                info = self._redis.info('stats')
                keyspace = self._redis.info('keyspace')
                
                hits = int(info.get('keyspace_hits', 0))
                misses = int(info.get('keyspace_misses', 0))
                total = hits + misses if (hits + misses) > 0 else 1
                
                return {
                    "mode": "redis",
                    "connected": True,
                    "host": self.host,
                    "port": self.port,
                    "used_memory": self._redis.info('memory').get('used_memory_human', 'unknown'),
                    "connected_clients": info.get('connected_clients'),
                    "keyspace_hits": hits,
                    "keyspace_misses": misses,
                    "hit_rate": f"{hits / total * 100:.1f}%",
                    "total_keys": sum(int(v.get('keys', 0)) for v in keyspace.values())
                }
            except Exception as e:
                return {
                    "mode": "redis",
                    "connected": False,
                    "error": str(e)
                }
        else:
            stats = self._memory_cache.stats()
            stats["connected"] = True
            return stats
    
    def is_redis_mode(self) -> bool:
        """是否使用 Redis 模式"""
        return self._mode == "redis"


# 全局缓存实例
cache = RedisCache(
    host='localhost',
    port=6379,
    db=0
)


# 便捷函数
def get_cached(key: str) -> Optional[Any]:
    """获取缓存"""
    return cache.get(key)


def set_cached(key: str, value: Any, ttl: int = 1800):
    """设置缓存"""
    cache.set(key, value, ttl)


def cached(ttl: int = 1800, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}{func.__name__}:{cache._generate_key(*args, **kwargs)}"
            
            # 尝试缓存
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
