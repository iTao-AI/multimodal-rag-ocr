"""
优化后的服务配置
包含超时、重试、连接池等优化参数
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ServiceConfig:
    """服务基础配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    timeout_keep_alive: int = 30

@dataclass
class TimeoutConfig:
    """超时配置（秒）"""
    request_timeout: int = 60          # 请求超时
    connect_timeout: int = 10          # 连接超时
    read_timeout: int = 30             # 读取超时
    write_timeout: int = 30            # 写入超时
    milvus_search_timeout: int = 30    # Milvus 检索超时
    llm_generate_timeout: int = 60     # LLM 生成超时

@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    retry_delay: float = 1.0           # 初始延迟（秒）
    retry_backoff: float = 2.0         # 退避倍数
    retry_on_timeout: bool = True
    retry_on_connection_error: bool = True

@dataclass
class ConnectionPoolConfig:
    """连接池配置"""
    # HTTP 连接池
    http_pool_size: int = 20
    http_max_keepalive: int = 100
    
    # Milvus 连接池
    milvus_pool_size: int = 10
    milvus_max_idle: int = 5
    
    # 数据库连接池
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    default_ttl: int = 3600
    vector_search_ttl: int = 1800      # 向量检索缓存 30 分钟
    query_result_ttl: int = 3600       # 查询结果缓存 1 小时
    max_memory: str = "256mb"

@dataclass
class PerformanceConfig:
    """性能优化配置"""
    # 批处理配置
    batch_size: int = 32               # 默认批处理大小
    max_batch_size: int = 100          # 最大批处理大小
    batch_timeout: float = 0.1         # 批处理超时（秒）
    
    # 并发配置
    max_concurrent_requests: int = 100
    semaphore_limit: int = 50
    
    # 内存管理
    max_memory_percent: float = 80.0   # 最大内存使用百分比
    gc_interval: int = 300             # GC 间隔（秒）
    
    # 日志配置
    log_slow_requests: bool = True
    slow_request_threshold: float = 1.0  # 慢请求阈值（秒）
    log_sample_rate: float = 1.0       # 日志采样率

@dataclass
class MonitoringConfig:
    """监控配置"""
    enabled: bool = True
    prometheus_port: int = 9090
    metrics_path: str = "/metrics"
    health_check_path: str = "/health"
    stats_path: str = "/stats"
    
    # 告警配置
    error_rate_threshold: float = 0.05   # 错误率告警阈值 5%
    latency_p95_threshold: float = 5.0   # P95 延迟告警阈值（秒）
    qps_threshold: int = 1000            # QPS 告警阈值

class OptimizedConfig:
    """优化配置总类"""
    
    def __init__(self):
        self.service = ServiceConfig(
            workers=int(os.getenv('WORKERS', '4')),
            port=int(os.getenv('SERVICE_PORT', '8000'))
        )
        
        self.timeout = TimeoutConfig(
            request_timeout=int(os.getenv('REQUEST_TIMEOUT', '60')),
            milvus_search_timeout=int(os.getenv('MILVUS_TIMEOUT', '30')),
            llm_generate_timeout=int(os.getenv('LLM_TIMEOUT', '60'))
        )
        
        self.retry = RetryConfig(
            max_retries=int(os.getenv('MAX_RETRIES', '3'))
        )
        
        self.pool = ConnectionPoolConfig(
            http_pool_size=int(os.getenv('HTTP_POOL_SIZE', '20')),
            milvus_pool_size=int(os.getenv('MILVUS_POOL_SIZE', '10'))
        )
        
        self.cache = CacheConfig(
            enabled=os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', '6379'))
        )
        
        self.performance = PerformanceConfig(
            batch_size=int(os.getenv('BATCH_SIZE', '32')),
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT', '100'))
        )
        
        self.monitoring = MonitoringConfig(
            enabled=os.getenv('MONITORING_ENABLED', 'true').lower() == 'true'
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'service': self.service.__dict__,
            'timeout': self.timeout.__dict__,
            'retry': self.retry.__dict__,
            'pool': self.pool.__dict__,
            'cache': self.cache.__dict__,
            'performance': self.performance.__dict__,
            'monitoring': self.monitoring.__dict__
        }

# 全局配置实例
config = OptimizedConfig()
