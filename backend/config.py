"""
配置管理模块
集中管理所有服务的配置
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

class Config:
    """基础配置"""
    
    # 服务配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # LLM 配置
    MODEL_URL = os.getenv("MODEL_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-vl-plus")
    API_KEY = os.getenv("API_KEY")
    
    # Embedding 配置
    EMBEDDING_URL = os.getenv("EMBEDDING_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-v4")
    EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
    
    # Milvus 配置
    MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT = int(os.getenv("MILVUS_PORT", 19530))
    MILVUS_USER = os.getenv("MILVUS_USER", "")
    MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", "")
    
    # Redis 配置（可选）
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))  # 缓存过期时间（秒）
    
    # 文件存储配置
    UPLOAD_BASE_DIR = os.getenv("UPLOAD_BASE_DIR", "./output/uploads")
    
    # CORS 配置
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # 限流配置
    RATE_LIMIT_DEFAULT = "60/minute"
    RATE_LIMIT_CHAT = "10/minute"
    RATE_LIMIT_SEARCH = "30/minute"
    RATE_LIMIT_UPLOAD = "5/minute"
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", 5))
    LOG_ROTATION_MB = int(os.getenv("LOG_ROTATION_MB", 10))
    
    @classmethod
    def validate(cls):
        """验证必要配置"""
        if not cls.API_KEY:
            raise ValueError("API_KEY 未配置")
        if not cls.EMBEDDING_API_KEY:
            raise ValueError("EMBEDDING_API_KEY 未配置")
        return True


class MilvusConfig:
    """Milvus 专用配置"""
    
    HOST = Config.MILVUS_HOST
    PORT = Config.MILVUS_PORT
    USER = Config.MILVUS_USER
    PASSWORD = Config.MILVUS_PASSWORD
    
    # 连接池配置
    MAX_CONNECTIONS = 10
    CONNECTION_TIMEOUT = 10  # 秒
    
    # 索引配置
    INDEX_TYPE = "HNSW"
    METRIC_TYPE = "IP"  # 内积相似度
    INDEX_PARAMS = {
        "M": 8,
        "efConstruction": 200
    }
    
    # 搜索配置
    SEARCH_PARAMS = {
        "ef": 64
    }


class CacheConfig:
    """Redis 缓存配置"""
    
    ENABLED = Config.REDIS_HOST is not None
    HOST = Config.REDIS_HOST
    PORT = Config.REDIS_PORT
    PASSWORD = Config.REDIS_PASSWORD or None
    DB = Config.REDIS_DB
    TTL = Config.CACHE_TTL
    
    # Key 前缀
    KEY_PREFIX = {
        "search": "rag:search:",
        "chat": "rag:chat:",
        "document": "rag:doc:",
    }
