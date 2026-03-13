# Multimodal RAG 后端测试指南

> 📚 完整的测试文档和示例代码

---

## 📋 目录结构

```
backend/
├── tests/
│   ├── conftest.py                    # Pytest 配置和夹具
│   ├── api_test_suite.py              # API 自动化测试套件
│   ├── performance_test.py            # 性能压力测试
│   ├── coverage_report.py             # 覆盖率报告生成
│   ├── test_pdf_extraction.py         # PDF 服务测试
│   ├── test_chunker.py                # 文本切分测试
│   ├── test_milvus_api.py             # Milvus 服务测试
│   ├── test_chat_service.py           # 对话服务测试
│   ├── test_benchmark.py              # 性能基准测试
│   └── multimodal_rag_postman...      # Postman 集合
├── logs/
│   ├── api_test_report.json           # API 测试报告
│   ├── coverage.json                  # 覆盖率数据
│   └── htmlcov/                       # HTML 覆盖率报告
├── TEST_REPORT.md                     # 测试报告
├── COVERAGE_REPORT.md                 # 覆盖率报告
├── TESTING_GUIDE.md                   # 测试指南 (本文档)
└── requirements-optimized.txt         # 测试依赖
```

---

## 🚀 快速开始

### 1. 安装测试依赖

```bash
cd ~/projects/demo/Multimodal_RAG/backend

# 安装 pytest 和覆盖率工具
pip install pytest pytest-cov pytest-benchmark requests aiohttp

# 或安装所有优化依赖
pip install -r requirements-optimized.txt
```

### 2. 启动服务

```bash
# 确保所有服务运行中
./start_all_services.sh

# 检查服务状态
./status_services.sh
```

### 3. 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_pdf_extraction.py -v

# 运行特定测试类
python -m pytest tests/test_pdf_extraction.py::TestPDFExtractionHealth -v

# 运行特定测试函数
python -m pytest tests/test_pdf_extraction.py::TestPDFExtractionHealth::test_health_endpoint -v
```

---

## 📊 测试类型

### 1. API 功能测试

**文件**: `tests/api_test_suite.py`

测试所有服务的 API 端点功能。

```bash
python tests/api_test_suite.py
```

**输出**:
- 控制台详细结果
- JSON 报告：`logs/api_test_report.json`
- Markdown 报告：`TEST_REPORT.md`

### 2. Pytest 单元测试

**文件**: `tests/test_*.py`

使用 pytest 框架的单元测试。

```bash
# 运行所有单元测试
pytest tests/ -v

# 运行特定服务测试
pytest tests/test_pdf_extraction.py -v
pytest tests/test_chunker.py -v
pytest tests/test_milvus_api.py -v
pytest tests/test_chat_service.py -v
```

### 3. 性能基准测试

**文件**: `tests/test_benchmark.py`

使用 pytest-benchmark 进行性能基准测试。

```bash
# 安装 benchmark 插件
pip install pytest-benchmark

# 运行基准测试
pytest tests/test_benchmark.py --benchmark-only

# 对比基准测试
pytest tests/test_benchmark.py --benchmark-compare
```

**输出示例**:
```
----------------------------- benchmark: 8 tests -----------------------------
Name (time in ms)              Min       Max      Mean   StdDev    Median
--------------------------------------------------------------------------
test_health_endpoint_latency  1.2345    2.3456   1.5678  0.1234   1.5432
test_chunk_small_text        12.3456   23.4567  15.6789  1.2345  15.4321
--------------------------------------------------------------------------
```

### 4. 压力测试

**文件**: `tests/performance_test.py`

模拟多用户并发访问。

```bash
python tests/performance_test.py
```

**测试内容**:
- 并发用户测试 (1/5/10/20 用户)
- QPS 测量
- 延迟统计 (P50/P95/P99)
- 错误率统计

### 5. 测试覆盖率

**文件**: `tests/coverage_report.py`

生成测试覆盖率报告。

```bash
# 运行覆盖率测试
python tests/coverage_report.py

# 或手动运行
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
```

**输出**:
- 终端覆盖率摘要
- HTML 报告：`logs/htmlcov/index.html`
- JSON 数据：`logs/coverage.json`
- Markdown 报告：`COVERAGE_REPORT.md`

---

## 🔧 测试配置

### Pytest 配置 (conftest.py)

```python
# 服务 URL 夹具
@pytest.fixture
def pdf_service_url(services_config: Dict) -> str:
    return f"{services_config['pdf_extraction']['host']}:{services_config['pdf_extraction']['port']}"

# 示例数据夹具
@pytest.fixture
def sample_markdown_text() -> str:
    return "# 标题\n\n这是内容。"

# HTTP 会话夹具
@pytest.fixture
def http_session() -> Generator[requests.Session, None, None]:
    session = requests.Session()
    yield session
    session.close()
```

### 环境变量配置

```bash
# 服务地址 (可选，默认 localhost)
export PDF_HOST=http://localhost
export PDF_PORT=8006
export CHUNKER_HOST=http://localhost
export CHUNKER_PORT=8001
export MILVUS_HOST=http://localhost
export MILVUS_PORT=8000
export CHAT_HOST=http://localhost
export CHAT_PORT=8501

# API 密钥
export DASHSCOPE_API_KEY=sk-your-api-key
```

---

## 📈 测试报告

### API 测试报告

查看 `TEST_REPORT.md`:

```markdown
# 测试摘要
- 总测试数：17
- 通过：7 (41%)
- 失败：5 (29%)
- 跳过：5 (29%)

# 性能统计
- 平均响应时间：2.40ms
- 最快响应：0.75ms
- 最慢响应：56.29ms
```

### 覆盖率报告

查看 `COVERAGE_REPORT.md`:

```markdown
# 覆盖率摘要
- 总行数：10,000
- 已覆盖：6,000
- 覆盖率：60.00%

# 文件覆盖率详情
| 文件 | 覆盖率 | 已覆盖 | 总行数 |
|------|--------|--------|--------|
| milvus_api.py | 75.5% | 1500 | 2000 |
| kb_chat.py | 65.2% | 1200 | 1800 |
```

---

## 🎯 测试最佳实践

### 1. 测试命名规范

```python
def test_<功能>_<条件>_<预期结果>():
    # 示例
    def test_health_endpoint_returns_200():
    def test_search_with_invalid_collection_returns_404():
    def test_chunk_large_text_completes_within_5s():
```

### 2. 测试夹具使用

```python
# 使用预定义的夹具
def test_api_with_fixture(
    pdf_service_url: str,
    http_session: requests.Session,
    sample_markdown_text: str
):
    response = http_session.post(
        f"{pdf_service_url}/chunk",
        json={"markdown": sample_markdown_text}
    )
    assert response.status_code == 200
```

### 3. 断言最佳实践

```python
# ✅ 好的断言
assert response.status_code == 200
assert "key" in response.json()
assert len(results) > 0
assert response.elapsed.total_seconds() < 1.0

# ❌ 避免的断言
assert response  # 太模糊
assert response.json() is not None  # 不够具体
```

### 4. 性能测试注意事项

```python
# 设置合理的超时
response = requests.get(url, timeout=30)

# 测量响应时间
start = time.time()
response = requests.get(url)
latency = (time.time() - start) * 1000
assert latency < 100  # < 100ms

# 并发测试使用会话池
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(make_request) for _ in range(10)]
```

---

## 🐛 常见问题

### Q: 测试失败 "Connection refused"

**A**: 确保服务已启动
```bash
./status_services.sh
./start_all_services.sh
```

### Q: 测试超时

**A**: 增加超时时间或检查服务性能
```python
response = requests.get(url, timeout=60)  # 增加到 60s
```

### Q: 覆盖率显示 0%

**A**: 确保测试实际运行了代码
```bash
# 检查测试是否真的调用了被测代码
pytest tests/ -v -s
```

### Q: 内存不足

**A**: 减少并发用户数或批次大小
```python
CONCURRENT_USERS = [1, 5]  # 减少到 [1, 5, 10, 20]
```

---

## 📚 参考资源

- [Pytest 文档](https://docs.pytest.org/)
- [pytest-cov 文档](https://pytest-cov.readthedocs.io/)
- [pytest-benchmark 文档](https://pytest-benchmark.readthedocs.io/)
- [Requests 文档](https://docs.python-requests.org/)

---

_最后更新：2026-03-11_
