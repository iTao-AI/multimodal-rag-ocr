# 向量检索优化实施文档

> 📅 实施日期：2026-03-05  
> 🎯 目标：使用阿里云百炼全套云服务，实现混合检索、查询改写、重排序和缓存

---

## ✅ 已完成

### 1. 配置文件更新

**文件**: `backend/.env`

**变更**:
- ✅ 嵌入模型：`text-embedding-v4` → `text-embedding-v3`
- ✅ 添加重排序配置（Qwen3.5-Plus）
- ✅ 添加混合检索权重配置
- ✅ 添加 Redis 缓存配置

```env
EMBEDDING_MODEL_NAME=text-embedding-v3
EMBEDDING_DIMENSION=1536

RERANK_MODEL_NAME=qwen3.5-plus
RERANK_API_KEY=sk-xxx

HYBRID_SEARCH_TOP_K=50
FINAL_TOP_K=10
BM25_WEIGHT=0.3
VECTOR_WEIGHT=0.7

CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
```

---

### 2. 新增服务模块

#### 2.1 混合检索服务
**文件**: `knowledge-base-api/src/services/hybrid_search_service.py`

**功能**:
- 向量检索 + BM25 关键词检索融合
- 中文分词（jieba）
- 分数归一化
- 加权排序

**依赖**:
```bash
pip install rank-bm25 jieba scikit-learn
```

---

#### 2.2 查询改写服务
**文件**: `knowledge-base-api/src/services/query_rewrite_service.py`

**功能**:
- 查询变体生成（Qwen3.5-Plus）
- 同义词扩展
- HyDE 假设性答案生成

**API**:
```python
rewrite_service = QueryRewriteService()
variations = rewrite_service.rewrite_query("RAG 是什么", num_variations=3)
expanded = rewrite_service.expand_query("RAG 优化方法", num_keywords=5)
hypothetical = rewrite_service.generate_hypothetical_answer("如何优化检索")
```

---

#### 2.3 重排序服务
**文件**: `knowledge-base-api/src/services/rerank_service.py`

**功能**:
- LLM-based 文档重排序
- 相关性打分
- 批量重排

**API**:
```python
rerank_service = RerankService()
reranked = rerank_service.rerank(
    query="RAG 技术",
    documents=doc_list,
    top_n=10
)
```

---

#### 2.4 缓存管理服务
**文件**: `knowledge-base-api/src/utils/cache_manager.py`

**功能**:
- Redis 缓存查询结果
- 嵌入向量缓存
- TTL 自动过期
- 统计信息

**依赖**:
```bash
pip install redis
```

**API**:
```python
cache = get_cache_manager()
cache.set_query_result("查询", results)
results = cache.get_query_result("查询")
```

---

#### 2.5 百炼配置中心
**文件**: `knowledge-base-api/src/core/bailian_config.py`

**功能**:
- 统一管理所有百炼模型配置
- 请求头生成
- 配置验证

---

### 3. 新增 API 端点

**文件**: `knowledge-base-api/src/api/v1/endpoints/search_enhanced.py`

**端点**:
- `POST /search` - 增强搜索接口
- `GET /search/stats` - 统计信息

**请求示例**:
```json
{
  "query": "RAG 检索优化方法",
  "top_k": 10,
  "use_rewrite": true,
  "use_rerank": true,
  "use_cache": true
}
```

**响应示例**:
```json
{
  "results": [...],
  "query_used": "RAG 检索优化方法",
  "rewrite_applied": false,
  "rerank_applied": true,
  "cache_hit": false,
  "total_results": 10
}
```

---

### 4. 依赖更新

**文件**: `backend/requirements.txt`

**新增依赖**:
```txt
rank-bm25==0.2.2
jieba==0.42.1
scikit-learn==1.3.2
redis==5.0.1
python-dotenv==1.0.0
```

---

## 🚀 部署步骤

### 1. 安装依赖

```bash
cd /home/ai/.openclaw/workspace/projects/Multimodal_RAG/backend

# 激活 Conda 环境
source ~/miniconda3/etc/profile.d/conda.sh && conda activate vlm_rag

# 安装新依赖
pip install rank-bm25==0.2.2 jieba==0.42.1 scikit-learn==1.3.2 redis==5.0.1 python-dotenv==1.0.0
```

### 2. 启动 Redis（可选，用于缓存）

```bash
# 检查 Redis 是否已安装
redis-cli ping

# 如果未安装，使用 Docker 启动
docker run -d --name redis -p 6379:6379 redis:latest
```

### 3. 配置验证

```bash
cd knowledge-base-api
python -c "from src.core.bailian_config import config; print(config.to_dict())"
```

### 4. 重启服务

```bash
cd /home/ai/.openclaw/workspace/projects/Multimodal_RAG/backend
bash stop_all_services.sh
bash start_all_services.sh
```

---

## 📊 性能预期

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 检索准确率@10 | ~70% | ~85% | +15% |
| 查询延迟 P95 | 150ms | 200ms | -50ms (可接受) |
| 缓存命中率 | 0% | 60%+ | - |
| 长尾查询效果 | 一般 | 良好 | 显著改善 |

---

## 💰 成本估算

按 1000 次查询计算：

| 项目 | 单价 | 用量 | 成本 |
|------|------|------|------|
| text-embedding-v3 | 0.002 元/千 tokens | 2000 tokens | 0.004 元 |
| Qwen3.5-Plus(改写) | 0.004 元/千 tokens | 500 tokens | 0.002 元 |
| Qwen3.5-Plus(重排序) | 0.004 元/千 tokens | 1000 tokens | 0.004 元 |
| **合计** | - | - | **~0.01 元/次查询** |

**1000 次查询成本**: ~10 元  
**日均 100 次查询月成本**: ~30 元

---

## 🔍 监控指标

### 关键指标
- 检索延迟（P50, P95, P99）
- 缓存命中率
- 重排序覆盖率
- API 调用成功率
- 单次查询成本

### 日志位置
```
backend/logs/search_*.log
backend/logs/rerank_*.log
backend/logs/cache_*.log
```

---

## ⚠️ 注意事项

### 1. Redis 缓存
- 缓存不是必需的，如果 Redis 不可用会自动降级
- 缓存 TTL 默认 1 小时，可根据需求调整
- 定期清理过期缓存

### 2. 重排序成本
- 重排序会调用 Qwen3.5-Plus，产生额外成本
- 可在请求中设置 `use_rerank=false` 关闭
- 建议对 top50 重排序，而不是全部结果

### 3. 查询改写
- 改写可能增加延迟（~200ms）
- 对简单查询可能不必要
- 可设置阈值，仅对短查询启用

---

## 🧪 测试建议

### 1. 单元测试
```bash
cd knowledge-base-api
pytest tests/test_hybrid_search.py
pytest tests/test_query_rewrite.py
pytest tests/test_rerank.py
```

### 2. 集成测试
```bash
# 测试完整搜索流程
curl -X POST "http://localhost:8001/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG 优化", "top_k": 10}'
```

### 3. A/B 测试
- 对比开启/关闭重排序的效果
- 对比不同权重配置（BM25 vs 向量）
- 对比缓存命中率

---

## 📝 后续优化

### Phase 2（可选）
- [ ] 添加查询日志分析
- [ ] 实现查询建议（autocomplete）
- [ ] 多路召回（标题、摘要、全文）
- [ ] 用户反馈收集（点赞/点踩）

### Phase 3（可选）
- [ ] 检索效果可视化面板
- [ ] A/B 测试框架
- [ ] 自动参数调优
- [ ] 查询意图识别

---

## 📞 问题排查

### 常见问题

**Q1: Redis 连接失败**
```bash
# 检查 Redis 是否运行
redis-cli ping

# 检查防火墙
sudo ufw status

# 查看日志
tail -f backend/logs/cache.log
```

**Q2: 百炼 API 调用失败**
```bash
# 检查 API Key 是否正确
echo $EMBEDDING_API_KEY

# 测试网络连通性
curl -I https://dashscope.aliyuncs.com

# 查看配额
# 登录阿里云百炼控制台
```

**Q3: 中文分词效果差**
```python
# 自定义词典
import jieba
jieba.add_word("RAG")
jieba.add_word("向量检索")
```

---

## 📚 参考资料

- [阿里云百炼文档](https://help.aliyun.com/zh/model-studio/)
- [text-embedding-v3 API](https://help.aliyun.com/zh/model-studio/developer-reference/text-embedding)
- [BM25 算法原理](https://en.wikipedia.org/wiki/Okapi_BM25)
- [HyDE 论文](https://arxiv.org/abs/2212.10496)

---

**实施完成时间**: 2026-03-05  
**实施者**: Sebastian 🎩
