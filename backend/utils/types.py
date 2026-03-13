"""
类型定义模块
提供共享的类型注解
"""
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Callable,
    Awaitable,
    Tuple,
    TypeVar,
    Generic
)
from pydantic import BaseModel


# ============ 通用类型 ============

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONObject = Dict[str, JSONValue]
JSONArray = List[JSONValue]


# ============ 文件相关类型 ============

class FileInfo(BaseModel):
    """文件信息"""
    filename: str
    file_id: str
    file_size: int
    file_extension: str
    mime_type: Optional[str] = None


class FileUploadResult(BaseModel):
    """文件上传结果"""
    success: bool
    file_id: str
    filename: str
    file_path: str
    message: str = ""


# ============ 分页类型 ============

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 20
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResult(BaseModel, Generic[T]):
    """分页结果"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============ 服务响应类型 ============

class ServiceResult(BaseModel, Generic[T]):
    """服务结果"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    message: str = ""


class HealthStatus(BaseModel):
    """健康状态"""
    status: str  # healthy, unhealthy, degraded
    service: str
    version: str = "1.0.0"
    timestamp: str
    checks: Dict[str, bool] = {}


# ============ 缓存类型 ============

CacheKey = str
CacheValue = Any
CacheTTL = int  # seconds


class CacheEntry(BaseModel, Generic[T]):
    """缓存条目"""
    key: CacheKey
    value: T
    expires_at: float  # timestamp
    created_at: float = None
    
    def is_expired(self) -> bool:
        import time
        return time.time() > self.expires_at


# ============ 任务类型 ============

TaskStatus = str  # pending, running, completed, failed
TaskId = str


class TaskInfo(BaseModel):
    """任务信息"""
    task_id: TaskId
    status: TaskStatus
    progress: float = 0.0  # 0-100
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


# ============ 日志类型 ============

LogLevel = str  # DEBUG, INFO, WARNING, ERROR, CRITICAL


class LogEntry(BaseModel):
    """日志条目"""
    level: LogLevel
    service: str
    message: str
    timestamp: str
    request_id: Optional[str] = None
    extra: Dict[str, Any] = {}


# ============ 性能指标类型 ============

class PerformanceMetrics(BaseModel):
    """性能指标"""
    request_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    qps: float = 0.0
    time_range: str = ""  # e.g., "1m", "5m", "1h"


# ============ 配置类型 ============

class ServiceConfig(BaseModel):
    """服务配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"


class DatabaseConfig(BaseModel):
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "app"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 10


class CacheConfig(BaseModel):
    """缓存配置"""
    enabled: bool = True
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    default_ttl: int = 3600
