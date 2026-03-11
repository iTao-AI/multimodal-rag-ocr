"""
Redis 缓存模块
提供统一的缓存接口
"""

import json
import hashlib
from typing import Any, Optional
from datetime import timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from config import CacheConfig


class CacheClient:
    """缓存客户端"""
    
    def __init__(self):
        self.client = None
        self.enabled = CacheConfig.ENABLED and REDIS_AVAILABLE
        
        if self.enabled:
            try:
                self.client = redis.Redis(
                    host=CacheConfig.HOST,
                    port=CacheConfig.PORT,
                    password=CacheConfig.PASSWORD,
                    db=CacheConfig.DB,
                    decode_responses=True,
                    socket_connect_timeout=5,
                )
                # 测试连接
                self.client.ping()
                print("✅ Redis 缓存已连接")
            except Exception as e:
                print(f"⚠️ Redis 连接失败：{e}")
                self.enabled = False
                self.client = None
        else:
            print("ℹ️ Redis 缓存未启用")
    
    def _generate_key(self, prefix: str, *args) -> str:
        """生成缓存 key"""
        key_data = ":".join(str(arg) for arg in args)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"
    
    def get(self, prefix: str, *args) -> Optional[Any]:
        """获取缓存"""
        if not self.enabled or not self.client:
            return None
        
        try:
            key = self._generate_key(prefix, *args)
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"缓存读取失败：{e}")
            return None
    
    def set(self, prefix: str, value: Any, *args, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        if not self.enabled or not self.client:
            return False
        
        try:
            key = self._generate_key(prefix, *args)
            ttl = ttl or CacheConfig.TTL
            self.client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            print(f"缓存写入失败：{e}")
            return False
    
    def delete(self, prefix: str, *args) -> bool:
        """删除缓存"""
        if not self.enabled or not self.client:
            return False
        
        try:
            key = self._generate_key(prefix, *args)
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"缓存删除失败：{e}")
            return False
    
    def clear_prefix(self, prefix: str) -> bool:
        """清除指定前缀的所有缓存"""
        if not self.enabled or not self.client:
            return False
        
        try:
            keys = self.client.keys(f"{prefix}:*")
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"缓存清除失败：{e}")
            return False
    
    def health_check(self) -> bool:
        """健康检查"""
        if not self.enabled or not self.client:
            return False
        
        try:
            return self.client.ping()
        except Exception:
            return False


# 全局缓存实例
cache = CacheClient()


# 便捷函数
def get_search_cache(query: str, kb_id: str) -> Optional[dict]:
    """获取搜索缓存"""
    return cache.get("search", kb_id, query)


def set_search_cache(query: str, kb_id: str, result: dict, ttl: Optional[int] = None) -> bool:
    """设置搜索缓存"""
    return cache.set("search", result, kb_id, query, ttl=ttl)


def get_chat_cache(query: str, kb_id: str, history_hash: str) -> Optional[dict]:
    """获取对话缓存"""
    return cache.get("chat", kb_id, query, history_hash)


def set_chat_cache(query: str, kb_id: str, history_hash: str, result: dict, ttl: Optional[int] = None) -> bool:
    """设置对话缓存"""
    return cache.set("chat", result, kb_id, query, history_hash, ttl=ttl)
