"""
缓存管理服务 - Redis 缓存查询结果和嵌入向量
"""
import logging
import json
import hashlib
from typing import Any, Optional, List, Dict
from datetime import timedelta
import os

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis 未安装，缓存功能将不可用")


class CacheManager:
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        ttl_seconds: int = 3600,
        enabled: bool = True
    ):
        """
        初始化缓存管理器
        
        Args:
            host: Redis 主机
            port: Redis 端口
            db: Redis 数据库编号
            ttl_seconds: 默认 TTL（秒）
            enabled: 是否启用缓存
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.ttl_seconds = ttl_seconds
        self.client = None
        
        if self.enabled:
            try:
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # 测试连接
                self.client.ping()
                logger.info(f"Redis 连接成功：{host}:{port}")
            except Exception as e:
                logger.warning(f"Redis 连接失败，禁用缓存：{e}")
                self.enabled = False
                self.client = None
    
    def _generate_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_string = ':'.join(key_parts)
        # 使用 MD5 哈希避免键过长
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.enabled or not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"缓存命中：{key}")
                return json.loads(value)
            logger.debug(f"缓存未命中：{key}")
            return None
        except Exception as e:
            logger.error(f"获取缓存失败：{e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        if not self.enabled or not self.client:
            return False
        
        try:
            ttl = ttl or self.ttl_seconds
            serialized = json.dumps(value, ensure_ascii=False)
            self.client.setex(key, ttl, serialized)
            logger.debug(f"缓存设置：{key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"设置缓存失败：{e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.delete(key)
            logger.debug(f"缓存删除：{key}")
            return True
        except Exception as e:
            logger.error(f"删除缓存失败：{e}")
            return False
    
    def clear_pattern(self, pattern: str) -> bool:
        """批量删除匹配模式的缓存"""
        if not self.enabled or not self.client:
            return False
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"批量删除缓存：{pattern}, 共 {len(keys)} 个")
            return True
        except Exception as e:
            logger.error(f"批量删除缓存失败：{e}")
            return False
    
    # ============ 便捷方法 ============
    
    def get_query_result(self, query: str) -> Optional[List[Dict]]:
        """获取查询结果缓存"""
        key = self._generate_key('query_result', query)
        return self.get(key)
    
    def set_query_result(self, query: str, results: List[Dict], ttl: Optional[int] = None) -> bool:
        """设置查询结果缓存"""
        key = self._generate_key('query_result', query)
        return self.set(key, results, ttl)
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取嵌入向量缓存"""
        key = self._generate_key('embedding', text)
        return self.get(key)
    
    def set_embedding(self, text: str, embedding: List[float], ttl: Optional[int] = None) -> bool:
        """设置嵌入向量缓存"""
        key = self._generate_key('embedding', text)
        return self.set(key, embedding, ttl)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.enabled or not self.client:
            return {'enabled': False}
        
        try:
            info = self.client.info('stats')
            return {
                'enabled': True,
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'connected_clients': info.get('connected_clients', 0)
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败：{e}")
            return {'enabled': False, 'error': str(e)}


# 全局缓存实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            ttl_seconds=int(os.getenv('CACHE_TTL_SECONDS', '3600')),
            enabled=os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        )
    return _cache_manager
