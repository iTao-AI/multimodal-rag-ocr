"""
Prometheus 指标暴露模块
为所有服务提供统一的性能指标监控
"""
import time
import threading
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json
import os

@dataclass
class MetricData:
    """指标数据"""
    count: int = 0
    total_time: float = 0.0
    total_size: float = 0.0  # for throughput
    error_count: int = 0
    last_updated: float = field(default_factory=time.time)

class PrometheusMetrics:
    """Prometheus 指标收集器"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._metrics: Dict[str, MetricData] = defaultdict(MetricData)
        self._lock = threading.Lock()
        self._start_time = time.time()
        
        # 性能指标
        self.request_latency = {}  # endpoint -> latency stats
        self.qps_window = []  # recent requests for QPS calculation
        self.qps_window_size = 60  # seconds
        
    def record_request(self, endpoint: str, duration: float, success: bool = True, size: float = 0):
        """记录请求指标"""
        with self._lock:
            metric = self._metrics[endpoint]
            metric.count += 1
            metric.total_time += duration
            metric.total_size += size
            if not success:
                metric.error_count += 1
            metric.last_updated = time.time()
            
            # 记录 QPS
            current_time = time.time()
            self.qps_window.append(current_time)
            # 清理过期数据
            self.qps_window = [t for t in self.qps_window if current_time - t < self.qps_window_size]
            
            # 记录延迟统计
            if endpoint not in self.request_latency:
                self.request_latency[endpoint] = []
            self.request_latency[endpoint].append(duration)
            # 保留最近 1000 个数据点
            if len(self.request_latency[endpoint]) > 1000:
                self.request_latency[endpoint] = self.request_latency[endpoint][-1000:]
    
    def get_qps(self) -> float:
        """获取当前 QPS"""
        with self._lock:
            current_time = time.time()
            recent_requests = [t for t in self.qps_window if current_time - t < self.qps_window_size]
            return len(recent_requests) / self.qps_window_size if self.qps_window_size > 0 else 0
    
    def get_metrics_summary(self) -> Dict:
        """获取指标摘要"""
        with self._lock:
            summary = {
                "service": self.service_name,
                "uptime_seconds": time.time() - self.start_time,
                "current_qps": self.get_qps(),
                "endpoints": {}
            }
            
            for endpoint, metric in self._metrics.items():
                avg_latency = metric.total_time / metric.count if metric.count > 0 else 0
                error_rate = metric.error_count / metric.count if metric.count > 0 else 0
                throughput = metric.total_size / metric.total_time if metric.total_time > 0 else 0
                
                # 计算延迟百分位数
                latencies = self.request_latency.get(endpoint, [])
                p50, p95, p99 = self._calculate_percentiles(latencies)
                
                summary["endpoints"][endpoint] = {
                    "request_count": metric.count,
                    "avg_latency_ms": round(avg_latency * 1000, 2),
                    "p50_latency_ms": round(p50 * 1000, 2),
                    "p95_latency_ms": round(p95 * 1000, 2),
                    "p99_latency_ms": round(p99 * 1000, 2),
                    "error_rate": round(error_rate, 4),
                    "throughput_mb_s": round(throughput / 1024 / 1024, 2),
                    "last_updated": metric.last_updated
                }
            
            return summary
    
    def _calculate_percentiles(self, data: list) -> tuple:
        """计算百分位数"""
        if not data:
            return 0, 0, 0
        
        sorted_data = sorted(data)
        n = len(sorted_data)
        
        p50 = sorted_data[int(n * 0.5)] if n > 0 else 0
        p95 = sorted_data[int(n * 0.95)] if n > 0 else 0
        p99 = sorted_data[int(n * 0.99)] if n > 0 else 0
        
        return p50, p95, p99
    
    def generate_prometheus_format(self) -> str:
        """生成 Prometheus 格式的指标"""
        lines = []
        summary = self.get_metrics_summary()
        
        # 服务正常运行时间
        lines.append(f'# HELP {self.service_name}_uptime_seconds Service uptime in seconds')
        lines.append(f'# TYPE {self.service_name}_uptime_seconds gauge')
        lines.append(f'{self.service_name}_uptime_seconds {summary["uptime_seconds"]:.2f}')
        
        # 当前 QPS
        lines.append(f'# HELP {self.service_name}_qps Current queries per second')
        lines.append(f'# TYPE {self.service_name}_qps gauge')
        lines.append(f'{self.service_name}_qps {summary["current_qps"]:.2f}')
        
        # 各端点指标
        for endpoint, stats in summary["endpoints"].items():
            safe_endpoint = endpoint.replace('/', '_').replace('-', '_')
            
            # 请求总数
            lines.append(f'# HELP {self.service_name}_requests_total Total requests to {endpoint}')
            lines.append(f'# TYPE {self.service_name}_requests_total counter')
            lines.append(f'{self.service_name}_requests_total{{endpoint="{endpoint}"}} {stats["request_count"]}')
            
            # 平均延迟
            lines.append(f'# HELP {self.service_name}_latency_ms Average latency in milliseconds')
            lines.append(f'# TYPE {self.service_name}_latency_ms gauge')
            lines.append(f'{self.service_name}_latency_ms{{endpoint="{endpoint}"}} {stats["avg_latency_ms"]}')
            
            # P95 延迟
            lines.append(f'# HELP {self.service_name}_latency_p95_ms P95 latency in milliseconds')
            lines.append(f'# TYPE {self.service_name}_latency_p95_ms gauge')
            lines.append(f'{self.service_name}_latency_p95_ms{{endpoint="{endpoint}"}} {stats["p95_latency_ms"]}')
            
            # 错误率
            lines.append(f'# HELP {self.service_name}_error_rate Error rate')
            lines.append(f'# TYPE {self.service_name}_error_rate gauge')
            lines.append(f'{self.service_name}_error_rate{{endpoint="{endpoint}"}} {stats["error_rate"]}')
        
        return '\n'.join(lines)

# 全局指标实例
_metrics_instances: Dict[str, PrometheusMetrics] = {}

def get_metrics(service_name: str) -> PrometheusMetrics:
    """获取或创建指标实例"""
    if service_name not in _metrics_instances:
        _metrics_instances[service_name] = PrometheusMetrics(service_name)
    return _metrics_instances[service_name]
