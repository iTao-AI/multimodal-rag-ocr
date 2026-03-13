#!/usr/bin/env python3
"""
性能基准测试脚本
测试各服务的响应时间、吞吐量、并发能力
"""
import requests
import time
import statistics
import json
import os
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============ 服务配置 ============

SERVICES = {
    "pdf_extraction": {"host": "http://localhost", "port": 8006, "name": "PDF 提取服务"},
    "chunker": {"host": "http://localhost", "port": 8001, "name": "文本切分服务"},
    "milvus_api": {"host": "http://localhost", "port": 8000, "name": "Milvus API 服务"},
    "chat": {"host": "http://localhost", "port": 8501, "name": "对话检索服务"},
}

# ============ 数据类 ============

@dataclass
class BenchmarkResult:
    """基准测试结果"""
    service: str
    endpoint: str
    test_type: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time_sec: float
    qps: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    error_rate: float

@dataclass
class PerformanceReport:
    """性能报告"""
    timestamp: str
    duration_sec: int
    results: List[BenchmarkResult]
    summary: Dict

# ============ 基准测试器 ============

class PerformanceBenchmark:
    """性能基准测试器"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.session = requests.Session()
        
    def _make_single_request(self, method: str, url: str, **kwargs) -> Tuple[bool, float]:
        """发送单个请求并返回 (成功与否，延迟 ms)"""
        start = time.time()
        try:
            if method == "GET":
                response = self.session.get(url, timeout=kwargs.get("timeout", 30))
            else:
                response = self.session.post(url, timeout=kwargs.get("timeout", 30), **kwargs)
            
            latency = (time.time() - start) * 1000
            return response.status_code < 500, latency
            
        except Exception as e:
            latency = (time.time() - start) * 1000
            return False, latency
    
    def _benchmark_endpoint(
        self,
        name: str,
        method: str,
        url: str,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        **kwargs
    ) -> BenchmarkResult:
        """基准测试单个端点"""
        latencies = []
        success_count = 0
        fail_count = 0
        start_time = time.time()
        
        def worker():
            success, latency = self._make_single_request(method, url, **kwargs)
            return success, latency
        
        # 并发执行
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(worker) for _ in range(concurrent_users * requests_per_user)]
            
            for future in as_completed(futures):
                success, latency = future.result()
                latencies.append(latency)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
        
        total_time = time.time() - start_time
        total_requests = len(latencies)
        
        # 计算统计值
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        result = BenchmarkResult(
            service=name,
            endpoint=url,
            test_type=f"并发={concurrent_users}, 请求数={total_requests}",
            total_requests=total_requests,
            successful_requests=success_count,
            failed_requests=fail_count,
            total_time_sec=round(total_time, 2),
            qps=round(total_requests / total_time, 2) if total_time > 0 else 0,
            avg_latency_ms=round(statistics.mean(latencies), 2),
            p50_latency_ms=round(sorted_latencies[int(n * 0.5)] if n > 0 else 0, 2),
            p95_latency_ms=round(sorted_latencies[int(n * 0.95)] if n > 0 else 0, 2),
            p99_latency_ms=round(sorted_latencies[int(n * 0.99)] if n > 0 else 0, 2),
            min_latency_ms=round(min(latencies) if latencies else 0, 2),
            max_latency_ms=round(max(latencies) if latencies else 0, 2),
            error_rate=round(fail_count / total_requests, 4) if total_requests > 0 else 0
        )
        
        return result
    
    # ========== PDF 提取服务基准测试 ==========
    
    def test_pdf_health(self) -> BenchmarkResult:
        """PDF 提取服务健康检查基准"""
        url = f"{SERVICES['pdf_extraction']['host']}:{SERVICES['pdf_extraction']['port']}/health"
        print(f"\n📄 测试 PDF 提取服务健康检查...")
        return self._benchmark_endpoint("PDF 提取", "GET", url, concurrent_users=10, requests_per_user=10)
    
    def test_pdf_docs(self) -> BenchmarkResult:
        """PDF 提取服务文档端点基准"""
        url = f"{SERVICES['pdf_extraction']['host']}:{SERVICES['pdf_extraction']['port']}/docs"
        print(f"📄 测试 PDF 提取服务文档端点...")
        return self._benchmark_endpoint("PDF 提取", "GET", url, concurrent_users=5, requests_per_user=5)
    
    # ========== 文本切分服务基准测试 ==========
    
    def test_chunker_docs(self) -> BenchmarkResult:
        """文本切分服务文档端点基准"""
        url = f"{SERVICES['chunker']['host']}:{SERVICES['chunker']['port']}/docs"
        print(f"✂️  测试文本切分服务文档端点...")
        return self._benchmark_endpoint("文本切分", "GET", url, concurrent_users=5, requests_per_user=5)
    
    def test_chunker_chunk(self) -> BenchmarkResult:
        """文本切分服务切分端点基准"""
        url = f"{SERVICES['chunker']['host']}:{SERVICES['chunker']['port']}/chunk"
        print(f"✂️  测试文本切分服务切分端点...")
        return self._benchmark_endpoint(
            "文本切分", "POST", url,
            concurrent_users=5, requests_per_user=5,
            json={"markdown": "这是测试内容。" * 100}
        )
    
    # ========== Milvus API 服务基准测试 ==========
    
    def test_milvus_health(self) -> BenchmarkResult:
        """Milvus API 服务健康检查基准"""
        url = f"{SERVICES['milvus_api']['host']}:{SERVICES['milvus_api']['port']}/health"
        print(f"🗄️  测试 Milvus API 服务健康检查...")
        return self._benchmark_endpoint("Milvus API", "GET", url, concurrent_users=10, requests_per_user=10)
    
    def test_milvus_search(self) -> BenchmarkResult:
        """Milvus API 服务搜索端点基准"""
        url = f"{SERVICES['milvus_api']['host']}:{SERVICES['milvus_api']['port']}/search"
        print(f"🗄️  测试 Milvus API 服务搜索端点...")
        return self._benchmark_endpoint(
            "Milvus API", "POST", url,
            concurrent_users=3, requests_per_user=3,
            json={"collection_name": "test", "query_text": "test", "top_k": 5}
        )
    
    # ========== 对话检索服务基准测试 ==========
    
    def test_chat_health(self) -> BenchmarkResult:
        """对话检索服务健康检查基准"""
        url = f"{SERVICES['chat']['host']}:{SERVICES['chat']['port']}/health"
        print(f"💬 测试对话检索服务健康检查...")
        return self._benchmark_endpoint("对话检索", "GET", url, concurrent_users=10, requests_per_user=10)
    
    def test_chat_docs(self) -> BenchmarkResult:
        """对话检索服务文档端点基准"""
        url = f"{SERVICES['chat']['host']}:{SERVICES['chat']['port']}/docs"
        print(f"💬 测试对话检索服务文档端点...")
        return self._benchmark_endpoint("对话检索", "GET", url, concurrent_users=5, requests_per_user=5)
    
    # ========== 运行所有基准测试 ==========
    
    def run_all_benchmarks(self) -> PerformanceReport:
        """运行所有基准测试"""
        print("="*80)
        print("🚀 Multimodal RAG 后端性能基准测试")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        start_time = time.time()
        
        # PDF 提取服务
        print("\n" + "="*40)
        print("📄 PDF 提取服务 (8006)")
        print("="*40)
        self.results.append(self.test_pdf_health())
        self.results.append(self.test_pdf_docs())
        
        # 文本切分服务
        print("\n" + "="*40)
        print("✂️  文本切分服务 (8001)")
        print("="*40)
        self.results.append(self.test_chunker_docs())
        self.results.append(self.test_chunker_chunk())
        
        # Milvus API 服务
        print("\n" + "="*40)
        print("🗄️  Milvus API 服务 (8000)")
        print("="*40)
        self.results.append(self.test_milvus_health())
        self.results.append(self.test_milvus_search())
        
        # 对话检索服务
        print("\n" + "="*40)
        print("💬 对话检索服务 (8501)")
        print("="*40)
        self.results.append(self.test_chat_health())
        self.results.append(self.test_chat_docs())
        
        total_time = time.time() - start_time
        
        # 生成摘要
        summary = {
            "total_tests": len(self.results),
            "total_time_sec": round(total_time, 2),
            "avg_qps": round(statistics.mean([r.qps for r in self.results]), 2),
            "avg_latency_ms": round(statistics.mean([r.avg_latency_ms for r in self.results]), 2),
            "avg_error_rate": round(statistics.mean([r.error_rate for r in self.results]), 4)
        }
        
        return PerformanceReport(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            duration_sec=round(total_time, 2),
            results=self.results,
            summary=summary
        )
    
    def print_report(self, report: PerformanceReport):
        """打印性能报告"""
        print("\n" + "="*80)
        print("📊 性能基准测试报告")
        print("="*80)
        print(f"时间：{report.timestamp}")
        print(f"总耗时：{report.duration_sec}秒")
        print(f"平均 QPS: {report.summary['avg_qps']}")
        print(f"平均延迟：{report.summary['avg_latency_ms']}ms")
        print(f"平均错误率：{report.summary['avg_error_rate']*100:.2f}%")
        print("="*80)
        
        for result in report.results:
            print(f"\n{result.service} - {result.endpoint}")
            print(f"  QPS: {result.qps}")
            print(f"  平均延迟：{result.avg_latency_ms}ms")
            print(f"  P50 延迟：{result.p50_latency_ms}ms")
            print(f"  P95 延迟：{result.p95_latency_ms}ms")
            print(f"  P99 延迟：{result.p99_latency_ms}ms")
            print(f"  错误率：{result.error_rate*100:.2f}%")
        
        print("\n" + "="*80)
    
    def save_report(self, report: PerformanceReport, output_file: str):
        """保存性能报告"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        report_data = {
            "timestamp": report.timestamp,
            "summary": report.summary,
            "results": [asdict(r) for r in report.results]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 报告已保存：{output_file}")


def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    
    # 运行所有基准测试
    report = benchmark.run_all_benchmarks()
    
    # 打印报告
    benchmark.print_report(report)
    
    # 保存报告
    output_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'performance_benchmark.json')
    benchmark.save_report(report, output_file)


if __name__ == "__main__":
    main()
