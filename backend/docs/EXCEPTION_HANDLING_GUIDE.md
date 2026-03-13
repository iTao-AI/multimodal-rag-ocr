# 全局异常处理使用指南

> 📚 统一错误响应格式和异常处理规范

---

## 📋 概述

本项目使用统一的全局异常处理机制，确保所有服务返回一致的错误响应格式，便于前端处理和日志追踪。

---

## 🎯 核心特性

1. **统一错误响应格式** - 所有错误使用相同的 JSON 结构
2. **Request ID 追踪** - 每个请求有唯一 ID，便于日志追踪
3. **完整的异常日志** - 记录异常堆栈和上下文
4. **性能监控** - 自动记录请求处理时间

---

## 📦 错误响应格式

### 标准格式

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息",
    "request_id": "uuid-xxxx-xxxx-xxxx",
    "status_code": 500,
    "details": {},
    "timestamp": "2026-03-12T15:00:00.000000",
    "path": "/api/endpoint"
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 错误代码（大写英文） |
| `message` | string | 用户友好的错误描述 |
| `request_id` | string | 请求唯一标识 |
| `status_code` | integer | HTTP 状态码 |
| `details` | object | 详细错误信息 |
| `timestamp` | string | ISO8601 时间戳 |
| `path` | string | 请求路径 |

---

## 🔧 使用方式

### 1. 在服务中集成

```python
from fastapi import FastAPI
from utils.exceptions import setup_global_exception_handlers, RequestIDMiddleware, PerformanceLoggingMiddleware

app = FastAPI(title="My Service")

# 添加中间件
app.add_middleware(RequestIDMiddleware)
app.add_middleware(PerformanceLoggingMiddleware)

# 设置全局异常处理器
setup_global_exception_handlers(app, service_name="my-service")
```

### 2. 使用快捷创建函数

```python
from utils.exceptions import create_app_with_exception_handling

app = create_app_with_exception_handling(service_name="my-service")
```

### 3. 抛出自定义异常

```python
from utils.exceptions import (
    ValidationException,
    NotFoundException,
    ExternalServiceException,
    ServiceUnavailableException
)

@app.post("/users/{user_id}")
async def get_user(user_id: str):
    user = await db.get_user(user_id)
    
    if not user:
        raise NotFoundException(resource="用户")
    
    if not user.is_active:
        raise ValidationException(
            message="用户已禁用",
            details={"user_id": user_id}
        )
    
    return user
```

---

## 📝 预定义异常类

### AppException (基础异常)

```python
raise AppException(
    message="错误消息",
    code="CUSTOM_ERROR",
    status_code=500,
    details={"key": "value"}
)
```

### ValidationException (验证异常) - 400

```python
raise ValidationException(
    message="数据验证失败",
    details={"field": "email", "reason": "格式不正确"}
)
```

### NotFoundException (不存在异常) - 404

```python
raise NotFoundException(
    resource="知识库",  # 输出："知识库不存在"
    details={"id": "kb_123"}
)
```

### AuthenticationException (认证异常) - 401

```python
raise AuthenticationException(
    message="Token 已过期",
    details={"expired_at": "2026-03-12T15:00:00"}
)
```

### AuthorizationException (授权异常) - 403

```python
raise AuthorizationException(
    message="无权访问此资源",
    details={"required_role": "admin"}
)
```

### ServiceUnavailableException (服务不可用) - 503

```python
raise ServiceUnavailableException(
    message="Milvus 服务暂时不可用",
    details={"retry_after": 30}
)
```

### ExternalServiceException (外部服务异常) - 502

```python
raise ExternalServiceException(
    service="LLM",
    message="API 调用超时",
    details={"timeout": 30}
)
```

---

## 📊 错误代码表

| 错误代码 | HTTP 状态码 | 说明 |
|---------|-----------|------|
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `VALIDATION_ERROR` | 400/422 | 数据验证失败 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `UNAUTHORIZED` | 401 | 未授权 |
| `FORBIDDEN` | 403 | 禁止访问 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |
| `BAD_GATEWAY` | 502 | 网关错误 |
| `TOO_MANY_REQUESTS` | 429 | 请求过多 |
| `EXTERNAL_SERVICE_ERROR` | 502 | 外部服务错误 |
| `APP_ERROR` | 500 | 应用错误 |

---

## 🔍 日志追踪

### 请求日志格式

```
2026-03-12 15:00:00 - api - INFO - [req-1234-5678] POST /api/chat - 200 - 45.23ms
```

### 异常日志格式

```
2026-03-12 15:00:00 - api - ERROR - 全局未捕获异常 [ID:req-1234-5678]: ValueError - 无效的值
Traceback (most recent call last):
  File "/path/to/app.py", line 10, in handler
    raise ValueError("无效的值")
ValueError: 无效的值
```

### 日志字段

| 字段 | 说明 |
|------|------|
| 时间戳 | 日志记录时间 |
| 服务名 | 日志来源服务 |
| 级别 | INFO/WARNING/ERROR |
| request_id | 请求唯一标识 |
| 方法 | HTTP 方法 |
| 路径 | 请求路径 |
| 状态码 | HTTP 状态码 |
| 处理时间 | 请求处理耗时 (ms) |

---

## 📁 文件结构

```
backend/
├── utils/
│   ├── __init__.py           # 模块导出
│   └── exceptions.py         # 异常处理核心
├── docs/
│   └── EXCEPTION_HANDLING_GUIDE.md  # 本文档
└── [各服务]/
    ├── main.py               # 服务入口
    └── ...
```

---

## 🧪 测试示例

### 测试异常响应

```python
import requests

# 测试 404
response = requests.get("http://localhost:8000/nonexistent")
assert response.status_code == 404
assert "error" in response.json()
assert response.json()["error"]["code"] == "NOT_FOUND"
assert "request_id" in response.json()["error"]

# 测试 500
response = requests.post("http://localhost:8000/api/error")
assert response.status_code == 500
assert response.json()["error"]["code"] == "INTERNAL_ERROR"

# 测试 request_id 传递
headers = {"X-Request-ID": "my-custom-id"}
response = requests.get("http://localhost:8000/health", headers=headers)
assert response.headers.get("X-Request-ID") == "my-custom-id"
```

---

## ⚠️ 注意事项

### 1. 不要捕获所有异常

```python
# ❌ 错误做法
try:
    do_something()
except Exception:
    pass  # 吞掉异常

# ✅ 正确做法
try:
    do_something()
except SpecificError as e:
    logger.warning(f"特定错误：{e}")
    raise  # 重新抛出或转换为自定义异常
```

### 2. 提供有意义的错误信息

```python
# ❌ 模糊的错误
raise AppException(message="出错了")

# ✅ 清晰的错误
raise AppException(
    message="PDF 文件解析失败：文件已损坏",
    code="PDF_PARSE_ERROR",
    details={"filename": "test.pdf", "size": "10MB"}
)
```

### 3. 始终传递 request_id

```python
# ✅ 在日志中包含 request_id
logger.info(f"[{request_id}] 处理完成")

# ✅ 使用 extra 参数
logger.info("处理完成", extra={"request_id": request_id})
```

---

## 📈 监控集成

### Prometheus 指标

```python
from prometheus_client import Counter, Histogram

# 错误计数器
error_counter = Counter(
    'app_errors_total',
    'Total errors',
    ['error_code', 'endpoint']
)

# 在异常处理器中增加
@app.exception_handler(Exception)
async def handler(request, exc):
    error_counter.labels(
        error_code="INTERNAL_ERROR",
        endpoint=request.url.path
    ).inc()
```

### 告警配置

```yaml
# Prometheus 告警规则
groups:
  - name: exceptions
    rules:
      - alert: HighErrorRate
        expr: rate(app_errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "高错误率"
          description: "错误率超过 10%"
```

---

## 🔧 故障排查

### 问题 1: 请求 ID 不一致

**症状**: 日志中的 request_id 与响应头不一致

**解决**:
```python
# 确保在中间件中设置
request.state.request_id = request_id
response.headers["X-Request-ID"] = request_id
```

### 问题 2: 异常未记录

**症状**: 500 错误但没有日志

**解决**:
```python
# 检查 logger 配置
logging.basicConfig(level=logging.INFO)

# 确保 exc_info=True
logger.error("错误", exc_info=True)
```

### 问题 3: 自定义异常未生效

**症状**: 抛出自定义异常但返回 500

**解决**:
```python
# 确保异常处理器注册顺序正确
# AppException 处理器应该在 Exception 处理器之前注册
setup_global_exception_handlers(app, service_name)
```

---

_文档版本：1.0.0_  
_最后更新：2026-03-12_
