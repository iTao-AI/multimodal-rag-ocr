#!/usr/bin/env python3
"""
全局异常处理测试脚本
验证各服务的异常处理是否正确集成
"""
import requests
import json
import sys
from typing import Dict, List

SERVICES = {
    "pdf_extraction": "http://localhost:8006",
    "chunker": "http://localhost:8001",
    "milvus_api": "http://localhost:8000",
    "chat": "http://localhost:8501",
}


class TestResult:
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
    
    def __str__(self):
        icon = "✅" if self.passed else "❌"
        return f"{icon} {self.name}: {self.message}"


def test_health_endpoint(service_name: str, base_url: str) -> TestResult:
    """测试健康检查端点"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "request_id" in response.headers or "X-Request-ID" in response.headers:
                return TestResult(
                    f"{service_name} 健康检查",
                    True,
                    f"返回 request_id: {response.headers.get('X-Request-ID', 'N/A')}"
                )
            else:
                return TestResult(
                    f"{service_name} 健康检查",
                    True,
                    "正常 (缺少 X-Request-ID 响应头)"
                )
        else:
            return TestResult(
                f"{service_name} 健康检查",
                False,
                f"状态码：{response.status_code}"
            )
    except Exception as e:
        return TestResult(
            f"{service_name} 健康检查",
            False,
            f"异常：{str(e)}"
        )


def test_404_response(service_name: str, base_url: str) -> TestResult:
    """测试 404 错误响应格式"""
    try:
        response = requests.get(f"{base_url}/nonexistent_endpoint", timeout=10)
        
        if response.status_code == 404:
            data = response.json()
            
            # 检查错误格式
            checks = []
            if "error" in data:
                checks.append("✓ error 字段")
                error = data["error"]
                
                if "code" in error:
                    checks.append("✓ code 字段")
                if "message" in error:
                    checks.append("✓ message 字段")
                if "request_id" in error:
                    checks.append("✓ request_id 字段")
                if "status_code" in error:
                    checks.append("✓ status_code 字段")
                if "timestamp" in error:
                    checks.append("✓ timestamp 字段")
            
            return TestResult(
                f"{service_name} 404 响应格式",
                True,
                f"格式正确 ({', '.join(checks)})"
            )
        else:
            return TestResult(
                f"{service_name} 404 响应格式",
                False,
                f"状态码：{response.status_code}"
            )
    except Exception as e:
        return TestResult(
            f"{service_name} 404 响应格式",
            False,
            f"异常：{str(e)}"
        )


def test_request_id_propagation(service_name: str, base_url: str) -> TestResult:
    """测试 request_id 传递"""
    try:
        custom_request_id = "test-request-id-12345"
        headers = {"X-Request-ID": custom_request_id}
        
        response = requests.get(f"{base_url}/health", headers=headers, timeout=10)
        
        returned_id = response.headers.get("X-Request-ID", "")
        
        if returned_id == custom_request_id:
            return TestResult(
                f"{service_name} request_id 传递",
                True,
                f"request_id 正确传递：{returned_id}"
            )
        else:
            return TestResult(
                f"{service_name} request_id 传递",
                False,
                f"request_id 不匹配：期望 {custom_request_id}, 实际 {returned_id}"
            )
    except Exception as e:
        return TestResult(
            f"{service_name} request_id 传递",
            False,
            f"异常：{str(e)}"
        )


def test_process_time_header(service_name: str, base_url: str) -> TestResult:
    """测试处理时间响应头"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        
        process_time = response.headers.get("X-Process-Time", "")
        
        if process_time:
            return TestResult(
                f"{service_name} 处理时间头",
                True,
                f"处理时间：{process_time}"
            )
        else:
            return TestResult(
                f"{service_name} 处理时间头",
                False,
                "缺少 X-Process-Time 响应头"
            )
    except Exception as e:
        return TestResult(
            f"{service_name} 处理时间头",
            False,
            f"异常：{str(e)}"
        )


def test_error_response_structure(service_name: str, base_url: str) -> TestResult:
    """测试错误响应结构完整性"""
    try:
        response = requests.get(f"{base_url}/nonexistent", timeout=10)
        data = response.json()
        
        required_fields = ["error", "code", "message", "request_id", "status_code", "timestamp"]
        missing_fields = []
        
        if "error" not in data:
            return TestResult(
                f"{service_name} 错误响应结构",
                False,
                "缺少 error 根字段"
            )
        
        error = data["error"]
        for field in required_fields[1:]:  # 跳过 error
            if field not in error:
                missing_fields.append(field)
        
        if missing_fields:
            return TestResult(
                f"{service_name} 错误响应结构",
                False,
                f"缺少字段：{', '.join(missing_fields)}"
            )
        else:
            return TestResult(
                f"{service_name} 错误响应结构",
                True,
                "所有必需字段都存在"
            )
    except Exception as e:
        return TestResult(
            f"{service_name} 错误响应结构",
            False,
            f"异常：{str(e)}"
        )


def run_all_tests() -> List[TestResult]:
    """运行所有测试"""
    results = []
    
    print("="*80)
    print("🧪 全局异常处理测试")
    print("="*80)
    print()
    
    for service_name, base_url in SERVICES.items():
        print(f"\n📦 测试 {service_name} ({base_url})")
        print("-"*60)
        
        # 测试健康检查
        results.append(test_health_endpoint(service_name, base_url))
        
        # 测试 404 响应
        results.append(test_404_response(service_name, base_url))
        
        # 测试 request_id 传递
        results.append(test_request_id_propagation(service_name, base_url))
        
        # 测试处理时间头
        results.append(test_process_time_header(service_name, base_url))
        
        # 测试错误响应结构
        results.append(test_error_response_structure(service_name, base_url))
        
        # 打印结果
        for result in results[-5:]:
            print(f"  {result}")
    
    return results


def print_summary(results: List[TestResult]):
    """打印测试摘要"""
    print()
    print("="*80)
    print("📊 测试摘要")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    
    print(f"总测试数：{total}")
    print(f"✅ 通过：{passed}")
    print(f"❌ 失败：{failed}")
    print(f"通过率：{passed/total*100:.1f}%")
    
    if failed > 0:
        print()
        print("失败的测试:")
        for result in results:
            if not result.passed:
                print(f"  ❌ {result.name}: {result.message}")
    
    print("="*80)


def main():
    """主函数"""
    results = run_all_tests()
    print_summary(results)
    
    # 保存测试结果
    report = {
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "total": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": len(results) - sum(1 for r in results if r.passed),
        "results": [
            {"name": r.name, "passed": r.passed, "message": r.message}
            for r in results
        ]
    }
    
    report_file = "logs/exception_handling_test.json"
    try:
        import os
        os.makedirs("logs", exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 测试报告已保存：{report_file}")
    except Exception as e:
        print(f"\n⚠️  保存报告失败：{e}")
    
    # 返回退出码
    sys.exit(0 if all(r.passed for r in results) else 1)


if __name__ == "__main__":
    main()
