"""
工具模块
- exceptions: 全局异常处理
- connection_pool: 连接池优化
"""
from .exceptions import (
    AppException,
    ServiceUnavailableException,
    ValidationException,
    NotFoundException,
    AuthenticationException,
    AuthorizationException,
    ExternalServiceException,
    setup_global_exception_handlers,
    create_error_response,
    RequestIDMiddleware,
    PerformanceLoggingMiddleware,
    logger
)

from .common import (
    generate_file_id,
    generate_request_id,
    ensure_directory,
    safe_json_dumps,
    safe_json_loads,
    BaseResponse,
    ErrorResponse,
    Timer
)

from .types import (
    FileInfo,
    ServiceResult,
    HealthStatus,
    PerformanceMetrics
)

from .async_processing import (
    process_executor,
    thread_executor,
    run_in_process,
    run_in_thread,
    gather_with_concurrency,
    batch_process,
    shutdown_executors,
    benchmark_async
)

from .connection_pool import (
    HTTPClientPool,
    MilvusConnectionPool,
    http_pool,
    milvus_pool,
    get_http_client,
    close_all_pools,
    get_pool_stats
)

__all__ = [
    # 异常处理
    'AppException',
    'ServiceUnavailableException',
    'ValidationException',
    'NotFoundException',
    'AuthenticationException',
    'AuthorizationException',
    'ExternalServiceException',
    'setup_global_exception_handlers',
    'create_error_response',
    'RequestIDMiddleware',
    'PerformanceLoggingMiddleware',
    'logger',
    
    # 连接池
    'HTTPClientPool',
    'MilvusConnectionPool',
    'http_pool',
    'milvus_pool',
    'get_http_client',
    'close_all_pools',
    'get_pool_stats',
    
    # 异步处理
    'process_executor',
    'thread_executor',
    'run_in_process',
    'run_in_thread',
    'gather_with_concurrency',
    'batch_process',
    'shutdown_executors',
    'benchmark_async',
    
    # 通用工具
    'generate_file_id',
    'generate_request_id',
    'ensure_directory',
    'safe_json_dumps',
    'safe_json_loads',
    'BaseResponse',
    'ErrorResponse',
    'Timer',
    
    # 类型定义
    'FileInfo',
    'ServiceResult',
    'HealthStatus',
    'PerformanceMetrics'
]
