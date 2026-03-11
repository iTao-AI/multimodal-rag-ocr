# 故障排查指南

**版本**: v1.0  
**最后更新**: 2026-03-11

---

## 🔍 快速诊断流程

```
故障发生
    ↓
1. 检查服务状态 (./status_services.sh)
    ↓
2. 查看错误日志 (tail -f logs/*.log)
    ↓
3. 识别错误类型
    ↓
4. 查找对应解决方案
    ↓
5. 执行修复
    ↓
6. 验证修复结果
```

---

## 📋 常见问题清单

### 服务启动类

#### 1. 服务无法启动

**症状**: 进程启动后立即退出

**排查步骤**:
```bash
# 1. 查看日志
tail -100 logs/app.log

# 2. 检查端口占用
lsof -i :8000

# 3. 检查依赖
pip list | grep fastapi

# 4. 检查配置
cat .env | grep API_KEY
```

**常见原因**:
- [ ] 端口被占用
- [ ] 依赖缺失
- [ ] 配置错误
- [ ] 权限不足

**解决方案**:
```bash
# 释放端口
kill -9 $(lsof -t -i:8000)

# 重新安装依赖
pip install -r requirements-optimized.txt --force-reinstall

# 检查环境变量
export API_KEY=your_key_here
```

---

#### 2. Milvus 连接失败

**症状**: `pymilvus.exceptions.ConnectionError`

**排查步骤**:
```bash
# 1. 检查 Milvus 状态
docker ps | grep milvus

# 2. 检查网络
telnet localhost 19530

# 3. 查看 Milvus 日志
docker logs milvus-standalone
```

**解决方案**:
```bash
# 重启 Milvus
docker compose restart milvus

# 或重新部署
docker compose up -d milvus

# 检查配置
cat .env | grep MILVUS
```

---

#### 3. 内存不足

**症状**: OOM Killer 杀死进程

**排查步骤**:
```bash
# 检查内存使用
free -h
ps aux | grep python | awk '{print $4}'

# 查看系统日志
dmesg | grep -i "killed process"
```

**解决方案**:
```bash
# 1. 增加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2. 限制服务内存
# 在 docker-compose.yml 中添加
deploy:
  resources:
    limits:
      memory: 2G
```

---

### PDF 处理类

#### 4. PDF 上传失败

**症状**: 上传返回错误 "Unsupported file format"

**排查步骤**:
```bash
# 1. 检查文件类型
file test.pdf

# 2. 检查文件大小
ls -lh test.pdf

# 3. 查看上传日志
tail -f logs/pdf_extraction.log
```

**常见原因**:
- [ ] 文件损坏
- [ ] 文件过大 (> 50MB)
- [ ] 非 PDF 格式
- [ ] 加密 PDF

**解决方案**:
```bash
# 1. 修复 PDF
gs -o fixed.pdf -sDEVICE=pdfwrite original.pdf

# 2. 压缩 PDF
gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook input.pdf output.pdf

# 3. 解密 PDF
qpdf --decrypt input.pdf output.pdf
```

---

#### 5. PDF 解析超时

**症状**: 上传后长时间无响应

**排查步骤**:
```bash
# 查看处理时间
grep "processing time" logs/pdf_extraction.log

# 检查 CPU 使用
top -pid $(pgrep -f pdf_extraction)
```

**解决方案**:
```python
# 修改 uvicorn 配置，延长超时时间
uvicorn.run(
    "main:app",
    timeout_keep_alive=600,  # 10 分钟
)
```

---

### 向量检索类

#### 6. 检索结果为空

**症状**: 搜索返回 0 条结果

**排查步骤**:
```bash
# 1. 检查 Milvus 连接
curl http://localhost:8000/health

# 2. 检查集合是否存在
python -c "from pymilvus import connections; connections.connect(); from pymilvus import utility; print(utility.list_collections())"

# 3. 检查数据量
# 查询数据库中文档数量
```

**解决方案**:
```bash
# 1. 重新创建集合
python scripts/recreate_collection.py

# 2. 重新上传文档
curl -X POST http://localhost:8000/api/v1/documents -F "file=@test.pdf"

# 3. 检查嵌入模型
curl -X POST https://dashscope.aliyuncs.com/api/v1/embeddings
```

---

#### 7. 检索速度慢

**症状**: 搜索响应时间 > 1 秒

**排查步骤**:
```bash
# 1. 检查 Milvus 性能
docker stats milvus-standalone

# 2. 检查索引
python -c "from pymilvus import connections, Collection; connections.connect(); c = Collection('your_collection'); print(c.index().params)"

# 3. 检查网络延迟
ping localhost
```

**解决方案**:
```python
# 优化索引参数
index_params = {
    "metric_type": "IP",
    "index_type": "HNSW",
    "params": {"M": 8, "efConstruction": 200}
}

# 添加缓存
from cache import get_search_cache, set_search_cache
```

---

### 对话问答类

#### 8. 对话无响应

**症状**: 发送消息后长时间无回复

**排查步骤**:
```bash
# 1. 检查 LLM API
curl -X POST https://dashscope.aliyuncs.com/api/v1/chat

# 2. 检查 API Key
cat .env | grep API_KEY

# 3. 查看对话日志
tail -f logs/chat.log
```

**解决方案**:
```bash
# 1. 更新 API Key
export API_KEY=sk-new-key

# 2. 检查配额
# 登录阿里云百炼控制台查看

# 3. 切换模型
# 在 .env 中修改 MODEL_NAME
```

---

#### 9. 答案不准确

**症状**: 回答与问题无关

**排查步骤**:
```bash
# 1. 检查检索结果
# 查看返回的上下文片段

# 2. 检查 Prompt
cat backend/chat/prompt.py

# 3. 检查温度参数
cat .env | grep TEMPERATURE
```

**解决方案**:
```python
# 调整温度参数
TEMPERATURE = 0.3  # 降低随机性

# 优化 Prompt
SYSTEM_PROMPT = """你是一个专业的助手，请基于以下上下文回答问题：

{context}

问题：{query}
"""
```

---

### 前端类

#### 10. 前端无法连接后端

**症状**: 前端显示 "Network Error"

**排查步骤**:
```bash
# 1. 检查后端服务
curl http://localhost:8000/health

# 2. 检查 CORS 配置
cat backend/knowledge-management/main.py | grep -A 5 CORS

# 3. 查看浏览器控制台
# F12 -> Console
```

**解决方案**:
```python
# 添加前端域名到白名单
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]
```

---

### 数据库类

#### 11. 数据库连接失败

**症状**: SQLAlchemy 连接错误

**排查步骤**:
```bash
# 1. 检查 MySQL 状态
docker ps | grep mysql

# 2. 测试连接
mysql -h localhost -u root -p

# 3. 查看连接字符串
cat .env | grep DATABASE
```

**解决方案**:
```bash
# 重启 MySQL
docker compose restart mysql

# 检查权限
mysql -u root -p -e "GRANT ALL PRIVILEGES ON *.* TO 'rag'@'%'; FLUSH PRIVILEGES;"
```

---

### 性能类

#### 12. 系统响应慢

**症状**: 所有操作都变慢

**排查步骤**:
```bash
# 1. 检查系统负载
uptime
top

# 2. 检查磁盘 I/O
iostat -x 1

# 3. 检查网络
iftop
```

**解决方案**:
```bash
# 1. 清理磁盘空间
df -h
docker system prune -a

# 2. 重启服务
./restart_all_services.sh

# 3. 增加资源限制
# 编辑 docker-compose.yml
```

---

## 🛠️ 诊断工具

### 健康检查脚本

```bash
#!/bin/bash
# health_check.sh

echo "=== 服务健康检查 ==="

# 检查端口
for port in 8000 8001 8006 8501; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "✅ Port $port is OK"
    else
        echo "❌ Port $port is DOWN"
    fi
done

# 检查 Milvus
docker ps | grep milvus

# 检查日志错误
echo "=== 最新错误日志 ==="
grep "ERROR" logs/*.log | tail -10
```

---

### 性能监控脚本

```bash
#!/bin/bash
# monitor.sh

echo "=== 系统资源 ==="
free -h
df -h

echo "=== 服务资源 ==="
ps aux | grep python | awk '{print $2, $3, $4, $11}'

echo "=== 网络连接 ==="
netstat -an | grep ESTABLISHED | wc -l
```

---

## 📞 获取帮助

### 内部资源
- [运维手册](OPERATIONS.md)
- [API 文档](API.md)
- [代码审查](CODE_REVIEW.md)

### 外部资源
- [Milvus 文档](https://milvus.io/docs)
- [FastAPI 文档](https://fastapi.tiangolo.com)
- [LangChain 文档](https://python.langchain.com)

---

## 📝 故障报告模板

```markdown
## 故障报告

**时间**: YYYY-MM-DD HH:mm
**影响范围**: [服务名称/功能]
**严重程度**: P0/P1/P2

### 现象描述
[详细描述故障表现]

### 影响用户
[受影响的用户范围]

### 根本原因
[故障的根本原因]

### 解决方案
[已采取的修复措施]

### 预防措施
[如何避免再次发生]
```

---

**维护者**: dev Agent  
**最后更新**: 2026-03-11
