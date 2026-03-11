#!/usr/bin/env python3
"""
Multimodal RAG 后端 API 测试套件
测试所有服务的功能接口
"""
import requests
import json
import time
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# ============ 测试配置 ============

SERVICES = {
    "pdf_extraction": {"host": "http://localhost", "port": 8006},
    "chunker": {"host": "http://localhost", "port": 8001},
    "milvus_api": {"host": "http://localhost", "port": 8000},
    "chat": {"host": "http://localhost", "port": 8501},
}

# ============ 测试结果 ============

@dataclass
class TestResult:
    """测试结果"""
    name: str
    endpoint: str
    method: str
    status: str  # pass/fail/skip
    status_code: int
    response_time_ms: float
    error: Optional[str] = None
    data: Optional[Dict] = None

@dataclass
class TestReport:
    """测试报告"""
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    total_time_ms: float
    results: List[TestResult]

# ============ 测试套件 ============

class APITestSuite:
    """API 测试套件"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.session = requests.Session()
        
    def _make_request(self, method: str, url: str, name: str = None, **kwargs) -> TestResult:
        """发送请求并记录结果"""
        start_time = time.time()
        test_name = name or url
        
        try:
            if method == "GET":
                response = self.session.get(url, timeout=30, **kwargs)
            elif method == "POST":
                response = self.session.post(url, timeout=30, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code < 400:
                status = "pass"
            elif response.status_code == 404:
                status = "skip"
            else:
                status = "fail"
            
            return TestResult(
                name=test_name,
                endpoint=url,
                method=method,
                status=status,
                status_code=response.status_code,
                response_time_ms=round(response_time, 2),
                data=response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            )
            
        except requests.exceptions.RequestException as e:
            response_time = (time.time() - start_time) * 1000
            return TestResult(
                name=test_name,
                endpoint=url,
                method=method,
                status="fail",
                status_code=0,
                response_time_ms=round(response_time, 2),
                error=str(e)
            )
    
    # ========== PDF 提取服务测试 (8006) ==========
    
    def test_pdf_extraction_health(self):
        """测试 PDF 提取服务健康检查"""
        url = f"{SERVICES['pdf_extraction']['host']}:{SERVICES['pdf_extraction']['port']}/health"
        return self._make_request("GET", url, name="PDF 提取服务 - 健康检查")
    
    def test_pdf_extraction_docs(self):
        """测试 PDF 提取服务 API 文档"""
        url = f"{SERVICES['pdf_extraction']['host']}:{SERVICES['pdf_extraction']['port']}/docs"
        return self._make_request("GET", url, name="PDF 提取服务 - API 文档")
    
    def test_pdf_extraction_extract_fast(self):
        """测试 PDF 快速提取接口"""
        url = f"{SERVICES['pdf_extraction']['host']}:{SERVICES['pdf_extraction']['port']}/extract/fast"
        # 注意：实际测试需要上传真实 PDF 文件
        return self._make_request("POST", url, json={"test": "data"}, name="PDF 提取 - 快速模式")
    
    def test_pdf_extraction_extract_accurate(self):
        """测试 PDF 精确提取接口"""
        url = f"{SERVICES['pdf_extraction']['host']}:{SERVICES['pdf_extraction']['port']}/extract/accurate"
        payload = {
            "api_key": "test_key",
            "model_name": "qwen3-vl-plus",
            "model_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        }
        return self._make_request("POST", url, json=payload, name="PDF 提取 - 精确模式")
    
    # ========== 文本切分服务测试 (8001) ==========
    
    def test_chunker_health(self):
        """测试文本切分服务健康检查"""
        url = f"{SERVICES['chunker']['host']}:{SERVICES['chunker']['port']}/health"
        return self._make_request("GET", url, name="文本切分服务 - 健康检查")
    
    def test_chunker_docs(self):
        """测试文本切分服务 API 文档"""
        url = f"{SERVICES['chunker']['host']}:{SERVICES['chunker']['port']}/docs"
        return self._make_request("GET", url, name="文本切分服务 - API 文档")
    
    def test_chunker_chunk(self):
        """测试文本切分接口"""
        url = f"{SERVICES['chunker']['host']}:{SERVICES['chunker']['port']}/chunk"
        payload = {
            "text": "这是一个测试文本。" * 100,
            "chunk_size": 500,
            "chunk_overlap": 50
        }
        return self._make_request("POST", url, json=payload, name="文本切分 - 基础切分")
    
    def test_chunker_chunk_markdown(self):
        """测试 Markdown 文本切分接口"""
        url = f"{SERVICES['chunker']['host']}:{SERVICES['chunker']['port']}/chunk/markdown"
        payload = {
            "markdown_text": "# 标题\n\n这是内容。\n\n## 子标题\n\n更多内容。",
            "min_chunk_size": 100,
            "max_chunk_size": 1000
        }
        return self._make_request("POST", url, json=payload, name="文本切分 - Markdown 切分")
    
    # ========== Milvus API 服务测试 (8000) ==========
    
    def test_milvus_health(self):
        """测试 Milvus API 服务健康检查"""
        url = f"{SERVICES['milvus_api']['host']}:{SERVICES['milvus_api']['port']}/health"
        return self._make_request("GET", url, name="Milvus API 服务 - 健康检查")
    
    def test_milvus_docs(self):
        """测试 Milvus API 服务 API 文档"""
        url = f"{SERVICES['milvus_api']['host']}:{SERVICES['milvus_api']['port']}/docs"
        return self._make_request("GET", url, name="Milvus API 服务 - API 文档")
    
    def test_milvus_collections(self):
        """测试获取集合列表接口"""
        url = f"{SERVICES['milvus_api']['host']}:{SERVICES['milvus_api']['port']}/collections"
        return self._make_request("GET", url, name="Milvus - 获取集合列表")
    
    def test_milvus_search(self):
        """测试向量检索接口"""
        url = f"{SERVICES['milvus_api']['host']}:{SERVICES['milvus_api']['port']}/search"
        payload = {
            "collection_name": "test_collection",
            "query_text": "测试查询",
            "top_k": 5
        }
        return self._make_request("POST", url, json=payload, name="Milvus - 向量检索")
    
    def test_milvus_insert(self):
        """测试向量插入接口"""
        url = f"{SERVICES['milvus_api']['host']}:{SERVICES['milvus_api']['port']}/insert"
        payload = {
            "collection_name": "test_collection",
            "vectors": [[0.1] * 768],
            "metadata": [{"filename": "test.pdf", "chunk_text": "测试文本"}]
        }
        return self._make_request("POST", url, json=payload, name="Milvus - 向量插入")
    
    # ========== 对话检索服务测试 (8501) ==========
    
    def test_chat_health(self):
        """测试对话检索服务健康检查"""
        url = f"{SERVICES['chat']['host']}:{SERVICES['chat']['port']}/health"
        return self._make_request("GET", url, name="对话检索服务 - 健康检查")
    
    def test_chat_docs(self):
        """测试对话检索服务 API 文档"""
        url = f"{SERVICES['chat']['host']}:{SERVICES['chat']['port']}/docs"
        return self._make_request("GET", url, name="对话检索服务 - API 文档")
    
    def test_chat_query(self):
        """测试对话问答接口"""
        url = f"{SERVICES['chat']['host']}:{SERVICES['chat']['port']}/chat"
        payload = {
            "query": "什么是 RAG？",
            "collection_name": "test_collection",
            "llm_config": {
                "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "test_key",
                "model_name": "qwen3-vl-plus"
            },
            "top_k": 5,
            "stream": False
        }
        return self._make_request("POST", url, json=payload, name="对话检索 - 问答接口")
    
    def test_chat_query_stream(self):
        """测试流式对话接口"""
        url = f"{SERVICES['chat']['host']}:{SERVICES['chat']['port']}/chat/stream"
        payload = {
            "query": "什么是 RAG？",
            "collection_name": "test_collection",
            "llm_config": {
                "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "test_key",
                "model_name": "qwen3-vl-plus"
            },
            "top_k": 5,
            "stream": True
        }
        return self._make_request("POST", url, json=payload, name="对话检索 - 流式问答")
    
    # ========== 运行所有测试 ==========
    
    def run_all_tests(self) -> TestReport:
        """运行所有测试"""
        print("🚀 开始 API 测试套件...")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        start_time = time.time()
        
        # PDF 提取服务测试
        print("\n📄 PDF 提取服务测试 (8006)")
        print("-"*40)
        self.results.append(self.test_pdf_extraction_health())
        self.results.append(self.test_pdf_extraction_docs())
        self.results.append(self.test_pdf_extraction_extract_fast())
        self.results.append(self.test_pdf_extraction_extract_accurate())
        
        # 文本切分服务测试
        print("\n✂️  文本切分服务测试 (8001)")
        print("-"*40)
        self.results.append(self.test_chunker_health())
        self.results.append(self.test_chunker_docs())
        self.results.append(self.test_chunker_chunk())
        self.results.append(self.test_chunker_chunk_markdown())
        
        # Milvus API 服务测试
        print("\n🗄️  Milvus API 服务测试 (8000)")
        print("-"*40)
        self.results.append(self.test_milvus_health())
        self.results.append(self.test_milvus_docs())
        self.results.append(self.test_milvus_collections())
        self.results.append(self.test_milvus_search())
        self.results.append(self.test_milvus_insert())
        
        # 对话检索服务测试
        print("\n💬 对话检索服务测试 (8501)")
        print("-"*40)
        self.results.append(self.test_chat_health())
        self.results.append(self.test_chat_docs())
        self.results.append(self.test_chat_query())
        self.results.append(self.test_chat_query_stream())
        
        # 统计结果
        total_time = (time.time() - start_time) * 1000
        passed = sum(1 for r in self.results if r.status == "pass")
        failed = sum(1 for r in self.results if r.status == "fail")
        skipped = sum(1 for r in self.results if r.status == "skip")
        
        report = TestReport(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_tests=len(self.results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            total_time_ms=round(total_time, 2),
            results=self.results
        )
        
        return report
    
    def print_report(self, report: TestReport):
        """打印测试报告"""
        print("\n" + "="*80)
        print("📊 API 测试报告")
        print("="*80)
        print(f"时间：{report.timestamp}")
        print(f"总测试数：{report.total_tests}")
        print(f"✅ 通过：{report.passed}")
        print(f"❌ 失败：{report.failed}")
        print(f"⚠️  跳过：{report.skipped}")
        print(f"总耗时：{report.total_time_ms:.2f}ms")
        print("="*80)
        
        # 详细结果
        print("\n📋 详细结果:")
        print("-"*80)
        
        for result in report.results:
            icon = "✅" if result.status == "pass" else ("❌" if result.status == "fail" else "⚠️")
            print(f"{icon} {result.name}")
            print(f"   端点：{result.method} {result.endpoint}")
            print(f"   状态码：{result.status_code}")
            print(f"   响应时间：{result.response_time_ms:.2f}ms")
            if result.error:
                print(f"   错误：{result.error}")
            print()
        
        # 性能统计
        print("-"*80)
        print("📈 性能统计:")
        response_times = [r.response_time_ms for r in report.results if r.status == "pass"]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            print(f"   平均响应时间：{avg_time:.2f}ms")
            print(f"   最大响应时间：{max_time:.2f}ms")
            print(f"   最小响应时间：{min_time:.2f}ms")
        
        print("="*80)
    
    def save_report(self, report: TestReport, output_file: str):
        """保存测试报告"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        report_data = {
            "timestamp": report.timestamp,
            "summary": {
                "total_tests": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
                "total_time_ms": report.total_time_ms
            },
            "results": [asdict(r) for r in report.results]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 报告已保存：{output_file}")


def main():
    """主函数"""
    suite = APITestSuite()
    
    # 运行所有测试
    report = suite.run_all_tests()
    
    # 打印报告
    suite.print_report(report)
    
    # 保存报告
    output_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'api_test_report.json')
    suite.save_report(report, output_file)
    
    # 返回退出码
    if report.failed > 0:
        exit(1)
    exit(0)


if __name__ == "__main__":
    main()
