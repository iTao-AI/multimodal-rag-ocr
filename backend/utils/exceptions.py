"""
全局异常处理模块
提供统一的异常处理和错误响应格式
"""
import uuid
import time
import traceback
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============ 自定义异常类 ============

class AppException(Exception):
    """应用基础异常"""
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ServiceUnavailableException(AppException):
    """服务不可用异常"""
    def __init__(self, message: str = "服务暂时不可用", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=503,
            details=details
        )


class ValidationException(AppException):
    """数据验证异常"""
    def __init__(self, message: str = "数据验证失败", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class NotFoundException(AppException):
    """资源不存在异常"""
    def __init__(self, resource: str = "资源", details: Optional[Dict] = None):
        super().__init__(
            message=f"{resource}不存在",
            code="NOT_FOUND",
            status_code=404,
            details=details
        )


class AuthenticationException(AppException):
    """认证失败异常"""
    def __init__(self, message: str = "认证失败", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class AuthorizationException(AppException):
    """授权失败异常"""
    def __init__(self, message: str = "无权访问", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )


class ExternalServiceException(AppException):
    """外部服务调用异常"""
    def __init__(self, service: str, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=f"{service}服务错误：{message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details=details
        )


# ============ 错误响应格式 ============

def create_error_response(
    code: str,
    message: str,
    request_id: str,
    status_code: int = 500,
    details: Optional[Dict] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """创建统一的错误响应"""
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "status_code": status_code,
            "details": details or {},
            "timestamp": timestamp or datetime.now().isoformat(),
            "path": None  # 将在处理器中设置
        }
    }


# ============ 全局异常处理器 ============

def setup_global_exception_handlers(app: FastAPI, service_name: str):
    """为 FastAPI 应用设置全局异常处理器"""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """处理应用自定义异常"""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        logger.warning(
            f"应用异常 [ID:{request_id}] [{exc.code}]: {exc.message}",
            exc_info=False
        )
        
        response = create_error_response(
            code=exc.code,
            message=exc.message,
            request_id=request_id,
            status_code=exc.status_code,
            details=exc.details,
            timestamp=datetime.now().isoformat()
        )
        response["error"]["path"] = str(request.url.path)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response,
            headers={"X-Request-ID": request_id}
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理 HTTP 异常"""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        logger.info(
            f"HTTP 异常 [ID:{request_id}] [{exc.status_code}]: {exc.detail}",
            exc_info=False
        )
        
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            408: "REQUEST_TIMEOUT",
            422: "VALIDATION_ERROR",
            429: "TOO_MANY_REQUESTS",
            500: "INTERNAL_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE"
        }
        
        response = create_error_response(
            code=code_map.get(exc.status_code, "HTTP_ERROR"),
            message=str(exc.detail),
            request_id=request_id,
            status_code=exc.status_code,
            timestamp=datetime.now().isoformat()
        )
        response["error"]["path"] = str(request.url.path)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response,
            headers={"X-Request-ID": request_id}
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """处理请求验证异常"""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error.get("loc", [])),
                "message": error.get("msg", ""),
                "type": error.get("type", "")
            })
        
        logger.warning(
            f"请求验证失败 [ID:{request_id}]: {errors}",
            exc_info=False
        )
        
        response = create_error_response(
            code="VALIDATION_ERROR",
            message="请求参数验证失败",
            request_id=request_id,
            status_code=422,
            details={"errors": errors},
            timestamp=datetime.now().isoformat()
        )
        response["error"]["path"] = str(request.url.path)
        
        return JSONResponse(
            status_code=422,
            content=response,
            headers={"X-Request-ID": request_id}
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """处理 Pydantic 验证异常"""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        logger.warning(
            f"Pydantic 验证失败 [ID:{request_id}]: {exc}",
            exc_info=False
        )
        
        response = create_error_response(
            code="VALIDATION_ERROR",
            message="数据格式验证失败",
            request_id=request_id,
            status_code=422,
            details={"error": str(exc)},
            timestamp=datetime.now().isoformat()
        )
        response["error"]["path"] = str(request.url.path)
        
        return JSONResponse(
            status_code=422,
            content=response,
            headers={"X-Request-ID": request_id}
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """处理所有未捕获的异常"""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # 记录完整堆栈
        logger.error(
            f"全局未捕获异常 [ID:{request_id}]: {type(exc).__name__} - {str(exc)}",
            exc_info=True
        )
        
        response = create_error_response(
            code="INTERNAL_ERROR",
            message="服务器内部错误，请稍后重试",
            request_id=request_id,
            status_code=500,
            details={
                "type": type(exc).__name__,
                "logged_at": datetime.now().isoformat()
            },
            timestamp=datetime.now().isoformat()
        )
        response["error"]["path"] = str(request.url.path)
        
        return JSONResponse(
            status_code=500,
            content=response,
            headers={"X-Request-ID": request_id}
        )
    
    # 记录服务启动信息
    logger.info(f"[{service_name}] 全局异常处理器已设置")


# ============ 请求 ID 中间件 ============

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求 ID 中间件 - 为每个请求生成唯一 ID"""
    
    async def dispatch(self, request: Request, call_next):
        # 从请求头获取或生成新的 request_id
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # 将 request_id 添加到请求状态
        request.state.request_id = request_id
        
        # 执行请求
        response = await call_next(request)
        
        # 在响应头中添加 request_id
        response.headers["X-Request-ID"] = request_id
        
        return response


# ============ 性能监控中间件 ============

class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """性能日志中间件 - 记录请求处理时间"""
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000  # ms
        
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"{response.status_code} - {process_time:.2f}ms",
            
        )
        
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        response.headers["X-Request-ID"] = request_id
        
        return response


# ============ 使用示例 ============

def create_app_with_exception_handling(service_name: str) -> FastAPI:
    """创建带有全局异常处理的 FastAPI 应用"""
    app = FastAPI(
        title=service_name,
        description=f"{service_name} API - 包含全局异常处理",
        version="1.0.0"
    )
    
    # 添加中间件
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(PerformanceLoggingMiddleware)
    
    # 设置异常处理器
    setup_global_exception_handlers(app, service_name)
    
    return app
