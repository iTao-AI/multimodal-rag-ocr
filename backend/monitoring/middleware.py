"""
FastAPI 性能监控中间件
自动记录请求延迟、QPS、错误率等指标
"""
import time
import asyncio
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from prometheus_metrics import get_metrics

def create_monitoring_middleware(app, service_name: str):
    """创建性能监控中间件"""
    metrics = get_metrics(service_name)
    
    @app.middleware("http")
    async def monitor_requests(request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 获取请求大小
        request_size = 0
        if request.headers.get('content-length'):
            try:
                request_size = int(request.headers['content-length'])
            except (ValueError, TypeError):
                pass
        
        # 执行请求
        try:
            response = await call_next(request)
            success = response.status_code < 500
        except Exception as e:
            # 记录异常
            duration = time.time() - start_time
            metrics.record_request(
                endpoint=request.url.path,
                duration=duration,
                success=False,
                size=request_size
            )
            raise
        
        # 记录指标
        duration = time.time() - start_time
        response_size = int(response.headers.get('content-length', 0))
        metrics.record_request(
            endpoint=request.url.path,
            duration=duration,
            success=success,
            size=request_size + response_size
        )
        
        # 添加响应头（性能指标）
        response.headers['X-Response-Time'] = f"{duration*1000:.2f}ms"
        response.headers['X-Service-Name'] = service_name
        
        return response
    
    # 添加指标暴露端点
    @app.get("/metrics")
    async def get_prometheus_metrics():
        """Prometheus 格式指标"""
        return Response(
            content=metrics.generate_prometheus_format(),
            media_type="text/plain"
        )
    
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return JSONResponse({
            "status": "healthy",
            "service": service_name,
            "timestamp": time.time()
        })
    
    @app.get("/stats")
    async def get_stats():
        """服务统计信息（JSON 格式）"""
        return JSONResponse(metrics.get_metrics_summary())
