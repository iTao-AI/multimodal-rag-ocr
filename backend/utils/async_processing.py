"""
异步处理模块
提供进程池和线程池用于 CPU 密集型任务
"""
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import asyncio
from typing import Callable, Any, List, TypeVar
import functools

T = TypeVar('T')

# ============ 执行器池 ============

# CPU 密集型任务使用进程池
process_executor = ProcessPoolExecutor(max_workers=4)

# I/O 密集型任务使用线程池
thread_executor = ThreadPoolExecutor(max_workers=10)


# ============ 异步包装器 ============

async def run_in_process(func: Callable, *args, **kwargs) -> Any:
    """在进程池中运行 CPU 密集型函数"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        process_executor,
        functools.partial(func, **kwargs),
        *args
    )


async def run_in_thread(func: Callable, *args, **kwargs) -> Any:
    """在线程池中运行 I/O 密集型函数"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_executor,
        functools.partial(func, **kwargs),
        *args
    )


async def gather_with_concurrency(n: int, *coros):
    """限制并发数的 gather"""
    semaphore = asyncio.Semaphore(n)
    
    async def sem_coro(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*(sem_coro(coro) for coro in coros))


# ============ 批量处理辅助 ============

async def batch_process(
    items: List[Any],
    func: Callable,
    batch_size: int = 10,
    max_concurrency: int = 5
) -> List[Any]:
    """批量处理项目"""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        tasks = [func(item) for item in batch]
        batch_results = await gather_with_concurrency(max_concurrency, *tasks)
        results.extend(batch_results)
    
    return results


# ============ 清理函数 ============

def shutdown_executors():
    """关闭执行器池"""
    process_executor.shutdown(wait=True)
    thread_executor.shutdown(wait=True)


# ============ 性能测试辅助 ============

import time

async def benchmark_async(
    func: Callable,
    items: List[Any],
    concurrent: bool = True
) -> dict:
    """性能基准测试"""
    
    if concurrent:
        # 异步并发
        start = time.time()
        tasks = [func(item) for item in items]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
    else:
        # 同步顺序
        start = time.time()
        results = []
        for item in items:
            result = await func(item)
            results.append(result)
        elapsed = time.time() - start
    
    return {
        "total_time": elapsed,
        "avg_time": elapsed / len(items),
        "items_per_second": len(items) / elapsed if elapsed > 0 else 0,
        "total_items": len(items),
        "concurrent": concurrent
    }
