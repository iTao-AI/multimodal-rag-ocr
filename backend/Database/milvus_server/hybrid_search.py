"""
混合检索服务 - 结合向量检索和 BM25 关键词检索
从原始 Multimodal_RAG 项目适配

原理:
1. Milvus 向量检索召回 Top-50 候选
2. BM25 对这 50 个候选进行关键词匹配打分
3. 分数归一化后加权融合 (vector_weight * vector_score + bm25_weight * bm25_score)
4. 按融合分数排序返回 Top-10

失败时降级到原始向量排序，不影响现有链路。
"""
import logging
from typing import List, Dict, Any

import jieba

logger = logging.getLogger(__name__)


def rrf_fusion(vector_results: list, bm25_results: list, k: int = 60) -> list:
    """
    RRF 倒数排名融合: score = sum(1 / (k + rank))
    比加权平均更稳定，不依赖分数绝对值
    """
    def get_doc_id(doc):
        return doc.get('id') or doc.get('chunk_id') or ''

    scores = {}
    doc_map = {}

    for rank, doc in enumerate(vector_results):
        doc_id = get_doc_id(doc)
        if doc_id:
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
            doc_map[doc_id] = doc

    for rank, doc in enumerate(bm25_results):
        doc_id = get_doc_id(doc)
        if doc_id:
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
            doc_map[doc_id] = doc

    sorted_ids = sorted(scores.keys(), key=lambda x: -scores[x])
    results = []
    for doc_id in sorted_ids:
        doc = doc_map[doc_id].copy()
        doc['score'] = scores[doc_id]
        results.append(doc)
    return results


def apply_trust_boost(documents: list, verified_ids: set = None) -> list:
    """对已验证文档进行 1.5x 分数提升"""
    if not verified_ids:
        return documents
    TRUST_BOOST = 1.5
    for doc in documents:
        doc_id = doc.get('id') or doc.get('chunk_id') or ''
        if doc_id in verified_ids:
            doc['score'] = doc.get('score', 0) * TRUST_BOOST
            doc['is_verified'] = True
    return documents


# 中文停用词
CHINESE_STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
    "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
    "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
}


def _tokenize_chinese(text: str) -> List[str]:
    """中文分词，去除停用词"""
    words = jieba.lcut(text.lower())
    return [w for w in words if w not in CHINESE_STOPWORDS and len(w.strip()) > 0]


def _normalize_scores(scores: List[float]) -> List[float]:
    """归一化分数到 0-1 范围"""
    if not scores:
        return scores
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [0.5] * len(scores)
    return [(s - min_score) / (max_score - min_score) for s in scores]


def hybrid_rerank(
    documents: List[Dict[str, Any]],
    query: str,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
    final_top_k: int = 10,
    use_rrf: bool = True,
    vector_results: List[Dict[str, Any]] = None,
    bm25_results: List[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    对 Milvus 向量检索结果进行 BM25 混合重排

    Args:
        documents: Milvus 返回的候选文档列表（已含 vector_score/score）
        query: 查询文本
        vector_weight: 向量检索权重
        bm25_weight: BM25 关键词权重
        final_top_k: 最终返回数量
        use_rrf: 是否使用 RRF 倒数排名融合（默认 True，比加权平均更稳定）
        vector_results: RRF 模式下的向量检索结果（可选）
        bm25_results: RRF 模式下的 BM25 检索结果（可选）

    Returns:
        重排后的文档列表
    """
    if not documents or len(documents) <= 1:
        return documents

    # RRF 融合模式
    if use_rrf and vector_results and bm25_results:
        try:
            fused = rrf_fusion(vector_results, bm25_results)
            return fused[:final_top_k]
        except Exception as e:
            logger.warning(f"RRF 融合失败，降级到加权平均: {e}")
            # 降级到下面的加权平均逻辑

    try:
        from rank_bm25 import BM25Okapi

        # 提取文本用于 BM25
        corpus_texts = [doc.get("chunk_text", "") for doc in documents]
        corpus_tokens = [_tokenize_chinese(t) for t in corpus_texts]
        query_tokens = _tokenize_chinese(query)

        if not query_tokens or all(len(t) == 0 for t in corpus_tokens):
            return documents

        # BM25 打分
        bm25 = BM25Okapi(corpus_tokens)
        bm25_scores = bm25.get_scores(query_tokens)
        if hasattr(bm25_scores, "tolist"):
            bm25_scores = bm25_scores.tolist()
        else:
            bm25_scores = list(bm25_scores)

        # 向量分数（原始 score 字段）
        vector_scores = [doc.get("score", 0.0) for doc in documents]

        # 归一化
        vector_scores_norm = _normalize_scores(vector_scores)
        bm25_scores_norm = _normalize_scores(bm25_scores)

        # 加权融合
        scored = []
        for i, doc in enumerate(documents):
            hybrid_score = vector_weight * vector_scores_norm[i] + bm25_weight * bm25_scores_norm[i]
            doc = doc.copy()
            doc["retrieval_score"] = doc.get("score", 0.0)
            doc["bm25_score"] = bm25_scores[i]
            doc["score"] = hybrid_score
            scored.append(doc)

        # 排序取 Top-K
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:final_top_k]

    except ImportError:
        logger.warning("rank-bm25 未安装，跳过混合检索")
        return documents

    except Exception as e:
        logger.error(f"BM25 混合检索失败，降级到原始排序: {e}")
        return documents
