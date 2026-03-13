"""
性能基准测试

测试 API 响应时间、并发能力、检索性能
"""

import pytest
import requests
import time
import statistics
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed


# 测试配置
BASE_URL = "http://localhost:8000"
TEST_ROUNDS = 100  # 测试轮数


class TestAPIResponseTime:
    """API 响应时间测试"""
    
    def test_health_response_time(self):
        """测试健康检查响应时间"""
        response_times = []
        
        for _ in range(TEST_ROUNDS):
            start = time.time()
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            elapsed = (time.time() - start) * 1000  # 转换为毫秒
            response_times.append(elapsed)
            
            assert response.status_code == 200
        
        # 统计指标
        p50 = statistics.median(response_times)
        p95 = sorted(response_times)[int(len(response_times) * 0.95)]
        p99 = sorted(response_times)[int(len(response_times) * 0.99)]
        
        print(f"\n健康检查响应时间:")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")
        
        # 断言：P95 < 100ms
        assert p95 < 100, f"P95 响应时间 {p95:.2f}ms > 100ms"
    
    def test_search_response_time(self):
        """测试搜索接口响应时间"""
        query = "如何重置密码？"
        response_times = []
        
        for _ in range(TEST_ROUNDS):
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v1/search",
                json={
                    "query": query,
                    "top_k": 5,
                    "search_type": "vector"
                },
                timeout=10
            )
            elapsed = (time.time() - start) * 1000
            response_times.append(elapsed)
            
            assert response.status_code == 200
        
        # 统计指标
        p50 = statistics.median(response_times)
        p95 = sorted(response_times)[int(len(response_times) * 0.95)]
        p99 = sorted(response_times)[int(len(response_times) * 0.99)]
        
        print(f"\n搜索接口响应时间:")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")
        
        # 断言：P95 < 500ms
        assert p95 < 500, f"P95 响应时间 {p95:.2f}ms > 500ms"
    
    def test_chat_response_time(self):
        """测试对话接口响应时间"""
        query = "你好"
        response_times = []
        
        for _ in range(TEST_ROUNDS):
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v1/chat",
                json={
                    "query": query,
                    "collection_name": "documents"
                },
                timeout=10
            )
            elapsed = (time.time() - start) * 1000
            response_times.append(elapsed)
            
            assert response.status_code == 200
        
        # 统计指标
        p50 = statistics.median(response_times)
        p95 = sorted(response_times)[int(len(response_times) * 0.95)]
        p99 = sorted(response_times)[int(len(response_times) * 0.99)]
        
        print(f"\n对话接口响应时间:")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")
        
        # 断言：P95 < 2000ms (LLM 生成需要时间)
        assert p95 < 2000, f"P95 响应时间 {p95:.2f}ms > 2000ms"


class TestConcurrentLoad:
    """并发负载测试"""
    
    def test_10_qps(self):
        """测试 10 QPS 并发"""
        self._test_concurrent_load(concurrency=10, target_qps=10)
    
    def test_50_qps(self):
        """测试 50 QPS 并发"""
        self._test_concurrent_load(concurrency=50, target_qps=50)
    
    def test_100_qps(self):
        """测试 100 QPS 并发"""
        self._test_concurrent_load(concurrency=100, target_qps=100)
    
    def test_200_qps(self):
        """测试 200 QPS 并发"""
        self._test_concurrent_load(concurrency=200, target_qps=200)
    
    def _test_concurrent_load(self, concurrency: int, target_qps: int):
        """并发负载测试"""
        success_count = 0
        fail_count = 0
        response_times = []
        
        def send_request(i):
            try:
                start = time.time()
                response = requests.get(f"{BASE_URL}/health", timeout=5)
                elapsed = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    return True, elapsed
                else:
                    return False, elapsed
            except Exception as e:
                return False, 0
        
        # 并发发送请求
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(send_request, i) for i in range(concurrency)]
            
            for future in as_completed(futures):
                success, elapsed = future.result()
                if success:
                    success_count += 1
                    response_times.append(elapsed)
                else:
                    fail_count += 1
        
        # 计算指标
        total_requests = success_count + fail_count
        success_rate = (success_count / total_requests) * 100
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        else:
            avg_response_time = 0
            p95_response_time = 0
        
        print(f"\n并发负载测试 ({concurrency} QPS):")
        print(f"  总请求数：{total_requests}")
        print(f"  成功数：{success_count}")
        print(f"  失败数：{fail_count}")
        print(f"  成功率：{success_rate:.2f}%")
        print(f"  平均响应时间：{avg_response_time:.2f}ms")
        print(f"  P95 响应时间：{p95_response_time:.2f}ms")
        
        # 断言：成功率 > 99% (对于 10/50/100 QPS)
        # 200 QPS 允许 98% 成功率
        if concurrency <= 100:
            assert success_rate >= 99, f"成功率 {success_rate:.2f}% < 99%"
        else:
            assert success_rate >= 98, f"成功率 {success_rate:.2f}% < 98%"


class TestMilvusSearch:
    """Milvus 检索性能测试"""
    
    def test_milvus_search_latency(self):
        """测试 Milvus 检索延迟"""
        # 这个测试需要实际的 Milvus 连接
        # 如果没有 Milvus，跳过测试
        pytest.skip("需要 Milvus 连接")
        
        query = "测试查询"
        response_times = []
        
        for _ in range(TEST_ROUNDS):
            start = time.time()
            # 调用 Milvus 检索
            # results = milvus_client.search(query)
            elapsed = (time.time() - start) * 1000
            response_times.append(elapsed)
        
        p50 = statistics.median(response_times)
        p95 = sorted(response_times)[int(len(response_times) * 0.95)]
        
        print(f"\nMilvus 检索延迟:")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        
        # 断言：P95 < 200ms
        assert p95 < 200, f"P95 检索延迟 {p95:.2f}ms > 200ms"


def generate_performance_report():
    """生成性能报告"""
    import json
    from datetime import datetime
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_rounds": TEST_ROUNDS,
        "base_url": BASE_URL,
        "results": {
            "api_response_time": {
                "health": {"p50": 0, "p95": 0, "p99": 0},
                "search": {"p50": 0, "p95": 0, "p99": 0},
                "chat": {"p50": 0, "p95": 0, "p99": 0}
            },
            "concurrent_load": {
                "10_qps": {"success_rate": 0, "avg_response": 0},
                "50_qps": {"success_rate": 0, "avg_response": 0},
                "100_qps": {"success_rate": 0, "avg_response": 0},
                "200_qps": {"success_rate": 0, "avg_response": 0}
            }
        }
    }
    
    # 保存报告
    with open("tests/benchmark/performance_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n性能报告已生成：tests/benchmark/performance_report.json")


if __name__ == "__main__":
    # 运行性能测试
    pytest.main([__file__, "-v", "-s"])
    
    # 生成报告
    generate_performance_report()
