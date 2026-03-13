#!/usr/bin/env python3
"""
异步处理性能测试脚本
对比同步 vs 异步性能
"""
import asyncio
import time
import aiohttp
import json
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class PerformanceResult:
    """性能测试结果"""
    test_name: str
    method: str  # sync/async
    total_time: float
    avg_time: float
    items_per_second: float
    total_items: int

async def benchmark_http_endpoint(
    session: aiohttp.ClientSession,
    url: str,
    method: str = "GET",
    payload: Dict = None,
    items: int = 10,
    concurrent: bool = True
) -> PerformanceResult:
    """基准测试 HTTP 端点"""
    
    async def make_request():
        start = time.time()
        try:
            if method == "GET":
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    await resp.read()
            else:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    await resp.read()
            return time.time() - start
        except Exception as e:
            print(f"Request error: {e}")
            return time.time() - start
    
    start_total = time.time()
    
    if concurrent:
        # 并发执行
        tasks = [make_request() for _ in range(items)]
        await asyncio.gather(*tasks)
    else:
        # 顺序执行
        for _ in range(items):
            await make_request()
    
    total_time = time.time() - start_total
    
    return PerformanceResult(
        test_name=url,
        method="async_concurrent" if concurrent else "sync_sequential",
        total_time=total_time,
        avg_time=total_time / items,
        items_per_second=items / total_time if total_time > 0 else 0,
        total_items=items
    )


async def test_chunker_performance():
    """测试文本切分服务性能"""
    print("\n" + "="*60)
    print("✂️  文本切分服务性能测试")
    print("="*60)
    
    base_url = "http://localhost:8001"
    test_text = "这是测试内容。" * 100  # 约 500 字
    
    async with aiohttp.ClientSession() as session:
        # 顺序测试
        print("\n📊 顺序处理 (10 次请求)...")
        sync_result = await benchmark_http_endpoint(
            session,
            f"{base_url}/chunk",
            method="POST",
            payload={"markdown": test_text},
            items=10,
            concurrent=False
        )
        print(f"  总时间：{sync_result.total_time:.2f}s")
        print(f"  平均时间：{sync_result.avg_time*1000:.2f}ms")
        print(f"  QPS: {sync_result.items_per_second:.2f}")
        
        # 并发测试
        print("\n📊 并发处理 (10 次请求)...")
        async_result = await benchmark_http_endpoint(
            session,
            f"{base_url}/chunk",
            method="POST",
            payload={"markdown": test_text},
            items=10,
            concurrent=True
        )
        print(f"  总时间：{async_result.total_time:.2f}s")
        print(f"  平均时间：{async_result.avg_time*1000:.2f}ms")
        print(f"  QPS: {async_result.items_per_second:.2f}")
        
        # 性能提升
        speedup = sync_result.total_time / async_result.total_time if async_result.total_time > 0 else 0
        print(f"\n🚀 性能提升：{speedup:.1f}x")
        
        return sync_result, async_result


async def test_pdf_service_performance():
    """测试 PDF 服务性能（健康检查）"""
    print("\n" + "="*60)
    print("📄 PDF 提取服务性能测试")
    print("="*60)
    
    base_url = "http://localhost:8006"
    
    async with aiohttp.ClientSession() as session:
        # 顺序测试
        print("\n📊 顺序处理 (20 次请求)...")
        sync_result = await benchmark_http_endpoint(
            session,
            f"{base_url}/health",
            items=20,
            concurrent=False
        )
        print(f"  总时间：{sync_result.total_time:.2f}s")
        print(f"  平均时间：{sync_result.avg_time*1000:.2f}ms")
        print(f"  QPS: {sync_result.items_per_second:.2f}")
        
        # 并发测试
        print("\n📊 并发处理 (20 次请求)...")
        async_result = await benchmark_http_endpoint(
            session,
            f"{base_url}/health",
            items=20,
            concurrent=True
        )
        print(f"  总时间：{async_result.total_time:.2f}s")
        print(f"  平均时间：{async_result.avg_time*1000:.2f}ms")
        print(f"  QPS: {async_result.items_per_second:.2f}")
        
        # 性能提升
        speedup = sync_result.total_time / async_result.total_time if async_result.total_time > 0 else 0
        print(f"\n🚀 性能提升：{speedup:.1f}x")
        
        return sync_result, async_result


async def test_chat_service_performance():
    """测试对话服务性能（健康检查）"""
    print("\n" + "="*60)
    print("💬 对话检索服务性能测试")
    print("="*60)
    
    base_url = "http://localhost:8501"
    
    async with aiohttp.ClientSession() as session:
        # 顺序测试
        print("\n📊 顺序处理 (20 次请求)...")
        sync_result = await benchmark_http_endpoint(
            session,
            f"{base_url}/health",
            items=20,
            concurrent=False
        )
        print(f"  总时间：{sync_result.total_time:.2f}s")
        print(f"  平均时间：{sync_result.avg_time*1000:.2f}ms")
        print(f"  QPS: {sync_result.items_per_second:.2f}")
        
        # 并发测试
        print("\n📊 并发处理 (20 次请求)...")
        async_result = await benchmark_http_endpoint(
            session,
            f"{base_url}/health",
            items=20,
            concurrent=True
        )
        print(f"  总时间：{async_result.total_time:.2f}s")
        print(f"  平均时间：{async_result.avg_time*1000:.2f}ms")
        print(f"  QPS: {async_result.items_per_second:.2f}")
        
        # 性能提升
        speedup = sync_result.total_time / async_result.total_time if async_result.total_time > 0 else 0
        print(f"\n🚀 性能提升：{speedup:.1f}x")
        
        return sync_result, async_result


async def main():
    """主函数"""
    print("="*80)
    print("🚀 异步处理性能基准测试")
    print(f"时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    all_results = []
    
    # 测试各服务
    try:
        all_results.append(("文本切分", await test_chunker_performance()))
    except Exception as e:
        print(f"文本切分测试失败：{e}")
    
    try:
        all_results.append(("PDF 服务", await test_pdf_service_performance()))
    except Exception as e:
        print(f"PDF 服务测试失败：{e}")
    
    try:
        all_results.append(("对话服务", await test_chat_service_performance()))
    except Exception as e:
        print(f"对话服务测试失败：{e}")
    
    # 汇总报告
    print("\n" + "="*80)
    print("📊 性能测试汇总")
    print("="*80)
    
    for service_name, (sync_result, async_result) in all_results:
        speedup = sync_result.total_time / async_result.total_time if async_result.total_time > 0 else 0
        print(f"\n{service_name}:")
        print(f"  顺序 QPS: {sync_result.items_per_second:.2f}")
        print(f"  并发 QPS: {async_result.items_per_second:.2f}")
        print(f"  性能提升：{speedup:.1f}x")
    
    print("\n" + "="*80)
    
    # 保存结果
    report = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "results": [
            {
                "service": name,
                "sync": {
                    "total_time": sync.total_time,
                    "avg_time_ms": sync.avg_time * 1000,
                    "qps": sync.items_per_second
                },
                "async": {
                    "total_time": async_.total_time,
                    "avg_time_ms": async_.avg_time * 1000,
                    "qps": async_.items_per_second
                },
                "speedup": sync.total_time / async_.total_time if async_.total_time > 0 else 0
            }
            for name, (sync, async_) in all_results
        ]
    }
    
    import os
    os.makedirs("logs", exist_ok=True)
    with open("logs/async_performance_report.json", 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 报告已保存：logs/async_performance_report.json")


if __name__ == "__main__":
    asyncio.run(main())
