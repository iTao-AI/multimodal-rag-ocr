"""
阿里云百炼模型配置
统一管理所有百炼 API 调用参数
"""
import os
from typing import Dict, Any


class BailianConfig:
    """阿里云百炼配置类"""
    
    # API 基础配置
    API_BASE_URL = os.getenv('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    
    # 嵌入模型配置
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL_NAME', 'text-embedding-v3')
    EMBEDDING_API_KEY = os.getenv('EMBEDDING_API_KEY')
    EMBEDDING_URL = os.getenv('EMBEDDING_URL', API_BASE_URL)
    EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', '1536'))
    
    # 重排序模型配置
    RERANK_MODEL = os.getenv('RERANK_MODEL_NAME', 'qwen3.5-plus')
    RERANK_API_KEY = os.getenv('RERANK_API_KEY', EMBEDDING_API_KEY)
    RERANK_URL = os.getenv('RERANK_API_URL', API_BASE_URL)
    
    # 多模态模型配置
    VL_MODEL = os.getenv('VL_MODEL_NAME', 'qwen3-vl-plus')
    VL_API_KEY = os.getenv('VL_API_KEY', EMBEDDING_API_KEY)
    VL_URL = os.getenv('VL_MODEL_URL', API_BASE_URL)
    
    # 检索策略配置
    HYBRID_SEARCH_TOP_K = int(os.getenv('HYBRID_SEARCH_TOP_K', '50'))
    FINAL_TOP_K = int(os.getenv('FINAL_TOP_K', '10'))
    BM25_WEIGHT = float(os.getenv('BM25_WEIGHT', '0.3'))
    VECTOR_WEIGHT = float(os.getenv('VECTOR_WEIGHT', '0.7'))
    
    # 缓存配置
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '3600'))
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    
    # 请求超时配置（秒）
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    EMBEDDING_TIMEOUT = int(os.getenv('EMBEDDING_TIMEOUT', '10'))
    RERANK_TIMEOUT = int(os.getenv('RERANK_TIMEOUT', '30'))
    
    # 重试配置
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = float(os.getenv('RETRY_DELAY', '1.0'))
    
    @classmethod
    def get_embedding_headers(cls) -> Dict[str, str]:
        """获取嵌入模型请求头"""
        return {
            'Authorization': f'Bearer {cls.EMBEDDING_API_KEY}',
            'Content-Type': 'application/json'
        }
    
    @classmethod
    def get_rerank_headers(cls) -> Dict[str, str]:
        """获取重排序请求头"""
        return {
            'Authorization': f'Bearer {cls.RERANK_API_KEY}',
            'Content-Type': 'application/json'
        }
    
    @classmethod
    def get_vl_headers(cls) -> Dict[str, str]:
        """获取多模态模型请求头"""
        return {
            'Authorization': f'Bearer {cls.VL_API_KEY}',
            'Content-Type': 'application/json'
        }
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否完整"""
        required_keys = [
            cls.EMBEDDING_API_KEY,
            cls.RERANK_API_KEY,
            cls.VL_API_KEY
        ]
        return all(key is not None for key in required_keys)
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            'embedding': {
                'model': cls.EMBEDDING_MODEL,
                'dimension': cls.EMBEDDING_DIMENSION,
                'url': cls.EMBEDDING_URL
            },
            'rerank': {
                'model': cls.RERANK_MODEL,
                'url': cls.RERANK_URL
            },
            'vl': {
                'model': cls.VL_MODEL,
                'url': cls.VL_URL
            },
            'search_strategy': {
                'hybrid_top_k': cls.HYBRID_SEARCH_TOP_K,
                'final_top_k': cls.FINAL_TOP_K,
                'bm25_weight': cls.BM25_WEIGHT,
                'vector_weight': cls.VECTOR_WEIGHT
            },
            'cache': {
                'enabled': cls.CACHE_ENABLED,
                'ttl_seconds': cls.CACHE_TTL_SECONDS,
                'redis_host': cls.REDIS_HOST,
                'redis_port': cls.REDIS_PORT
            }
        }


# 全局配置实例
config = BailianConfig()
