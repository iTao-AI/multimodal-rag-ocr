"""
通用工具函数模块
提取各服务共享的通用功能
"""
import os
import uuid
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field


# ============ ID 生成 ============

def generate_file_id(filename: Optional[str] = None) -> str:
    """生成唯一文件 ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = uuid.uuid4().hex[:8]
    
    if filename:
        name_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        return f"{timestamp}_{name_hash}_{random_part}"
    
    return f"{timestamp}_{random_part}"


def generate_request_id() -> str:
    """生成请求 ID"""
    return str(uuid.uuid4())


# ============ 文件操作 ============

def ensure_directory(path: Union[str, Path]) -> Path:
    """确保目录存在，不存在则创建"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Union[str, Path]) -> int:
    """获取文件大小（字节）"""
    return Path(file_path).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_file_extension(filename: str) -> str:
    """获取文件扩展名（小写）"""
    return Path(filename).suffix.lower()


def is_valid_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """检查文件扩展名是否允许"""
    ext = get_file_extension(filename)
    return ext in [ext.lower() for ext in allowed_extensions]


# ============ 数据序列化 ============

def safe_json_dumps(data: Any, ensure_ascii: bool = False, indent: int = 2) -> str:
    """安全的 JSON 序列化"""
    return json.dumps(data, ensure_ascii=ensure_ascii, indent=indent, default=str)


def safe_json_loads(json_str: str) -> Any:
    """安全的 JSON 反序列化"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None


# ============ 响应模型 ============

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: str
    error_code: str = "UNKNOWN_ERROR"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    request_id: Optional[str] = None


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    success: bool = True
    data: List[Any]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.total > 0 and self.page_size > 0:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size


# ============ 验证器 ============

def validate_not_empty(value: Any, field_name: str) -> None:
    """验证值不为空"""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field_name} 不能为空")


def validate_positive(value: Union[int, float], field_name: str) -> None:
    """验证值为正数"""
    if value <= 0:
        raise ValueError(f"{field_name} 必须为正数")


def validate_range(value: Union[int, float], field_name: str, min_val: float, max_val: float) -> None:
    """验证值在范围内"""
    if not (min_val <= value <= max_val):
        raise ValueError(f"{field_name} 必须在 {min_val} 到 {max_val} 之间")


# ============ 日志辅助 ============

def format_log_message(level: str, service: str, message: str, **kwargs) -> str:
    """格式化日志消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_id = kwargs.get('request_id', '-')
    
    extra_parts = []
    for key, value in kwargs.items():
        if key != 'request_id':
            extra_parts.append(f"{key}={value}")
    
    extra_str = " ".join(extra_parts)
    
    return f"{timestamp} [{level}] [{service}] [{request_id}] {message} {extra_str}".strip()


# ============ 性能监控 ============

class Timer:
    """性能计时器"""
    
    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.elapsed_ms = 0.0
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        import time
        self.end_time = time.time()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000
    
    def elapsed(self) -> float:
        """获取经过时间（毫秒）"""
        return self.elapsed_ms


# ============ 缓存辅助 ============

def generate_cache_key(*args, prefix: str = "") -> str:
    """生成缓存键"""
    key_parts = [str(arg) for arg in args]
    key_str = ":".join(key_parts)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()
    
    if prefix:
        return f"{prefix}:{key_hash}"
    return key_hash


# ============ 重试辅助 ============

async def retry_async(func, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """异步重试包装器"""
    import asyncio
    
    current_delay = delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                await asyncio.sleep(current_delay)
                current_delay *= backoff
    
    raise last_exception


def retry_sync(func, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """同步重试包装器"""
    import time
    
    current_delay = delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(current_delay)
                current_delay *= backoff
    
    raise last_exception
