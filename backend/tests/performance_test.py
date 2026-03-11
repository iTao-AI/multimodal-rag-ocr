#!/usr/bin/env python3
"""
性能压力测试脚本
测试各服务的并发性能、延迟、错误率
"""
import asyncio
import aiohttp
import time
import statistics
import json
import os
from typing import List, Dict
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

@dataclass
class TestResult:
    """测试结果"""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    qps: float
    error_rate: float

class PerformanceTester:
    """性能测试器"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        
    async def _make_request(self, session: aiohttp.ClientSession, method: str, endpoint: str, 
                           payload: Dict = None) -> tuple:
        """发送单个请求"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method == "GET":
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    await response.read()
            elif method == "POST":
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    await response.read()
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            latency = (time.time() - start_time) * 1000  # ms
            success = response.status < 500
            return success, latency, response.status
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return False, latency, 0
    
    async def _stress_test(self, endpoint: str, method: str, payload: Dict, 
                          concurrent_users: int, requests_per_user: int) -> TestResult:
        """压力测试"""
        latencies = []
        success_count = 0
        fail_count = 0
        start_time = time.time()
        
        connector = aiohttp.TCPConnector(limit=concurrent_users)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for _ in range(concurrent_users * requests_per_user):
                task = self._make_request(session, method, endpoint, payload)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    fail_count += 1
                    latencies.append(0)
                else:
                    success, latency, status = result
                    latencies.append(latency)
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
        
        total_time = time.time() - start_time
        valid_latencies = [l for l in latencies if l > 0]
        
        if not valid_latencies:
            valid_latencies = [0]
        
        sorted_latencies = sorted(valid_latencies)
        n = len(sorted_latencies)
        
        return TestResult(
            endpoint=endpoint,
            total_requests=len(results),
            successful_requests=success_count,
            failed_requests=fail_count,
            total_time=total_time,
            avg_latency_ms=statistics.mean(valid_latencies),
            p50_latency_ms=sorted_latencies[int(n * 0.5)] if n > 0 else 0,
            p95_latency_ms=sorted_latencies[int(n * 0.95)] if n > 0 else 0,
            p99_latency_ms=sorted_latencies[int(n * 0.99)] if n > 0 else 0,
            qps=len(results) / total_time if total_time > 0 else 0,
            error_rate=fail_count / len(results) if len(results) > 0 else 0
        )
    
    async def test_pdf_extraction_service(self, concurrent_users: int = 10, 
                                         requests_per_user: int = 5) -> TestResult:
        """测试 PDF 提取服务"""
        print(f"\n📄 测试 PDF 提取服务 (并发：{concurrent_users}, 请求数：{concurrent_users * requests_per_user})")
        return await self._stress_test(
            endpoint="/extract/fast",
            method="POST",
            payload={"test": "data"},
            concurrent_users=concurrent_users,
            requests_per_user=requests_per_user
        )
    
    async def test_chunker_service(self, concurrent_users: int = 10, 
                                  requests_per_user: int = 10) -> TestResult:
        """测试文本切分服务"""
        print(f"\n✂️  测试文本切分服务 (并发：{concurrent_users}, 请求数：{concurrent_users * requests_per_user})")
        return await self._stress_test(
            endpoint="/chunk",
            method="POST",
            payload={"text": "test content" * 100},
            concurrent_users=concurrent_users,
            requests_per_user=requests_per_user
        )
    
    async def test_milvus_api(self, concurrent_users: int = 5, 
                             requests_per_user: int = 5) -> TestResult:
        """测试 Milvus API 服务"""
        print(f"\n🗄️  测试 Milvus API 服务 (并发：{concurrent_users}, 请求数：{concurrent_users * requests_per_user})")
        return await self._stress_test(
            endpoint="/search",
            method="POST",
            payload={"collection_name": "test", "query_text": "test query", "top_k": 5},
            concurrent_users=concurrent_users,
            requests_per_user=requests_per_user
        )
    
    async def test_chat_service(self, concurrent_users: int = 5, 
                               requests_per_user: int = 5) -> TestResult:
        """测试对话检索服务"""
        print(f"\n💬 测试对话检索服务 (并发：{concurrent_users}, 请求数：{concurrent_users * requests_per_user})")
        return await self._stress_test(
            endpoint="/chat",
            method="POST",
            payload={
                "query": "test question",
                "collection_name": "test",
                "llm_config": {
                    "api_url": "http://test",
                    "api_key": "test",
                    "model_name": "test"
                }
            },
            concurrent_users=concurrent_users,
            requests_per_user=requests_per_user
        )
    
    async def test_health_endpoints(self) -> Dict:
        """测试健康检查端点"""
        print("\n🏥 测试健康检查端点...")
        endpoints = [
            ("/docs", "Swagger UI"),
            ("/health", "Health Check"),
            ("/metrics", "Prometheus Metrics"),
            ("/stats", "Service Stats")
        ]
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for endpoint, name in endpoints:
                try:
                    async with session.get(f"{self.base_url}{endpoint}", 
                                         timeout=aiohttp.ClientTimeout(total=5)) as response:
                        results[name] = {
                            "status": response.status,
                            "available": response.status == 200
                        }
                except Exception as e:
                    results[name] = {
                        "status": 0,
                        "available": False,
                        "error": str(e)
                    }
        
        return results
    
    def print_report(self, results: List[TestResult], health_results: Dict):
        """打印测试报告"""
        print("\n" + "="*80)
        print("📊 性能测试报告")
        print("="*80)
        
        for result in results:
            print(f"\n{result.endpoint}")
            print(f"  总请求数：{result.total_requests}")
            print(f"  成功/失败：{result.successful_requests}/{result.failed_requests}")
            print(f"  QPS: {result.qps:.2f}")
            print(f"  平均延迟：{result.avg_latency_ms:.2f}ms")
            print(f"  P50 延迟：{result.p50_latency_ms:.2f}ms")
            print(f"  P95 延迟：{result.p95_latency_ms:.2f}ms")
            print(f"  P99 延迟：{result.p99_latency_ms:.2f}ms")
            print(f"  错误率：{result.error_rate*100:.2f}%")
        
        print("\n" + "-"*80)
        print("🏥 健康检查端点")
        print("-"*80)
        for name, info in health_results.items():
            status = "✅" if info.get("available") else "❌"
            print(f"  {status} {name}: {info.get('status', 'N/A')}")
        
        print("\n" + "="*80)

async def main():
    """主函数"""
    print("🚀 开始性能压力测试...")
    print(f"测试目标：http://localhost")
    print(f"时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = PerformanceTester(base_url="http://localhost")
    
    # 测试各服务（使用较小的并发数避免压垮服务）
    results = []
    
    # 健康检查
    health_results = await tester.test_health_endpoints()
    
    # PDF 提取服务 (端口 8006)
    tester.base_url = "http://localhost:8006"
    result = await tester.test_pdf_extraction_service(concurrent_users=5, requests_per_user=3)
    results.append(result)
    
    # 文本切分服务 (端口 8001)
    tester.base_url = "http://localhost:8001"
    result = await tester.test_chunker_service(concurrent_users=5, requests_per_user=5)
    results.append(result)
    
    # Milvus API 服务 (端口 8000)
    tester.base_url = "http://localhost:8000"
    result = await tester.test_milvus_api(concurrent_users=3, requests_per_user=3)
    results.append(result)
    
    # 对话检索服务 (端口 8501)
    tester.base_url = "http://localhost:8501"
    result = await tester.test_chat_service(concurrent_users=3, requests_per_user=3)
    results.append(result)
    
    # 打印报告
    tester.print_report(results, health_results)
    
    # 保存报告
    report = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "results": [
            {
                "endpoint": r.endpoint,
                "total_requests": r.total_requests,
                "successful_requests": r.successful_requests,
                "qps": r.qps,
                "avg_latency_ms": r.avg_latency_ms,
                "p95_latency_ms": r.p95_latency_ms,
                "error_rate": r.error_rate
            }
            for r in results
        ],
        "health_endpoints": health_results
    }
    
    report_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'performance_report.json')
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 报告已保存：{report_file}")

if __name__ == "__main__":
    asyncio.run(main())
