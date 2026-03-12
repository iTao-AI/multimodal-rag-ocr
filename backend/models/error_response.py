"""
统一错误响应模型

所有服务使用统一的错误响应格式，便于前端处理和日志追踪。
"""

import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """错误详情"""
    
    code: str = Field(
        ..., 
        description="错误码 (如：INTERNAL_ERROR, VALIDATION_ERROR)",
        examples=["INTERNAL_ERROR"]
    )
    message: str = Field(
        ..., 
        description="错误消息",
        examples="服务器内部错误"
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="请求 ID，用于日志追踪",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="可选的错误详情",
        examples=[{"field": "query", "issue": "required"}]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "details": None
            }
        }


class ErrorResponse(BaseModel):
    """统一错误响应"""
    
    error: ErrorDetail = Field(
        ..., 
        description="错误详情"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "服务器内部错误",
                    "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    "details": None
                }
            }
        }


# ============ 预定义错误码 ============

class ErrorCodes:
    """预定义错误码"""
    
    # 通用错误 (1000-1999)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # 认证授权 (2000-2999)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # 资源相关 (3000-3999)
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_EXISTS = "RESOURCE_EXISTS"
    RESOURCE_LOCKED = "RESOURCE_LOCKED"
    
    # 业务逻辑 (4000-4999)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BUSINESS_ERROR = "BUSINESS_ERROR"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    
    # 外部服务 (5000-5999)
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    API_TIMEOUT = "API_TIMEOUT"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    
    # 文件处理 (6000-6999)
    FILE_UPLOAD_ERROR = "FILE_UPLOAD_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    
    # 数据库 (7000-7999)
    DATABASE_ERROR = "DATABASE_ERROR"
    QUERY_ERROR = "QUERY_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"


# ============ 快捷创建函数 ============

def create_error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """
    创建错误响应的快捷函数
    
    Args:
        code: 错误码
        message: 错误消息
        details: 可选的错误详情
        request_id: 可选的请求 ID（默认自动生成）
    
    Returns:
        ErrorResponse 对象
    """
    return ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=request_id or str(uuid.uuid4()),
            details=details
        )
    )


def create_internal_error(
    message: str = "服务器内部错误",
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """创建内部错误响应"""
    return create_error_response(ErrorCodes.INTERNAL_ERROR, message, details)


def create_validation_error(
    message: str = "请求参数验证失败",
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """创建验证错误响应"""
    return create_error_response(ErrorCodes.VALIDATION_ERROR, message, details)


def create_not_found_error(
    resource: str = "资源",
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """创建资源未找到错误响应"""
    return create_error_response(
        ErrorCodes.NOT_FOUND,
        f"{resource}不存在",
        details
    )


def create_unauthorized_error(
    message: str = "未授权访问",
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """创建未授权错误响应"""
    return create_error_response(ErrorCodes.UNAUTHORIZED, message, details)
